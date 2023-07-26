import os
import discord
import constants
import cache_races
import environment_variables as env
import roles
import stats_helpers as stats
import image_generators as image_gen
import helpers
from bot_database import BotDatabase, BotDatabaseError
from irslashdata.client import Client as IracingClient
from irslashdata import constants as irConstants
import logging
import asyncio

from datetime import datetime, timezone, timedelta


async def get_race_results(bot: discord.Bot, db: BotDatabase, ir: IracingClient):

    try:
        member_dicts = await db.fetch_member_dicts()
    except BotDatabaseError as e:
        logging.getLogger('respobot.bot').warning(e)

    if member_dicts is None or len(member_dicts) < 1:
        logging.getLogger('respobot.bot').info("No members in the database, skipping race checks.")
        return

    for member_dict in member_dicts:
        if 'iracing_custid' not in member_dict:
            logging.getLogger('respobot.bot').warning(f"Skipping member because member_dict did not contain an iracing_custid key: {member_dict}")
            continue

        iracing_custid = member_dict['iracing_custid']

        logging.getLogger('respobot.bot').info(f"Searching for new races for cust_id: {iracing_custid}")

        if 'last_race_check' in member_dict and (member_dict['last_race_check'] is None or member_dict['last_race_check'] == ''):
            # This person has never had their races cached. Cache them now.
            logging.getLogger('respobot.bot').info(f"Found a new member. Caching races for cust_id: {iracing_custid}")
            await cache_races.cache_races(db, ir, [iracing_custid])
        else:
            on_a_hiatus = False
            # Grab all series races since their previous cached race
            start_high = datetime.now(timezone.utc)
            start_low = datetime.fromisoformat(member_dict['last_race_check'])

            if start_high - start_low > timedelta(days=90):
                start_high = start_low + timedelta(days=90)
                on_a_hiatus = True
            start_low_str = start_low.isoformat().replace('+00:00', 'Z')
            start_high_str = start_high.isoformat().replace('+00:00', 'Z')

            races_list = None

            try:
                races_list = await ir.search_results_new(cust_id=iracing_custid, start_range_begin=start_low_str, start_range_end=start_high_str)
            except ValueError:
                logging.getLogger('respobot.bot').warning(f"search_results_new() for cust_id {iracing_custid} failed due to insufficient information.")
            except Exception as e:
                logging.getLogger('respobot.bot').warning(e)

            try:
                hosted_races_list = await ir.search_hosted_new(cust_id=iracing_custid, start_range_begin=start_low_str, start_range_end=start_high_str)
                races_list += hosted_races_list
            except ValueError:
                logging.getLogger('respobot.bot').warning(f"search_hosted_new() for cust_id {iracing_custid} failed due to insufficient information.")
            except Exception as e:
                logging.getLogger('respobot.bot').warning(e)

            if races_list is None:
                return

            for race in races_list:
                race_found = await db.is_subsession_in_db(race['subsession_id'])

                if race_found is False:
                    new_race = await ir.subsession_data_new(race['subsession_id'])
                    await db.add_subsessions([new_race])
                    if 'host_id' in new_race and 'league_id' in new_race and (new_race['league_id'] is None or new_race['league_id'] < 1):
                        # This is just some random hosted session. Don't report it.
                        continue
                    await process_race_result(bot, db, new_race, embed_type='auto')

            if on_a_hiatus is True:
                await db.set_member_last_race_check(member_dict['iracing_custid'], start_high - timedelta(days=2))


async def process_race_result(bot: discord.Bot, db: BotDatabase, subsession_data: dict, embed_type: str = 'auto'):
    multi_report = False
    role_change_reason = ""
    message_text = ""
    channel = helpers.fetch_channel(bot)

    (current_year, current_quarter, current_racing_week, _, _) = await db.get_current_iracing_week()

    if 'subsession_id' not in subsession_data:
        logging.getLogger('respobot.iracing').warning("iRacing returned subsession data without a subsession_id.")
        return

    member_custid_list = await db.fetch_iracing_cust_ids()
    all_member_dicts = await db.fetch_member_dicts()

    # 1. Find the results dict for the main event
    race_results_list = None

    if 'session_results' not in subsession_data or len(subsession_data['session_results']) < 1:
        logging.getLogger('respobot.iracing').warning(f"iRacing returned data for subsession {subsession_data['subsession_id']} that was missing the session_results list.")
        return

    for results_dict in subsession_data['session_results']:
        if 'simsession_number' in results_dict and results_dict['simsession_number'] == 0:
            if 'simsession_type' in results_dict and results_dict['simsession_type'] != irConstants.SimSessionType.race.value:
                logging.getLogger('respobot.iracing').warning(f"The main event for subsession {subsession_data['subsession_id']} was not a race. Ignoring.")
                return
            if 'results' not in results_dict or len(results_dict['results']) < 1:
                logging.getLogger('respobot.iracing').warning(f"iRacing returned no results list in the session_results for the main event for subsession {subsession_data['subsession_id']}")
                return
            race_results_list = results_dict['results']

    if race_results_list is None:
        logging.getLogger('respobot.iracing').warning(f"No results list found in subsession {subsession_data['subsession_id']}")

    # 2. Generate the list of car numbers containing Respo members
    respo_car_numbers = []

    for result_dict in race_results_list:
        if 'cust_id' in result_dict:
            if 'livery' not in result_dict:
                continue
            if 'car_number' not in result_dict['livery']:
                continue

            if result_dict['cust_id'] in member_custid_list:
                respo_car_numbers.append(result_dict['livery']['car_number'])
        elif 'team_id' in result_dict:
            if 'driver_results' not in result_dict:
                continue
            for driver_result_dict in result_dict['driver_results']:
                if 'cust_id' not in driver_result_dict:
                    continue
                if 'livery' not in driver_result_dict:
                    continue
                if 'car_number' not in driver_result_dict['livery']:
                    continue
                if driver_result_dict['cust_id'] in member_custid_list:
                    respo_car_numbers.append(driver_result_dict['livery']['car_number'])

    # Remove duplicates
    respo_car_numbers = list(set(respo_car_numbers))

    # 3. Calculate Respo champ points for race reports. This section calculates points before the new race is accounted for.

    if current_racing_week is None or current_racing_week < 0:
        current_racing_week = 12

    week_data_before = await stats.get_respo_champ_points(db, all_member_dicts, current_year, current_quarter, current_racing_week, subsession_to_ignore=subsession_data['subsession_id'])
    stats.calc_total_champ_points(week_data_before, constants.respo_weeks_to_count)
    week_data_before = dict(sorted(week_data_before.items(), key=lambda item: item[1]['total_points'], reverse=True))
    to_remove = []
    for inner_member in week_data_before:
        if week_data_before[inner_member]['total_points'] == 0:
            to_remove.append(inner_member)

    for inner_member in to_remove:
        week_data_before.pop(inner_member)

    # 4. For each car number driven by a Respo member, generate a race report:
    for car_number in respo_car_numbers:
        race_summary_dict = await db.get_race_summary(subsession_data['subsession_id'])
        race_summary_dict['respo_driver_results'] = []
        member_dicts = await db.fetch_members_in_subsession(subsession_data['subsession_id'], car_number=car_number)

        num_respo_drivers = len(member_dicts)

        if num_respo_drivers > 1:
            multi_report = True
            message_text = "Well lookie here. "

        drivers_listed = 0

        if member_dicts is None or len(member_dicts) < 1:
            logging.getLogger('respobot.iracing').warning(f"Attempted to process race that returned no Respo members. Verify that the results table is populated for subsession {subsession_data['subsession_id']}")
            return

        for member in member_dicts:
            driver_result_dict = await db.get_driver_result_summary(subsession_data['subsession_id'], member['iracing_custid'])
            race_summary_dict['respo_driver_results'].append(driver_result_dict)

            # update the message text with the participants' names
            if drivers_listed < num_respo_drivers - 1:
                if drivers_listed == 0 and num_respo_drivers == 2:
                    message_text += member['name'] + " "
                else:
                    message_text += member['name'] + ", "
            else:
                message_text += "and " + member['name'] + " "

            drivers_listed += 1

            # Promote / demote Discord roles based on new iRating. Populate role_change_reason if they have crossed the pleb line.
            if race_summary_dict['track_category_id'] == irConstants.Category.road.value and driver_result_dict['newi_rating'] > 0 and driver_result_dict['oldi_rating'] > 0:
                if driver_result_dict['newi_rating'] >= constants.pleb_line:
                    await roles.promote_driver(helpers.fetch_guild(bot), member['discord_id'])
                    if driver_result_dict['oldi_rating'] < constants.pleb_line:
                        role_change_reason = member['name'] + " has risen above the pleb line and proven themself worthy of the title God Amongst Men."
                else:
                    await roles.demote_driver(helpers.fetch_guild(bot), member['discord_id'])
                    if driver_result_dict['oldi_rating'] >= constants.pleb_line:
                        role_change_reason = member['name'] + " has dropped below the pleb line and has been banished from Mount Olypmus to carry out the rest of their days among the peasants."

            ###################################################
            # TODO: Determine if this is even needed anymore. #
            ###################################################
            old_last_race_check = await db.get_member_last_race_check(member['iracing_custid'])
            if race_summary_dict['start_time'] > old_last_race_check:
                await db.set_member_last_race_check(member['iracing_custid'], race_summary_dict['start_time'])

            if role_change_reason:
                await channel.send(role_change_reason)

        # 5. Now that we know which class the car in this report ran, we can determine class count.
        race_summary_dict['cars_in_class'] = await db.get_drivers_in_class(subsession_data['subsession_id'], race_summary_dict['respo_driver_results'][0]['car_class_id'], simsession_type=6)

        # 6. Generate the report for this car.
        if env.SUPPRESS_RACE_RESULTS == "False":

            if multi_report is True:
                message_text += "just finished playing with each other for hours on end."

            if embed_type != 'auto':
                if embed_type == 'compact':
                    await send_results_embed_compact(db, channel, race_summary_dict)
                else:
                    await send_results_embed(db, channel, race_summary_dict)
            else:
                if multi_report is False:
                    await send_results_embed_compact(db, channel, race_summary_dict)
                else:
                    await send_results_embed(db, channel, race_summary_dict)

    # 7. Calculate Respo champ points for race reports. This section calculates points after the new race is accounted for.
    week_data_after = await stats.get_respo_champ_points(db, all_member_dicts, current_year, current_quarter, current_racing_week)
    stats.calc_total_champ_points(week_data_after, constants.respo_weeks_to_count)

    week_data_after = dict(sorted(week_data_after.items(), key=lambda item: item[1]['total_points'], reverse=True))
    to_remove = []
    for inner_member in week_data_after:
        if week_data_after[inner_member]['total_points'] == 0:
            to_remove.append(inner_member)

    for inner_member in to_remove:
        week_data_after.pop(inner_member)

    # This will break if Respo ever reaches 12 members who actually race.
    for inner_member in week_data_after:
        place_after = list(week_data_after.keys()).index(inner_member)
        place_after_string = str(place_after + 1)
        if place_after_string[-1] == '1':
            place_after_string += "st"
        elif place_after_string[-1] == '2':
            place_after_string += "nd"
        elif place_after_string[-1] == '3':
            place_after_string += "rd"
        else:
            place_after_string += "th"

        if inner_member in week_data_before:
            place_before = list(week_data_before.keys()).index(inner_member)

            if place_after < place_before:
                await channel.send(inner_member + " just moved up the Respo championship leaderboard to " + place_after_string + " place with " + str(week_data_after[inner_member]['total_points']) + " points.")
        else:
            await channel.send(inner_member + " is now on the Respo championship leaderboard and in " + place_after_string + " place.")


async def send_results_embed(db: BotDatabase, channel, race_summary_dict):
    track = ""
    irating_change = 0
    safety_rating = ""
    safety_rating_change = ""
    multi_report = False

    if 'respo_driver_results' in race_summary_dict:
        if len(race_summary_dict['respo_driver_results']) > 1:
            multi_report = True

    if multi_report is False:
        iracing_custid = race_summary_dict['respo_driver_results'][0]['iracing_custid']
        member_dict = await db.fetch_member_dict(iracing_custid=iracing_custid)

    track = race_summary_dict['track_name']
    if(race_summary_dict['track_config_name'] and race_summary_dict['track_config_name'] != "N/A" and race_summary_dict['track_config_name'] != ""):
        track += " (" + race_summary_dict['track_config_name'] + ")"

    if multi_report is False:
        filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discord_id'], 128)
    else:
        filepath = env.BOT_DIRECTORY + "media/respo_logo.png"

    with open(filepath, "rb") as f_avatar:
        picture = discord.File(f_avatar, filename="user_avatar.png")

        title = ""
        url = "https://members.iracing.com/membersite/member/EventResult.do?&subsessionid=" + str(race_summary_dict['subsession_id'])

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            title = "Race result for "
        else:
            title = "Hosted result for "

        if multi_report is False:
            url += "&custid=" + str(race_summary_dict['respo_driver_results'][0]['iracing_custid'])
            title += member_dict['name']
        else:
            title += "Respo Racing"

        embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

        embedVar.set_thumbnail(url="attachment://user_avatar.png")

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            embedVar.add_field(name="Series", value=race_summary_dict['series_name'], inline=False)
        else:
            embedVar.add_field(name="Session", value=race_summary_dict['session_name'], inline=False)

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            car_classes = await db.get_season_car_classes(season_id=race_summary_dict['season_id'])
            if len(car_classes) > 1:
                embedVar.add_field(name="Class", value=race_summary_dict['respo_driver_results'][0]['car_class_short_name'], inline=True)

        embedVar.add_field(name="Track", value=track, inline=False)
        embedVar.add_field(name="SOF", value=str(race_summary_dict['event_strength_of_field']), inline=False)
        if race_summary_dict['max_team_drivers'] > 1:
            embedVar.add_field(name="Teams in Class", value=str(race_summary_dict['cars_in_class']))
        else:
            embedVar.add_field(name="Car #", value=str(race_summary_dict['respo_driver_results'][0]['livery_car_number']), inline=True)
            embedVar.add_field(name="Drivers", value=str(race_summary_dict['cars_in_class']), inline=True)

        embedVar.add_field(name="Started", value=str(race_summary_dict['respo_driver_results'][0]['starting_position_in_class']), inline=True)
        embedVar.add_field(name="Finished", value=str(race_summary_dict['respo_driver_results'][0]['finish_position_in_class']), inline=True)

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            embedVar.add_field(name="Champ. Pts", value=str(race_summary_dict['respo_driver_results'][0]['champ_points']), inline=True)

            for report_driver in race_summary_dict['respo_driver_results']:
                irating_change = report_driver["newi_rating"] - report_driver["oldi_rating"]

                if report_driver['new_license_level'] > 20:
                    safety_rating = "P"
                elif report_driver['new_license_level'] > 16:
                    safety_rating = "A"
                elif report_driver['new_license_level'] > 12:
                    safety_rating = "B"
                elif report_driver['new_license_level'] > 8:
                    safety_rating = "C"
                elif report_driver['new_license_level'] > 4:
                    safety_rating = "D"
                else:
                    safety_rating = "R"
                safety_rating += f"{(report_driver['new_sub_level'] / 100):.2f}"

                if multi_report is False:
                    safety_rating_change = f"({((report_driver['new_sub_level'] - report_driver['old_sub_level']) / 100):+.2f}, {report_driver['incidents']}x)"
                else:
                    safety_rating_change = f"{((report_driver['new_sub_level'] - report_driver['old_sub_level']) / 100):+.2f}"

                if multi_report is False:
                    embedVar.add_field(name=f"iRating", value=f"{report_driver['newi_rating']} ({irating_change:+d})", inline=False)
                    embedVar.add_field(name=f"Safety Rating", value=f"{safety_rating} {safety_rating_change}", inline=False)
                else:
                    # embedVar.add_field(name=report_driver['leaderboard_name'], value=f"iR: {report_driver['irating_new']} ({irating_change:+d})\nSR: {safety_rating} {safety_rating_change}\nLaps: {report_driver['laps']}", inline=False)
                    if (report_driver["newi_rating"] < 0) or (report_driver['laps_complete'] < 1):
                        embedVar.add_field(name=report_driver['name'], value=f"{report_driver['laps']} Laps", inline=False)
                    else:
                        embedVar.add_field(name=report_driver['name'], value=f"{irating_change:+d} iR ({report_driver['oldi_rating']}), {safety_rating_change} SR ({report_driver['incidents']}x), {report_driver['laps_complete']} Laps", inline=False)
        else:
            for report_driver in race_summary_dict['respo_driver_results']:
                if multi_report is False:
                    embedVar.add_field(name=f"Incidents", value=f"{report_driver['incidents']}x", inline=False)
                else:
                    embedVar.add_field(name=report_driver['name'], value=f"{report_driver['incidents']}x", inline=False)

        await channel.send(content="", file=picture, embed=embedVar)
        # await thread.send(content="", file=picture, embed=embedVar)

        picture.close()

    if multi_report is False and os.path.exists(filepath):
        await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
        os.remove(filepath)

    return


async def send_results_embed_compact(db, channel, race_summary_dict):
    irating_change = 0
    multi_report = False

    track = race_summary_dict['track_name']
    if(race_summary_dict['track_config_name'] and race_summary_dict['track_config_name'] != "N/A" and race_summary_dict['track_config_name'] != ""):
        track += " (" + race_summary_dict['track_config_name'] + ")"

    if 'respo_driver_results' in race_summary_dict:
        if len(race_summary_dict['respo_driver_results']) > 1:
            multi_report = True

    if multi_report is False:
        iracing_custid = race_summary_dict['respo_driver_results'][0]['iracing_custid']
        member_dict = await db.fetch_member_dict(iracing_custid=iracing_custid)

    if multi_report is False:
        filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discord_id'], 128)
    else:
        filepath = env.BOT_DIRECTORY + "media/respo_logo.png"

    with open(filepath, "rb") as f_avatar:
        picture = discord.File(f_avatar, filename="user_avatar.png")

        title = ""
        url = "https://members.iracing.com/membersite/member/EventResult.do?&subsessionid=" + str(race_summary_dict['subsession_id'])

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            title = "Race result for "
        else:
            title = "Hosted result for "

        if multi_report is False:
            url += "&custid=" + str(race_summary_dict['respo_driver_results'][0]['iracing_custid'])
            title += member_dict['name']
        else:
            title += "Respo Racing"

        embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

        embedVar.set_thumbnail(url="attachment://user_avatar.png")

        event_description = ""
        field_name = ""

        # if 'hosted_name' not in race_summary_dict:
        if race_summary_dict['league_name'] is None:
            field_name = race_summary_dict['series_name']
        else:
            field_name = race_summary_dict['session_name']

        event_description = "at " + track

        embedVar.add_field(name=field_name, value=event_description, inline=False)

        pos_change = int(race_summary_dict['respo_driver_results'][0]['starting_position_in_class'] - race_summary_dict['respo_driver_results'][0]['finish_position_in_class'])
        pos_change_str = " (↕0)"

        if pos_change < 0:
            pos_change_str = " (↓" + str(abs(pos_change)) + ")"
        elif pos_change > 0:
            pos_change_str = " (↑" + str(pos_change) + ")"

        result_field_name = "Result: P" + str(race_summary_dict['respo_driver_results'][0]['finish_position_in_class']) + " of " + str(race_summary_dict['cars_in_class']) + pos_change_str
        # if race_summary_dict['team_event'] is True:
        #     result_field_name += " teams"
        # else:
        #     result_field_name += " cars"

        if multi_report is True:
            result_string = ""
            # if 'hosted_name' not in race_summary_dict:
            if race_summary_dict['league_name'] is None:
                result_string += str(race_summary_dict['respo_driver_results'][0]['champ_points']) + " pts, "
            result_string += str(race_summary_dict['event_strength_of_field']) + " SoF"
            embedVar.add_field(name=result_field_name, value=result_string, inline=False)

            for report_driver in race_summary_dict['respo_driver_results']:
                result_string = ""
                # if 'hosted_name' not in race_summary_dict:
                if race_summary_dict['league_name'] is None:
                    irating_change = report_driver["newi_rating"] - report_driver["oldi_rating"]
                    result_string += f"{irating_change:+d}" + " iR (" + str(report_driver['newi_rating']) + "), "
                result_string += str(report_driver['incidents']) + "x, " + str(report_driver['laps_complete']) + " laps"
                embedVar.add_field(name=report_driver['name'], value=result_string, inline=False)
        else:
            result_string = ""
            # if 'hosted_name' not in race_summary_dict:
            if race_summary_dict['league_name'] is None:
                result_string += str(race_summary_dict['respo_driver_results'][0]['champ_points']) + " pts"
                irating_change = race_summary_dict['respo_driver_results'][0]["newi_rating"] - race_summary_dict['respo_driver_results'][0]['oldi_rating']
                result_string += ", " + f"{irating_change:+d}" + " iR (" + str(race_summary_dict['respo_driver_results'][0]['newi_rating']) + "), "
            result_string += str(race_summary_dict['respo_driver_results'][0]['incidents']) + "x, "
            result_string += str(race_summary_dict['event_strength_of_field']) + " SoF"
            embedVar.add_field(name=result_field_name, value=result_string, inline=False)
        message = await channel.send(content="", file=picture, embed=embedVar)

        picture.close()

    if multi_report is False and os.path.exists(filepath):
        await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
        os.remove(filepath)

    return message

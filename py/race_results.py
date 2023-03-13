import os
import discord
import global_vars
import cache_races
import environment_variables as env
import roles
import stats_helpers as stats
import image_generators as image_gen
from pyracing import constants as pyracingConstants
import asyncio

from datetime import datetime


async def get_race_results():
    global_vars.members_locks += 1
    for member in global_vars.members:
        if "iracingCustID" not in global_vars.members[member]:
            continue

        iracing_id = global_vars.members[member]["iracingCustID"]
        if str(iracing_id) not in global_vars.race_cache:
            # This person has never had their races cached. Cache them now.
            await cache_races(global_vars.ir, iracing_id)
        else:
            # Grab all series races since their previous cached race
            start_high = int(datetime.timestamp(datetime.now()) * 1000)
            start_low = global_vars.members[member]['last_race_check']
            if start_high - start_low > 90 * 24 * 60 * 60 * 1000:
                start_high = start_low + 90 * 24 * 60 * 60 * 1000 + 1000
            races_list = await global_vars.ir.search_results(iracing_id, start_low=start_low, start_high=start_high)

            # Grab all hosted races in the last week
            now = int(datetime.now().timestamp()) * 1000
            start_time = now - 7 * 24 * 60 * 60 * 1000
            hosted_races_list = await global_vars.ir.private_results(iracing_id, start_time, now, sort=pyracingConstants.Sort.start_time.value, order=pyracingConstants.Sort.descending.value)

            if len(hosted_races_list) > 0:
                for race in hosted_races_list:
                    races_list.append(race)

            for race in races_list:
                race_found = False
                # If an official series, check if this race is in the cache
                if not hasattr(race, 'host_cust_id'):
                    global_vars.race_cache_locks += 1
                    for year in global_vars.race_cache[str(iracing_id)]:
                        for quarter in global_vars.race_cache[str(iracing_id)][str(year)]:
                            for series in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)]:
                                for cached_race in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series)]:
                                    if int(cached_race) == race.subsession_id:
                                        race_found = True
                    global_vars.race_cache_locks -= 1
                else:
                    if str(iracing_id) in global_vars.hosted_cache:
                        if str(race.subsession_id) in global_vars.hosted_cache[str(iracing_id)]:
                            race_found = True

                if race_found is False:
                    await process_race_result(member, race)

    global_vars.members_locks -= 1
    # global_vars.dump_json()


async def process_race_result(member, race):
    multi_report = False
    role_change_reason = ""
    message_text = ""

    if 'iracingCustID' in global_vars.members[member]:
        iracing_id = global_vars.members[member]['iracingCustID']
    else:
        return

    results_dict = await get_results_summary(iracing_id, race.subsession_id, race=race)

    if results_dict is not None and results_dict != {}:

        if 'respo_drivers' in results_dict:

            weeks_to_count = 6
            current_racing_week = await stats.get_current_iracing_week(-1)

            if current_racing_week < 0:
                current_racing_week = 12

            week_data_before = stats.get_respo_champ_points(global_vars.series_info['misc']['current_year'], global_vars.series_info['misc']['current_quarter'], current_racing_week)
            stats.calc_total_champ_points(week_data_before, weeks_to_count)
            week_data_before = dict(sorted(week_data_before.items(), key=lambda item: item[1]['total_points'], reverse=True))
            to_remove = []
            for inner_member in week_data_before:
                if week_data_before[inner_member]['total_points'] == 0:
                    to_remove.append(inner_member)

            for inner_member in to_remove:
                week_data_before.pop(inner_member)

            num_respo_drivers = len(results_dict['respo_drivers'])
            if num_respo_drivers > 1:
                multi_report = True
                message_text = "Well lookie here. "

            drivers_listed = 0

            # Add the race to the cache for every member that took part.
            for inner_member in global_vars.members:
                if str(global_vars.members[inner_member]['iracingCustID']) in results_dict['respo_drivers']:
                    # update the message text with the participants' names
                    if drivers_listed < num_respo_drivers - 1:
                        if drivers_listed == 0 and num_respo_drivers == 2:
                            message_text += global_vars.members[inner_member]['leaderboardName'] + " "
                        else:
                            message_text += global_vars.members[inner_member]['leaderboardName'] + ", "
                    else:
                        message_text += "and " + global_vars.members[inner_member]['leaderboardName'] + " "

                    drivers_listed += 1

                    # Find where to save it
                    driver_id = global_vars.members[inner_member]['iracingCustID']
                    if not hasattr(race, 'host_cust_id'):
                        while global_vars.race_cache_locks > 0:
                            asyncio.sleep(1)

                        if str(race.season_year) not in global_vars.race_cache[str(driver_id)]:
                            global_vars.race_cache[str(driver_id)][str(race.season_year)] = {}
                        if str(race.season_quarter) not in global_vars.race_cache[str(driver_id)][str(race.season_year)]:
                            global_vars.race_cache[str(driver_id)][str(race.season_year)][str(race.season_quarter)] = {}
                        if str(race.series_id) not in global_vars.race_cache[str(driver_id)][str(race.season_year)][str(race.season_quarter)]:
                            global_vars.race_cache[str(driver_id)][str(race.season_year)][str(race.season_quarter)][str(race.series_id)] = {}

                        global_vars.race_cache[str(driver_id)][str(race.season_year)][str(race.season_quarter)][str(race.series_id)][str(race.subsession_id)] = {}
                        new_race_dict = global_vars.race_cache[str(driver_id)][str(race.season_year)][str(race.season_quarter)][str(race.series_id)][str(race.subsession_id)]
                    else:
                        if str(driver_id) not in global_vars.hosted_cache:
                            global_vars.hosted_cache[str(driver_id)] = {}

                        global_vars.hosted_cache[str(driver_id)][str(race.subsession_id)] = {}
                        new_race_dict = global_vars.hosted_cache[str(driver_id)][str(race.subsession_id)]

                    new_race_dict['official'] = results_dict['official']
                    new_race_dict['time_start_raw'] = results_dict['time_start_raw']
                    new_race_dict['category'] = results_dict['category']
                    new_race_dict['points_champ'] = results_dict['points_champ']
                    new_race_dict['race_week'] = results_dict['race_week']
                    new_race_dict['car_class_id'] = results_dict['car_class_id']
                    new_race_dict['pos_start_class'] = results_dict['pos_start_class']
                    new_race_dict['pos_finish_class'] = results_dict['pos_finish_class']
                    new_race_dict['incidents'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['incidents']
                    new_race_dict['laps'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['laps']
                    new_race_dict['laps_led'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['laps_led']
                    new_race_dict['irating_old'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_old']
                    new_race_dict['irating_new'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_new']
                    new_race_dict['drivers_in_class'] = results_dict['drivers_in_class']
                    new_race_dict['team_drivers_max'] = results_dict['team_drivers_max']

                    if hasattr(race, 'official_session') and race.official_session and race.category_id == pyracingConstants.Category.road.value and "discordID" in global_vars.members[inner_member]:
                        if results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_old'] < global_vars.pleb_line and results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_new'] >= global_vars.pleb_line:
                            await roles.promote_driver(global_vars.members[inner_member]["discordID"])
                            role_change_reason = global_vars.members[inner_member]['leaderboardName'] + " risen above the pleb line and proven themself worthy of the title God Amongst Men."
                        elif results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_old'] >= global_vars.pleb_line and results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_new'] < global_vars.pleb_line:
                            await roles.demote_driver(global_vars.members[inner_member]["discordID"])
                            role_change_reason = global_vars.members[inner_member]['leaderboardName'] + " has dropped below the pleb line and has been banished from Mount Olypmus to carry out the rest of their days among the peasants."

                    if hasattr(race, 'category_id') and race.category_id == pyracingConstants.Category.road.value:
                        if 'last_race_check' not in global_vars.members[inner_member]:
                            global_vars.members[inner_member]['last_race_check'] = race.time_start_raw
                        else:
                            if race.time_start_raw > global_vars.members[inner_member]['last_race_check']:
                                global_vars.members[inner_member]['last_race_check'] = race.time_start_raw
                                if results_dict['official'] == 1:
                                    global_vars.members[inner_member]['last_known_ir'] = results_dict['respo_drivers'][str(global_vars.members[inner_member]['iracingCustID'])]['irating_new']

            week_data_after = stats.get_respo_champ_points(global_vars.series_info['misc']['current_year'], global_vars.series_info['misc']['current_quarter'], current_racing_week)
            stats.calc_total_champ_points(week_data_after, weeks_to_count)

            week_data_after = dict(sorted(week_data_after.items(), key=lambda item: item[1]['total_points'], reverse=True))
            to_remove = []
            for inner_member in week_data_after:
                if week_data_after[inner_member]['total_points'] == 0:
                    to_remove.append(inner_member)

            for inner_member in to_remove:
                week_data_after.pop(inner_member)

            if env.SUPPRESS_RACE_RESULTS == "False":

                if multi_report is True:
                    message_text += "just finished playing with each other for hours on end."

                for guild in global_vars.bot.guilds:
                    if guild.id == env.GUILD:
                        for channel in guild.channels:
                            if channel.id == env.CHANNEL:
                                if multi_report is False:
                                    await send_results_embed_compact(channel, results_dict, global_vars.members[member])
                                    if role_change_reason:
                                        await channel.send(role_change_reason)
                                else:
                                    await channel.send(message_text)
                                    await send_results_embed(channel, results_dict, global_vars.members[member])

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


async def get_results_summary(iracing_id, subsession_id, **kwargs):
    subsession = await global_vars.ir.subsession_data(subsession_id)

    if not subsession:
        return {}
    if subsession.team_drivers_max > 1:
        team_event = True
    else:
        team_event = False

    class_count = 0
    car_number = 1
    respo_driver = None
    team_number = -1

    new_race_dict = {}

    new_race_dict['respo_drivers'] = {}

    # Prelim scan drivers to get class and which car this member ran in
    for driver in subsession.drivers:
        if driver.sim_ses_type_name == 'Race':
            if driver.cust_id == iracing_id:
                respo_driver = driver
                team_number = driver.car_num

    # Make sure this member actually drove in the race.
    if respo_driver is None:
        return None

    # Second scan to get class count and all respo members on this team
    for driver in subsession.drivers:
        if driver.car_class_id == respo_driver.car_class_id and driver.sim_ses_type_name == 'Race':
            if team_event is True:
                if driver.cust_id < 0:  # Teams have a negative customer ID, so count the teams
                    class_count += 1
            else:
                class_count += 1  # If not a team event, count every driver in the race

        if driver.car_num == team_number:
            for member in global_vars.members:
                if driver.cust_id == global_vars.members[member]['iracingCustID']:
                    new_race_dict['respo_drivers'][str(driver.cust_id)] = {}
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['irating_old'] = driver.irating_old
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['irating_new'] = driver.irating_new
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['sub_level_old'] = driver.sub_level_old
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['sub_level_new'] = driver.sub_level_new
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['incidents'] = driver.incidents
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['license_level_new'] = driver.license_level_new
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['leaderboard_name'] = global_vars.members[member]['leaderboardName']
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['laps'] = driver.laps_comp
                    new_race_dict['respo_drivers'][str(driver.cust_id)]['laps_led'] = driver.laps_led

    # Scan drivers a third time to get the car number for non-team events
    if team_event is False:
        for driver in subsession.drivers:
            if driver.car_class_id == respo_driver.car_class_id and driver.sim_ses_type_name == 'Race' and isinstance(driver.irating_old, int) and driver.irating_old > respo_driver.irating_old:
                car_number += 1

    new_race_dict['hosted'] = False
    if "race" in kwargs and hasattr(kwargs['race'], 'time_start_raw'):
        new_race_dict["pos_start_class"] = kwargs['race'].pos_start_class
        new_race_dict['time_start_raw'] = kwargs["race"].time_start_raw
    else:
        if "race" in kwargs and hasattr(kwargs['race'], 'host_cust_id'):
            new_race_dict['hosted'] = True
            new_race_dict['hosted_name'] = kwargs["race"].session_name

        new_race_dict['time_start_raw'] = respo_driver.time_session_start
        new_race_dict["pos_start_class"] = 1
        for driver in subsession.drivers:
            if driver.car_class_id == respo_driver.car_class_id and driver.sim_ses_type_name == 'Race' and driver.pos_start < respo_driver.pos_start and (not team_event or driver.cust_id < 0):
                new_race_dict["pos_start_class"] += 1
    new_race_dict["official"] = respo_driver.official
    new_race_dict["category"] = subsession.cat_id
    new_race_dict["points_champ"] = respo_driver.points_champ
    new_race_dict["race_week"] = subsession.race_week
    new_race_dict["car_id"] = respo_driver.car_id
    new_race_dict["car_class_id"] = respo_driver.car_class_id
    new_race_dict["car_class_name"] = respo_driver.car_class_name
    new_race_dict["pos_finish_class"] = respo_driver.pos_finish_class + 1
    new_race_dict['drivers_in_class'] = class_count
    new_race_dict['team_drivers_max'] = subsession.team_drivers_max
    new_race_dict['track_name'] = subsession.track
    new_race_dict['track_config_name'] = subsession.track_config
    new_race_dict['series_id'] = subsession.series_id
    new_race_dict['series_name'] = subsession.series_name
    new_race_dict['subsession_id'] = subsession.subsession_id
    new_race_dict['cust_id'] = respo_driver.cust_id
    new_race_dict['strength_of_field'] = subsession.strength_of_field
    new_race_dict['team_event'] = team_event
    new_race_dict['cars_in_class'] = class_count
    new_race_dict['car_number'] = car_number

    return new_race_dict


async def send_results_embed(channel, results_dict, member_dict):
    track = ""
    irating_change = 0
    safety_rating = ""
    safety_rating_change = ""
    multi_report = False

    if 'respo_drivers' in results_dict:
        if len(results_dict['respo_drivers']) > 1:
            multi_report = True

    track = results_dict['track_name']
    if(results_dict['track_config_name'] and results_dict['track_config_name'] != "N/A" and results_dict['track_config_name'] != ""):
        track += " (" + results_dict['track_config_name'] + ")"

    if multi_report is False:
        filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discordID'], 128)
    else:
        filepath = env.BOT_DIRECTORY + "media/respo_logo.png"

    with open(filepath, "rb") as f_avatar:
        picture = discord.File(f_avatar, filename="user_avatar.png")

        title = ""
        url = "https://members.iracing.com/membersite/member/EventResult.do?&subsessionid=" + str(results_dict['subsession_id'])

        if 'hosted_name' not in results_dict:
            title = "Race result for "
        else:
            title = "Hosted result for "

        if multi_report is False:
            url += "&custid=" + str(results_dict['cust_id'])
            title += member_dict['leaderboardName']
        else:
            title += "Respo Racing"

        embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

        embedVar.set_thumbnail(url="attachment://user_avatar.png")

        if 'hosted_name' not in results_dict:
            embedVar.add_field(name="Series", value=results_dict['series_name'], inline=False)
        else:
            embedVar.add_field(name="Session", value=results_dict['hosted_name'], inline=False)

        if 'hosted_name' not in results_dict:
            if str(results_dict['series_id']) in global_vars.series_info:
                if 'classes' in global_vars.series_info[str(results_dict['series_id'])] and len(global_vars.series_info[str(results_dict['series_id'])]['classes']) > 1:
                    embedVar.add_field(name="Class", value=results_dict['car_class_name'], inline=True)

        embedVar.add_field(name="Track", value=track, inline=False)
        embedVar.add_field(name="SOF", value=str(results_dict['strength_of_field']), inline=False)
        if results_dict['team_event'] is True:
            embedVar.add_field(name="Teams in Class", value=str(results_dict['cars_in_class']))
        else:
            embedVar.add_field(name="Car #", value=str(results_dict['car_number']), inline=True)
            embedVar.add_field(name="Drivers", value=str(results_dict['cars_in_class']), inline=True)

        embedVar.add_field(name="Started", value=str(results_dict['pos_start_class']), inline=True)
        embedVar.add_field(name="Finished", value=str(results_dict['pos_finish_class']), inline=True)
        if 'hosted_name' not in results_dict:

            embedVar.add_field(name="Champ. Pts", value=str(results_dict['points_champ']), inline=True)

            for report_driver in results_dict['respo_drivers']:
                irating_change = results_dict['respo_drivers'][report_driver]["irating_new"] - results_dict['respo_drivers'][report_driver]["irating_old"]

                if results_dict['respo_drivers'][report_driver]['license_level_new'] > 20:
                    safety_rating = "P"
                elif results_dict['respo_drivers'][report_driver]['license_level_new'] > 16:
                    safety_rating = "A"
                elif results_dict['respo_drivers'][report_driver]['license_level_new'] > 12:
                    safety_rating = "B"
                elif results_dict['respo_drivers'][report_driver]['license_level_new'] > 8:
                    safety_rating = "C"
                elif results_dict['respo_drivers'][report_driver]['license_level_new'] > 4:
                    safety_rating = "D"
                else:
                    safety_rating = "R"
                safety_rating += f"{(results_dict['respo_drivers'][report_driver]['sub_level_new'] / 100):.2f}"

                if multi_report is False:
                    safety_rating_change = f"({((results_dict['respo_drivers'][report_driver]['sub_level_new'] - results_dict['respo_drivers'][report_driver]['sub_level_old']) / 100):+.2f}, {results_dict['respo_drivers'][report_driver]['incidents']}x)"
                else:
                    safety_rating_change = f"{((results_dict['respo_drivers'][report_driver]['sub_level_new'] - results_dict['respo_drivers'][report_driver]['sub_level_old']) / 100):+.2f}"

                if multi_report is False:
                    embedVar.add_field(name=f"iRating", value=f"{results_dict['respo_drivers'][report_driver]['irating_new']} ({irating_change:+d})", inline=False)
                    embedVar.add_field(name=f"Safety Rating", value=f"{safety_rating} {safety_rating_change}", inline=False)
                else:
                    # embedVar.add_field(name=results_dict['respo_drivers'][report_driver]['leaderboard_name'], value=f"iR: {results_dict['respo_drivers'][report_driver]['irating_new']} ({irating_change:+d})\nSR: {safety_rating} {safety_rating_change}\nLaps: {results_dict['respo_drivers'][report_driver]['laps']}", inline=False)
                    embedVar.add_field(name=results_dict['respo_drivers'][report_driver]['leaderboard_name'], value=f"{irating_change:+d} iR, {safety_rating_change} SR ({results_dict['respo_drivers'][report_driver]['incidents']}x), {results_dict['respo_drivers'][report_driver]['laps']} Laps", inline=False)
        else:
            for report_driver in results_dict['respo_drivers']:
                if multi_report is False:
                    embedVar.add_field(name=f"Incidents", value=f"{results_dict['respo_drivers'][report_driver]['incidents']}x", inline=False)
                else:
                    embedVar.add_field(name=results_dict['respo_drivers'][report_driver]['leaderboard_name'], value=f"{results_dict['respo_drivers'][report_driver]['incidents']}x", inline=False)

        await channel.send(content="", file=picture, embed=embedVar)
        # await thread.send(content="", file=picture, embed=embedVar)

        picture.close()

    if multi_report is False and os.path.exists(filepath):
        await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
        os.remove(filepath)

    return


async def send_results_embed_compact(channel, results_dict, member_dict):
    track = ""
    irating_change = 0
    multi_report = False

    if 'respo_drivers' in results_dict:
        if len(results_dict['respo_drivers']) > 1:
            multi_report = True

    track = results_dict['track_name']
    if(results_dict['track_config_name'] and results_dict['track_config_name'] != "N/A" and results_dict['track_config_name'] != ""):
        track += " (" + results_dict['track_config_name'] + ")"

    if multi_report is False:
        filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discordID'], 128)
    else:
        filepath = env.BOT_DIRECTORY + "media/respo_logo.png"

    with open(filepath, "rb") as f_avatar:
        picture = discord.File(f_avatar, filename="user_avatar.png")

        title = ""
        url = "https://members.iracing.com/membersite/member/EventResult.do?&subsessionid=" + str(results_dict['subsession_id'])

        if 'hosted_name' not in results_dict:
            title = "Race result for "
        else:
            title = "Hosted result for "

        if multi_report is False:
            url += "&custid=" + str(results_dict['cust_id'])
            title += member_dict['leaderboardName']
        else:
            title += "Respo Racing"

        embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

        embedVar.set_thumbnail(url="attachment://user_avatar.png")

        if 'hosted_name' not in results_dict:
            embedVar.add_field(name="Series", value=results_dict['series_name'], inline=False)
        else:
            embedVar.add_field(name="Session", value=results_dict['hosted_name'], inline=False)

        result_string = "P" + str(results_dict['pos_finish_class'])
        if' hosted_name' not in results_dict:
            result_string += ", " + str(results_dict['points_champ']) + " champ pts"

        for cust_id in results_dict['respo_drivers']:
            if int(cust_id) == member_dict['iracingCustID']:
                irating_change = results_dict['respo_drivers'][cust_id]["irating_new"] - results_dict['respo_drivers'][cust_id]["irating_old"]
                result_string += ", " + f"{irating_change:+d}" + " iR, " + str(results_dict['respo_drivers'][cust_id]['incidents']) + "x"

        embedVar.add_field(name="Result", value=result_string, inline=True)

        message = await channel.send(content="", file=picture, embed=embedVar)

        picture.close()

    if multi_report is False and os.path.exists(filepath):
        await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
        os.remove(filepath)

    return message

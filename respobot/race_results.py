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
import subsession_summary
import logging
import traceback

from datetime import datetime, timezone, timedelta


async def get_race_results(bot: discord.Bot, db: BotDatabase, ir: IracingClient):

    try:
        member_dicts = await db.fetch_member_dicts()
    except BotDatabaseError as exc:
        logging.getLogger('respobot.bot').warning(
            f"During get_race_results the following exception was encountered: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"During get_race_results the following exception was encountered: {exc}"
        )
        return

    if member_dicts is None or len(member_dicts) < 1:
        logging.getLogger('respobot.bot').info("No members in the database, skipping race checks.")
        return

    for member_dict in member_dicts:
        if 'iracing_custid' not in member_dict:
            logging.getLogger('respobot.bot').warning(
                f"Skipping member because member_dict did not contain an iracing_custid key: {member_dict}"
            )
            continue

        iracing_custid = member_dict['iracing_custid']

        logging.getLogger('respobot.bot').info(f"Searching for new races for cust_id: {iracing_custid}")

        if 'latest_session_found' in member_dict and member_dict['latest_session_found'] is None:
            # This person needs to have their sessions cached.
            logging.getLogger('respobot.bot').info(f"Found a new member. Caching races for cust_id: {iracing_custid}")
            await cache_races.cache_races(bot, db, ir, [iracing_custid])
            continue

        on_a_hiatus = False
        # Grab all series races since their previous cached race
        start_high = datetime.now(timezone.utc)
        start_low = member_dict['latest_session_found']

        if start_low is None:
            continue

        if start_high - start_low > timedelta(days=90):
            start_high = start_low + timedelta(days=90)
            on_a_hiatus = True
        start_low_str = start_low.isoformat().replace('+00:00', 'Z')
        start_high_str = start_high.isoformat().replace('+00:00', 'Z')

        subsessions_list = []

        # finish_range_... are used to account for the following scenario:
        # 1. User signs up for long race and crashes out early.
        # 2. User then signs up for short race which ends before the previous long race
        # 3. Bot scans for races and results for the later short race show up.
        # 4. Latest session found is updated to the start time of this later shorter race.
        # 5. The longer race ends but is never found because latest_session_found is later than this race.
        # Scanning based on finish time eliminates this issue.
        try:
            series_subsessions_list = await ir.search_results(
                cust_id=iracing_custid,
                finish_range_begin=start_low_str,
                finish_range_end=start_high_str
            )
            if series_subsessions_list is not None:
                subsessions_list += series_subsessions_list
        except ValueError:
            logging.getLogger('respobot.bot').warning(
                f"search_results() for cust_id {iracing_custid} failed due to insufficient information."
            )
        except Exception as e:
            logging.getLogger('respobot.bot').warning(e)

        try:
            hosted_subsessions_list = await ir.search_hosted(
                cust_id=iracing_custid,
                finish_range_begin=start_low_str,
                finish_range_end=start_high_str
            )
            if hosted_subsessions_list is not None:
                subsessions_list += hosted_subsessions_list
        except ValueError:
            logging.getLogger('respobot.bot').warning(
                f"search_hosted() for cust_id {iracing_custid} failed due to insufficient information."
            )
        except Exception as e:
            logging.getLogger('respobot.bot').warning(e)

        if subsessions_list is None:
            continue

        latest_new_session = None
        for subsession in subsessions_list:
            try:
                race_found = await db.is_subsession_in_db(subsession['subsession_id'])
                laps_found = await db.is_subsession_in_laps_table(subsession['subsession_id'])
            except BotDatabaseError as exc:
                logging.getLogger('respobot.bot').warning(
                    "During get_race_results() an exception was caught when "
                    f"checking if subsession {subsession['subsession_id']} was in the database.: {exc}"
                )
                await helpers.send_bot_failure_dm(
                    bot,
                    "During get_race_results() an exception was caught when "
                    f"checking if subsession {subsession['subsession_id']} was in the database.: {exc}"
                )
                continue

            if race_found is False:
                logging.getLogger('respobot.bot').info(f"Adding new subsession: {subsession['subsession_id']}")
                try:
                    new_subsession = await ir.subsession_data(subsession['subsession_id'])
                except Exception as exc:
                    logging.getLogger('respobot.bot').warning(
                        "During get_race_results() an exception was caught when fetching data "
                        f"for subsession {subsession['subsession_id']}: {exc}"
                    )
                    await helpers.send_bot_failure_dm(
                        bot,
                        "During get_race_results() an exception was caught when fetching data "
                        f"for subsession {subsession['subsession_id']}: {exc}"
                    )
                    continue

                new_session_end_time = datetime.fromisoformat(subsession['end_time'])

                try:
                    await db.add_subsessions([new_subsession])
                except BotDatabaseError as exc:
                    logging.getLogger('respobot.bot').warning(
                        "During get_race_results() an exception was caught when adding "
                        f"subsession {subsession['subsession_id']} to the database: {exc}"
                    )
                    await helpers.send_bot_failure_dm(
                        bot,
                        "During get_race_results() an exception was caught when adding "
                        f"subsession {subsession['subsession_id']} to the database: {exc}"
                    )
                    continue

                # And now for the laps
                if (
                    laps_found is False
                    and 'session_results' in new_subsession
                    and len(new_subsession['session_results']) > 0
                ):

                    for session_result_dict in new_subsession['session_results']:
                        if 'simsession_number' not in session_result_dict or 'results' not in session_result_dict:
                            continue

                        try:
                            lap_dicts = await ir.lap_data(
                                new_subsession['subsession_id'],
                                session_result_dict['simsession_number']
                            )
                        except Exception as exc:
                            logging.getLogger('respobot.bot').warning(
                                "During get_race_results() an exception was caught when fetching lap data "
                                f"for subsession {subsession['subsession_id']}: {exc}"
                            )
                            await helpers.send_bot_failure_dm(
                                bot,
                                "During get_race_results() an exception was caught when fetching lap data "
                                f"for subsession {subsession['subsession_id']}: {exc}"
                            )
                            continue

                        if lap_dicts is None or len(lap_dicts) < 1:
                            continue

                        try:
                            await db.add_laps(
                                lap_dicts, new_subsession['subsession_id'],
                                session_result_dict['simsession_number']
                            )
                        except BotDatabaseError as exc:
                            logging.getLogger('respobot.bot').warning(
                                f"During cache_races() an exception was encountered when adding "
                                f"laps to the database: {exc}"
                            )
                            await helpers.send_bot_failure_dm(
                                bot,
                                f"During cache_races() an exception was encountered when adding "
                                f"laps to the database: {exc}"
                            )

                # Update latest_new_session
                if latest_new_session is None or latest_new_session < new_session_end_time:
                    latest_new_session = new_session_end_time

                logging.getLogger('respobot.bot').info(f"Successfully added subsession: {subsession['subsession_id']}")

                if (
                    'host_id' in new_subsession
                    and 'league_id' in new_subsession
                    and (new_subsession['league_id'] is None or new_subsession['league_id'] < 1)
                ):
                    # This is just some random hosted session. Don't report it.
                    continue
                elif 'event_type' in new_subsession and new_subsession['event_type'] != 5:
                    # This is a non-hosted practice, qualifying, or time-trial. Don't report it.
                    continue

                await generate_race_report(bot, db, new_subsession['subsession_id'], embed_type='auto')

        try:
            db_latest_session_found = await db.get_member_latest_session_found(member_dict['iracing_custid'])
            if latest_new_session is not None and latest_new_session > db_latest_session_found:
                await db.set_member_latest_session_found(member_dict['iracing_custid'], latest_new_session)

            if on_a_hiatus is True:
                await db.set_member_latest_session_found(member_dict['iracing_custid'], start_high - timedelta(days=2))
        except BotDatabaseError as exc:
            logging.getLogger('respobot.bot').warning(
                "During get_race_results() an exception was caught when updating "
                f"latest_session_found for {member_dict['name']}: {exc}"
            )
            await helpers.send_bot_failure_dm(
                bot,
                "During get_race_results() an exception was caught when updating "
                f"latest_session_found for {member_dict['name']}: {exc}"
            )


async def generate_race_report(bot: discord.Bot, db: BotDatabase, subsession_id: int, embed_type: str = 'auto'):
    try:
        multi_report = False
        role_change_reason = ""
        message_text = ""
        channel = helpers.fetch_channel(bot)

        (current_year, current_quarter, current_racing_week, _, _) = await db.get_current_iracing_week()

        all_member_dicts = await db.fetch_member_dicts()
        all_member_iracing_custids = await db.fetch_iracing_cust_ids()

        # 1. Get the list of car numbers containing Respo members
        respo_car_numbers = await db.fetch_member_car_numbers_in_subsession(subsession_id)

        # 2. Calculate Respo champ points. This section calculates points before the new race is accounted for.
        if current_racing_week is None or current_racing_week < 0:
            current_racing_week = await stats.get_number_of_race_weeks(db, datetime.now(timezone.utc))

        week_data_before = await stats.get_respo_champ_points(
            db,
            all_member_dicts,
            current_year,
            current_quarter,
            current_racing_week,
            subsession_to_ignore=subsession_id
        )
        stats.calc_total_champ_points(week_data_before, constants.RESPO_WEEKS_TO_COUNT)
        week_data_before = dict(
            sorted(week_data_before.items(), key=lambda item: item[1]['total_points'], reverse=True)
        )
        to_remove = []
        for inner_member in week_data_before:
            if week_data_before[inner_member]['total_points'] == 0:
                to_remove.append(inner_member)

        for inner_member in to_remove:
            week_data_before.pop(inner_member)

        # 4. For each car number driven by a Respo member, generate a race report:
        for car_number in respo_car_numbers:
            car_results = await subsession_summary.generate_subsession_summary(bot, db, subsession_id, car_number)

            num_respo_drivers = len(car_results.driver_race_results)

            if num_respo_drivers > 1:
                multi_report = True
                message_text = "Well lookie here. "

            # Cycle through the driver race results and if they are a Respo member,
            # overwrite their display_name with their Respo member name.
            # Also prepare the name list and any promotions/demotions.
            drivers_listed = 0
            for driver_race_result in car_results.driver_race_results:
                member_dict = await db.fetch_member_dict(iracing_custid=driver_race_result.cust_id)
                himself_herself_themself = "themself"
                if member_dict is not None:
                    driver_race_result.display_name = member_dict['name']
                    if member_dict["pronoun_type"] == "male":
                        himself_herself_themself = "himself"
                    elif member_dict["pronoun_type"] == "female":
                        himself_herself_themself = "herself"

                # update the message text with the participants' names
                if drivers_listed < num_respo_drivers - 1:
                    if drivers_listed == 0 and num_respo_drivers == 2:
                        message_text += driver_race_result.display_name + " "
                    else:
                        message_text += driver_race_result.display_name + ", "
                else:
                    message_text += "and " + driver_race_result.display_name + " "

                drivers_listed += 1

                # Promote / demote Discord roles based on new iRating.
                # Populate role_change_reason if they have crossed the pleb line.
                if (
                    driver_race_result.cust_id in all_member_iracing_custids
                    and car_results.track_category_id == irConstants.Category.road.value
                    and driver_race_result.irating_new > 0 and driver_race_result.irating_old > 0
                ):
                    if driver_race_result.irating_new >= constants.PLEB_LINE:
                        await roles.promote_driver(helpers.fetch_guild(bot), member_dict['discord_id'])
                        if driver_race_result.irating_old < constants.PLEB_LINE:
                            if role_change_reason != "":
                                role_change_reason += "\n"  # Add a newline if not the first driver.
                            role_change_reason += (
                                driver_race_result.display_name
                                + (
                                    f" has risen above the pleb line and proven "
                                    f"{himself_herself_themself} worthy of the title God Amongst Men."
                                )
                            )
                    else:
                        await roles.demote_driver(helpers.fetch_guild(bot), member_dict['discord_id'])
                        if driver_race_result.irating_old >= constants.PLEB_LINE:
                            if role_change_reason != "":
                                role_change_reason += "\n"  # Add a newline if not the first driver.
                            role_change_reason += (
                                driver_race_result.display_name
                                + (
                                    " has dropped below the pleb line and has been banished from "
                                    "Mount Olypmus to carry out the rest of their days among the peasants."
                                )
                            )

                if env.SUPPRESS_RACE_RESULTS is False and role_change_reason:
                    await channel.send(role_change_reason)

            # Cycle through the driver heat results and if they are a Respo member,
            # overwrite their display_name with their Respo member name.
            # Currently nothing is done with heat results.
            if car_results.driver_heat_results is not None:
                for driver_heat_result in car_results.driver_heat_results:
                    member_dict = await db.fetch_member_dict(iracing_custid=driver_heat_result.cust_id)
                    if member_dict is not None:
                        driver_heat_result.display_name = member_dict['name']

            # 6. Send the report for this car.
            if env.SUPPRESS_RACE_RESULTS is False:

                if multi_report is True:
                    message_text += "just finished playing with each other for hours on end."

                if embed_type == 'compact' or (embed_type == 'auto' and multi_report is False):
                    await send_results_embed_compact(bot, db, channel, car_results)
                else:
                    await send_results_embed(bot, db, channel, car_results)

                race_message = await generate_race_event_message(db, car_results)
                if race_message is not None and race_message != "":
                    await channel.send(race_message)

        # 7. Calculate Respo champ points for race reports.
        # This section calculates points after the new race is accounted for.
        week_data_after = await stats.get_respo_champ_points(
            db,
            all_member_dicts,
            current_year,
            current_quarter,
            current_racing_week
        )
        stats.calc_total_champ_points(week_data_after, constants.RESPO_WEEKS_TO_COUNT)

        week_data_after = dict(sorted(week_data_after.items(), key=lambda item: item[1]['total_points'], reverse=True))
        to_remove = []
        for inner_member in week_data_after:
            if week_data_after[inner_member]['total_points'] == 0:
                to_remove.append(inner_member)

        for inner_member in to_remove:
            week_data_after.pop(inner_member)

        if env.SUPPRESS_RACE_RESULTS is False:
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
                        await channel.send(
                            inner_member
                            + " just moved up the Respo championship leaderboard to "
                            + place_after_string
                            + " place with "
                            + str(week_data_after[inner_member]['total_points'])
                            + " points."
                        )
                else:
                    await channel.send(
                        inner_member
                        + " is now on the Respo championship leaderboard and in "
                        + place_after_string
                        + " place."
                    )

    except Exception as exc:
        traceback_lines = traceback.format_exception(exc)
        traceback_string = ""
        for line in traceback_lines:
            traceback_string += line

        logging.getLogger('respobot.bot').warning(
            f"During generate_race_report() the following exception was caught: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"During generate_race_report() the following exception was caught: {exc}\nTraceback: {traceback_string}"
        )


async def generate_race_event_message(db: BotDatabase, car_results: subsession_summary.CarResultSummary):
    message = ""
    racers = ""
    was_were = ""
    is_are = ""
    himself_herself_themself = ""
    him_her_them = ""
    his_her_their = ""
    he_she_they = ""
    boy_girl_people = ""

    if len(car_results.driver_race_results) > 1:
        racers = "these jokers"
        was_were = "were"
        is_are = "are"
        himself_herself_themself = "themselves"
        him_her_them = "them"
        his_her_their = "their"
        he_she_they = "they"
        boy_girl_people = "people"
    else:
        member_dict = await db.fetch_member_dict(iracing_custid=car_results.driver_race_results[0].cust_id)
        racers = car_results.driver_race_results[0].display_name
        was_were = "was"
        is_are = "is"
        if member_dict['pronoun_type'] == "male":
            himself_herself_themself = "himself"
            him_her_them = "him"
            his_her_their = "his"
            he_she_they = "he"
            boy_girl_people = "boy"
        elif member_dict['pronoun_type'] == "female":
            himself_herself_themself = "herself"
            him_her_them = "her"
            his_her_their = "her"
            he_she_they = "she"
            boy_girl_people = "girl"
        else:
            himself_herself_themself = "themself"
            him_her_them = "them"
            his_her_their = "their"
            he_she_they = "they"
            boy_girl_people = "my friend"

    self_spin_laps = [lap for lap in car_results.lost_control_laps if lap not in car_results.car_contact_laps]

    if car_results.disqualified:
        message = (
            f"Hey, everyone! {he_she_they[0].upper()}{he_she_they[1:]} {was_were} "
            f"disqualified from the race. <:KEKW:821408061960486992>"
        )
    if car_results.did_not_finish:
        message = (
            f"Positively delightful! {he_she_they[0].upper()}{he_she_they[1:]} DNFed "
            "from the race. <:KEKW:821408061960486992>"
        )
    elif car_results.black_flag_laps is not None and len(car_results.black_flag_laps) > 0:
        message = (
            f"Pathetic. {he_she_they[0].upper()}{he_she_they[1:]} {was_were} black flagged "
            "on lap {min(car_results.black_flag_laps)}. <:KEKW:821408061960486992>"
        )
    elif car_results.green_flag_lap_num in car_results.tow_laps:
        message = (
            f"I'm no pro or anything, but I'm pretty sure having to tow on the green flag lap isn't a good strategy."
        )
    elif car_results.checkered_flag_lap_num in car_results.tow_laps:
        message = f"You tried so hard and got so far, but in the end you had to tow on the checkered flag lap."
    elif (
        (
            len([lap for lap in car_results.tow_laps if lap < car_results.green_flag_lap_num]) < 1
            and len(car_results.tow_laps) > 0
        )
        or len(car_results.tow_laps) > 1
    ):
        message = f"You should look into getting a AAA membership with all the towing you do."
    elif len(car_results.car_contact_laps) > 2:
        message = f"Car contact on {len(car_results.car_contact_laps)} separate laps? Settle down a little."
    elif len(self_spin_laps) > 1:
        message = (
            f"How amusing. {he_she_they[0].upper()}{he_she_they[1:]} lost control all by "
            f"{himself_herself_themself} on lap{'s' if len(self_spin_laps) > 1 else ''} "
            f"{helpers.format_grammar_for_item_list(self_spin_laps)}."
        )
    elif car_results.race_finish_position_in_class is not None and car_results.race_finish_position_in_class == 0:
        message = f"Holy shit, {he_she_they} won the damn race. Congrats!"
    elif len(car_results.laps_led) > 0 and car_results.race_finish_position_in_class != 0:
        if len(car_results.laps_led) == 1:
            lap_desc = 'a lap'
        else:
            lap_desc = f"{len(car_results.laps_led)} laps"
        message = f"How sad, {he_she_they} led {lap_desc} but couldn't complete the win."
    elif car_results.race_finish_position_in_class is not None and car_results.race_finish_position_in_class < 3:
        message = f"A podium finish. Great work!"
    elif (
        car_results.race_finish_position_relative_to_car_num is not None
        and car_results.race_finish_position_relative_to_car_num > 9
    ):
        message = (
            f"Respect where respect is due. {he_she_they[0].upper()}{he_she_they[1:]} finished "
            f"{car_results.race_finish_position_relative_to_car_num} positions better than "
            f"{his_her_their} car number."
        )
    elif len(car_results.contact_laps) > 2:
        message = (
            f"You made contact with track objects on {car_results.contact_count} separate laps. "
            f"At some point it's just vandalism."
        )
    elif car_results.race_incidents > 9:
        message = f"{car_results.race_incidents}x? Were you trying for a new high score?"
    elif car_results.laps_down:
        int_laps_down = abs(int(car_results.laps_down))
        message = (
            f"{he_she_they[0].upper()}{he_she_they[1:]} finished {int_laps_down} "
            f"lap{'s' if int_laps_down > 1 else ''} down. Git gud, {boy_girl_people}."
        )
    elif car_results.close_finishers is not None and len(car_results.close_finishers) == 1:
        message = f"It was a photo finish between {him_her_them} and car {car_results.close_finishers[0][0]} "
        if car_results.close_finishers[0][1] > 0:
            message += (
                f"but unfortunately {he_she_they} didn't have it in {him_her_them} and "
                f"{he_she_they} lost by {car_results.close_finishers[0][1]/1000}s."
            )
        else:
            message += (
                f"and miraculously {he_she_they} came out ahead by {abs(car_results.close_finishers[0][1]/1000)}s."
            )
    elif car_results.close_finishers is not None and len(car_results.close_finishers) > 1:
        cars_ahead = [tup[0] for tup in car_results.close_finishers if tup[1] > 0]
        cars_behind = [tup[0] for tup in car_results.close_finishers if tup[1] < 0]
        message = (
            f"It was a photo finish between {him_her_them} and cars "
            f"{helpers.format_grammar_for_item_list([tup[0] for tup in car_results.close_finishers])}. "
        )
        if len(cars_ahead) == 0:
            message += f"Somehow {he_she_they} came out on top of the rest."
        elif len(cars_behind) == 0:
            message += f"It should come as a surprise to no-one that {he_she_they} came out the loser in the bunch."
        else:
            message += (
                f"Car{'s' if len(cars_ahead) > 1 else ''} {helpers.format_grammar_for_item_list(cars_ahead)} "
                f"came out ahead of {him_her_them} and "
                f"car{'s' if len(cars_behind) > 1 else ''} {helpers.format_grammar_for_item_list(cars_behind)} "
                f"finished behind."
            )
    elif len([lap for lap in car_results.car_contact_laps if lap < car_results.green_flag_lap_num]) > 0:
        message = f"What a shame. You couldn't even make it to the green flag before you had car contact."
    elif len([lap for lap in car_results.contact_laps if lap < car_results.green_flag_lap_num]) > 0:
        message = f"You couldn't even make it to the green flag before hitting shit."

    if message == "":
        return None

    return message


async def send_results_embed(
    bot: discord.Bot,
    db: BotDatabase,
    channel: discord.TextChannel,
    car_results: subsession_summary.CarResultSummary
):
    try:
        multi_report = len(car_results.driver_race_results) > 1

        if multi_report is False:
            iracing_custid = car_results.driver_race_results[0].cust_id
            member_dict = await db.fetch_member_dict(iracing_custid=iracing_custid)

        track = car_results.track_name
        config = car_results.track_config_name
        if(config and config != "N/A" and config != ""):
            track += " (" + config + ")"

        if multi_report is False:
            avatar_filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discord_id'], 128)
        else:
            avatar_filepath = env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.RESPO_LOGO_FILENAME

        with open(avatar_filepath, "rb") as f_avatar:
            picture = discord.File(f_avatar, filename="user_avatar.png")

            title = ""
            url = car_results.results_url

            if car_results.league_name is None:
                title = "Race result for "
            else:
                title = "Hosted result for "

            if multi_report is False:
                url += "&custid=" + str(car_results.driver_race_results[0].cust_id)
                title += member_dict['name']
            else:
                title += "Respo Racing"

            embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

            embedVar.set_thumbnail(url="attachment://user_avatar.png")

            if car_results.league_name is None:
                embedVar.add_field(name="Series", value=car_results.series_name, inline=False)
            else:
                embedVar.add_field(name="Session", value=car_results.session_name, inline=False)

            if car_results.league_name is None and car_results.is_multiclass:
                embedVar.add_field(name="Class", value=car_results.car_class_name, inline=True)

            embedVar.add_field(name="Track", value=track, inline=False)

            if car_results.class_strength_of_field is not None and car_results.is_multiclass:
                embedVar.add_field(name="Class SOF", value=str(car_results.class_strength_of_field), inline=False)
            else:
                embedVar.add_field(name="SOF", value=str(car_results.event_strength_of_field), inline=False)

            if car_results.max_team_drivers > 1:
                if car_results.is_multiclass:
                    embedVar.add_field(name="Teams in Class", value=str(car_results.cars_in_class))
                else:
                    embedVar.add_field(name="Teams", value=str(car_results.cars_in_class))
            else:
                if car_results.league_name is None and car_results.max_team_drivers == 1:
                    embedVar.add_field(name="Car #", value=str(car_results.car_number_in_class + 1), inline=True)
                if car_results.is_multiclass:
                    embedVar.add_field(name="Drivers in Class", value=str(car_results.cars_in_class), inline=True)
                else:
                    embedVar.add_field(name="Drivers", value=str(car_results.cars_in_class), inline=True)

            embedVar.add_field(name="Started", value=str(car_results.race_starting_position_in_class + 1), inline=True)
            embedVar.add_field(name="Finished", value=str(car_results.race_finish_position_in_class + 1), inline=True)

            if car_results.league_name is None:
                embedVar.add_field(
                    name="Champ. Pts",
                    value=str(car_results.driver_race_results[0].champ_points),
                    inline=True
                )

                for driver_race_result in car_results.driver_race_results:
                    irating_change = driver_race_result.irating_new - driver_race_result.irating_old

                    if driver_race_result.license_level_new > irConstants.LicenseLevel.A4.value:
                        safety_rating = "P"
                    elif driver_race_result.license_level_new > irConstants.LicenseLevel.B4.value:
                        safety_rating = "A"
                    elif driver_race_result.license_level_new > irConstants.LicenseLevel.C4.value:
                        safety_rating = "B"
                    elif driver_race_result.license_level_new > irConstants.LicenseLevel.D4.value:
                        safety_rating = "C"
                    elif driver_race_result.license_level_new > irConstants.LicenseLevel.R4.value:
                        safety_rating = "D"
                    else:
                        safety_rating = "R"
                    safety_rating += f"{(driver_race_result.license_sub_level_new / 100):.2f}"

                    safety_rating_change_val = (
                        driver_race_result.license_sub_level_new
                        - driver_race_result.license_sub_level_old
                    )
                    if multi_report is False:
                        safety_rating_change = (
                            f"({((safety_rating_change_val) / 100):+.2f}, "
                            f"{driver_race_result.incidents}x)"
                        )
                    else:
                        safety_rating_change = (
                            f"{((safety_rating_change_val) / 100):+.2f}"
                        )

                    if multi_report is False:
                        embedVar.add_field(
                            name=f"iRating",
                            value=f"{driver_race_result.irating_new} ({irating_change:+d})",
                            inline=False
                        )
                        embedVar.add_field(
                            name=f"Safety Rating",
                            value=f"{safety_rating} {safety_rating_change}",
                            inline=False
                        )
                    else:
                        if (driver_race_result.irating_new < 0) or (driver_race_result.laps_complete < 1):
                            embedVar.add_field(name=driver_race_result.display_name, value=f"0 Laps", inline=False)
                        else:
                            info = (
                                f"{irating_change:+d} iR ({driver_race_result.irating_old}), "
                                f"{safety_rating_change} SR ({driver_race_result.incidents}x), "
                                f"{driver_race_result.laps_complete} Laps"
                            )
                            embedVar.add_field(
                                name=driver_race_result.display_name,
                                value=info,
                                inline=False
                            )
            else:
                for driver_race_result in car_results.driver_race_results:
                    if multi_report is False:
                        embedVar.add_field(
                            name=f"Incidents",
                            value=f"{driver_race_result.incidents}x",
                            inline=False
                        )
                    else:
                        embedVar.add_field(
                            name=driver_race_result.display_name,
                            value=f"{driver_race_result.incidents}x",
                            inline=False
                        )

            await channel.send(content="", file=picture, embed=embedVar)

            picture.close()

        if multi_report is False and os.path.exists(avatar_filepath):
            os.remove(avatar_filepath)

    except Exception as exc:
        logging.getLogger('respobot.bot').warning(
            f"During send_results_embed() the following exception was caught: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"During send_results_embed() the following exception was caught: {exc}"
        )


async def send_results_embed_compact(
    bot: discord.bot,
    db: BotDatabase,
    channel: discord.TextChannel,
    car_results: subsession_summary.CarResultSummary
):
    try:
        multi_report = len(car_results.driver_race_results) > 1

        if multi_report is False:
            iracing_custid = car_results.driver_race_results[0].cust_id
            member_dict = await db.fetch_member_dict(iracing_custid=iracing_custid)

        track = car_results.track_name
        config = car_results.track_config_name
        if(config and config != "N/A" and config != ""):
            track += " (" + config + ")"

        if multi_report is False:
            avatar_filepath = await image_gen.generate_avatar_image(channel.guild, member_dict['discord_id'], 128)
        else:
            avatar_filepath = env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + constants.RESPO_LOGO_FILENAME

        with open(avatar_filepath, "rb") as f_avatar:
            picture = discord.File(f_avatar, filename="user_avatar.png")

            title = ""
            url = car_results.results_url

            # if 'hosted_name' not in race_summary_dict:
            if car_results.league_name is None:
                title = "Race result for "
            else:
                title = "Hosted result for "

            if multi_report is False:
                url += "&custid=" + str(car_results.driver_race_results[0].cust_id)
                title += member_dict['name']
            else:
                title += "Respo Racing"

            embedVar = discord.Embed(title=title, description="", color=0xff0000, url=url)

            embedVar.set_thumbnail(url="attachment://user_avatar.png")

            event_description = ""
            field_name = ""

            # if 'hosted_name' not in race_summary_dict:
            if car_results.league_name is None:
                field_name = car_results.series_name
            else:
                field_name = car_results.session_name

            event_description = "at " + track

            embedVar.add_field(name=field_name, value=event_description, inline=False)

            pos_change = int(car_results.race_starting_position_in_class - car_results.race_finish_position_in_class)
            pos_change_str = " (↕0)"

            if pos_change < 0:
                pos_change_str = " (↓" + str(abs(pos_change)) + ")"
            elif pos_change > 0:
                pos_change_str = " (↑" + str(pos_change) + ")"

            result_field_name = (
                "Result: P" + str(car_results.race_finish_position_in_class + 1)
                + " of " + str(car_results.cars_in_class)
                + pos_change_str
            )

            if multi_report is True:
                result_string = ""
                # if 'hosted_name' not in race_summary_dict:
                if car_results.league_name is None:
                    result_string += str(car_results.driver_race_results[0].champ_points) + " pts, "
                if car_results.class_strength_of_field is not None and car_results.is_multiclass:
                    result_string += str(car_results.class_strength_of_field) + " Class SoF"
                else:
                    result_string += str(car_results.event_strength_of_field) + " SoF"

                embedVar.add_field(name=result_field_name, value=result_string, inline=False)

                for driver_race_result in car_results.driver_race_results:
                    result_string = ""
                    # if 'hosted_name' not in race_summary_dict:
                    if car_results.league_name is None:
                        irating_change = driver_race_result.irating_new - driver_race_result.irating_old
                        result_string += f"{irating_change:+d}" + " iR (" + str(driver_race_result.irating_new) + "), "
                    result_string += (
                        str(driver_race_result.incidents) + "x, "
                        + str(driver_race_result.laps_complete) + " laps"
                    )
                    embedVar.add_field(name=driver_race_result.display_name, value=result_string, inline=False)
            else:
                result_string = ""
                if car_results.league_name is None:
                    result_string += str(car_results.driver_race_results[0].champ_points) + " pts"
                    irating_change = (
                        car_results.driver_race_results[0].irating_new
                        - car_results.driver_race_results[0].irating_old
                    )
                    result_string += (
                        ", " + f"{irating_change:+d}"
                        + " iR (" + str(car_results.driver_race_results[0].irating_new) + "), "
                    )
                result_string += str(car_results.driver_race_results[0].incidents) + "x, "
                if car_results.class_strength_of_field is not None:
                    result_string += str(car_results.class_strength_of_field) + " Class SoF"
                else:
                    result_string += str(car_results.event_strength_of_field) + " SoF"
                embedVar.add_field(name=result_field_name, value=result_string, inline=False)
            await channel.send(content="", file=picture, embed=embedVar)

            picture.close()

        if multi_report is False and os.path.exists(avatar_filepath):
            os.remove(avatar_filepath)

    except Exception as exc:
        logging.getLogger('respobot.bot').warning(
            f"During send_results_embed_compact() the following exception was caught: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"During send_results_embed_compact() the following exception was caught: {exc}"
        )
        raise exc

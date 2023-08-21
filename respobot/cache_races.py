from datetime import date, datetime, timezone, timedelta
import logging
import discord
from irslashdata.client import Client as IracingClient
from irslashdata.exceptions import AuthenticationError, ServerDownError
from bot_database import BotDatabase, BotDatabaseError
import constants
import helpers


async def cache_races(bot: discord.bot, db: BotDatabase, ir: IracingClient, iracing_custids: list):

    try:
        (current_season_year, current_season_quarter, _, _, _) = await db.get_current_iracing_week()
    except BotDatabaseError:
        await helpers.send_bot_failure_dm(bot, "During cache_races() an exception was encountered when fetching current iRacing week. Abandoning.")
        return

    try:
        member_info = await ir.get_member_info_new(iracing_custids)
    except AuthenticationError:
        logging.getLogger('respobot.iracing').warning("Authentication to the iRacing server failed when getting member info. Abandoning cache_races().")
        await helpers.send_bot_failure_dm(bot, "Authentication to the iRacing server failed. Abandoning cache_races().")
        return
    except ServerDownError:
        logging.getLogger('respobot.iracing').warning("The iRacing servers are down for maintenance. Abandoning cache_races().")
        await helpers.send_bot_failure_dm(bot, "The iRacing servers are down for maintenance. Abandoning cache_races().")
        return

    for member in member_info:

        if 'cust_id' not in member:
            continue
        iracing_custid = member['cust_id']
        try:
            date_started = date.fromisoformat(member['member_since'])
        except ValueError:
            await helpers.send_bot_failure_dm(bot, f"During cache_raceas() iRacing returned a malformed member_since value for {member['display_name']}. Skipping this member.")
            continue

        year = date_started.year
        logging.getLogger('respobot.bot').info(str(iracing_custid) + " joined iRacing on " + member['member_since'] + " year: " + str(year))
        logging.getLogger('respobot.bot').info("Gathering subsessions for " + member['display_name'] + " back to " + str(year))
        quarter = 1

        subsession_summary_dicts = []

        # Get all hosted sessions
        caching_done = False
        start_time = datetime(date_started.year, 1, 1, tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=90)
        latest_session_end_time = None

        while caching_done is False:
            logging.getLogger('respobot.bot').info("Gathering list of hosted subsessions for " + str(start_time) + " to " + str(end_time))
            finish_range_begin = start_time.isoformat().replace("+00:00", "Z")
            finish_range_end = end_time.isoformat().replace("+00:00", "Z")

            try:
                hosted_results_dicts = await ir.search_hosted_new(cust_id=iracing_custid, finish_range_begin=finish_range_begin, finish_range_end=finish_range_end)
            except AuthenticationError:
                logging.getLogger('respobot.iracing').warning("Authentication to the iRacing server failed when searching hosted races. Abandoning cache_races().")
                await helpers.send_bot_failure_dm(bot, "Authentication to the iRacing server failed. Abandoning cache_races().")
                return
            except ServerDownError:
                logging.getLogger('respobot.iracing').warning("The iRacing servers are down for maintenance. Abandoning cache_races().")
                await helpers.send_bot_failure_dm(bot, "The iRacing servers are down for maintenance. Abandoning cache_races().")
                return

            logging.getLogger('respobot.bot').info(str(len(hosted_results_dicts)) + " subsessions found.")
            # subsession_summary_dicts.append(hosted_results_dicts)
            subsession_summary_dicts += hosted_results_dicts

            start_time = end_time
            end_time = start_time + timedelta(days=90)
            if end_time > datetime.now(timezone.utc):
                end_time = datetime.now(timezone.utc)
            end_time = end_time.replace(second=0, microsecond=0)

            if end_time - start_time < timedelta(seconds=constants.RACE_SCAN_INTERVAL):
                caching_done = True

        # Get all series sessions
        caching_done = False

        while caching_done is False:
            logging.getLogger('respobot.bot').info("Gathering list of series subsessions for " + str(year) + "s" + str(quarter))
            series_results_dicts = await ir.search_results_new(cust_id=iracing_custid, season_year=year, season_quarter=quarter)

            logging.getLogger('respobot.bot').info(str(len(series_results_dicts)) + " subsessions found.")
            # subsession_summary_dicts.append(series_results_dicts)
            subsession_summary_dicts += series_results_dicts

            quarter += 1

            if quarter > 4:
                quarter = 1
                year += 1

            if year > current_season_year or (year == current_season_year and quarter > current_season_quarter):
                caching_done = True

        # Now iterate through all the subsession_summary_dicts and cache the subsession data and laps for each
        latest_session_end_time = None
        subsession_count = 0
        for subsession_summary_dict in subsession_summary_dicts:
            subsession_count += 1
            logging.getLogger('respobot.bot').info(f"Caching subsession {subsession_count} of {len(subsession_summary_dicts)}")
            if 'end_time' in subsession_summary_dict:
                new_race_end_time = datetime.fromisoformat(subsession_summary_dict['end_time'])
                if latest_session_end_time is None or new_race_end_time > latest_session_end_time:
                    latest_session_end_time = new_race_end_time

            new_subsession = await ir.subsession_data_new(subsession_summary_dict['subsession_id'])

            if new_subsession is None:
                continue

            try:
                if await db.is_subsession_in_db(subsession_summary_dict['subsession_id']):
                    continue
            except BotDatabaseError as exc:
                logging.getLogger('respobot.bot').warning(
                    f"During cache_races() an exception was caught when checking if "
                    f"subsession {subsession_summary_dict['subsession_id']} is in the database. "
                    f"Subsession skipped: Exception: {exc}"
                )
                await helpers.send_bot_failure_dm(
                    bot,
                    f"During cache_races() an exception was caught when checking if "
                    f"subsession {subsession_summary_dict['subsession_id']} is in the database. "
                    f"Subsession skipped: Exception: {exc}"
                )
                continue

            # Add the new race to the database
            try:
                await db.add_subsessions([new_subsession])
            except BotDatabaseError as exc:
                logging.getLogger('respobot.bot').warning(
                    f"During cache_races() an exception was encountered when adding "
                    f"subsession {new_subsession['subsession_id']} to the database: {exc}"
                )
                await helpers.send_bot_failure_dm(
                    bot,
                    f"During cache_races() an exception was encountered when adding "
                    f"subsession {new_subsession['subsession_id']} to the database: {exc}"
                )

            # And now for the laps
            if 'session_results' not in new_subsession or len(new_subsession['session_results']) < 1:
                continue

            for session_result_dict in new_subsession['session_results']:
                if 'simsession_number' not in session_result_dict or 'results' not in session_result_dict:
                    continue

                lap_dicts = await ir.lap_data_new(new_subsession['subsession_id'], session_result_dict['simsession_number'])

                if lap_dicts is None or len(lap_dicts) < 1:
                    continue

                try:
                    await db.add_laps(lap_dicts, new_subsession['subsession_id'], session_result_dict['simsession_number'])
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

        # If the person has never done a hosted session or a race, set the latest_session_found to two days ago
        # to make sure we don't miss a session in the off chance they were added right while they were finishing
        # a 24-hour event.
        if latest_session_end_time is None:
            latest_session_end_time = datetime.now(timezone.utc) - timedelta(days=2)

        try:
            await db.set_member_latest_session_found(iracing_custid, latest_session_end_time)
        except BotDatabaseError as exc:
            logging.getLogger('respobot.bot').warning(
                f"During cache_races() an exception was encountered when updating "
                f"last_session_found for {member['display_name']}: {exc}"
            )
            await helpers.send_bot_failure_dm(
                bot,
                f"During cache_races() an exception was encountered when updating "
                f"last_session_found for {member['display_name']}: {exc}"
            )

    logging.getLogger('respobot.bot').info("Done caching races!")

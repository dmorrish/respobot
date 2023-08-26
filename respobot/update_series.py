import logging
import httpx
import traceback
from datetime import datetime, timedelta, timezone
from bot_database import BotDatabase
import constants
from irslashdata.client import Client as IracingClient
from irslashdata import constants as irConstants


async def update_season_dates(
    db: BotDatabase,
    ir: IracingClient,
    season_year: int = None,
    season_quarter: int = None
):

    try:
        series_dicts = await ir.stats_series_new()

        if series_dicts is None or len(series_dicts) < 1:
            return

        if season_year is None or season_quarter is None:
            min_year = 3000
            min_quarter = 4
            max_year = 0
            max_quarter = 0
            for series_dict in series_dicts:
                for season_dict in series_dict['seasons']:
                    if season_dict['season_year'] < min_year:
                        min_year = season_dict['season_year']
                        min_quarter = season_dict['season_quarter']
                    elif season_dict['season_year'] == min_year:
                        if season_dict['season_quarter'] < min_quarter:
                            min_quarter = season_dict['season_quarter']

                    if season_dict['season_year'] > max_year:
                        max_year = season_dict['season_year']
                        max_quarter = season_dict['season_quarter']
                    elif season_dict['season_year'] == max_year:
                        if season_dict['season_quarter'] > max_quarter:
                            max_quarter = season_dict['season_quarter']
        else:
            min_year = season_year
            min_quarter = season_quarter
            max_year = season_year
            max_quarter = season_quarter

        year = min_year
        quarter = min_quarter
        done = False

        season_dicts = []

        while done is False:
            logging.getLogger('respobot.bot').info(f"Updating season dates for {year}s{quarter}")
            result_dicts = await ir.search_results_new(
                season_year=year,
                season_quarter=quarter,
                race_week_num=0,
                series_id=constants.REFERENCE_SERIES,
                official_only=True,
                event_types=[irConstants.EventType.race.value])

            if result_dicts is not None and len(result_dicts) > 0:
                min_start_time = datetime.fromisoformat(result_dicts[0]['start_time'])
                subsession_id = result_dicts[0]['subsession_id']

                for result_dict in result_dicts:
                    new_start_time = datetime.fromisoformat(result_dict['start_time'])
                    if new_start_time < min_start_time:
                        min_start_time = new_start_time
                        subsession_id = result_dict['subsession_id']

                subsession_data = await ir.subsession_data_new(subsession_id)

                if subsession_data is None:
                    continue

                max_weeks = subsession_data['max_weeks']

                start_time = datetime(
                    min_start_time.year,
                    min_start_time.month,
                    min_start_time.day,
                    tzinfo=timezone.utc
                )

                end_time = start_time + timedelta(days=7 * max_weeks)

                new_season_dict = {
                    'season_year': year,
                    'season_quarter': quarter,
                    'start_time': start_time,
                    'end_time': end_time
                }

                season_dicts.append(new_season_dict)
            quarter += 1

            if quarter > 4:
                quarter = 1
                year += 1

            if year >= max_year and quarter > max_quarter:
                done = True
        await db.update_season_dates(season_dicts)
        logging.getLogger('respobot.bot').info("Done updating season_dates table!")
    except httpx.HTTPError:
        logging.getLogger('respobot.bot').warning(
            "Connection to iRacing timed out during the respobot.update_series.update_series_dates() method."
        )
    except RecursionError:
        logging.getLogger('respobot.bot').warning(
            "iRacing client hit the recursion limit during the respobot.update_series.update_series_dates() method."
        )
    except Exception as ex:
        print(traceback.format_exc())
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logging.getLogger('respobot.bot').error(message)

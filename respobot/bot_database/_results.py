"""
/bot_database/_restults.py

Methods that mainly interact with the results table.
"""

import logging
from aiosqlite import Error
from datetime import datetime
from ._queries import *
from irslashdata import constants as irConstants
from bot_database import BotDatabaseError


async def get_subsession_results(
    self,
    subsession_id: int,
    iracing_custid: int = None,
    team_id: int = None,
    simsession_number: int = None,
    simsession_type: int = None
):
    """Get subsession results from the 'results' table. If you provide multiple kwargs,
    only results that match all kwargs will be returned.

    Arguments:
        subsession_id (int): The id of the subsession to grab results from.

    Keyword arguments:
        iracing_custid (int): The iRacing cust_id of the member whose results to return.
        team_id (int): The id of the team whose members you wish to grab results from.
        simsession_number (int): THe number of the subsession to grab results from. 0 is the
                                 main event, -1 is the event before 0, -2 before -1, etc.
        simsession_type (int): The type of simsession to grab results from. See irslashdata.constants.

    Returns:
        A list of dicts containing the results that match the kwargs. Each dict contains a key
        for every column in the 'results' table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT *
        FROM results
        WHERE
            subsession_id = ? AND"""

    parameters = (subsession_id,)

    if iracing_custid is not None:
        query += " cust_id = ? AND"
        parameters += (iracing_custid,)

    if team_id is not None:
        query += " team_id = ? AND"
        parameters += (team_id,)

    if simsession_number is not None:
        query += " simsession_number = ? AND"
        parameters += (simsession_number,)

    if simsession_type is not None:
        query += " simsession_type = ? AND"
        parameters += (simsession_type,)

    query = query[:-4]

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_driver_result_summary() for driver {iracing_custid} in subsession {subsession_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_driver_result_summary() for driver {iracing_custid} in subsession {subsession_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if result_tuples is None or len(result_tuples) < 1:
        return []

    driver_result_dicts = await self._map_tuples_to_dicts(result_tuples, 'results')

    return driver_result_dicts


async def get_champ_points_data(
    self,
    iracing_custid: int,
    season_year: int = None,
    season_quarter: int = None,
    event_type: int = irConstants.EventType.race.value,
    simsession_number: int = 0,
    simsession_type: int = irConstants.SimSessionType.race.value
):
    """Returns pertinent subsession and results data for calculating champ points.

    Arguments:

    Keyword arguments:

    Returns:

    Raises:
    """
    query = """
        SELECT
            subsessions.subsession_id,
            subsessions.series_id,
            subsessions.start_time,
            subsessions.race_week_num,
            subsessions.official_session,
            results.cust_id,
            results.champ_points
        FROM results
        INNER JOIN subsessions
        ON subsessions.subsession_id = results.subsession_id
        WHERE
            results.cust_id = ? AND
    """
    parameters = (iracing_custid,)

    if season_year is not None:
        query += " subsessions.season_year = ? AND"
        parameters += (season_year,)

    if season_quarter is not None:
        query += " subsessions.season_quarter = ? AND"
        parameters += (season_quarter,)

    if event_type is not None:
        query += " subsessions.event_type = ? AND"
        parameters += (event_type,)

    if simsession_number is not None:
        query += " results.simsession_number = ? AND"
        parameters += (simsession_number,)

    if simsession_type is not None:
        query += " results.simsession_type = ? AND"
        parameters += (simsession_type,)

    query = query[0:-4]

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_driver_result_summary() for driver {iracing_custid} in subsession {subsession_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_driver_result_summary() for driver {iracing_custid} in subsession {subsession_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if result_tuples is None or len(result_tuples) < 1:
        return []

    result_dicts = []

    for result_tuple in result_tuples:
        new_dict = {
            "subsession_id": result_tuple[0],
            "series_id": result_tuple[1],
            "start_time": result_tuple[2],
            "race_week_num": result_tuple[3],
            "official_session": result_tuple[4],
            "cust_id": result_tuple[5],
            "champ_points": result_tuple[6]
        }

        try:
            start_time = datetime.fromisoformat(result_tuple[2])
            new_dict["start_time"] = start_time
        except ValueError:
            logging.getLogger('respobot.bot').error(
                f"Invalid datetime string for 'start_time' in subsession {result_tuple[0]}"
            )

        result_dicts.append(new_dict)

    return result_dicts

"""
/bot_database/_restults.py

Methods that mainly interact with the results table.
"""

import logging
from aiosqlite import Error
from ._queries import *


async def get_results(
    self, subsession_id: int,
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

"""
/bot_database/_series.py

Methods that mainly interact with the 'series' table.
"""

import logging
from aiosqlite import Error
from ._queries import *
from bot_database import BotDatabaseError, ErrorCodes


async def is_series_in_series_table(self, series_id):
    """Check if a series given by series_id is in the 'series' table.

    Arguments:
        series_id (int)

    Returns:
        A bool that is True if the series was found in the 'series' table, False otherwise.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT series_id
        FROM series
        WHERE series_id = ?
    """
    parameters = (series_id,)
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_series_in_series_table() fpr series_id {series_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"is_series_in_series_table() fpr series_id {series_id}."
            ),
            ErrorCodes.general_failure.value
        )
    return len(result) > 0


async def get_all_series(self):
    """Get a list of dicts for each series in the 'series' table.

    Arguments:
        None.

    Returns:
        A list of dict object where each key corresponds to a column in the
        'series' table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT *
        FROM series
    """

    try:
        series_tuples = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_all_series()."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_all_series().",
            ErrorCodes.general_failure.value
        )

    series_dicts = await self._map_tuples_to_dicts(series_tuples, 'series')

    return series_dicts


async def get_series_name_from_id(self, series_id: int):
    """Get the name of a series from the series_id.

    Arguments:
        series_id (int)

    Returns:
        A str containing the name of the provided series.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = "SELECT series_name FROM series WHERE series_id = ?"
    parameters = (series_id,)

    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_series_last_run_season() for series_id {series_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_series_last_run_season() for series_id {series_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if len(result) > 1:
        raise BotDatabaseError(
            f"get_series_name_from_id() returned more than one result for series_id = {series_id}.",
            ErrorCodes.general_failure.value
        )
    elif len(result) == 1:
        return result[0][0]
    else:
        return (None, None)

"""
/bot_database/_members.py

Methods that mainly interact with the 'special_events' table.
"""

import logging
from aiosqlite import Error
from datetime import date
from ._queries import *
from bot_database import BotDatabaseError, ErrorCodes


async def get_special_events(self, earliest_date: date = None):
    """Get a list of dicts for each special event in the calendar.
    Optionally, provide an earliest_date to only return events on
    or after that date.

    Arguments:
        member_dict (dict): A dictionary which represents one row from
        the 'members' table. This dictionary should be the result of a
        call to the fetch_member(s) function to ensure proper formatting.

    Returns:
        A list of dict object where each key corresponds to a column in the
        'special_events' table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT *
        FROM special_events
    """

    if earliest_date is not None:
        query += """
        WHERE
            end_date >= ?
        """
        parameters = (earliest_date.isoformat(),)
    else:
        parameters = ()

    query += """
        ORDER BY start_date
    """

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_special_events() for earliest_date {earliest_date}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_special_events() for earliest_date {earliest_date}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) < 1:
        return None

    event_dicts = await self._map_tuples_to_dicts(results, 'special_events')

    return event_dicts


async def add_special_event(
    self,
    name,
    start_date,
    end_date,
    track,
    cars,
    category
):
    """Add a new special event to the calendar.

    Arguments:
        name (str)
        start_date (str): Use YYYY-MM-dd
        end_date (str): Use YYYY-MM-dd
        track (str)
        cars (str): Provide a comma separated list
        catergory (str): one of [road, oval, dirt_road, dirt_oval]

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if name is None or start_date is None or end_date is None or track is None or cars is None or category is None:
        raise BotDatabaseError(
            "You must provide all args to add a special event to the database.",
            ErrorCodes.insufficient_info.value
        )
        return
    elif name == "" or start_date == "" or end_date == "" or track == "" or cars == "" or category == "":
        raise BotDatabaseError(
            "You must provide all args to add a special event to the database.",
            ErrorCodes.insufficient_info.value
        )
        return

    query = """
        INSERT INTO special_events (
            name,
            start_date,
            end_date,
            track,
            cars,
            category
        )
        VALUES (
            ?, ?, ?, ?, ?, ?
        )
    """

    parameters = (name, start_date, end_date, track, cars, category)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during add_special_event() for "
            f"name: {name}, start_date: {start_date}, end_daye: {end_date}, track: {track}, "
            f"cars: {cars}, category: {category}.")
        raise BotDatabaseError("Error adding member.", ErrorCodes.general_failure.value)


async def remove_special_event(self, uid):
    """Remove a special event from the calendar.

    Arguments:
        uid (int)

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        DELETE FROM special_events
        WHERE uid = ?
    """
    parameters = (uid,)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"remove_special_event() for event uid: {uid}")
        raise BotDatabaseError("Error removing member.", ErrorCodes.general_failure.value)


async def edit_special_event(
    self,
    uid: int,
    name: str = None,
    start_date: str = None,
    end_date: str = None,
    track: str = None,
    cars: str = None,
    category: str = None
):
    """Edit a special event in the calendar. Will only update
    the values of the given kwargs.

    Arguments:
        uid (int)

    Keyword arguments:
        name (str)
        start_date (str): Use YYYY-MM-dd
        end_date (str): Use YYYY-MM-dd
        track (str)
        cars (str): Provide a comma separated list
        catergory (str): one of [road, oval, dirt_road, dirt_oval]

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if name is None and start_date is None and end_date is None and track is None and cars is None and category is None:
        logging.getLogger('respobot.database').warning(f"edit_special_event() called with no kwargs. Nothing to edit.")
        raise BotDatabaseError("edit_special_event() called with no kwargs", ErrorCodes.insufficient_info.value)

    query = "UPDATE 'special_events' SET "

    parameters = ()

    if name is not None:
        query += "name = ?,"
        parameters += (name,)

    if start_date is not None:
        query += "start_date = ?,"
        parameters += (start_date,)

    if end_date is not None:
        query += "end_date = ?,"
        parameters += (end_date,)

    if track is not None:
        query += "track = ?,"
        parameters += (track,)

    if cars is not None:
        query += "cars = ?,"
        parameters += (cars,)

    if category is not None:
        query += "category = ?,"
        parameters += (category,)

    # Remove the trailing comma
    query = query[:-1]

    query += " WHERE uid = ?"

    parameters += (uid,)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during edit_special_event() for "
            f"uid: {uid}, name: {name}, start_date: {start_date}, end_date: {end_date}, track: {track}, "
            f"cars: {cars}, category: {category}.")
        raise BotDatabaseError("Error editing special event.", ErrorCodes.general_failure.value)

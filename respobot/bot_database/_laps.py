"""
/bot_database/_laps.py

Methods that mainly interact with the laps table.
"""

import logging
from aiosqlite import Error
from ._queries import *
from bot_database import BotDatabaseError, ErrorCodes


async def add_laps(self, lap_dicts, subsession_id, simsession_number):
    """Add laps to the 'laps' table in the database.

    Arguments:
        lap_dicts (list): A list of lap dicts as returned from the iRacing /Data API.
        subsession_id: The id of the subsession that these laps correspond to.
        simsession_number: The simsession_number that these laps correspond to (see irslashdata.constants)

    Returns:
        None

    Raises:
        BotDatabaseError: Raised for any error when inserting the new laps.
    """
    lap_parameters = []
    for lap_dict in lap_dicts:

        lap_events = ""

        if 'lap_events' in lap_dict and lap_dict['lap_events'] is not None and len(lap_dict['lap_events']) > 0:
            for lap_event in lap_dict['lap_events']:
                lap_events += lap_event + ","
            lap_events = lap_events[:-1]

        lap_parameters.append((
            subsession_id,
            simsession_number,
            lap_dict['group_id'] if 'group_id' in lap_dict else None,
            lap_dict['name'] if 'name' in lap_dict else None,
            lap_dict['cust_id'] if 'cust_id' in lap_dict else None,
            lap_dict['display_name'] if 'display_name' in lap_dict else None,
            lap_dict['lap_number'] if 'lap_number' in lap_dict else None,
            lap_dict['flags'] if 'flags' in lap_dict else None,
            lap_dict['incident'] if 'incident' in lap_dict else None,
            lap_dict['session_time'] if 'session_time' in lap_dict else None,
            lap_dict['session_start_time'] if 'session_start_time' in lap_dict else None,
            lap_dict['lap_time'] if 'lap_time' in lap_dict else None,
            lap_dict['team_fastest_lap'] if 'team_fastest_lap' in lap_dict else None,
            lap_dict['personal_best_lap'] if 'personal_best_lap' in lap_dict else None,
            lap_dict['license_level'] if 'license_level' in lap_dict else None,
            lap_dict['car_number'] if 'car_number' in lap_dict else None,
            lap_events,
            lap_dict['lap_position'] if 'lap_position' in lap_dict else None,
            lap_dict['interval'] if 'interval' in lap_dict else None,
            lap_dict['interval_units'] if 'interval_units' in lap_dict else None,
            lap_dict['fastest_lap'] if 'fastest_lap' in lap_dict else None,
            lap_dict['ai'] if 'ai' in lap_dict else None
        ))

    try:
        await self._execute_write_query(INSERT_LAPS, params=lap_parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add laps(s) from "
            f"subsession {subsession_id}, simsession {simsession_number} to the laps table."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add laps(s) from "
            f"subsession {subsession_id}, simsession {simsession_number} to the laps table."
        )


async def get_laps(self, subsession_id: int, car_number: str = None, iracing_custid: int = None, simsession_number: int = None):
    """Get laps from the 'laps' table in the database.

    Arguments:
        subsession_id: The id of the subsession from which you are gathering laps.
    
    Keyword arguments:
        car_number (str): The car number of the car whose laps to grab. If you specify 
                          cust_id as well, only laps that satisfy BOTH parameters
                          will be returned.
        iracing_custid (int): The cust_id of the driver whose laps to grab. If you specify
                              car_number as well, only laps that saisfy BOTH parameters
                              will be returned.
        simsession_number (int): This simsession from which to grab laps. 0 is the main event,
                                 -1 is the event that preceeds 0, -2 precedes -1, etc.

    Returns:
        A list of dicts where each dict represents a lap and the dict keys correspond to the
        columns in the 'laps' table.

    Raises:
        BotDatabaseError: Raised for any error when getting the laps.
    """
    query = """
        SELECT *
        FROM laps
        WHERE
            subsession_id = ? AND
    """

    parameters = (subsession_id,)

    if car_number is not None:
        query += " car_number = ? AND"
        parameters += (car_number,)

    if iracing_custid is not None:
        query += " cust_id = ? AND"
        parameters += (iracing_custid,)

    if simsession_number is not None:
        query += " simsession_number = ? AND"
        parameters += (simsession_number, )

    query = query[0:-4]

    try:
        lap_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_laps() for "
            f"subsession {subsession_id}, iracing_custid {iracing_custid}, and simsession_number {simsession_number}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_laps() for "
            f"subsession {subsession_id}, iracing_custid {iracing_custid}, and simsession_number {simsession_number}."
        )

    lap_dicts = await self._map_tuples_to_dicts(lap_tuples, 'laps')

    return lap_dicts


async def is_subsession_in_laps_table(self, subsession_id: int):
    """Determine if there are any laps logged for the given subsession.
    This does not determine if ALL the laps have been logged fo the
    subsession. It just determines if ANY lap has been logged.

    Arguments:
        subsession_id: The id of the subsession being checked.

    Returns:
        A bool that is True if the subsession was found in the laps table
        and False otherwise.

    Raises:
        BotDatabaseError: Raised for any error when checking for the subsession.
    """
    query = """
        SELECT subsession_id
        FROM laps
        WHERE subsession_id = ?
    """
    parameters = (subsession_id,)

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_subsession_in_db() for "
            f"subsession_id: {subsession_id}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_subsession_in_db() for "
            f"subsession_id: {subsession_id}.",
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) < 1:
        return False
    else:
        return True

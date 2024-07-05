"""
/bot_database/_current_car_classes.py

Methods that mainly interact with the current_car_classes table.
"""

import logging
from aiosqlite import Error
from ._queries import *
from bot_database import BotDatabaseError


async def get_car_class_num_cars(self, car_class_id):
    """Add laps to the 'laps' table in the database.

    Arguments:
        car_class_id (int): The iRacing car class id.

    Returns:
        The number of cars in that car class.

    Raises:
        BotDatabaseError: Raised for any error when getting the number of cars in the provided class.
    """

    query = """
        SELECT COUNT(car_id)
        FROM current_car_classes
        WHERE
            car_class_id = ?
    """

    parameters = (car_class_id,)

    try:
        results = await self._execute_read_query(query, params=parameters)
        if len(results) > 0:
            (num_cars,) = results[0]
        else:
            num_cars = 0

    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_laps() for "
            f"subsession {subsession_id}, iracing_custid {iracing_custid}, and simsession_number {simsession_number}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_laps() for "
            f"subsession {subsession_id}, iracing_custid {iracing_custid}, and simsession_number {simsession_number}."
        )

    return num_cars

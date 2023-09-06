"""
/bot_database/_quotes.py

Methods that mainly interact with the quotes table.
"""

import logging
from aiosqlite import Error
from ._queries import *
from bot_database import BotDatabaseError


async def get_quotes(
    self,
    quote_id: int = None,
    discord_id: int = None
):
    """Gets all quotes by a specific member or a specific quote based on uid.
    Quotes are returned as a list of dicts where each dict has a key for each column in the quotes table.

    Keyword arguments:
        quote_id (int): The unique id of the quote to fetch. If discord_id is also provided,
                        quote_id takes precedence.
        discord_id (int): The Discord id of the memebr whose quotes to return. If quote_id
                          is also provided, this argument will be ignored.

    Returns:
        A list of dicts where each dict contains the data for one row in the 'quotes' table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if quote_id is not None:
        query = """
            SELECT *
            FROM quotes
            WHERE uid = ?
        """
        parameters = (quote_id,)

    elif discord_id is not None:
        query = """
            SELECT *
            FROM quotes
            WHERE discord_id = ?
        """
        parameters = (discord_id,)
    else:
        return None

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quotes() for "
            f"discord_id {discord_id}, quote_id {quote_id}"
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quotes() for "
            f"discord_id {discord_id}, quote_id {quote_id}",
            ErrorCodes.general_failure.value
        )

    if len(result_tuples) < 1:
        return None

    quote_dicts = await self._map_tuples_to_dicts(result_tuples, 'quotes')

    return quote_dicts


async def is_quote_in_db(self, message_id: int):
    """Check if a specific Discord message has already been added as a quote in the 'quotes' table.'

    Arguments:
        message_id (int): The id of the Discord message being checked.

    Returns:
        A bool that is True if the message provided has been added, False otherwise.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT message_id
        FROM quotes
        WHERE message_id = ?
    """
    parameters = (message_id,)

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_quote_in_db() for message_id {message_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"is_quote_in_db() for message_id {message_id}."
            ),
            ErrorCodes.general_failure.value
        )

    return len(result_tuples) > 0


async def get_quote_leaderboard(self):
    """Generates a list of tuples containing (name, discord_id, quote_count) for each member in the 'memebrs' table.

    Arguments:
        None.

    Returns:
        A list of tuples of the form (name, discord_id, quote_count).

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT members.name, members.discord_id, IFNULL(quote_count,0)
        FROM members
        LEFT OUTER JOIN (
            SELECT quotes.discord_id, COUNT(quotes.discord_id) as quote_count
            FROM quotes
            GROUP BY quotes.discord_id
        ) as quote_leaderboard
        ON members.discord_id = quote_leaderboard.discord_id
        ORDER BY quote_count DESC, members.discord_id
    """

    try:
        results = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_leaderboard().")
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_leaderboard().",
            ErrorCodes.general_failure.value
        )

    return results


async def get_quote_ids(self):
    """Gets the uid of every quote in the database.

    Arguments:
        None.

    Returns:
        A list of ints where each int is the uid of a quote in the 'quotes' table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT uid FROM quotes
        ORDER BY uid
    """

    try:
        results = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_ids()."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_ids().",
            ErrorCodes.general_failure.value
        )

    id_list = []

    for result_tuple in results:
        id_list.append(result_tuple[0])

    return id_list


async def add_quote(self, quote_dict):
    """Adds a new quote to the database.

    Arguments:
        quote_dict (dict): A dict of the form
            quote_dict = {
                "discord_id": 123,
                "message_id": 234,
                "name": "First Last",
                "quote": "The text of the quote",
                "replied_to_name": "First Last",
                "replied_to_quote": "The text of the quote that the original quote was a reply to.",
                "replied_to_message_id": 345
            }

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    quote_tuple = (
        quote_dict['discord_id'] if 'discord_id' in quote_dict else None,
        quote_dict['message_id'] if 'message_id' in quote_dict else None,
        quote_dict['name'] if 'name' in quote_dict else None,
        quote_dict['quote'] if 'quote' in quote_dict else None,
        quote_dict['replied_to_name'] if 'replied_to_name' in quote_dict else None,
        quote_dict['replied_to_quote'] if 'replied_to_quote' in quote_dict else None,
        quote_dict['replied_to_message_id'] if 'replied_to_message_id' in quote_dict else None
    )

    try:
        await self._execute_write_query(INSERT_QUOTE, params=quote_tuple)
    except Error as e:
        if e.sqlite_errorcode == 1555:
            logging.getLogger('respobot.database').warning(
                f"Quote already in database. Did you remember to check before inserting?"
            )
            raise BotDatabaseError(
                f"Quote already in database. Did you remember to check before inserting?",
                ErrorCodes.general_failure.value
            )
        else:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add a quote to the quotes table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to add a quote to the quotes table."
                ),
                ErrorCodes.general_failure.value
            )

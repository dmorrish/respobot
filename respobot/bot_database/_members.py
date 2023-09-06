"""
/bot_database/_members.py

Methods that mainly interact with the 'members' table.
"""

import logging
from aiosqlite import Error
from datetime import datetime, date
from ._queries import *
from irslashdata import constants as irConstants
from bot_database import BotDatabaseError


def _update_member_dict_objects(member_dict: dict):
    """Convert the graph colour retrieved from the database from a
    comma separated string "r,g,b,a" to a list of ints [r, g, b, a]
    and convert and dates/datetimes from iso format strings to objects.

    Arguments:
        member_dict (dict): A dictionary which represents one row from
        the 'members' table. This dictionary should be the result of a
        call to the fetch_member(s) function to ensure proper formatting.

    Returns:
        The updated member_dict object.
    """
    if 'graph_colour' in member_dict and member_dict['graph_colour'] is not None:
        graph_colour_list_text = member_dict['graph_colour'].split(',')
        if len(graph_colour_list_text) >= 4:
            try:
                graph_colour = [
                    int(graph_colour_list_text[0]),
                    int(graph_colour_list_text[1]),
                    int(graph_colour_list_text[2]),
                    int(graph_colour_list_text[3])
                ]
            except ValueError:
                logging.getLogger('respobot.database').warning(
                    f"Member {member_dict['name']} has an invalid ir_member_since value. Not in iso format."
                )
                graph_colour = None
            finally:
                member_dict['graph_colour'] = graph_colour

    if 'latest_session_found' in member_dict and member_dict['latest_session_found'] is not None:
        try:
            latest_session_found = datetime.fromisoformat(member_dict['latest_session_found'])
        except ValueError:
            logging.getLogger('respobot.database').warning(
                f"Member {member_dict['name']} has an invalid latest_session_found value. Not in iso format."
            )
            latest_session_found = None
        finally:
            member_dict['latest_session_found'] = latest_session_found

    if 'ir_member_since' in member_dict and member_dict['ir_member_since'] is not None:
        try:
            ir_member_since = date.fromisoformat(member_dict['ir_member_since'])
        except ValueError:
            logging.getLogger('respobot.database').warning(
                f"Member {member_dict['name']} has an invalid ir_member_since value. Not in iso format."
            )
            ir_member_since = None
        finally:
            member_dict['ir_member_since'] = ir_member_since

    return member_dict


async def fetch_guild_member_ids(self):
    """Get a list of all the Discord ids for the members.

    Arguments:
        None.

    Returns:
        A list of ints containing all the Discord id values for the members.

    Raises:
        BotDatabaseError: Raised for any error when getting the list of ids.
    """
    query = "SELECT discord_id FROM members"

    try:
        result = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_guild_member_ids()."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_guild_member_ids().",
            ErrorCodes.general_failure.value
        )

    guild_ids = []

    for member_tuple in result:
        if len(member_tuple) == 1 and member_tuple[0] is not None:
            guild_ids.append(member_tuple[0])

    return guild_ids


async def fetch_iracing_cust_ids(self):
    """Get a list of all the iRacing cust_ids for the members.

    Arguments:
        None.

    Returns:
        A list of ints containing all the iRacing cust_id values for the members.

    Raises:
        BotDatabaseError: Raised for any error when getting the list of ids.
    """
    query = "SELECT iracing_custid FROM members"

    try:
        cust_ids_tuples = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_iracing_cust_ids()"
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_iracing_cust_ids()",
            ErrorCodes.general_failure.value
        )

    cust_ids = []

    if cust_ids_tuples is not None and len(cust_ids_tuples) > 0:
        for cust_id in cust_ids_tuples:
            cust_ids.append(cust_id[0])

    return cust_ids


async def fetch_name(self, iracing_custid):
    """Get the name of a member based on the iRacing cust_id.

    Arguments:
        iracing_custid (int): The id of the member whose name is being fetched.

    Returns:
        A string representing the name of the member.

    Raises:
        BotDatabaseError: Raised for any errors.
    """
    query = """
        SELECT name
        FROM members
        WHERE iracing_custid = ?
    """
    parameters = (iracing_custid,)

    try:
        tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"fetch_name() for iracing_custid {iracing_custid}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"fetch_name() for iracing_custid {iracing_custid}."
            ),
            ErrorCodes.general_failure.value
        )

    name = None

    if tuples is not None and len(tuples) > 0:
        name = tuples[0][0]

    return name


async def get_member_latest_session_found(self, iracing_custid: int):
    """Get the datetime of the latest logged session end time for the member
    given by the iRacing cust_id.

    Arguments:
        iracing_custid (int): The id of the member.

    Returns:
        A datetime object representing the session end time of their latest logged session.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = f"""
        SELECT latest_session_found
        FROM members
        WHERE iracing_custid = ?
    """
    parameters = (iracing_custid,)

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_member_latest_session_found() for iracing_custid {iracing_custid}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_member_latest_session_found() for iracing_custid {iracing_custid}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) < 1:
        return None
    else:
        try:
            latest_session_found = datetime.fromisoformat(results[0][0])
        except ValueError:
            logging.getLogger('respobot.database').error(
                f"'latest_session_found' found in member info with "
                f"iracing_custid: {iracing_custid} is not in iso format."
            )
            return None
        return latest_session_found


async def set_member_latest_session_found(
    self,
    iracing_custid: int,
    latest_session_found: datetime
):
    """Set the datetime of the latest logged session end time for a member.

    Arguments:
        iracing_custid (int): The id of the member.
        latest_session_found (datetime): The datetime representing the session end time
                                         of the latest session logged for this member.

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if latest_session_found is None:
        latest_session_found_str = None
    else:
        latest_session_found_str = latest_session_found.isoformat().replace('+00:00', 'Z')
    query = f"""
        UPDATE 'members'
        SET latest_session_found = ?
        WHERE iracing_custid = ?
    """
    parameters = (latest_session_found_str, iracing_custid)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"set_member_latest_session_found() for iracing_custid = {iracing_custid}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"set_member_latest_session_found() for iracing_custid = {iracing_custid}."
            ),
            ErrorCodes.general_failure.value
        )


async def get_member_ir(
    self,
    iracing_custid: int,
    category_id: int = irConstants.Category.road.value
):
    """Get the iRating for a member for a specific racing category.

    Arguments:
        iracing_custid (int): The id of the member.

    Keyword arguments:
        category_id (int): The id of the racing category. Defaults to road.

    Returns:
        An int representing the iRating of the member.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT MAX(results.subsession_id), newi_rating
        FROM results
        INNER JOIN subsessions
        ON subsessions.subsession_id = results.subsession_id
        WHERE
            cust_id = ? AND
            track_category_id = ? AND
            results.simsession_number = 0
        ORDER BY results.subsession_id DESC
    """

    parameters = (iracing_custid, category_id)

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_member_ir() for iracing_custid {iracing_custid}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_member_ir() for iracing_custid {iracing_custid}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) != 1:
        return None

    return results[0][1]


async def fetch_member_dict(
    self,
    uid: int = None,
    iracing_custid: int = None,
    discord_id: int = None,
    name: str = None
):
    """Fetch a dict containing the information in the 'members' table for a spcific member.
    The member fetched will be based off the first provided keyword in the order
    uid->iracing_custid->discord_id->name.

    Arguments:
        None.

    Keyword arguments:
        uid (int): The unique row id for the entry in the 'members' table.
        iracing_custid (int): The iRacing cust_id of the memebr.
        discord_id (int): The Discord id of the memeber.
        name (str): The name of the member. Must be an exact match.

    Returns:
        A dict containing the member's info where each key is a column from the members table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT *
        FROM members
    """

    if uid is not None:
        query += """    WHERE uid = ?
        """
        parameters = (uid,)
    elif iracing_custid is not None:
        query += """    WHERE iracing_custid = ?
        """
        parameters = (iracing_custid,)
    elif discord_id is not None:
        query += """    WHERE discord_id = ?
        """
        parameters = (discord_id,)
    elif name is not None:
        query += f"""    WHERE name = ?
        """
        parameters = (name,)
    else:
        error_message = "Error fetching member dict. You must provide either uid, iracing_custid, discord_id, or name."
        logging.getLogger('respobot.database').error(error_message)
        raise BotDatabaseError(error_message, ErrorCodes.insufficient_info.value)

    try:
        tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        if iracing_custid is not None:
            member = iracing_custid
        elif discord_id is not None:
            member = discord_id
        elif name is not None:
            member = name
        else:
            member = "everyone"
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"fetch_member_dict() for {member}.")
        raise BotDatabaseError("Error fetching member dict.", ErrorCodes.general_failure.value)

    if tuples is None or len(tuples) < 1:
        return None

    if len(tuples) > 1:
        error_message = (
            "Error: More than one result found in fetch_member_dict(). "
            "This indicates an issue with the database."
        )
        logging.getLogger('respobot.database').error(error_message)
        raise BotDatabaseError(error_message, ErrorCodes.general_failure.value)

    member_dicts = await self._map_tuples_to_dicts(tuples, 'members')

    # Scan through the resulting dicts and convert the graph colours to a
    # list of values and datetimes/dates to appropriate objects.
    for member_dict in member_dicts:
        _update_member_dict_objects(member_dict)

    return member_dicts[0]


async def fetch_member_dicts(self):
    """Fetch a list of dicts containing the information in the 'members' table for all members.

    Arguments:
        None.

    Returns:
        A list of dicts containing the members' info where each key is a column from the members table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT *
        FROM members
    """

    try:
        tuples = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_member_dicts()."
        )
        raise BotDatabaseError("Error fetching member dicts.", ErrorCodes.general_failure.value)

    if tuples is None or len(tuples) < 1:
        return None

    member_dicts = await self._map_tuples_to_dicts(tuples, 'members')

    # Scan through the resulting dicts and convert the graph colours to a
    # list of values and datetimes/dates to appropriate objects.
    for member_dict in member_dicts:
        _update_member_dict_objects(member_dict)

    return member_dicts


async def add_member(self, name: str, iracing_custid: int, discord_id: int, ir_member_since: str, pronoun_type: str):
    """Add a new entry to the 'members' table.

    Arguments:
        name (str): The name as it will be displayed in all bot responses.
        iracing_custid (int): The member's iRacing cust_id.
        discord_id (int): The member's Discord id.
        ir_member_since (str): The member's iRacing sign-up date in iso format, YYYY-MM-dd
        pronoun_type (str): A string representing the pronouns to use. Should be one of "male", "female", or "neutral"

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        INSERT INTO members (
            name,
            iracing_custid,
            discord_id,
            ir_member_since,
            pronoun_type
        )
        VALUES (
            ?, ?, ?, ?, ?
        )
    """

    parameters = (name, iracing_custid, discord_id, ir_member_since, pronoun_type)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during add_member() for "
            f"name: {name}, iracing_custid: {iracing_custid}, discord_id: {discord_id}, "
            f"ir_member_since: {ir_member_since}.")
        raise BotDatabaseError("Error adding member.", ErrorCodes.general_failure.value)


async def remove_member(self, uid: int):
    """Remove an entry from the 'members' table.

    Arguments:
        uid (int): The row id for the entry in the 'members' table to remove.

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        DELETE FROM members
        WHERE uid = ?"""
    parameters = (uid,)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during remove_member() for uid: {uid}")
        raise BotDatabaseError("Error removing member.", ErrorCodes.general_failure.value)


async def edit_member(
    self,
    uid: int,
    name: str = None,
    iracing_custid: int = None,
    discord_id: int = None,
    ir_member_since: str = None,
    pronoun_type: str = None
):
    """Edit an entry in the 'members' table.

    Arguments:
        uid (int): The row id for the entry in the 'members' table to edit.

    Keyword arguments:
        name (str): The name as it will be displayed in all bot responses.
        iracing_custid (int): The member's iRacing cust_id.
        discord_id (int): The member's Discord id.
        ir_member_since (str): The member's iRacing sign-up date in iso format, YYYY-MM-dd
        pronoun_type (str): A string representing the pronouns to use. Should be one of "male", "female", or "neutral"

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if (
        name is None
        and iracing_custid is None
        and discord_id is None
        and ir_member_since is None
        and pronoun_type is None
    ):
        logging.getLogger('respobot.database').warning(f"edit_member() called with no kwargs. Nothing to edit.")
        raise BotDatabaseError("edit_member() called with no kwargs", ErrorCodes.insufficient_info.value)

    query = "UPDATE 'members' SET "

    parameters = ()

    if name is not None:
        query += "name = ?,"
        parameters += (name,)

    if iracing_custid is not None:
        query += "iracing_custid = ?,"
        parameters += (iracing_custid,)

    if discord_id is not None:
        query += "discord_id = ?,"
        parameters += (discord_id,)

    if ir_member_since is not None:
        query += "ir_member_since = ?,"
        parameters += (ir_member_since,)

    if pronoun_type is not None:
        query += "pronoun_type = ?,"
        parameters += (pronoun_type,)

    # Remove the trailing comma
    query = query[:-1]

    query += " WHERE uid = ?"

    parameters += (uid,)

    try:
        await self._execute_write_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during edit_member() for "
            f"uid: {uid}, name: {name}, iracing_custid: {iracing_custid}, discord_id: {discord_id}, "
            f"ir_member_since: {ir_member_since}, pronoun_type: {pronoun_type}.")
        raise BotDatabaseError("Error editing member.", ErrorCodes.general_failure.value)


async def fetch_graph_colour(self, iracing_custid=None, discord_id=None):
    """Fetch the graph colour for a member and return as a list of ints [r, g, b, a].

    Arguments:
        None.

    Keyword arguments:
        iracing_custid (int): The iRacing cust_id of the member. If discord_id is
                              also provided, iracing_custid will take precedent.
        discord_id (int): The Discord id of the member. If iracing_custid is also
                          provided, it will take priority over discord_id.

    Returns:
        A list of ints representing the graph colour in [r, g, b, a] form.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if iracing_custid is not None:
        query = """
            SELECT graph_colour
            FROM members
            WHERE iracing_custid = ?
        """
        parameters = (iracing_custid,)
    elif discord_id is not None:
        query = """
            SELECT graph_colour
            FROM members
            WHERE discord_id = ?
        """
        parameters = (discord_id,)
    else:
        return None

    try:
        tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"fetch_graph_colour() for iracing_custid {iracing_custid} and discord_id {discord_id}"
        )
        tuples = None
        raise BotDatabaseError(
            (
                f"Error fetching graph_colour from database for "
                f"iracing_custid {iracing_custid} and discord_id {discord_id}"
            ),
            ErrorCodes.general_failure.value
        )

    if tuples is not None and len(tuples) > 0:
        colour_strings = tuples[0][0].split(",")

        if len(colour_strings) != 4:
            logging.getLogger('respobot.database').warning(
                f"graph_colour incorrectly formatted in database for "
                f"iracing_custid:{iracing_custid} discord_id:{discord_id}"
            )
            raise BotDatabaseError(
                (
                    f"Incorrectly formatted graph_colour in database for "
                    f"iracing_custid {iracing_custid} and discord_id {discord_id}"
                ),
                ErrorCodes.value_error.value
            )

        return [colour_strings[0], colour_strings[1], colour_strings[2], colour_strings[3]]

    else:
        return None


async def set_graph_colour(self, graph_colour: list[int], iracing_custid: int = None, discord_id: int = None):
    """Set the graph colour for a member.

    Arguments:
        graph_colour (list): A list of four ints representing the [r, g, b, a] value of the colour.

    Keyword arguments:
        iracing_custid (int): The iRacing cust_id of the member. If discord_id is
                              also provided, iracing_custid will take precedent.
        discord_id (int): The Discord id of the member. If iracing_custid is also
                          provided, it will take priority over discord_id.

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if len(graph_colour) != 4:
        logging.getLogger('respobot.database').error(
            f"Incorrectly formatted graph_colour provded: {graph_colour}. Must be in form [r, g, b, a]."
        )
        raise BotDatabaseError(
            (
                f"Incorrectly formatted graph_colour provded: {graph_colour}. Must be in form [r, g, b, a]."
            ),
            ErrorCodes.value_error.value
        )

    str_graph_colour = (
        str(graph_colour[0]) + "," + str(graph_colour[1]) + "," + str(graph_colour[2]) + "," + str(graph_colour[3])
    )

    if iracing_custid is not None:
        query = """
            UPDATE members
            SET graph_colour = ?
            WHERE iracing_custid = ?
        """
        parameters = (str_graph_colour, iracing_custid)
    elif discord_id is not None:
        query = """
            UPDATE members
            SET graph_colour = ?
            WHERE discord_id = ?
        """
        parameters = (str_graph_colour, discord_id)
    else:
        raise BotDatabaseError(
            "You must provide either iracing_custid or discord_id.",
            ErrorCodes.insufficient_info.value
        )

    try:
        await self._execute_write_query(query, params=parameters)
    except BotDatabaseError:
        raise
    except Error as e:
        member = "custid: " + str(iracing_custid) if iracing_custid is not None else "discord_id: " + str(discord_id)
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
            f"update graph colour to {graph_colour} for {member}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                f"update graph colour to {graph_colour} for {member}."
            ),
            ErrorCodes.general_failure.value
        )

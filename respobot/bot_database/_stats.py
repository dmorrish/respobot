import logging
from aiosqlite import Error
from datetime import datetime
from ._queries import *
from irslashdata import constants as irConstants
from bot_database import BotDatabaseError


async def get_latest_ir(
    self,
    iracing_custid: int = None,
    discord_id: int = None,
    name: str = None,
    category_id: int = irConstants.Category.road.value
):
    """Get the latest iRating for the member specified by iracing_custid, sicord_id, or name (full name).
    If more than one kwarg is provided, they will be considered in the following order:
    iracing_custid->discord_id->name

    Arguments:
        iracing_custid (int): The iRacing cust_id of the member. Will override both discord_id and name.
        discord_id (int): The Discord id of the member. Will override name.
        name (str): The full name of the member.
        category_id (int): The iRacing category id of the iRating to grab. See irslashdata.constants.

    Returns:
        An int representing the latest iRating for the chosen member in the chosen category.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if iracing_custid is None and discord_id is None and name is None:
        raise BotDatabaseError(
            "You must provide either iracing_custid, discord_id, or name.",
            ErrorCodes.insufficient_info.value
        )

    member_dict = await self.fetch_member_dict(iracing_custid=iracing_custid, discord_id=discord_id, name=name)

    if member_dict is None:
        return None

    query = """
        SELECT newi_rating, MAX(subsessions.end_time)
        FROM results
        INNER JOIN subsessions
        ON subsessions.subsession_id = results.subsession_id
        WHERE
            cust_id = ? AND
            subsessions.official_session = 1 AND
            subsessions.license_category_id = ? AND
            results.simsession_type = ? AND
            results.newi_rating > 0
    """
    parameters = (member_dict['iracing_custid'], category_id, irConstants.SimSessionType.race.value)

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        member = iracing_custid if iracing_custid is not None else discord_id if discord_id is not None else name
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_latest_ir() for {member}"
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_latest_ir() for {member}"
            ),
            ErrorCodes.general_failure.value
        )

    if result_tuples is None or len(result_tuples) < 1:
        return None

    return result_tuples[0][0]


async def get_ir_data(
    self,
    iracing_custid: int = None,
    discord_id: int = None,
    name: str = None,
    category_id: int = None
):
    """Fetch the data required to plot an iRating graph. Data is returned as a list of tuples of
    the form (datetime, int) containing (end_time, newi_rating).

    Arguments:
        None.

    Keyword arguments:
        iracing_custid (int): The iRacing cust_id of the member. Will override both discord_id and name.
        discord_id (int): The Discord id of the member. Will override name.
        name (str): The full name of the member.
        category_id (int): The iRacing category id of the iRating data to grab. See irslashdata.constants.

    Returns:
        A list of tuples of the form (datetime, int) containing (end_time, newi_rating).

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if iracing_custid is None and discord_id is None and name is None:
        raise BotDatabaseError(
            "You must provide either iracing_custid, discord_id, or name.",
            ErrorCodes.insufficient_info.value
        )

    member_dict = await self.fetch_member_dict(iracing_custid=iracing_custid, discord_id=discord_id, name=name)

    if category_id is None:
        category_id = 2

    if member_dict is None:
        return None

    query = """
        SELECT
            subsessions.end_time,
            results.newi_rating
        FROM results
        INNER JOIN subsessions
        ON subsessions.subsession_id = results.subsession_id
        WHERE
            results.cust_id = ? AND
            subsessions.official_session = 1 AND
            subsessions.license_category_id = ? AND
            subsessions.track_category_id = ? AND
            results.simsession_type = ? AND
            results.newi_rating > 0
        ORDER BY subsessions.end_time
    """
    parameters = (member_dict['iracing_custid'], category_id, category_id, irConstants.SimSessionType.race.value)

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        member = iracing_custid if iracing_custid is not None else discord_id if discord_id is not None else name
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_ir_data() for member {member}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_ir_data() for member {member}."
            ),
            ErrorCodes.general_failure.value
        )

    converted_tuples = []

    for result_tuple in result_tuples:
        time_point = datetime.fromisoformat(result_tuple[0])
        converted_tuples.append((time_point, result_tuple[1]))

    return converted_tuples


async def get_race_incidents_and_corners(
    self,
    iracing_custid: int,
    series_id: int = None,
    car_class_id: int = None,
    category: int = irConstants.Category.road.value
):
    """Fetch the data required to plot a corners-per-incident graph.
    Data is returned as a list of tuples of the form:
    (datetime, int) containing (end_time, newi_rating).

    Arguments:
        None.

    Keyword arguments:
        iracing_custid (int): The iRacing cust_id of the member. Will override both discord_id and name.
        discord_id (int): The Discord id of the member. Will override name.
        name (str): The full name of the member.
        category_id (int): The iRacing category id of the iRating data to grab. See irslashdata.constants.

    Returns:
        A list of tuples of the form (datetime, int) containing (end_time, newi_rating).

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = f"""
        SELECT
            subsessions.end_time,
            incidents,
            laps_complete * corners_per_lap
        FROM results
        INNER JOIN subsessions
        ON subsessions.subsession_id = results.subsession_id
        WHERE
            cust_id = ? AND
            official_session = 1 AND
            simsession_type = {irConstants.SimSessionType.race.value} AND
            event_type = {irConstants.EventType.race.value} AND
            track_category_id = ?
    """

    parameters = (iracing_custid, category)

    if series_id is not None:
        query += " AND series_id = ?"
        parameters += (series_id,)

    if car_class_id is not None:
        query += " AND car_class_id = ?"
        parameters += (car_class_id,)

    query += " ORDER BY subsessions.subsession_id ASC"

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_race_incidents_and_corners() for member {iracing_custid} and series_id: {series_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_race_incidents_and_corners() for member {iracing_custid} and series_id: {series_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if result_tuples is None or len(result_tuples) < 1:
        return None

    converted_tuples = []

    for result_tuple in result_tuples:
        time_point = datetime.fromisoformat(result_tuple[0])
        converted_tuples.append((time_point, result_tuple[1], result_tuple[2]))

    return converted_tuples


async def get_member_race_results(
    self,
    iracing_custid: int,
    series_id: int = None,
    car_class_id: int = None,
    season_year: int = None,
    season_quarter: int = None,
    license_category_id: int = None,
    official_session: int = 1,
    simsession_type: int = irConstants.SimSessionType.race.value,
    event_type: int = irConstants.EventType.race.value
):
    """Fetch race results as a dict containing pertinent information about the subsession and the result.
    Only results that match every provided kwarg will be returned. Simsession_type and event_type are
    defaulted to only return results from race sessions within race events. See irslashdata.constants.

    Arguments:
        iracing_custid (int)

    Keyword arguments:
        series_id (int)
        car_class_id (int)
        season_year (int)
        season_quarter (int)
        license_category_id (int): See irslashdata.constants
        official_session (int): 1 for official, 0 for not official
        simsession_type (int): See irslashdata.constants
        event_type (int): See irslashdata.constants

    Returns:
        A list of dicts of the form:
        result_dict = {
            "subsession_id": int,
            "laps_led": int,
            "laps_complete": int,
            "reason_out_id": int,
            "champ_points": int,
            "starting_position_in_class": int,
            "finish_position_in_class": int,
            "class_interval": int,
            "oldi_rating": int,
            "newi_rating": int,
            "incidents": int,
            "car_id": int,
            "car_class_id": int,
            "official_session": int,
            "start_time": datetime,
            "event_strength_of_field": int,
            "license_category_id": int,
            "track_category_id": int,
            "race_week_num": int,
            "max_team_driver": int,
        }

    Raises:
        BotDatabaseError: Raised for any error.
    """
    race_dicts = []

    query = """
        SELECT
            results.subsession_id,
            laps_lead,
            laps_complete,
            reason_out_id,
            champ_points,
            starting_position_in_class,
            finish_position_in_class,
            class_interval,
            oldi_rating,
            newi_rating,
            incidents,
            car_id,
            car_class_id,
            official_session,
            start_time,
            event_strength_of_field,
            license_category_id,
            track_category_id,
            race_week_num,
            max_team_drivers
        FROM results
        INNER JOIN subsessions ON subsessions.subsession_id = results.subsession_id
        WHERE cust_id = ? AND"""
    parameters = (iracing_custid,)

    if series_id is not None:
        query += " series_id = ? AND"
        parameters += (series_id,)

    if car_class_id is not None:
        query += " car_class_id = ? AND"
        parameters += (car_class_id,)

    if season_year is not None and season_quarter is not None:
        query += " season_year = ? AND season_quarter = ? AND"
        parameters += (season_year, season_quarter)

    if license_category_id is not None:
        query += " license_category_id = ? AND"
        parameters += (license_category_id,)

    if official_session is not None:
        query += " official_session = ? AND"
        parameters += (official_session,)

    if simsession_type is not None:
        query += " simsession_type = ? AND"
        parameters += (simsession_type,)

    if event_type is not None:
        query += " event_type = ? AND"
        parameters += (event_type,)

    query = query[:-4]

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_race_results() for "
            f"iracing_custid {iracing_custid}, series_id {series_id}, car_class_id {car_class_id}, "
            f"season_year {season_year}, season_quarter {season_quarter}, license_category_id {license_category_id}"
            f"official_session {official_session}, simsession_type {simsession_type}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_race_results() for "
            f"iracing_custid {iracing_custid}, series_id {series_id}, car_class_id {car_class_id}, "
            f"season_year {season_year}, season_quarter {season_quarter}, license_category_id {license_category_id}"
            f"official_session {official_session}, simsession_type {simsession_type}.",
            ErrorCodes.general_failure.value
        )

    if results is None:
        return None

    for result_tuple in results:
        if len(result_tuple) > 19:
            new_race_dict = {}
            new_race_dict['subsession_id'] = result_tuple[0]
            new_race_dict['laps_led'] = result_tuple[1]
            new_race_dict['laps_complete'] = result_tuple[2]
            new_race_dict['reason_out_id'] = result_tuple[3]
            new_race_dict['champ_points'] = result_tuple[4]
            new_race_dict['starting_position_in_class'] = result_tuple[5]
            new_race_dict['finish_position_in_class'] = result_tuple[6]
            new_race_dict['class_interval'] = result_tuple[7]
            new_race_dict['oldi_rating'] = result_tuple[8]
            new_race_dict['newi_rating'] = result_tuple[9]
            new_race_dict['incidents'] = result_tuple[10]
            new_race_dict['car_id'] = result_tuple[11]
            new_race_dict['car_class_id'] = result_tuple[12]
            new_race_dict['official_session'] = result_tuple[13]
            new_race_dict['start_time'] = datetime.fromisoformat(result_tuple[14])
            new_race_dict['event_strength_of_field'] = result_tuple[15]
            new_race_dict['license_category_id'] = result_tuple[16]
            new_race_dict['track_category_id'] = result_tuple[17]
            new_race_dict['race_week_num'] = result_tuple[18]
            new_race_dict['max_team_drivers'] = result_tuple[19]
            race_dicts.append(new_race_dict)
        else:
            return None

    return race_dicts


async def get_member_official_race_subsession_ids(self, iracing_custid, category: int = None):
    """Get a list of subsession_id values for every official race entered by the member.

    Arguments:
        iracing_custid (int)

    Keyword arguments:
        category (int): If None, will return all categories. See irslashdata.constants.

    Returns:
        A list of subsession_id ints.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT subsessions.subsession_id
        FROM subsessions
        INNER JOIN results
        ON results.subsession_id = subsessions.subsession_id
        WHERE
            official_session = 1 AND
            event_type = ? AND
            simsession_number = 0 AND
            cust_id = ? AND"""

    parameters = (irConstants.EventType.race.value, iracing_custid,)

    if category is not None:
        query += " license_category_id = ? AND"
        parameters += (category,)

    query = query[:-4]

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_official_race_subsession_ids() for iracing_custid {iracing_custid}, category {category}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_official_race_subsession_ids() for iracing_custid {iracing_custid}, category {category}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) < 1:
        return []

    race_list = []
    for result_tuple in results:
        race_list.append(result_tuple[0])

    return race_list


async def get_member_series_raced(
    self,
    iracing_custid: int,
    season_year: int = None,
    season_quarter: int = None,
    license_category_id: int = None,
    official_session: int = 1,
    simsession_type: int = irConstants.SimSessionType.race.value
):
    """Get a list of series_ids for every series that a member has raced. Results can be filtered

    Arguments:
        iracing_custid (int)

    Keyword arguments:
        season_year (int)
        season_quarter (int): If provided, must also provide season_year otherwise BotDatabaseError is raised
                              with error code value_error.
        license_category_id (int)
        official_session (int): 1 is official, 0 is unofficial.
        simsession_type (int): See irslashdata.constants.

    Returns:
        A list of ints containing the series_ids raced by the member which match the provided kwargs.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    series_ids = []

    query = """
        SELECT
            series_id
        FROM results
        INNER JOIN subsessions ON subsessions.subsession_id = results.subsession_id
        WHERE cust_id = ? AND"""
    parameters = (iracing_custid,)

    if season_year is not None:
        query += " season_year = ? AND"
        parameters += (season_year,)

    if season_quarter is not None:
        if season_year is None:
            logging.getLogger('respobot.database').error(
                f"Error in get_member_series_raced(). If you provde a season_quarter, you must "
                f" also provide a season_year."
            )
            raise BotDatabaseError(
                (
                    f"Error in get_member_series_raced(). If you provde a season_quarter, you must "
                    f" also provide a season_year."
                ),
                ErrorCodes.value_error.value
            )
        query += " season_quarter = ? AND"
        parameters += (season_quarter,)

    if license_category_id is not None:
        query += " license_category_id = ? AND"
        parameters += (license_category_id,)

    if official_session is not None:
        query += " official_session = ? AND"
        parameters += (official_session,)

    if simsession_type is not None:
        query += " simsession_type = ? AND"
        parameters += (simsession_type,)

    query = query[:-4]

    query += " GROUP BY series_id"

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_series_raced() "
            f"for iracing_custid {iracing_custid}, season_year {season_year}, season_quarter {season_quarter}, "
            f"license_category_id {license_category_id}, official_session {official_session}, "
            f"simsession_type {simsession_type}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_series_raced() "
                f"for iracing_custid {iracing_custid}, season_year {season_year}, season_quarter {season_quarter}, "
                f"license_category_id {license_category_id}, official_session {official_session}, "
                f"simsession_type {simsession_type}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None:
        return None

    for result_tuple in results:
        if len(result_tuple) > 0:
            series_ids.append(result_tuple[0])
        else:
            return None

    return series_ids

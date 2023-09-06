"""
/bot_database/_seasons.py

Methods that mainly interact with the following tables:
    seasons
    season_car_classes
    season_dates
    current_seasons
    current_car_classes
"""

import logging
from aiosqlite import Error
from ._queries import *
import constants
from bot_database import BotDatabaseError


async def is_season_in_seasons_table(self, season_id):
    """Check if a season is already in the seasons table.

    Arguments:
        season_id (int)

    Returns:
        A bool that is True if the season is found, False otherwise.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT season_id
        FROM seasons
        WHERE season_id = ?
    """
    parameters = (season_id, )
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_season_in_season_table() for season_id {season_id}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_season_in_season_table() for season_id {season_id}.", ErrorCodes.general_failure.value
        )
    return len(result) > 0


async def is_car_class_in_season_car_classes_table(self, season_id, car_class_id):
    """Check if a car class is in the 'season_car_classes' table for a specific season.

    Arguments:
        season_id (int)
        car_class_id (int)

    Returns:
        A bool that is True if the car class is found for the specific season.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT season_id
        FROM season_car_classes
        WHERE
            season_id = ? AND
            car_class_id = ?
    """
    parameters = (season_id, car_class_id)
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_car_class_in_season_car_classes_table() for season_id {season_id} and "
            f"car_class_id {car_class_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"is_car_class_in_season_car_classes_table() for season_id {season_id} and "
                f"car_class_id {car_class_id}."
            ),
            ErrorCodes.general_failure.value
        )
    return len(result) > 0


async def is_season_in_season_dates_table(self, season_year, season_quarter):
    """Check if a season has been added to the season_dates table.
    The season dates are determined using a long-running series
    defined by constants.REFERENCE_SERIES

    Arguments:
        season_year (int)
        season_quarter (int)

    Keyword arguments:
        None.

    Returns:
        A bool that is True if the dates for the given season are in the table.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT season_year
        FROM season_dates
        WHERE
            season_year = ? AND
            season_quarter = ?
    """
    parameters = (season_year, season_quarter)
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_season_in_season_dates_table() for season_year {season_year} and "
            f"season_quarter {season_quarter}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"is_season_in_season_dates_table() for season_year {season_year} and "
                f"season_quarter {season_quarter}."
            ),
            ErrorCodes.general_failure.valu
        )
    return len(result) > 0


async def is_car_class_car_in_current_car_classes(self, car_class_id, car_id):
    """Check if a car has already been added to a specific car class in the
    current_car_classes table.

    Arguments:
        car_class_id (int)
        car_id (int)

    Returns:
        A bool that is True if the car class given by car_class_id has an
        entry in the table for the car given by car_id and False otherwise.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT
            car_class_id,
            car_id
        FROM current_car_classes
        WHERE
            car_class_id = ? AND
            car_id = ?
    """
    parameters = (car_class_id, car_id)
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_car_class_car_in_current_car_classes() for car_class_id {car_class_id} "
            f"and car_id {car_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"is_car_class_car_in_current_car_classes() for car_class_id {car_class_id} "
                f"and car_id {car_id}."
            ),
            ErrorCodes.general_failure.value
        )
    return len(result) > 0


async def update_current_seasons(self, current_season_dicts):
    """Update the 'current_seasons' table using JSON as returned from the
    /data/series/seasons iRacing endpoint

    Arguments:
        current_season_dicts (list): A list of dicts as returned from /data/series/seasons.
    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = "DELETE FROM current_seasons"
    try:
        await self._execute_write_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} "
            f"during update_current_seasons() when deleting the existing entries."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"update_current_seasons() when deleting the existing entries."
            ),
            ErrorCodes.general_failure.value
        )

    new_current_season_parameters = []

    for current_season_dict in current_season_dicts:

        if 'season_id' not in current_season_dict or current_season_dict['season_id'] is None:
            continue

        if (
            'allowed_season_members' in current_season_dict
            and current_season_dict['allowed_season_members'] is not None
        ):
            allowed_season_members = ""
            for allowed_season_member in current_season_dict['allowed_season_members']:
                new_member = str(current_season_dict['allowed_season_members'][allowed_season_member]['cust_id'])
                allowed_season_members += new_member + ","
            allowed_season_members = allowed_season_members[:-1]
        else:
            allowed_season_members = None

        if 'car_class_ids' in current_season_dict and current_season_dict['car_class_ids'] is not None:
            car_class_ids = ""
            for car_class_id in current_season_dict['car_class_ids']:
                car_class_ids += str(car_class_id) + ","
            car_class_ids = car_class_ids[:-1]
        else:
            car_class_ids = None

        if 'car_types' in current_season_dict and current_season_dict['car_types'] is not None:
            car_types = ""
            for car_type_dict in current_season_dict['car_types']:
                if 'car_type' in car_type_dict:
                    car_types += str(car_type_dict['car_type']) + ","
            car_types = car_types[:-1]
        else:
            car_types = None

        if 'license_group_types' in current_season_dict and current_season_dict['license_group_types'] is not None:
            license_group_types = ""
            for license_group_type_dict in current_season_dict['license_group_types']:
                if 'license_group_type' in license_group_type_dict:
                    license_group_types += str(license_group_type_dict['license_group_type']) + ","
            license_group_types = license_group_types[:-1]
        else:
            license_group_types = None

        if 'track_types' in current_season_dict and current_season_dict['track_types'] is not None:
            track_types = ""
            for track_type_dict in current_season_dict['track_types']:
                if 'track_type' in track_type_dict:
                    track_types += str(track_type_dict['track_type']) + ","
            track_types = track_types[:-1]
        else:
            track_types = None

        season_tuple = (
            current_season_dict['active'] if 'active' in current_season_dict else None,
            allowed_season_members,
            car_class_ids,
            car_types,
            current_season_dict['caution_laps_do_not_count'] if (
                'caution_laps_do_not_count' in current_season_dict
            ) else None,
            current_season_dict['complete'] if 'complete' in current_season_dict else None,
            current_season_dict['cross_license'] if 'cross_license' in current_season_dict else None,
            current_season_dict['driver_change_rule'] if 'driver_change_rule' in current_season_dict else None,
            current_season_dict['driver_changes'] if 'driver_changes' in current_season_dict else None,
            current_season_dict['drops'] if 'drops' in current_season_dict else None,
            current_season_dict['enable_pitlane_collisions'] if (
                'enable_pitlane_collisions' in current_season_dict
            ) else None,
            current_season_dict['fixed_setup'] if 'fixed_setup' in current_season_dict else None,
            current_season_dict['green_white_checkered_limit'] if (
                'green_white_checkered_limit' in current_season_dict
            ) else None,
            current_season_dict['grid_by_class'] if 'grid_by_class' in current_season_dict else None,
            current_season_dict['hardcore_level'] if 'hardcore_level' in current_season_dict else None,
            current_season_dict['heat_ses_info']['heat_info_id'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_info_id' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['cust_id'] if (
                'heat_ses_info' in current_season_dict
                and 'cust_id' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['hidden'] if (
                'heat_ses_info' in current_season_dict
                and 'hidden' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['created'] if (
                'heat_ses_info' in current_season_dict
                and 'created' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_info_name'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_info_name' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['description'] if (
                'heat_ses_info' in current_season_dict
                and 'description' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['max_entrants'] if (
                'heat_ses_info' in current_season_dict
                and 'max_entrants' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['race_style'] if (
                'heat_ses_info' in current_season_dict
                and 'race_style' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['open_practice'] if (
                'heat_ses_info' in current_season_dict
                and 'open_practice' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['pre_qual_practice_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'pre_qual_practice_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['pre_qual_num_to_main'] if (
                'heat_ses_info' in current_season_dict
                and 'pre_qual_num_to_main' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_style'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_style' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_laps'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_laps' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_num_to_main'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_num_to_main' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_scoring'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_scoring' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_caution_type'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_caution_type' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_open_delay_seconds'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_open_delay_seconds' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['qual_scores_champ_points'] if (
                'heat_ses_info' in current_season_dict
                and 'qual_scores_champ_points' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_laps'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_laps' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_max_field_size'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_max_field_size' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_num_position_to_invert'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_num_position_to_invert' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_caution_type'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_caution_type' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_num_from_each_to_main'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_num_from_each_to_main' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_scores_champ_points'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_scores_champ_points' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_num_to_consolation'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_num_to_consolation' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_num_to_main'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_num_to_main' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_first_max_field_size'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_first_max_field_size' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_first_session_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_first_session_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_first_session_laps'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_first_session_laps' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_delta_max_field_size'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_delta_max_field_size' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_delta_session_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_delta_session_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_delta_session_laps'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_delta_session_laps' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_num_position_to_invert'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_num_position_to_invert' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_scores_champ_points'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_scores_champ_points' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['consolation_run_always'] if (
                'heat_ses_info' in current_season_dict
                and 'consolation_run_always' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['pre_main_practice_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'pre_main_practice_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['main_length_minutes'] if (
                'heat_ses_info' in current_season_dict
                and 'main_length_minutes' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['main_laps'] if (
                'heat_ses_info' in current_season_dict
                and 'main_laps' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['main_max_field_size'] if (
                'heat_ses_info' in current_season_dict
                and 'main_max_field_size' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['main_num_position_to_invert'] if (
                'heat_ses_info' in current_season_dict
                and 'main_num_position_to_invert' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['heat_ses_info']['heat_session_minutes_estimate'] if (
                'heat_ses_info' in current_season_dict
                and 'heat_session_minutes_estimate' in current_season_dict['heat_ses_info']
            ) else None,
            current_season_dict['ignore_license_for_practice'] if (
                'ignore_license_for_practice' in current_season_dict
            ) else None,
            current_season_dict['incident_limit'] if 'incident_limit' in current_season_dict else None,
            current_season_dict['incident_warn_mode'] if 'incident_warn_mode' in current_season_dict else None,
            current_season_dict['incident_warn_param1'] if 'incident_warn_param1' in current_season_dict else None,
            current_season_dict['incident_warn_param2'] if 'incident_warn_param2' in current_season_dict else None,
            current_season_dict['is_heat_racing'] if 'is_heat_racing' in current_season_dict else None,
            current_season_dict['license_group'] if 'license_group' in current_season_dict else None,
            license_group_types,
            current_season_dict['lucky_dog'] if 'lucky_dog' in current_season_dict else None,
            current_season_dict['max_team_drivers'] if 'max_team_drivers' in current_season_dict else None,
            current_season_dict['max_weeks'] if 'max_weeks' in current_season_dict else None,
            current_season_dict['min_team_drivers'] if 'min_team_drivers' in current_season_dict else None,
            current_season_dict['multiclass'] if 'multiclass' in current_season_dict else None,
            current_season_dict['must_use_diff_tire_types_in_race'] if (
                'must_use_diff_tire_types_in_race' in current_season_dict
            ) else None,
            current_season_dict['next_race_session'] if 'next_race_session' in current_season_dict else None,
            current_season_dict['num_opt_laps'] if 'num_opt_laps' in current_season_dict else None,
            current_season_dict['official'] if 'official' in current_season_dict else None,
            current_season_dict['op_duration'] if 'op_duration' in current_season_dict else None,
            current_season_dict['open_practice_session_type_id'] if (
                'open_practice_session_type_id' in current_season_dict
            ) else None,
            current_season_dict['qualifier_must_start_race'] if (
                'qualifier_must_start_race' in current_season_dict
            ) else None,
            current_season_dict['race_week'] if 'race_week' in current_season_dict else None,
            current_season_dict['race_week_to_make_divisions'] if (
                'race_week_to_make_divisions' in current_season_dict
            ) else None,
            current_season_dict['reg_user_count'] if 'reg_user_count' in current_season_dict else None,
            current_season_dict['region_competition'] if 'region_competition' in current_season_dict else None,
            current_season_dict['restrict_by_member'] if 'restrict_by_member' in current_season_dict else None,
            current_season_dict['restrict_to_car'] if 'restrict_to_car' in current_season_dict else None,
            current_season_dict['restrict_viewing'] if 'restrict_viewing' in current_season_dict else None,
            current_season_dict['schedule_description'] if 'schedule_description' in current_season_dict else None,
            current_season_dict['season_name'] if 'season_name' in current_season_dict else None,
            current_season_dict['season_quarter'] if 'season_quarter' in current_season_dict else None,
            current_season_dict['season_short_name'] if 'season_short_name' in current_season_dict else None,
            current_season_dict['season_year'] if 'season_year' in current_season_dict else None,
            current_season_dict['send_to_open_practice'] if 'send_to_open_practice' in current_season_dict else None,
            current_season_dict['series_id'] if 'series_id' in current_season_dict else None,
            current_season_dict['short_parade_lap'] if 'short_parade_lap' in current_season_dict else None,
            current_season_dict['start_date'] if 'start_date' in current_season_dict else None,
            current_season_dict['start_on_qual_tire'] if 'start_on_qual_tire' in current_season_dict else None,
            current_season_dict['start_zone'] if 'start_zone' in current_season_dict else None,
            track_types,
            current_season_dict['unsport_conduct_rule_mode'] if (
                'unsport_conduct_rule_mode' in current_season_dict
            ) else None,
            current_season_dict['season_id'] if 'season_id' in current_season_dict else None
        )

        new_current_season_parameters.append(season_tuple)

    if len(new_current_season_parameters) > 0:
        try:
            await self._execute_write_query(INSERT_CURRENT_SEASONS, params=new_current_season_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add season to the current_seasons table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to add season to the current_seasons table."
                ),
                ErrorCodes.general_failure.value
            )


async def update_seasons(self, series_dicts):
    """Update the 'series', 'seasons', and 'season_car_classes' tables using
    JSON as returned from the /data/series/stats_series iRacing endpoint

    Arguments:
        series_dicts (list): A list of dicts as returned from /data/series/stats_series

    Returns:
        None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    new_series_parameters = []
    existing_series_parameters = []

    new_season_parameters = []
    existing_season_parameters = []

    new_car_class_parameters = []
    existing_car_class_parameters = []

    for series_dict in series_dicts:
        if 'series_id' not in series_dict or series_dict['series_id'] is None:
            continue

        if 'license_group_types' in series_dict and series_dict['license_group_types'] is not None:
            license_group_types = ""
            for license_group_type_dict in series_dict['license_group_types']:
                if 'license_group_type' in license_group_type_dict:
                    license_group_types += str(license_group_type_dict['license_group_type']) + ","
            license_group_types = license_group_types[:-1]
        else:
            license_group_types = None

        if 'allowed_licenses' in series_dict and series_dict['allowed_licenses'] is not None:
            allowed_licenses = ""
            for allowed_license in series_dict['allowed_licenses']:
                if 'min_license_level' in allowed_license and 'max_license_level' in allowed_license:
                    for i in range(allowed_license['min_license_level'], allowed_license['max_license_level'] + 1):
                        allowed_licenses += str(i) + ','
            allowed_licenses = allowed_licenses[:-1]
        else:
            allowed_licenses = None

        series_tuple = (
            series_dict['series_name'] if 'series_name' in series_dict else None,
            series_dict['series_short_name'] if 'series_short_name' in series_dict else None,
            series_dict['category_id'] if 'category_id' in series_dict else None,
            series_dict['category'] if 'category' in series_dict else None,
            series_dict['active'] if 'active' in series_dict else None,
            series_dict['official'] if 'official' in series_dict else None,
            series_dict['fixed_setup'] if 'fixed_setup' in series_dict else None,
            series_dict['search_filters'] if 'search_filters' in series_dict else None,
            series_dict['logo'] if 'logo' in series_dict else None,
            series_dict['license_group'] if 'license_group' in series_dict else None,
            license_group_types,
            allowed_licenses,
            series_dict['series_id'] if 'series_id' in series_dict else None
        )

        try:
            if await self.is_series_in_series_table(int(series_dict['series_id'])) is False:
                new_series_parameters.append(series_tuple)
            else:
                existing_series_parameters.append(series_tuple)
        except BotDatabaseError:
            raise

        if 'seasons' not in series_dict:
            continue

        for season_dict in series_dict['seasons']:

            if 'season_id' not in season_dict or season_dict['season_id'] is None:
                continue

            if 'car_classes' in season_dict and season_dict['car_classes'] is not None:
                for car_class_dict in season_dict['car_classes']:
                    car_class_tuple = (
                        car_class_dict['short_name'] if 'short_name' in car_class_dict else None,
                        car_class_dict['name'] if 'name' in car_class_dict else None,
                        car_class_dict['relative_speed'] if 'relative_speed' in car_class_dict else None,
                        season_dict['season_id'] if 'season_id' in season_dict else None,
                        car_class_dict['car_class_id'] if 'car_class_id' in car_class_dict else None
                    )

                    try:
                        s_id = season_dict['season_id']
                        c_id = car_class_dict['car_class_id']
                        if await self.is_car_class_in_season_car_classes_table(s_id, c_id) is False:
                            new_car_class_parameters.append(car_class_tuple)
                        else:
                            existing_car_class_parameters.append(car_class_tuple)
                    except BotDatabaseError:
                        raise

            if 'license_group_types' in season_dict and season_dict['license_group_types'] is not None:
                license_group_types = ""
                for license_group_type_dict in season_dict['license_group_types']:
                    if 'license_group_type' in license_group_type_dict:
                        license_group_types += str(license_group_type_dict['license_group_type']) + ","
                license_group_types = license_group_types[:-1]
            else:
                license_group_types = None

            max_race_week = None
            if 'race_weeks' in season_dict and season_dict['race_weeks'] is not None:
                max_race_week = -1
                for race_week in season_dict['race_weeks']:
                    if 'track_typerace_week_num' in race_week:
                        if race_week['race_week_num'] > max_race_week:
                            max_race_week = race_week['race_week_num'] + 1
            if max_race_week is not None and max_race_week < 0:
                max_race_week = None

            season_tuple = (
                season_dict['series_id'] if 'series_id' in season_dict else None,
                season_dict['season_name'] if 'season_name' in season_dict else None,
                season_dict['season_short_name'] if 'season_short_name' in season_dict else None,
                season_dict['season_year'] if 'season_year' in season_dict else None,
                season_dict['season_quarter'] if 'season_quarter' in season_dict else None,
                season_dict['active'] if 'active' in season_dict else None,
                season_dict['official'] if 'official' in season_dict else None,
                season_dict['driver_changes'] if 'driver_changes' in season_dict else None,
                season_dict['fixed_setup'] if 'fixed_setup' in season_dict else None,
                season_dict['license_group'] if 'license_group' in season_dict else None,
                license_group_types,
                max_race_week,
                season_dict['season_id'] if 'season_id' in season_dict else None
            )

            try:
                if await self.is_season_in_seasons_table(int(season_dict['season_id'])) is False:
                    new_season_parameters.append(season_tuple)
                else:
                    existing_season_parameters.append(season_tuple)
            except BotDatabaseError:
                raise

    if len(new_season_parameters) > 0:
        try:
            await self._execute_write_query(INSERT_SEASONS, params=new_season_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add new seasons to the seasons table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to add new seasons to the seasons table."
                ),
                ErrorCodes.general_failure.value
            )

    if len(existing_season_parameters) > 0:
        try:
            await self._execute_write_query(UPDATE_SEASONS, params=existing_season_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to update seasons in the seasons table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to update seasons in the seasons table."
                ),
                ErrorCodes.general_failure.value
            )

    if len(new_series_parameters) > 0:
        try:
            await self._execute_write_query(INSERT_SERIES, params=new_series_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add new series to the series table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to add new series to the series table."
                ),
                ErrorCodes.general_failure.value
            )

    if len(existing_series_parameters) > 0:
        try:
            await self._execute_write_query(UPDATE_SERIES, params=existing_series_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to update series in the series table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to update series in the series table."
                ),
                ErrorCodes.general_failure.value
            )

    if len(new_car_class_parameters) > 0:
        try:
            await self._execute_write_query(INSERT_SEASON_CAR_CLASSES, params=new_car_class_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add new car class to the season_car_classes table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    f"trying to add new car class to the season_car_classes table."
                ),
                ErrorCodes.general_failure.value
            )

    if len(existing_car_class_parameters) > 0:
        try:
            await self._execute_write_query(UPDATE_SEASON_CAR_CLASSES, params=existing_car_class_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to update car class in the season_car_classes table."
            )
            raise BotDatabaseError(
                (
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                    "trying to update car class in the season_car_classes table."
                ),
                ErrorCodes.general_failure.value
            )


async def update_season_dates(self, season_dicts):
    """Update the 'season_dates' table using the dates of previous races
    in a long-running series defined by constants.REFERENCE_SERIES

    Arguments:
        season_dicts (list): A list of dicts of the form:
            season_dict = {
                "season_year": int,
                "season_quarter": int,
                "start_time": datetime,
                "end_time": datetime
            }

    Keyword arguments:
        None.

    Returns:
        None

    Raises:
        BotDatabaseError: Raised for any error.
    """
    new_season_parameters = []
    existing_season_parameters = []

    for season_dict in season_dicts:

        if 'season_year' not in season_dict or season_dict['season_year'] is None:
            continue

        if 'season_quarter' not in season_dict or season_dict['season_quarter'] is None:
            continue

        if 'start_time' not in season_dict or season_dict['start_time'] is None:
            continue

        if 'end_time' not in season_dict or season_dict['end_time'] is None:
            continue

        start_time = season_dict['start_time'].isoformat().replace('+00:00', 'Z')
        end_time = season_dict['end_time'].isoformat().replace('+00:00', 'Z')

        season_tuple = (
            start_time,
            end_time,
            season_dict['season_year'],
            season_dict['season_quarter'],
        )

        try:
            year = season_dict['season_year']
            quarter = season_dict['season_quarter']
            if await self.is_season_in_season_dates_table(year, quarter) is False:
                new_season_parameters.append(season_tuple)
            else:
                existing_season_parameters.append(season_tuple)
        except BotDatabaseError:
            raise

    try:
        if len(new_season_parameters) > 0:
            await self._execute_write_query(INSERT_SEASON_DATES, params=new_season_parameters)
        if len(existing_season_parameters) > 0:
            await self._execute_write_query(UPDATE_SEASON_DATES, params=existing_season_parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
            f"trying to add/update {season_dict['season_year']}s{season_dict['season_quarter']} "
            f"in the season_dates table."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add/update {season_dict['season_year']}s{season_dict['season_quarter']} "
                f"in the season_dates table."
            ),
            ErrorCodes.general_failure.value
        )


async def update_current_car_classes(self, car_class_dicts):
    """Update the 'current_car_classes' table using JSON as returned from the /data/carclass/get
    iRacing endpoint at https://members-ng.iracing.com/data/carclass/get

    Arguments:
        car_class_dicts (list): A list of dicts as returned from /data/carclass/get

    Keyword arguments:
        None.

    Returns:
        None

    Raises:
        BotDatabaseError: Raised for any error.
    """
    new_car_class_parameters = []
    existing_car_class_parameters = []

    for car_class_dict in car_class_dicts:

        if 'car_class_id' not in car_class_dict or car_class_dict['car_class_id'] is None:
            continue

        if 'cars_in_class' in car_class_dict and car_class_dict['cars_in_class'] is not None:
            for car_dict in car_class_dict['cars_in_class']:
                """ Queries are designed so that adding a new value and updating a value
                    both have the columns lined up equally so that the same tuple can be
                    applied to either query. """
                car_tuple = (
                    car_dict['car_dirpath'] if 'car_dirpath' in car_dict else None,
                    car_dict['retired'] if 'retired' in car_dict else None,
                    car_class_dict['cust_id'] if 'cust_id' in car_class_dict else None,
                    car_class_dict['name'] if 'name' in car_class_dict else None,
                    car_class_dict['relative_speed'] if 'relative_speed' in car_class_dict else None,
                    car_class_dict['short_name'] if 'short_name' in car_class_dict else None,
                    car_class_dict['car_class_id'] if 'car_class_id' in car_class_dict else None,
                    car_dict['car_id'] if 'car_id' in car_dict else None
                )

                c_class = car_class_dict['car_class_id']
                c_id = car_dict['car_id']
                if await self.is_car_class_car_in_current_car_classes(c_class, c_id) is False:
                    new_car_class_parameters.append(car_tuple)
                else:
                    existing_car_class_parameters.append(car_tuple)

    try:
        if len(new_car_class_parameters) > 0:
            await self._execute_write_query(INSERT_CURRENT_CAR_CLASSES, params=new_car_class_parameters)
        if len(existing_car_class_parameters) > 0:
            await self._execute_write_query(UPDATE_CURRENT_CAR_CLASSES, params=existing_car_class_parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
            f"trying to add subsession {car_class_dict['subsession_id']} the subsessions table."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when "
                f"trying to add subsession {car_class_dict['subsession_id']} the subsessions table."
            ),
            ErrorCodes.general_failure.value
        )


async def is_season_active(self):
    """Determine if there is currently an active season on iRacing.
    This is determined by checking a long-running series defined by
    constants.REFERENCE_SERIES.

    Arguments:
        None.

    Keyword arguments:
        None.

    Returns:
        None

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT COUNT(active)
        FROM seasons
        WHERE series_id = ? AND
        active = 1
    """
    parameters = (constants.REFERENCE_SERIES,)
    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_season_active()."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_season_active()."
            ),
            ErrorCodes.general_failure.value
        )

    return result[0][0] > 0


async def get_current_iracing_week(self, series_id: int = constants.REFERENCE_SERIES):
    """Returns a tuple of (season_year, season_quarter, race_week, max_weeks, active) based on
    the 'current_seasons' table. If series_id is not provided, the info from the reference
    series defined in constants.REFERENCE_SERIES will be used.

    Arguments:
        None.

    Keyword arguments:
        series_id (int)

    Returns:
        A tuple containing (season_year, season_quarter, race_week, max_weeks, active).
        All values are ints where active == 1 if the season is currently active at this
        moment. 'current_seasons' is updated every constants.FAST_LOOP_INTERVAL seconds.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if series_id is None or series_id < 0:
        series_id = constants.REFERENCE_SERIES

    query = f"""
        SELECT
            MAX(season_year) as year,
            quarter,
            race_week,
            max_weeks,
            active
        FROM (
            SELECT
                series_id,
                season_id,
                season_year,
                MAX(season_quarter) AS quarter,
                race_week,
                max_weeks,
                active
            FROM current_seasons
            WHERE series_id = ?
            GROUP BY season_year
        )
    """
    parameters = (series_id,)

    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_current_iracing_week() for series_id {series_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_current_iracing_week() for series_id {series_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if len(result) > 0:
        return result[0]
    else:
        return (None, None, None, None, None)


async def get_season_basic_info(self, series_id: int = None, season_year: int = None, season_quarter: int = None):
    """Returns a list of tuples containing
    (season_id, series_id, season_name, series_name, latest_year, latest_quarter, max_race_week)
    for the latest season for each series in the 'seasons' table that matches the kwargs provided.

    Arguments:
        None.

    Keyword arguments:
        series_id (int)
        season_year (int): Must be provided along with season_quarter otherwise ignored.
        season_quarter (int): Must be provided along with season_year otherwise ignored.

    Returns:
        A list of tuples containing
        (season_id, series_id, season_name, series_name, latest_year, latest_quarter, max_race_week)
        where latest_year and latest_quarter for the last time this series was run.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT
            season_id,
            series.series_id,
            season_name,
            series_name,
            season_year,
            season_quarter,
            max_race_week
        FROM (
            SELECT
                season_name,
                series_id,
                season_id,
                season_year,
                season_quarter,
                max_race_week
            FROM seasons
    """
    parameters = tuple()

    if series_id is not None or (season_year is not None and season_quarter is not None):

        query += "WHERE"

        if series_id is not None:
            query += " series_id = ? AND"
            parameters += (series_id,)

        if season_year is not None and season_quarter is not None:
            query += " season_year = ? AND season_quarter = ? AND"
            parameters += (season_year, season_quarter)

        query = query[:-4]

    query += """
        ORDER BY
            series_id,
            season_year DESC,
            season_quarter DESC
        ) inner_result
        INNER JOIN series
        ON series.series_id = inner_result.series_id
        GROUP BY series.series_id
    """

    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_basic_info() for "
            f"series_id = {series_id}, season_year = {season_year}, season_quarter = {season_quarter}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_basic_info() for "
            f"series_id = {series_id}, season_year = {season_year}, season_quarter = {season_quarter}.",
            ErrorCodes.general_failure.value
        )

    if len(result) > 0:
        return result
    else:
        return None


async def get_series_last_run_season(self, series_id: int):
    """Returns a tuple of (season_year, season_quarter) representing the last time a series was run.

    Arguments:
        series_id (int)

    Returns:
        A tuple containing (season_year, season_quarter) representing the last time the series ran. If
        no matches are found, (None, None) is returned.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT
            season_year,
            season_quarter
        FROM (
            SELECT
                series_id,
                season_year,
                season_quarter
            FROM seasons
            WHERE series_id = ?
            ORDER BY
                season_year DESC,
                season_quarter DESC
        )
        GROUP BY series_id
    """
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

    if len(result) > 0:
        return result[0]
    else:
        return (None, None)


async def get_series_id_from_season_name(
    self,
    season_name: str,
    season_year: int = None,
    season_quarter: int = None
):
    """Search the 'seasons' table for a matching season_name and return the series_id.
    If you provide season_year and season_quarter, then only the seasons in a specific
    iRacing season will be checked.

    Arguments:
        season_name

    Keyword arguments:
        season_year (int): Must be provided along with season_quarter otherwise ignored.
        season_quarter (int): Must be provided along with season_year otherwise ignored.

    Returns:
        An int representing the series_id if found, otherwise None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    try:
        series_tuples = await self.get_season_basic_info(season_year=season_year, season_quarter=season_quarter)
    except BotDatabaseError:
        raise

    for series_tuple in series_tuples:
        if series_tuple[2] == season_name:
            return series_tuple[1]

    return None


async def get_car_class_id_from_car_class_name(
    self,
    car_class_name: str,
    season_id: int = None,
    series_id: int = None,
    season_year: int = None,
    season_quarter: int = None
):
    """Search the 'season_car_classes' table for a matching car_class_name
    and return the car_class_id. If you provide a season_id, only that specific
    series season will be searched. If you provide a series_id, without a
    season_year and season_quarter, the latest season in that series will be searched.
    If you only provide season_year and season_quarter, then all series that ran that
    season will be searched.

    Arguments:
        car_class_name (str)

    Keyword arguments:
        season_id (int)
        series_id (int)
        season_year (int): Must be provided with season_quarter, otherwise ignored.
        season_quarter (int): Must be provided with season_year, otherwise ignored.

    Returns:
        An int representing the car_class_id if found, otherwise None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    try:
        car_class_tuples = await self.get_season_car_classes(
            season_id=season_id,
            series_id=series_id,
            season_year=season_year,
            season_quarter=season_quarter
        )
    except BotDatabaseError:
        raise

    if len(car_class_tuples) < 1:
        return None

    for car_class_tuple in car_class_tuples:
        if car_class_tuple[2] == car_class_name:
            return car_class_tuple[1]

    return None


async def get_season_car_classes(
    self,
    season_id: int = None,
    series_id: int = None,
    season_year: int = None,
    season_quarter: int = None
):
    """Returns a list of (season_id, car_class_id, name) for each class in a specific season.
        If you specify a season_id, that will be used. If you specify a series_id, the
        last time that series was run will be used. If you specify a season_year and season_quarter
        but not season_id or series_id, all car classes for that season_year and season_quarter
        will be returned.

    Arguments:
        None.

    Keyword arguments:
        season_id (int)
        series_id (int)
        season_year (int)
        season_quarter (int)

    Returns:
        A list of tuples containing (season_id, car_class_id, name).

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if season_id is not None:
        query = """
            SELECT
                season_car_classes.season_id,
                car_class_id,
                name
            FROM season_car_classes
            INNER JOIN seasons
            ON seasons.season_id = season_car_classes.season_id
            WHERE
                seasons.season_id = ?
        """
        parameters = (season_id,)
    elif series_id is not None:
        if season_year is None or season_quarter is None:
            try:
                (season_year, season_quarter) = await self.get_series_last_run_season(series_id)
            except BotDatabaseError:
                raise

        if season_year is not None and season_quarter is not None:
            query = """
                SELECT
                    season_car_classes.season_id,
                    season_car_classes.car_class_id,
                    season_car_classes.name
                FROM season_car_classes
                INNER JOIN seasons
                ON seasons.season_id = season_car_classes.season_id
                WHERE
                    seasons.series_id = ? AND
                    season_year = ? AND
                    season_quarter = ?
            """
            parameters = (series_id, season_year, season_quarter)
    elif season_year is not None and season_quarter is not None:
        query = """
            SELECT
                seasons.season_id,
                car_class_id,
                name
            FROM season_car_classes
            INNER JOIN seasons
            ON seasons.season_id = season_car_classes.season_id
            WHERE
                seasons.season_year = ? AND
                seasons.season_quarter = ?
        """
        parameters = (season_year, season_quarter)
    else:
        return []

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_season_car_classes() for season_id {season_id}, series_id {series_id}, "
            f"season_year {season_year}, season_quarter {season_quarter}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_season_car_classes() for season_id {season_id}, series_id {series_id}, "
                f"season_year {season_year}, season_quarter {season_quarter}."
            ),
            ErrorCodes.general_failure.value
        )

    return results


async def get_season_car_classes_for_all_series(self, season_year: int, season_quarter: int):
    """Returns a list of (season_id, car_class_id, name) for each car class in a specific season.

    Arguments:
        season_year (int)
        season_quarter (int)

    Returns:
        A list of tuples containing (season_id, car_class_id, name)

    Raises:
        BotDatabaseError: Raised for any error.
    """
    if season_year is not None and season_quarter is not None:
        query = """
            SELECT
                seasons.season_id,
                car_class_id,
                name
            FROM season_car_classes
            INNER JOIN seasons
            ON seasons.season_id = season_car_classes.season_id
            WHERE
                seasons.season_year = ? AND
                seasons.season_quarter = ?
        """
        parameters = (season_year, season_quarter)
    else:
        return []

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_season_car_classes_for_all_series() for season_year {season_year}, "
            f"season_quarter {season_quarter}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_season_car_classes_for_all_series() for season_year {season_year}, "
                f"season_quarter {season_quarter}."
            ),
            ErrorCodes.general_failure.value
        )

    return results


async def get_season_id(self, series_id: int, season_year: int, season_quarter: int):
    """Get the season_id for a specific series for an iRacing season.
    Returns None if this series was not run in the given season.

    Arguments:
        series_id (int)
        season_year (int)
        season_quarter (int)

    Returns:
        An int containing the season_id if found, otherwise None.

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT season_id
        FROM seasons
        WHERE
            series_id = ? AND
            season_year = ? AND
            season_quarter = ?
    """
    parameters = (series_id, season_year, season_quarter)

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_id() for "
            f"series_id: {series_id}, season_year {season_year}, season_quarter {season_quarter}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_id() for "
            f"series_id: {series_id}, season_year {season_year}, season_quarter {season_quarter}.",
            ErrorCodes.general_failure.value
        )

    if len(results) < 1:
        return None
    else:
        return results[0][0]


async def get_season_dates(self):
    """Get the start and end times for all rows in the 'season_dates' table.

    Arguments:
        None.

    Returns:
        A list of tuples containing (season_year, season_quarter, start_time, end_time).

    Raises:
        BotDatabaseError: Raised for any error.
    """
    query = """
        SELECT
            season_year,
            season_quarter,
            start_time,
            end_time
        FROM season_dates
        ORDER BY start_time ASC
    """

    try:
        result = await self._execute_read_query(query)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_season_dates()."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_season_dates()."
            ),
            ErrorCodes.general_failure.value
        )

    if result is None or len(result) < 1:
        return None

    return result

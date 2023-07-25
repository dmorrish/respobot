# import respobot_logging as log
import logging
from datetime import datetime, date
import aiosqlite
from aiosqlite import Error
import bot_database_queries as dbq
from pyracing import constants as pyracingConstants
from enum import Enum


class ErrorCodes(Enum):
    insert_collision = 100
    insufficient_info = 101
    general_failure = 102


class BotDatabaseError(Exception):
    """Raised when there is any issue communicating with the database"""

    def __init__(self, message, error_code: int = None):
        self.error_code = error_code
        super(BotDatabaseError, self).__init__(message)


class BotDatabase:
    def __init__(self, filename):
        self.filename = filename

    async def init(self):
        try:
            if not await self._table_exists('members'):
                logging.getLogger('respobot.database').info("creating table: members")
                await self.execute_query(dbq.CREATE_TABLE_MEMBERS)

            if not await self._table_exists('quotes'):
                logging.getLogger('respobot.database').info("creating table: quotes")
                await self.execute_query(dbq.CREATE_TABLE_QUOTES)
                await self.execute_query(dbq.CREATE_INDEX_QUOTES)

            if not await self._table_exists('subsessions'):
                logging.getLogger('respobot.database').info("creating table: subsessions")
                await self.execute_query(dbq.CREATE_TABLE_SUBSESSIONS)
                await self.execute_query(dbq.CREATE_INDEX_SUBSESSIONS_ID)

            if not await self._table_exists('results'):
                logging.getLogger('respobot.database').info("creating table: results")
                await self.execute_query(dbq.CREATE_TABLE_RESULTS)
                await self.execute_query(dbq.INDEX_RESULTS_SESNUM_SUBID_CUSTID)
                await self.execute_query(dbq.INDEX_RESULTS_IRATING_GRAPH)

            if not await self._table_exists('current_seasons'):
                logging.getLogger('respobot.database').info("creating table: current_seasons")
                await self.execute_query(dbq.CREATE_TABLE_CURRENT_SEASONS)

            if not await self._table_exists('series'):
                logging.getLogger('respobot.database').info("creating table: series")
                await self.execute_query(dbq.CREATE_TABLE_SERIES)

            if not await self._table_exists('seasons'):
                logging.getLogger('respobot.database').info("creating table: seasons")
                await self.execute_query(dbq.CREATE_TABLE_SEASONS)

            if not await self._table_exists('season_car_classes'):
                logging.getLogger('respobot.database').info("creating table: season_car_classes")
                await self.execute_query(dbq.CREATE_TABLE_SEASON_CAR_CLASSES)

            if not await self._table_exists('current_car_classes'):
                logging.getLogger('respobot.database').info("creating table: current_car_classes")
                await self.execute_query(dbq.CREATE_TABLE_CURRENT_CAR_CLASSES)

            if not await self._table_exists('season_dates'):
                logging.getLogger('respobot.database').info("creating table: season_dates")
                await self.execute_query(dbq.CREATE_TABLE_SEASON_DATES)

            if not await self._table_exists('special_events'):
                logging.getLogger('respobot.database').info("creating table: special_events")
                await self.execute_query(dbq.CREATE_TABLE_SPECIAL_EVENTS)

                logging.getLogger('respobot.database').info("Done initializing database.")
        except Error:
            logging.getLogger('respobot.database').error("Error initializing database.")
        else:
            logging.getLogger('respobot.database').info("Successfully initialized the database.")

        return self

    async def _table_exists(self, table_name: str):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        parameters = (table_name,)
        async with aiosqlite.connect(self.filename) as connection:
            async with connection.execute(query, parameters) as cursor:
                try:
                    result = await cursor.fetchall()
                    return len(result) > 0
                except Error as e:
                    logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when running _table_exists() with query:\n{query}\nwith params:\n{parameters}")

    async def execute_query(self, query, params=None):
        try:
            async with aiosqlite.connect(self.filename) as connection:
                async with connection.cursor() as cursor:
                    if params is None:
                        await cursor.execute(query)
                    elif isinstance(params, tuple):
                        await cursor.execute(query, params)
                    elif isinstance(params, list):
                        await cursor.executemany(query, params)
                    else:
                        raise Error("If you pass params into execute_query() they must be a tuple or a list of tuples")
                    await connection.commit()
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when running execute_query() with query:\n{query}\nwith params:\n{params}")
            raise e

    async def execute_read_query(self, query, params=None):
        try:
            async with aiosqlite.connect(self.filename) as connection:
                async with connection.cursor() as cursor:
                    result = None
                    if params is None:
                        await cursor.execute(query)
                    elif isinstance(params, tuple):
                        await cursor.execute(query, params)
                    elif isinstance(params, list):
                        await cursor.executemany(query, params)
                    else:
                        raise Error("If you pass params into execute_read_query() they must be a tuple or a list of tuples")
                    result = await cursor.fetchall()
                    return result
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when running execute_read_query() with query:\n{query}\nwith params:\n{params}")
            raise e

    async def add_subsessions(self, subsession_dicts):
        for subsession_dict in subsession_dicts:

            subsession_parameters = []
            result_parameters = []

            subsession_parameters.append((
                subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                subsession_dict['season_id'] if 'season_id' in subsession_dict else None,
                subsession_dict['season_name'] if 'season_name' in subsession_dict else None,
                subsession_dict['season_short_name'] if 'season_short_name' in subsession_dict else None,
                subsession_dict['season_year'] if 'season_year' in subsession_dict else None,
                subsession_dict['season_quarter'] if 'season_quarter' in subsession_dict else None,
                subsession_dict['series_id'] if 'series_id' in subsession_dict else None,
                subsession_dict['series_name'] if 'series_name' in subsession_dict else None,
                subsession_dict['series_short_name'] if 'series_short_name' in subsession_dict else None,
                subsession_dict['series_logo'] if 'series_logo' in subsession_dict else None,
                subsession_dict['race_week_num'] if 'race_week_num' in subsession_dict else None,
                subsession_dict['session_id'] if 'session_id' in subsession_dict else None,
                subsession_dict['license_category_id'] if 'license_category_id' in subsession_dict else None,
                subsession_dict['license_category'] if 'license_category' in subsession_dict else None,
                subsession_dict['private_session_id'] if 'private_session_id' in subsession_dict else None,
                subsession_dict['host_id'] if 'host_id' in subsession_dict else None,
                subsession_dict['session_name'] if 'session_name' in subsession_dict else None,
                subsession_dict['league_id'] if 'league_id' in subsession_dict else None,
                subsession_dict['league_name'] if 'league_name' in subsession_dict else None,
                subsession_dict['league_season_id'] if 'league_season_id' in subsession_dict else None,
                subsession_dict['league_season_name'] if 'league_season_name' in subsession_dict else None,
                subsession_dict['restrict_results'] if 'restrict_results' in subsession_dict else None,
                subsession_dict['start_time'] if 'start_time' in subsession_dict else None,
                subsession_dict['end_time'] if 'end_time' in subsession_dict else None,
                subsession_dict['num_laps_for_qual_average'] if 'num_laps_for_qual_average' in subsession_dict else None,
                subsession_dict['num_laps_for_solo_average'] if 'num_laps_for_solo_average' in subsession_dict else None,
                subsession_dict['corners_per_lap'] if 'corners_per_lap' in subsession_dict else None,
                subsession_dict['caution_type'] if 'caution_type' in subsession_dict else None,
                subsession_dict['event_type'] if 'event_type' in subsession_dict else None,
                subsession_dict['event_type_name'] if 'event_type_name' in subsession_dict else None,
                subsession_dict['driver_changes'] if 'driver_changes' in subsession_dict else None,
                subsession_dict['min_team_drivers'] if 'min_team_drivers' in subsession_dict else None,
                subsession_dict['max_team_drivers'] if 'max_team_drivers' in subsession_dict else None,
                subsession_dict['driver_change_rule'] if 'driver_change_rule' in subsession_dict else None,
                subsession_dict['driver_change_param1'] if 'driver_change_param1' in subsession_dict else None,
                subsession_dict['driver_change_param2'] if 'driver_change_param2' in subsession_dict else None,
                subsession_dict['max_weeks'] if 'max_weeks' in subsession_dict else None,
                subsession_dict['points_type'] if 'points_type' in subsession_dict else None,
                subsession_dict['event_strength_of_field'] if 'event_strength_of_field' in subsession_dict else None,
                subsession_dict['event_average_lap'] if 'event_average_lap' in subsession_dict else None,
                subsession_dict['event_laps_complete'] if 'event_laps_complete' in subsession_dict else None,
                subsession_dict['num_cautions'] if 'num_cautions' in subsession_dict else None,
                subsession_dict['num_caution_laps'] if 'num_caution_laps' in subsession_dict else None,
                subsession_dict['num_lead_changes'] if 'num_lead_changes' in subsession_dict else None,
                subsession_dict['official_session'] if 'official_session' in subsession_dict else None,
                subsession_dict['heat_info_id'] if 'heat_info_id' in subsession_dict else None,
                subsession_dict['special_event_type'] if 'special_event_type' in subsession_dict else None,
                subsession_dict['damage_model'] if 'damage_model' in subsession_dict else None,
                subsession_dict['can_protest'] if 'can_protest' in subsession_dict else None,
                subsession_dict['cooldown_minutes'] if 'cooldown_minutes' in subsession_dict else None,
                subsession_dict['limit_minutes'] if 'limit_minutes' in subsession_dict else None,
                subsession_dict['track']['track_id'] if ('track' in subsession_dict and 'track_id' in subsession_dict['track']) else None,
                subsession_dict['track']['track_name'] if ('track' in subsession_dict and 'track_name' in subsession_dict['track']) else None,
                subsession_dict['track']['config_name'] if ('track' in subsession_dict and 'config_name' in subsession_dict['track']) else None,
                subsession_dict['track']['category_id'] if ('track' in subsession_dict and 'category_id' in subsession_dict['track']) else None,
                subsession_dict['track']['category'] if ('track' in subsession_dict and 'category' in subsession_dict['track']) else None,
                subsession_dict['weather']['version'] if ('weather' in subsession_dict and 'version' in subsession_dict['weather']) else None,
                subsession_dict['weather']['type'] if ('weather' in subsession_dict and 'type' in subsession_dict['weather']) else None,
                subsession_dict['weather']['temp_units'] if ('weather' in subsession_dict and 'temp_units' in subsession_dict['weather']) else None,
                subsession_dict['weather']['temp_value'] if ('weather' in subsession_dict and 'temp_value' in subsession_dict['weather']) else None,
                subsession_dict['weather']['rel_humidity'] if ('weather' in subsession_dict and 'rel_humidity' in subsession_dict['weather']) else None,
                subsession_dict['weather']['fog'] if ('weather' in subsession_dict and 'fog' in subsession_dict['weather']) else None,
                subsession_dict['weather']['wind_dir'] if ('weather' in subsession_dict and 'wind_dir' in subsession_dict['weather']) else None,
                subsession_dict['weather']['wind_units'] if ('weather' in subsession_dict and 'wind_units' in subsession_dict['weather']) else None,
                subsession_dict['weather']['wind_value'] if ('weather' in subsession_dict and 'wind_value' in subsession_dict['weather']) else None,
                subsession_dict['weather']['skies'] if ('weather' in subsession_dict and 'skies' in subsession_dict['weather']) else None,
                subsession_dict['weather']['weather_var_initial'] if ('weather' in subsession_dict and 'weather_var_initial' in subsession_dict['weather']) else None,
                subsession_dict['weather']['weather_var_ongoing'] if ('weather' in subsession_dict and 'weather_var_ongoing' in subsession_dict['weather']) else None,
                subsession_dict['weather']['allow_fog'] if ('weather' in subsession_dict and 'allow_fog' in subsession_dict['weather']) else None,
                subsession_dict['weather']['track_water'] if ('weather' in subsession_dict and 'track_water' in subsession_dict['weather']) else None,
                subsession_dict['weather']['precip_option'] if ('weather' in subsession_dict and 'precip_option' in subsession_dict['weather']) else None,
                subsession_dict['weather']['time_of_day'] if ('weather' in subsession_dict and 'time_of_day' in subsession_dict['weather']) else None,
                subsession_dict['weather']['simulated_start_utc_time'] if ('weather' in subsession_dict and 'simulated_start_utc_time' in subsession_dict['weather']) else None,
                subsession_dict['weather']['simulated_start_utc_offset'] if ('weather' in subsession_dict and 'simulated_start_utc_offset' in subsession_dict['weather']) else None,
                subsession_dict['track_state']['leave_marbles'] if ('track_state' in subsession_dict and 'leave_marbles' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['practice_rubber'] if ('track_state' in subsession_dict and 'practice_rubber' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['qualify_rubber'] if ('track_state' in subsession_dict and 'qualify_rubber' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['warmup_rubber'] if ('track_state' in subsession_dict and 'warmup_rubber' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['race_rubber'] if ('track_state' in subsession_dict and 'race_rubber' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['practice_grip_compound'] if ('track_state' in subsession_dict and 'practice_grip_compound' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['qualify_grip_compound'] if ('track_state' in subsession_dict and 'qualify_grip_compound' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['warmup_grip_compound'] if ('track_state' in subsession_dict and 'warmup_grip_compound' in subsession_dict['track_state']) else None,
                subsession_dict['track_state']['race_grip_compound'] if ('track_state' in subsession_dict and 'race_grip_compound' in subsession_dict['track_state']) else None,
                subsession_dict['race_summary']['num_opt_laps'] if ('race_summary' in subsession_dict and 'num_opt_laps' in subsession_dict['race_summary']) else None,
                subsession_dict['race_summary']['has_opt_path'] if ('race_summary' in subsession_dict and 'has_opt_path' in subsession_dict['race_summary']) else None,
                subsession_dict['race_summary']['special_event_type'] if ('race_summary' in subsession_dict and 'special_event_type' in subsession_dict['race_summary']) else None,
                subsession_dict['race_summary']['special_event_type_text'] if ('race_summary' in subsession_dict and 'special_event_type_text' in subsession_dict['race_summary']) else None,
                subsession_dict['results_restricted'] if 'results_restricted' in subsession_dict else None
            ))

            for session_result_dict in subsession_dict['session_results']:
                for result_dict in session_result_dict['results']:
                    result_parameters.append((
                        subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                        session_result_dict['simsession_number'] if 'simsession_number' in session_result_dict else None,
                        session_result_dict['simsession_type'] if 'simsession_type' in session_result_dict else None,
                        session_result_dict['simsession_type_name'] if 'simsession_type_name' in session_result_dict else None,
                        session_result_dict['simsession_subtype'] if 'simsession_subtype' in session_result_dict else None,
                        session_result_dict['simsession_name'] if 'simsession_name' in session_result_dict else None,
                        result_dict['cust_id'] if 'cust_id' in result_dict else None,
                        result_dict['team_id'] if 'team_id' in result_dict else None,
                        result_dict['display_name'] if 'display_name' in result_dict else None,
                        result_dict['finish_position'] if 'finish_position' in result_dict else None,
                        result_dict['finish_position_in_class'] if 'finish_position_in_class' in result_dict else None,
                        result_dict['laps_lead'] if 'laps_lead' in result_dict else None,
                        result_dict['laps_complete'] if 'laps_complete' in result_dict else None,
                        result_dict['opt_laps_complete'] if 'opt_laps_complete' in result_dict else None,
                        result_dict['interval'] if 'interval' in result_dict else None,
                        result_dict['class_interval'] if 'class_interval' in result_dict else None,
                        result_dict['average_lap'] if 'average_lap' in result_dict else None,
                        result_dict['best_lap_num'] if 'best_lap_num' in result_dict else None,
                        result_dict['best_lap_time'] if 'best_lap_time' in result_dict else None,
                        result_dict['best_nlaps_num'] if 'best_nlaps_num' in result_dict else None,
                        result_dict['best_nlaps_time'] if 'best_nlaps_time' in result_dict else None,
                        result_dict['best_qual_lap_at'] if 'best_qual_lap_at' in result_dict else None,
                        result_dict['best_qual_lap_num'] if 'best_qual_lap_num' in result_dict else None,
                        result_dict['best_qual_lap_time'] if 'best_qual_lap_time' in result_dict else None,
                        result_dict['reason_out_id'] if 'reason_out_id' in result_dict else None,
                        result_dict['reason_out'] if 'reason_out' in result_dict else None,
                        result_dict['champ_points'] if 'champ_points' in result_dict else None,
                        result_dict['drop_race'] if 'drop_race' in result_dict else None,
                        result_dict['club_points'] if 'club_points' in result_dict else None,
                        result_dict['position'] if 'position' in result_dict else None,
                        result_dict['qual_lap_time'] if 'qual_lap_time' in result_dict else None,
                        result_dict['starting_position'] if 'starting_position' in result_dict else None,
                        result_dict['starting_position_in_class'] if 'starting_position_in_class' in result_dict else None,
                        result_dict['car_class_id'] if 'car_class_id' in result_dict else None,
                        result_dict['car_class_name'] if 'car_class_name' in result_dict else None,
                        result_dict['car_class_short_name'] if 'car_class_short_name' in result_dict else None,
                        result_dict['club_id'] if 'club_id' in result_dict else None,
                        result_dict['club_name'] if 'club_name' in result_dict else None,
                        result_dict['club_shortname'] if 'club_shortname' in result_dict else None,
                        result_dict['division'] if 'division' in result_dict else None,
                        result_dict['division_name'] if 'division_name' in result_dict else None,
                        result_dict['old_license_level'] if 'old_license_level' in result_dict else None,
                        result_dict['old_sub_level'] if 'old_sub_level' in result_dict else None,
                        result_dict['old_cpi'] if 'old_cpi' in result_dict else None,
                        result_dict['oldi_rating'] if 'oldi_rating' in result_dict else None,
                        result_dict['old_ttrating'] if 'old_ttrating' in result_dict else None,
                        result_dict['new_license_level'] if 'new_license_level' in result_dict else None,
                        result_dict['new_sub_level'] if 'new_sub_level' in result_dict else None,
                        result_dict['new_cpi'] if 'new_cpi' in result_dict else None,
                        result_dict['newi_rating'] if 'newi_rating' in result_dict else None,
                        result_dict['new_ttrating'] if 'new_ttrating' in result_dict else None,
                        result_dict['multiplier'] if 'multiplier' in result_dict else None,
                        result_dict['license_change_oval'] if 'license_change_oval' in result_dict else None,
                        result_dict['license_change_road'] if 'license_change_road' in result_dict else None,
                        result_dict['incidents'] if 'incidents' in result_dict else None,
                        result_dict['max_pct_fuel_fill'] if 'max_pct_fuel_fill' in result_dict else None,
                        result_dict['weight_penalty_kg'] if 'weight_penalty_kg' in result_dict else None,
                        result_dict['league_points'] if 'league_points' in result_dict else None,
                        result_dict['league_agg_points'] if 'league_agg_points' in result_dict else None,
                        result_dict['car_id'] if 'car_id' in result_dict else None,
                        result_dict['car_name'] if 'car_name' in result_dict else None,
                        result_dict['aggregate_champ_points'] if 'aggregate_champ_points' in result_dict else None,
                        result_dict['livery']['car_id'] if ('livery' in result_dict and 'car_id' in result_dict['livery']) else None,
                        result_dict['livery']['pattern'] if ('livery' in result_dict and 'pattern' in result_dict['livery']) else None,
                        result_dict['livery']['color1'] if ('livery' in result_dict and 'color1' in result_dict['livery']) else None,
                        result_dict['livery']['color2'] if ('livery' in result_dict and 'color2' in result_dict['livery']) else None,
                        result_dict['livery']['color3'] if ('livery' in result_dict and 'color3' in result_dict['livery']) else None,
                        result_dict['livery']['number_font'] if ('livery' in result_dict and 'number_font' in result_dict['livery']) else None,
                        result_dict['livery']['number_color1'] if ('livery' in result_dict and 'number_color1' in result_dict['livery']) else None,
                        result_dict['livery']['number_color2'] if ('livery' in result_dict and 'number_color2' in result_dict['livery']) else None,
                        result_dict['livery']['number_color3'] if ('livery' in result_dict and 'number_color3' in result_dict['livery']) else None,
                        result_dict['livery']['number_slant'] if ('livery' in result_dict and 'number_slant' in result_dict['livery']) else None,
                        result_dict['livery']['sponsor1'] if ('livery' in result_dict and 'sponsor1' in result_dict['livery']) else None,
                        result_dict['livery']['sponsor2'] if ('livery' in result_dict and 'sponsor2' in result_dict['livery']) else None,
                        result_dict['livery']['car_number'] if ('livery' in result_dict and 'car_number' in result_dict['livery']) else None,
                        result_dict['livery']['wheel_color'] if ('livery' in result_dict and 'wheel_color' in result_dict['livery']) else None,
                        result_dict['livery']['rim_type'] if ('livery' in result_dict and 'rim_type' in result_dict['livery']) else None,
                        result_dict['suit']['pattern'] if ('suit' in result_dict and 'pattern' in result_dict['suit']) else None,
                        result_dict['suit']['color1'] if ('suit' in result_dict and 'color1' in result_dict['suit']) else None,
                        result_dict['suit']['color2'] if ('suit' in result_dict and 'color2' in result_dict['suit']) else None,
                        result_dict['suit']['color3'] if ('suit' in result_dict and 'color3' in result_dict['suit']) else None,
                        result_dict['helmet']['pattern'] if ('helmet' in result_dict and 'pattern' in result_dict['helmet']) else None,
                        result_dict['helmet']['color1'] if ('helmet' in result_dict and 'color1' in result_dict['helmet']) else None,
                        result_dict['helmet']['color2'] if ('helmet' in result_dict and 'color2' in result_dict['helmet']) else None,
                        result_dict['helmet']['color3'] if ('helmet' in result_dict and 'color3' in result_dict['helmet']) else None,
                        result_dict['helmet']['face_type'] if ('helmet' in result_dict and 'face_type' in result_dict['helmet']) else None,
                        result_dict['helmet']['helmet_type'] if ('helmet' in result_dict and 'helmet_type' in result_dict['helmet']) else None,
                        result_dict['ai'] if 'ai' in result_dict else None
                    ))

                    if 'team_id' in result_dict and 'driver_results' in result_dict:
                        for driver_result in result_dict['driver_results']:
                            result_parameters.append((
                                subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                                session_result_dict['simsession_number'] if 'simsession_number' in session_result_dict else None,
                                session_result_dict['simsession_type'] if 'simsession_type' in session_result_dict else None,
                                session_result_dict['simsession_type_name'] if 'simsession_type_name' in session_result_dict else None,
                                session_result_dict['simsession_subtype'] if 'simsession_subtype' in session_result_dict else None,
                                session_result_dict['simsession_name'] if 'simsession_name' in session_result_dict else None,
                                driver_result['cust_id'] if 'cust_id' in driver_result else None,
                                driver_result['team_id'] if 'team_id' in driver_result else None,
                                driver_result['display_name'] if 'display_name' in driver_result else None,
                                driver_result['finish_position'] if 'finish_position' in driver_result else None,
                                driver_result['finish_position_in_class'] if 'finish_position_in_class' in driver_result else None,
                                driver_result['laps_lead'] if 'laps_lead' in driver_result else None,
                                driver_result['laps_complete'] if 'laps_complete' in driver_result else None,
                                driver_result['opt_laps_complete'] if 'opt_laps_complete' in driver_result else None,
                                driver_result['interval'] if 'interval' in driver_result else None,
                                driver_result['class_interval'] if 'class_interval' in driver_result else None,
                                driver_result['average_lap'] if 'average_lap' in driver_result else None,
                                driver_result['best_lap_num'] if 'best_lap_num' in driver_result else None,
                                driver_result['best_lap_time'] if 'best_lap_time' in driver_result else None,
                                driver_result['best_nlaps_num'] if 'best_nlaps_num' in driver_result else None,
                                driver_result['best_nlaps_time'] if 'best_nlaps_time' in driver_result else None,
                                driver_result['best_qual_lap_at'] if 'best_qual_lap_at' in driver_result else None,
                                driver_result['best_qual_lap_num'] if 'best_qual_lap_num' in driver_result else None,
                                driver_result['best_qual_lap_time'] if 'best_qual_lap_time' in driver_result else None,
                                driver_result['reason_out_id'] if 'reason_out_id' in driver_result else None,
                                driver_result['reason_out'] if 'reason_out' in driver_result else None,
                                driver_result['champ_points'] if 'champ_points' in driver_result else None,
                                driver_result['drop_race'] if 'drop_race' in driver_result else None,
                                driver_result['club_points'] if 'club_points' in driver_result else None,
                                driver_result['position'] if 'position' in driver_result else None,
                                driver_result['qual_lap_time'] if 'qual_lap_time' in driver_result else None,
                                driver_result['starting_position'] if 'starting_position' in driver_result else None,
                                driver_result['starting_position_in_class'] if 'starting_position_in_class' in driver_result else None,
                                driver_result['car_class_id'] if 'car_class_id' in driver_result else None,
                                driver_result['car_class_name'] if 'car_class_name' in driver_result else None,
                                driver_result['car_class_short_name'] if 'car_class_short_name' in driver_result else None,
                                driver_result['club_id'] if 'club_id' in driver_result else None,
                                driver_result['club_name'] if 'club_name' in driver_result else None,
                                driver_result['club_shortname'] if 'club_shortname' in driver_result else None,
                                driver_result['division'] if 'division' in driver_result else None,
                                driver_result['division_name'] if 'division_name' in driver_result else None,
                                driver_result['old_license_level'] if 'old_license_level' in driver_result else None,
                                driver_result['old_sub_level'] if 'old_sub_level' in driver_result else None,
                                driver_result['old_cpi'] if 'old_cpi' in driver_result else None,
                                driver_result['oldi_rating'] if 'oldi_rating' in driver_result else None,
                                driver_result['old_ttrating'] if 'old_ttrating' in driver_result else None,
                                driver_result['new_license_level'] if 'new_license_level' in driver_result else None,
                                driver_result['new_sub_level'] if 'new_sub_level' in driver_result else None,
                                driver_result['new_cpi'] if 'new_cpi' in driver_result else None,
                                driver_result['newi_rating'] if 'newi_rating' in driver_result else None,
                                driver_result['new_ttrating'] if 'new_ttrating' in driver_result else None,
                                driver_result['multiplier'] if 'multiplier' in driver_result else None,
                                driver_result['license_change_oval'] if 'license_change_oval' in driver_result else None,
                                driver_result['license_change_road'] if 'license_change_road' in driver_result else None,
                                driver_result['incidents'] if 'incidents' in driver_result else None,
                                driver_result['max_pct_fuel_fill'] if 'max_pct_fuel_fill' in driver_result else None,
                                driver_result['weight_penalty_kg'] if 'weight_penalty_kg' in driver_result else None,
                                driver_result['league_points'] if 'league_points' in driver_result else None,
                                driver_result['league_agg_points'] if 'league_agg_points' in driver_result else None,
                                driver_result['car_id'] if 'car_id' in driver_result else None,
                                driver_result['car_name'] if 'car_name' in driver_result else None,
                                driver_result['aggregate_champ_points'] if 'aggregate_champ_points' in driver_result else None,
                                driver_result['livery']['car_id'] if ('livery' in driver_result and 'car_id' in driver_result['livery']) else None,
                                driver_result['livery']['pattern'] if ('livery' in driver_result and 'pattern' in driver_result['livery']) else None,
                                driver_result['livery']['color1'] if ('livery' in driver_result and 'color1' in driver_result['livery']) else None,
                                driver_result['livery']['color2'] if ('livery' in driver_result and 'color2' in driver_result['livery']) else None,
                                driver_result['livery']['color3'] if ('livery' in driver_result and 'color3' in driver_result['livery']) else None,
                                driver_result['livery']['number_font'] if ('livery' in driver_result and 'number_font' in driver_result['livery']) else None,
                                driver_result['livery']['number_color1'] if ('livery' in driver_result and 'number_color1' in driver_result['livery']) else None,
                                driver_result['livery']['number_color2'] if ('livery' in driver_result and 'number_color2' in driver_result['livery']) else None,
                                driver_result['livery']['number_color3'] if ('livery' in driver_result and 'number_color3' in driver_result['livery']) else None,
                                driver_result['livery']['number_slant'] if ('livery' in driver_result and 'number_slant' in driver_result['livery']) else None,
                                driver_result['livery']['sponsor1'] if ('livery' in driver_result and 'sponsor1' in driver_result['livery']) else None,
                                driver_result['livery']['sponsor2'] if ('livery' in driver_result and 'sponsor2' in driver_result['livery']) else None,
                                driver_result['livery']['car_number'] if ('livery' in driver_result and 'car_number' in driver_result['livery']) else None,
                                driver_result['livery']['wheel_color'] if ('livery' in driver_result and 'wheel_color' in driver_result['livery']) else None,
                                driver_result['livery']['rim_type'] if ('livery' in driver_result and 'rim_type' in driver_result['livery']) else None,
                                driver_result['suit']['pattern'] if ('suit' in driver_result and 'pattern' in driver_result['suit']) else None,
                                driver_result['suit']['color1'] if ('suit' in driver_result and 'color1' in driver_result['suit']) else None,
                                driver_result['suit']['color2'] if ('suit' in driver_result and 'color2' in driver_result['suit']) else None,
                                driver_result['suit']['color3'] if ('suit' in driver_result and 'color3' in driver_result['suit']) else None,
                                driver_result['helmet']['pattern'] if ('helmet' in driver_result and 'pattern' in driver_result['helmet']) else None,
                                driver_result['helmet']['color1'] if ('helmet' in driver_result and 'color1' in driver_result['helmet']) else None,
                                driver_result['helmet']['color2'] if ('helmet' in driver_result and 'color2' in driver_result['helmet']) else None,
                                driver_result['helmet']['color3'] if ('helmet' in driver_result and 'color3' in driver_result['helmet']) else None,
                                driver_result['helmet']['face_type'] if ('helmet' in driver_result and 'face_type' in driver_result['helmet']) else None,
                                driver_result['helmet']['helmet_type'] if ('helmet' in driver_result and 'helmet_type' in driver_result['helmet']) else None,
                                driver_result['ai'] if 'ai' in driver_result else None
                            ))

            try:
                await self.execute_query(dbq.INSERT_SUBSESSIONS, params=subsession_parameters)
            except Error as e:
                subsessions = []
                for subsession_dict in subsession_dicts:
                    subsessions.append(subsession_dict['subsession_id'])
                if e.sqlite_errorcode == 1555:
                    logging.getLogger('respobot.database').warning(f"Subsession already in database, ignoring.")
                    raise BotDatabaseError(f"Error inserting new race data for subsession {subsessions}", BotDatabaseError.insert_collision.value)
                else:
                    logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add subsession(s) {subsessions} to the subsessions table.")
                    raise BotDatabaseError(f"Error inserting new race data for subsession {subsessions}", BotDatabaseError.general_failure.value)

            try:
                await self.execute_query(dbq.INSERT_RESULTS, params=result_parameters)
            except Error as e:
                subsessions = []
                for subsession_dict in subsession_dicts:
                    subsessions.append(subsession_dict['subsession_id'])
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add a result from subsession(s) {subsessions} to the results table.")
                raise BotDatabaseError(f"Error inserting results data for subsession(s) {subsessions} to the results table.", BotDatabaseError.general_failure.value)

    async def get_race_summary(self, subsession_id: int):
        query = """
            SELECT
                subsessions.subsession_id,
                subsessions.season_id,
                subsessions.track_category_id,
                subsessions.start_time,
                subsessions.official_session,
                subsessions.track_name,
                subsessions.track_config_name,
                subsessions.series_id,
                subsessions.series_name,
                subsessions.event_strength_of_field,
                subsessions.max_team_drivers,
                subsessions.league_name,
                subsessions.session_name
            FROM subsessions
            WHERE
                subsession_id = ?
        """

        parameters = (subsession_id,)

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_race_summary() for subsession {subsession_id}.")
            raise BotDatabaseError(f"Error getting race summary for subsession_id {subsession_id}.", BotDatabaseError.general_failure.value)
        if results is None or len(results) < 1:
            return {}

        race_summary_dict = {
            'subsession_id': results[0][0],
            'season_id': results[0][1],
            'track_category_id': results[0][2],
            'start_time': datetime.fromisoformat(results[0][3]),
            'official_session': results[0][4],
            'track_name': results[0][5],
            'track_config_name': results[0][6],
            'series_id': results[0][7],
            'series_name': results[0][8],
            'event_strength_of_field': results[0][9],
            'max_team_drivers': results[0][10],
            'league_name': results[0][11],
            'session_name': results[0][12]
        }

        query = """
            SELECT car_class_id
            FROM season_car_classes
            WHERE season_id = ?
        """

        parameters = (race_summary_dict['season_id'],)

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_race_summary() when determining if subsession {subsession_id} was multiclass.")

        if len(results) > 1:
            race_summary_dict['is_multiclass'] = True
        else:
            race_summary_dict['is_multiclass'] = False

        return race_summary_dict

    async def get_driver_result_summary(self, subsession_id: int, iracing_custid: int, simsession_number: int = 0, simsession_type: int = 6):
        query = """
            SELECT
                members.iracing_custid,
                members.name,
                results.newi_rating,
                results.oldi_rating,
                results.starting_position_in_class,
                results.finish_position_in_class,
                results.livery_car_number,
                results.champ_points,
                results.new_license_level,
                results.old_license_level,
                results.new_sub_level,
                results.old_sub_level,
                results.laps_complete,
                results.incidents,
                results.car_class_id,
                results.car_class_short_name
            FROM results
            INNER JOIN members
            ON members.iracing_custid = results.cust_id
            WHERE
                subsession_id = ? AND
                simsession_number = ? AND
                simsession_type = ? AND
                cust_id = ?
        """

        parameters = (subsession_id, simsession_number, simsession_type, iracing_custid)

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_driver_result_summary() for driver {iracing_custid} in subsession {subsession_id}.")

        if results is None or len(results) < 1:
            return {}

        driver_result_summary_dict = {
            'iracing_custid': results[0][0],
            'name': results[0][1],
            'newi_rating': results[0][2],
            'oldi_rating': results[0][3],
            'starting_position_in_class': results[0][4] + 1,
            'finish_position_in_class': results[0][5] + 1,
            'livery_car_number': results[0][6],
            'champ_points': results[0][7],
            'new_license_level': results[0][8],
            'old_license_level': results[0][9],
            'new_sub_level': results[0][10],
            'old_sub_level': results[0][11],
            'laps_complete': results[0][12],
            'incidents': results[0][13],
            'car_class_id': results[0][14],
            'car_class_short_name': results[0][15]
        }

        return driver_result_summary_dict

    async def is_season_in_seasons_table(self, season_id):
        query = """
            SELECT season_id
            FROM seasons
            WHERE season_id = ?
        """
        parameters = (season_id, )
        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_season_in_season_table() for season_id {season_id}.")
        return len(result) > 0

    async def is_series_in_series_table(self, series_id):
        query = """
            SELECT series_id
            FROM series
            WHERE series_id = ?
        """
        parameters = (series_id,)
        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_series_in_series_table() fpr series_id {series_id}.")
        return len(result) > 0

    async def is_car_class_in_season_car_classes_table(self, season_id, car_class_id):
        query = """
            SELECT season_id
            FROM season_car_classes
            WHERE
                season_id = ? AND
                car_class_id = ?
        """
        parameters = (season_id, car_class_id)
        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_car_class_in_season_car_classes_table() for season_id {season_id} and car_class_id {car_class_id}.")
        return len(result) > 0

    async def is_season_in_season_dates_table(self, season_year, season_quarter):
        query = """
            SELECT season_year
            FROM season_dates
            WHERE
                season_year = ? AND
                season_quarter = ?
        """
        parameters = (season_year, season_quarter)
        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_season_in_season_dates_table() for season_year {season_year} and season_quarter {season_quarter}.")
        return len(result) > 0

    async def is_car_class_car_in_db(self, car_class_id, car_id):
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
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_car_class_car_in_db() for car_class_id {car_class_id} and car_id {car_id}.")
        return len(result) > 0

    async def update_current_seasons(self, current_season_dicts):
        query = "DELETE FROM current_seasons"
        try:
            await self.execute_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during update_current_seasons() when deleting the existing entries.")

        new_current_season_parameters = []

        for current_season_dict in current_season_dicts:

            if 'season_id' not in current_season_dict or current_season_dict['season_id'] is None:
                continue

            if 'allowed_season_members' in current_season_dict and current_season_dict['allowed_season_members'] is not None:
                allowed_season_members = ""
                for allowed_season_member in current_season_dict['allowed_season_members']:
                    allowed_season_members += str(current_season_dict['allowed_season_members'][allowed_season_member]['cust_id']) + ","
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
                current_season_dict['caution_laps_do_not_count'] if 'caution_laps_do_not_count' in current_season_dict else None,
                current_season_dict['complete'] if 'complete' in current_season_dict else None,
                current_season_dict['cross_license'] if 'cross_license' in current_season_dict else None,
                current_season_dict['driver_change_rule'] if 'driver_change_rule' in current_season_dict else None,
                current_season_dict['driver_changes'] if 'driver_changes' in current_season_dict else None,
                current_season_dict['drops'] if 'drops' in current_season_dict else None,
                current_season_dict['enable_pitlane_collisions'] if 'enable_pitlane_collisions' in current_season_dict else None,
                current_season_dict['fixed_setup'] if 'fixed_setup' in current_season_dict else None,
                current_season_dict['green_white_checkered_limit'] if 'green_white_checkered_limit' in current_season_dict else None,
                current_season_dict['grid_by_class'] if 'grid_by_class' in current_season_dict else None,
                current_season_dict['hardcore_level'] if 'hardcore_level' in current_season_dict else None,
                current_season_dict['heat_ses_info']['heat_info_id'] if ('heat_ses_info' in current_season_dict and 'heat_info_id' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['cust_id'] if ('heat_ses_info' in current_season_dict and 'cust_id' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['hidden'] if ('heat_ses_info' in current_season_dict and 'hidden' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['created'] if ('heat_ses_info' in current_season_dict and 'created' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_info_name'] if ('heat_ses_info' in current_season_dict and 'heat_info_name' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['description'] if ('heat_ses_info' in current_season_dict and 'description' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['max_entrants'] if ('heat_ses_info' in current_season_dict and 'max_entrants' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['race_style'] if ('heat_ses_info' in current_season_dict and 'race_style' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['open_practice'] if ('heat_ses_info' in current_season_dict and 'open_practice' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['pre_qual_practice_length_minutes'] if ('heat_ses_info' in current_season_dict and 'pre_qual_practice_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['pre_qual_num_to_main'] if ('heat_ses_info' in current_season_dict and 'pre_qual_num_to_main' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_style'] if ('heat_ses_info' in current_season_dict and 'qual_style' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_length_minutes'] if ('heat_ses_info' in current_season_dict and 'qual_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_laps'] if ('heat_ses_info' in current_season_dict and 'qual_laps' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_num_to_main'] if ('heat_ses_info' in current_season_dict and 'qual_num_to_main' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_scoring'] if ('heat_ses_info' in current_season_dict and 'qual_scoring' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_caution_type'] if ('heat_ses_info' in current_season_dict and 'qual_caution_type' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_open_delay_seconds'] if ('heat_ses_info' in current_season_dict and 'qual_open_delay_seconds' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['qual_scores_champ_points'] if ('heat_ses_info' in current_season_dict and 'qual_scores_champ_points' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_length_minutes'] if ('heat_ses_info' in current_season_dict and 'heat_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_laps'] if ('heat_ses_info' in current_season_dict and 'heat_laps' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_max_field_size'] if ('heat_ses_info' in current_season_dict and 'heat_max_field_size' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_num_position_to_invert'] if ('heat_ses_info' in current_season_dict and 'heat_num_position_to_invert' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_caution_type'] if ('heat_ses_info' in current_season_dict and 'heat_caution_type' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_num_from_each_to_main'] if ('heat_ses_info' in current_season_dict and 'heat_num_from_each_to_main' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_scores_champ_points'] if ('heat_ses_info' in current_season_dict and 'heat_scores_champ_points' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_num_to_consolation'] if ('heat_ses_info' in current_season_dict and 'consolation_num_to_consolation' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_num_to_main'] if ('heat_ses_info' in current_season_dict and 'consolation_num_to_main' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_first_max_field_size'] if ('heat_ses_info' in current_season_dict and 'consolation_first_max_field_size' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_first_session_length_minutes'] if ('heat_ses_info' in current_season_dict and 'consolation_first_session_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_first_session_laps'] if ('heat_ses_info' in current_season_dict and 'consolation_first_session_laps' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_delta_max_field_size'] if ('heat_ses_info' in current_season_dict and 'consolation_delta_max_field_size' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_delta_session_length_minutes'] if ('heat_ses_info' in current_season_dict and 'consolation_delta_session_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_delta_session_laps'] if ('heat_ses_info' in current_season_dict and 'consolation_delta_session_laps' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_num_position_to_invert'] if ('heat_ses_info' in current_season_dict and 'consolation_num_position_to_invert' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_scores_champ_points'] if ('heat_ses_info' in current_season_dict and 'consolation_scores_champ_points' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['consolation_run_always'] if ('heat_ses_info' in current_season_dict and 'consolation_run_always' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['pre_main_practice_length_minutes'] if ('heat_ses_info' in current_season_dict and 'pre_main_practice_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['main_length_minutes'] if ('heat_ses_info' in current_season_dict and 'main_length_minutes' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['main_laps'] if ('heat_ses_info' in current_season_dict and 'main_laps' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['main_max_field_size'] if ('heat_ses_info' in current_season_dict and 'main_max_field_size' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['main_num_position_to_invert'] if ('heat_ses_info' in current_season_dict and 'main_num_position_to_invert' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['heat_ses_info']['heat_session_minutes_estimate'] if ('heat_ses_info' in current_season_dict and 'heat_session_minutes_estimate' in current_season_dict['heat_ses_info']) else None,
                current_season_dict['ignore_license_for_practice'] if 'ignore_license_for_practice' in current_season_dict else None,
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
                current_season_dict['must_use_diff_tire_types_in_race'] if 'must_use_diff_tire_types_in_race' in current_season_dict else None,
                current_season_dict['next_race_session'] if 'next_race_session' in current_season_dict else None,
                current_season_dict['num_opt_laps'] if 'num_opt_laps' in current_season_dict else None,
                current_season_dict['official'] if 'official' in current_season_dict else None,
                current_season_dict['op_duration'] if 'op_duration' in current_season_dict else None,
                current_season_dict['open_practice_session_type_id'] if 'open_practice_session_type_id' in current_season_dict else None,
                current_season_dict['qualifier_must_start_race'] if 'qualifier_must_start_race' in current_season_dict else None,
                current_season_dict['race_week'] if 'race_week' in current_season_dict else None,
                current_season_dict['race_week_to_make_divisions'] if 'race_week_to_make_divisions' in current_season_dict else None,
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
                current_season_dict['unsport_conduct_rule_mode'] if 'unsport_conduct_rule_mode' in current_season_dict else None,
                current_season_dict['season_id'] if 'season_id' in current_season_dict else None
            )

            new_current_season_parameters.append(season_tuple)

        if len(new_current_season_parameters) > 0:
            try:
                await self.execute_query(dbq.INSERT_CURRENT_SEASONS, params=new_current_season_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add season to the current_seasons table.")

    async def update_seasons(self, series_dicts):
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

            if await self.is_series_in_series_table(int(series_dict['series_id'])) is False:
                new_series_parameters.append(series_tuple)
            else:
                existing_series_parameters.append(series_tuple)

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

                        if await self.is_car_class_in_season_car_classes_table(int(season_dict['season_id']), int(car_class_dict['car_class_id'])) is False:
                            new_car_class_parameters.append(car_class_tuple)
                        else:
                            existing_car_class_parameters.append(car_class_tuple)

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

                if await self.is_season_in_seasons_table(int(season_dict['season_id'])) is False:
                    new_season_parameters.append(season_tuple)
                else:
                    existing_season_parameters.append(season_tuple)

        if len(new_season_parameters) > 0:
            try:
                await self.execute_query(dbq.INSERT_SEASONS, params=new_season_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add new seasons to the seasons table.")

        if len(existing_season_parameters) > 0:
            try:
                await self.execute_query(dbq.UPDATE_SEASONS, params=existing_season_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to update seasons in the seasons table.")

        if len(new_series_parameters) > 0:
            try:
                await self.execute_query(dbq.INSERT_SERIES, params=new_series_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add new series to the series table.")

        if len(existing_series_parameters) > 0:
            try:
                await self.execute_query(dbq.UPDATE_SERIES, params=existing_series_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to update series in the series table.")

        if len(new_car_class_parameters) > 0:
            try:
                await self.execute_query(dbq.INSERT_SEASON_CAR_CLASSES, params=new_car_class_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add new car class to the season_car_classes table.")

        if len(existing_car_class_parameters) > 0:
            try:
                await self.execute_query(dbq.UPDATE_SEASON_CAR_CLASSES, params=existing_car_class_parameters)
            except Error as e:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to update car class in the season_car_classes table.")

    async def update_season_dates(self, season_dicts):
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

            season_tuple = (
                season_dict['start_time'] if 'start_time' in season_dict else None,
                season_dict['end_time'] if 'end_time' in season_dict else None,
                season_dict['season_year'] if 'season_year' in season_dict else None,
                season_dict['season_quarter'] if 'season_quarter' in season_dict else None,
            )

            if await self.is_season_in_season_dates_table(int(season_dict['season_year']), int(season_dict['season_quarter'])) is False:
                new_season_parameters.append(season_tuple)
            else:
                existing_season_parameters.append(season_tuple)

        try:
            if len(new_season_parameters) > 0:
                await self.execute_query(dbq.INSERT_SEASON_DATES, params=new_season_parameters)
            if len(existing_season_parameters) > 0:
                await self.execute_query(dbq.UPDATE_SEASON_DATES, params=existing_season_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add/update {season_dict['season_year']}s{season_dict['season_quarter']} in the season_dates table.")

    async def fetch_guild_member_ids(self):
        query = "SELECT discord_id FROM members"

        try:
            result = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_guild_member_ids().")

        guild_ids = []

        for member_tuple in result:
            if len(member_tuple) == 1 and member_tuple[0] is not None:
                guild_ids.append(member_tuple[0])

        return guild_ids

    async def fetch_iracing_cust_ids(self):
        query = "SELECT iracing_custid FROM members"

        try:
            cust_ids_tuples = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_iracing_cust_ids()")

        cust_ids = []

        if cust_ids_tuples is not None and len(cust_ids_tuples) > 0:
            for cust_id in cust_ids_tuples:
                cust_ids.append(cust_id[0])

        return cust_ids

    async def fetch_name(self, iracing_custid):
        query = """
            SELECT name
            FROM members
            WHERE iracing_custid = ?
        """
        parameters = (iracing_custid,)

        try:
            tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_name() for iracing_custid {iracing_custid}.")

        name = None

        if tuples is not None and len(tuples) > 0:
            name = tuples[0][0]

        return name

    async def get_member_last_race_check(self, iracing_custid: int):
        query = """
            SELECT last_race_check
            FROM members
            WHERE iracing_custid = ?
        """
        parameters = (iracing_custid,)

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_last_race_check() for iracing_custid {iracing_custid}.")

        if results is None or len(results) < 1:
            return None
        else:
            last_race_check = datetime.fromisoformat(results[0][0])
            return last_race_check

    async def set_member_last_race_check(self, iracing_custid: int, last_race_check: datetime):
        last_race_check_str = last_race_check.isoformat().replace('+00:00', 'Z')
        query = """
            UPDATE 'members'
            SET last_race_check = ?
            WHERE iracing_custid = ?
        """
        parameters = (last_race_check_str, iracing_custid)

        try:
            await self.execute_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during set_member_last_race_check() for iracing_custid = {iracing_custid}.")

    async def get_member_ir(self, iracing_custid: int, category_id: int = pyracingConstants.Category.road.value):
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
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_ir() for iracing_custid {iracing_custid}.")

        if results is None or len(results) != 1:
            return None

        return results[0][1]

    async def fetch_member_dict(self, iracing_custid: int = None, discord_id: int = None, first_name: str = None):
        query = """
            SELECT
                name,
                iracing_custid,
                discord_id,
                timezone,
                graph_colour,
                last_race_check,
                last_hosted_check,
                last_known_ir,
                ir_member_since
            FROM members
        """

        if iracing_custid is not None:
            query += """    WHERE iracing_custid = ?
            """
            parameters = (iracing_custid,)
        elif discord_id is not None:
            query += """    WHERE discord_id = ?
            """
            parameters = (discord_id,)
        elif first_name is not None:
            query += f"""    WHERE name LIKE ?
            """
            parameters = (first_name + "%",)
        else:
            parameters = ()

        try:
            tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            member = iracing_custid if iracing_custid is not None else discord_id if discord_id is not None else first_name if first_name is not None else "everyone"
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_member_dict() for {member}.")
            raise BotDatabaseError("Error fetching member dicts.", BotDatabaseError.general_failure.value)

        if tuples is None or len(tuples) < 1:
            return None

        member_dicts = []
        for member_tuple in tuples:
            graph_colour_list = member_tuple[4].split(',')

            member_dict = {
                'name': member_tuple[0],
                'iracing_custid': member_tuple[1],
                'discord_id': member_tuple[2],
                'timezone': member_tuple[3],
                'graph_colour': [int(graph_colour_list[0]), int(graph_colour_list[1]), int(graph_colour_list[2]), int(graph_colour_list[3])],
                'last_race_check': member_tuple[5],
                'last_hosted_check': member_tuple[6],
                'last_known_ir': member_tuple[7],
                'ir_member_since': date.fromisoformat(member_tuple[8])
            }

            if len(tuples) == 1 and (iracing_custid is not None or discord_id is not None or first_name is not None):
                # If one member is found and a specific member was being fetched, return it directly and not in a list.
                return member_dict

            member_dicts.append(member_dict)

        return member_dicts

    async def fetch_member_dicts(self):
        return await self.fetch_member_dict()

    async def fetch_members_in_subsession(self, subsession_id: int, car_number: int = None):
        query = """
            SELECT
                members.name,
                members.iracing_custid,
                members.discord_id,
                members.timezone,
                members.graph_colour,
                members.last_race_check,
                members.last_hosted_check,
                members.last_known_ir
            FROM results
            INNER JOIN members
            ON members.iracing_custid = results.cust_id
            WHERE
                simsession_number = 0 AND
                simsession_type = ? AND
                subsession_id = ?
        """

        if car_number is not None:
            query += """
                AND livery_car_number = ?
            """
            parameters = (pyracingConstants.SimSessionType.race.value, subsession_id, car_number)
        else:
            parameters = (pyracingConstants.SimSessionType.race.value, subsession_id)

        try:
            tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_members_in_subsession() for subsession_id {subsession_id} and car_number {car_number}.")

        if tuples is None or len(tuples) < 1:
            return None

        member_dicts = []

        for result_tuple in tuples:
            graph_colour_list = result_tuple[4].split(',')

            member_dict = {
                'name': result_tuple[0],
                'iracing_custid': result_tuple[1],
                'discord_id': result_tuple[2],
                'timezone': result_tuple[3],
                'graph_colour': [int(graph_colour_list[0]), int(graph_colour_list[1]), int(graph_colour_list[2]), int(graph_colour_list[3])],
                'last_race_check': result_tuple[5],
                'last_hosted_check': result_tuple[6],
                'last_known_ir': result_tuple[7]
            }

            member_dicts.append(member_dict)

        return member_dicts

    async def fetch_graph_colour(self, iracing_custid=None, discord_id=None):
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
            tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during fetch_graph_colour() for iracing_custid {iracing_custid} and discord_id {discord_id}")

        if tuples is not None and len(tuples) > 0:
            colour_strings = tuples[0][0].split(",")

            if len(colour_strings) != 4:
                logging.getLogger('respobot.database').warning(f"graph_colour incorrectly formatted in database for iracing_custid:{iracing_custid} discord_id:{discord_id}")
                return None

            return [colour_strings[0], colour_strings[1], colour_strings[2], colour_strings[3]]

        else:
            return None

    async def set_graph_colour(self, graph_colour: list[int], iracing_custid: int = None, discord_id: int = None):

        if len(graph_colour) != 4:
            logging.getLogger('respobot.database').warning("Graph colours must be lists of 4 integers: [r, g, b, a].")
            return

        str_graph_colour = str(graph_colour[0]) + "," + str(graph_colour[1]) + "," + str(graph_colour[2]) + "," + str(graph_colour[3])

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
            raise BotDatabaseError("You must provide either iracing_custid or discord_id.", ErrorCodes.insufficient_info.value)

        try:
            await self.execute_query(query, params=parameters)
        except Error as e:
            member = "custid: " + str(iracing_custid) if iracing_custid is not None else "discord_id: " + str(discord_id)
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to update graph colour to {graph_colour} for {member}.")

    async def get_latest_ir(self, iracing_custid: int = None, discord_id: int = None, first_name: str = None, category_id: int = pyracingConstants.Category.road.value):

        if iracing_custid is None and discord_id is None and first_name is None:
            raise BotDatabaseError("You must provide either iracing_custid, discord_id, or first_name.", ErrorCodes.insufficient_info.value)

        member_dict = await self.fetch_member_dict(iracing_custid=iracing_custid, discord_id=discord_id, first_name=first_name)

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
        parameters = (member_dict['iracing_custid'], category_id, pyracingConstants.SimSessionType.race.value)

        try:
            result_tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            member = iracing_custid if iracing_custid is not None else discord_id if discord_id is not None else first_name
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_latest_ir() for {member}")

        if result_tuples is None or len(result_tuples) < 1:
            return None

        return result_tuples[0][0]

    async def get_ir_data(self, iracing_custid: int = None, discord_id: int = None, first_name: str = None, category_id: int = None):

        if iracing_custid is None and discord_id is None and first_name is None:
            raise BotDatabaseError("You must provide either iracing_custid, discord_id, or first_name.", ErrorCodes.insufficient_info.value)

        member_dict = await self.fetch_member_dict(iracing_custid=iracing_custid, discord_id=discord_id, first_name=first_name)

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
        parameters = (member_dict['iracing_custid'], category_id, category_id, pyracingConstants.SimSessionType.race.value)

        try:
            result_tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            member = iracing_custid if iracing_custid is not None else discord_id if discord_id is not None else first_name
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_ir_data() for member {member}.")

        converted_tuples = []

        for result_tuple in result_tuples:
            time_point = datetime.fromisoformat(result_tuple[0])
            timestamp = time_point.timestamp() * 1000
            converted_tuples.append((timestamp, result_tuple[1]))

        return converted_tuples

    async def update_car_classes(self, car_class_dicts):
        new_car_class_parameters = []
        existing_car_class_parameters = []

        for car_class_dict in car_class_dicts:

            if 'car_class_id' not in car_class_dict or car_class_dict['car_class_id'] is None:
                continue

            if 'cars_in_class' in car_class_dict and car_class_dict['cars_in_class'] is not None:
                for car_dict in car_class_dict['cars_in_class']:
                    """ Queries are designed so that adding a new value and updating a value both have the columns lined up equally
                        so that the same tuple can be applied to either query. """
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

                    if await self.is_car_class_car_in_db(car_class_dict['car_class_id'], car_dict['car_id']) is False:
                        new_car_class_parameters.append(car_tuple)
                    else:
                        existing_car_class_parameters.append(car_tuple)

        try:
            if len(new_car_class_parameters) > 0:
                await self.execute_query(dbq.INSERT_CURRENT_CAR_CLASSES, params=new_car_class_parameters)
            if len(existing_car_class_parameters) > 0:
                await self.execute_query(dbq.UPDATE_CURRENT_CAR_CLASSES, params=existing_car_class_parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add subsession {car_class_dict['subsession_id']} the subsessions table.")

    async def is_season_active(self):
        query = """
            SELECT COUNT(active)
            FROM seasons
            WHERE series_id = 139 AND
            active = 1
        """
        try:
            result = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_season_active().")

        return result[0][0] > 0

    async def get_current_iracing_week(self, series_id: int = 139):
        """ Returns a tuple of (season_year, season_quarter, race_week, max_weeks, active) based on the seasons table. """
        if series_id is None or series_id < 0:
            series_id = 139

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
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_current_iracing_week() for series_id {series_id}.")

        if len(result) > 0:
            return result[0]
        else:
            return (None, None, None, None, None)

    async def get_season_basic_info(self, series_id: int = None, season_year: int = None, season_quarter: int = None):
        """ Returns a list of tuples of (series_id, season_name, latest_year, latest_quarter, max_race_week) for the latest season for each series in the 'seasons' table.
            latest_year and latest_quarter represent the last time this series was run.
            Alternatively, you can supply a season_year and season_quarter to only get season tuples for a specific iRacing season."""

        query = """
            SELECT
                season_id,
                series_id,
                season_name,
                season_year,
                season_quarter,
                max_race_week
            FROM (
                SELECT season_name,
                series_id, season_id,
                season_year,
                season_quarter,
                max_race_week
                FROM seasons
        """
        parameters = tuple()

        if series_id is not None or (season_year is not None and season_quarter is not None):

            query += "WHERE "

            if series_id is not None:
                query += "series_id = ? AND "
                parameters += (series_id,)

            if season_year is not None and season_quarter is not None:
                query += "season_year = ? AND season_quarter = ? AND "
                parameters += (season_year, season_quarter)

            query = query[:-5]

        query += """
            ORDER BY
                series_id,
                season_year DESC,
                season_quarter DESC
            )
            GROUP BY series_id
        """

        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_basic_info() for "
                f"series_id = {series_id}, season_year = {season_year}, season_quarter = {season_quarter}."
            )

        if len(result) > 0:
            return result
        else:
            return None

    async def get_series_last_run_season(self, series_id: int):
        """ Returns a tuple of (season_year, season_quarter) representing the last time a series was run. """

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
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_series_last_run_season() for series_id {series_id}.")

        if len(result) > 0:
            return result[0]
        else:
            return (None, None)

    async def get_series_id_from_season_name(self, season_name: str, season_year: int = None, season_quarter: int = None):

        try:
            series_tuples = await self.get_season_basic_info(season_year=season_year, season_quarter=season_quarter)
        except BotDatabaseError:
            raise

        for series_tuple in series_tuples:
            if series_tuple[2] == season_name:
                return series_tuple[1]

        return None

    async def get_car_class_id_from_car_class_name(self, car_class_name: str, season_id: int = None, series_id: int = None, season_year: int = None, season_quarter: int = None):

        try:
            car_class_tuples = await self.get_season_car_classes(season_id=season_id, series_id=series_id, season_year=season_year, season_quarter=season_quarter)
        except BotDatabaseError:
            raise

        if len(car_class_tuples) < 1:
            return None

        for car_class_tuple in car_class_tuples:
            if car_class_tuple[1] == car_class_name:
                return car_class_tuple[0]

        return None

    async def get_season_car_classes(self, season_id: int = None, series_id: int = None, season_year: int = None, season_quarter: int = None):
        """ Returns a list of (car_class_id, short_name) for each class in a specific season. """

        if season_id is not None:
            query = """
                SELECT
                    car_class_id,
                    short_name
                FROM season_car_classes
                INNER JOIN seasons
                ON seasons.season_id = season_car_classes.season_id
                WHERE
                    seasons.season_id = ?
            """
            parameters = (season_id,)
        elif series_id is not None:
            if season_year is None or season_quarter is None:
                (season_year, season_quarter) = await self.get_series_last_run_season(series_id)

            if season_year is not None and season_quarter is not None:
                query = """
                    SELECT
                        season_car_classes.car_class_id,
                        season_car_classes.short_name
                    FROM season_car_classes
                    INNER JOIN seasons
                    ON seasons.season_id = season_car_classes.season_id
                    WHERE
                        seasons.series_id = ? AND
                        season_year = ? AND
                        season_quarter = ?
                """
                parameters = (series_id, season_year, season_quarter)
        else:
            return []

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_car_classes() for "
                f"season_id {season_id}, series_id {series_id}, season_year {season_year}, season_quarter {season_quarter}."
            )

        return results

    async def get_season_car_classes_for_all_series(self, season_year: int, season_quarter: int):
        """ Returns a list of (season_id, car_class_id, short_name) for each class in a specific season. """

        if season_year is not None and season_quarter is not None:
            query = """
                SELECT
                    seasons.season_id,
                    car_class_id,
                    short_name
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
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_car_classes_for_all_series() for "
                f"season_year {season_year}, season_quarter {season_quarter}."
            )

        return results

    async def get_season_id(self, series_id: int, season_year: int, season_quarter: int):
        """ Returns the season_id for a specific series for an iRacing season. Returns None if this series was not run in the given season. """
        query = """
            SELECT season_id
            FROM seasons
            WHERE
                series_id = ? AND
                season_year = ? AND
                season_quarter = ?
        """
        parameters = (series_id, season_year, season_quarter)

        results = await self.execute_read_query(query, params=parameters)

        if len(results) < 1:
            return None
        else:
            return results[0][0]

    async def is_subsession_in_db(self, subsession_id: int):
        query = """
            SELECT subsession_id
            FROM subsessions
            WHERE subsession_id = ?
        """
        parameters = (subsession_id,)
        results = await self.execute_read_query(query, params=parameters)

        if results is None or len(results) < 1:
            return False
        else:
            return True

    async def get_member_race_results(
        self, iracing_custid: int,
        series_id: int = None,
        car_class_id: int = None,
        season_year: int = None,
        season_quarter: int = None,
        license_category_id: int = None,
        official_session: int = 1,
        simsession_type: int = 6
    ):
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
            WHERE cust_id = ? AND
        """
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

        query = query[:-4]

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_race_results() for "
                f"iracing_custid {iracing_custid}, series_id {series_id}, car_class_id {car_class_id}, "
                f"season_year {season_year}, season_quarter {season_quarter}, license_category_id {license_category_id}"
                f"official_session {official_session}, simsession_type {simsession_type}."
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
                new_race_dict['start_time'] = result_tuple[14]
                new_race_dict['event_strength_of_field'] = result_tuple[15]
                new_race_dict['license_category_id'] = result_tuple[16]
                new_race_dict['track_category_id'] = result_tuple[17]
                new_race_dict['race_week_num'] = result_tuple[18]
                new_race_dict['max_team_driver'] = result_tuple[19]
                race_dicts.append(new_race_dict)
            else:
                return None

        return race_dicts

    async def get_member_series_raced(
        self,
        iracing_custid: int,
        season_year: int = None,
        season_quarter: int = None,
        license_category_id: int = None,
        official_session: int = 1,
        simsession_type: int = 6
    ):
        series_ids = []

        query = """
            SELECT
                series_id
            FROM results
            INNER JOIN subsessions ON subsessions.subsession_id = results.subsession_id
            WHERE cust_id = ? AND
        """
        parameters = (iracing_custid,)

        if season_year is not None:
            query += " season_year = ? AND"
            parameters += (season_year,)

        if season_quarter is not None:
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
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_member_series_raced() for "
                f"iracing_custid {iracing_custid}, season_year {season_year}, season_quarter {season_quarter}, "
                f"license_category_id {license_category_id}, official_session {official_session}, simsession_type {simsession_type}."
            )

        if results is None:
            return None

        for result_tuple in results:
            if len(result_tuple) > 0:
                series_ids.append(result_tuple[0])
            else:
                return None

        return series_ids

    async def get_drivers_in_class(self, subsession_id, car_class_id, simsession_number: int = 0, simsession_type: int = 6):

        query = """
            SELECT livery_car_number
            FROM results
            WHERE
                subsession_id = ? AND
                car_class_id = ? AND
                simsession_number = ? AND
                simsession_type = ?
            GROUP BY livery_car_number
        """
        parameters = (subsession_id, car_class_id, simsession_number, simsession_type)

        try:
            result = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_drivers_in_class() for "
                f"subsession_id {subsession_id}, car_class_id {car_class_id}, simsession_number {simsession_number}, simsession_type {simsession_type}."
            )

        return len(result)

    async def get_season_dates(self):
        query = "SELECT * FROM season_dates"
        
        try:
            result = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_season_dates().")

        if result is None or len(result) < 1:
            return None

        return result

    async def get_quotes(
        self,
        discord_id: int = None,
        quote_id: int = None,
    ):

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
            result_tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quotes() for "
                f"discord_id {discord_id}, quote_id {quote_id}"
            )

        if len(result_tuples) < 1:
            return None

        result_dicts = []

        for result_tuple in result_tuples:
            result_dict = {
                'uid': result_tuple[0],
                'discord_id': result_tuple[1],
                'message_id': result_tuple[2],
                'name': result_tuple[3],
                'quote': result_tuple[4],
                'replied_to_name': result_tuple[5],
                'replied_to_quote': result_tuple[6],
                'replied_to_message_id': result_tuple[7]
            }

            result_dicts.append(result_dict)

        return result_dicts

    async def is_quote_in_db(self, message_id: int):
        query = """
            SELECT message_id
            FROM quotes
            WHERE message_id = ?
        """
        parameters = (message_id,)

        try:
            result_tuples = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during is_quote_in_db() for message_id {message_id}.")

        return len(result_tuples) > 0

    async def get_quote_leaderboard(self):
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
            results = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_leaderboard().")

        return results

    async def get_quote_ids(self):
        query = """
            SELECT uid FROM quotes
            ORDER BY uid
        """

        try:
            results = await self.execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_quote_ids().")

        id_list = []

        for result_tuple in results:
            id_list.append(result_tuple[0])

        return id_list

    async def add_quote(self, quote_dict):
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
            await self.execute_query(dbq.INSERT_QUOTE, params=quote_tuple)
        except Error as e:
            if e.sqlite_errorcode == 1555:
                logging.getLogger('respobot.database').warning(f"Quote already in database, ignoring.")
            else:
                logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to add a quote to the quotes table.")

    async def get_special_events(self, earliest_date):
        query = """
            SELECT *
            FROM special_events
            WHERE
                end_date > ?
            ORDER BY start_date
        """
        parameters = (earliest_date,)

        try:
            results = await self.execute_read_query(query, params=parameters)
        except Error as e:
            logging.getLogger('respobot.database').error(f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_special_events() for earliest_date {earliest_date}.")

        if results is None or len(results) < 1:
            return None

        event_dicts = []

        for result_tuple in results:
            if len(result_tuple) < 6:
                continue
            event_dict = {
                'name': result_tuple[1],
                'start_date': result_tuple[2],
                'end_date': result_tuple[3],
                'track': result_tuple[4],
                'cars': result_tuple[5],
                'category': result_tuple[6]
            }

            event_dicts.append(event_dict)

        return event_dicts

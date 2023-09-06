"""
/bot_database/_subsessions.py

Methods that mainly interact with the subsessions table.
"""

import logging
from aiosqlite import Error
from ._queries import *
from ._members import _update_member_dict_objects
from bot_database import BotDatabaseError


async def add_subsessions(self, subsession_dicts):
    """Adds subsessions to the database.

    Arguments:
        subsession_dicts (list): a list of dictionaries as returned from the iRacing /data API.
    """
    for subsession_dict in subsession_dicts:

        subsession_parameters = []
        result_parameters = []
        car_class_parameters = []

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
            subsession_dict['track']['track_id'] if (
                'track' in subsession_dict and 'track_id' in subsession_dict['track']
            ) else None,
            subsession_dict['track']['track_name'] if (
                'track' in subsession_dict and 'track_name' in subsession_dict['track']
            ) else None,
            subsession_dict['track']['config_name'] if (
                'track' in subsession_dict and 'config_name' in subsession_dict['track']
            ) else None,
            subsession_dict['track']['category_id'] if (
                'track' in subsession_dict and 'category_id' in subsession_dict['track']
            ) else None,
            subsession_dict['track']['category'] if (
                'track' in subsession_dict and 'category' in subsession_dict['track']
            ) else None,
            subsession_dict['weather']['version'] if (
                'weather' in subsession_dict and 'version' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['type'] if (
                'weather' in subsession_dict and 'type' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['temp_units'] if (
                'weather' in subsession_dict and 'temp_units' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['temp_value'] if (
                'weather' in subsession_dict and 'temp_value' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['rel_humidity'] if (
                'weather' in subsession_dict and 'rel_humidity' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['fog'] if (
                'weather' in subsession_dict and 'fog' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['wind_dir'] if (
                'weather' in subsession_dict and 'wind_dir' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['wind_units'] if (
                'weather' in subsession_dict and 'wind_units' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['wind_value'] if (
                'weather' in subsession_dict and 'wind_value' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['skies'] if (
                'weather' in subsession_dict and 'skies' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['weather_var_initial'] if (
                'weather' in subsession_dict and 'weather_var_initial' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['weather_var_ongoing'] if (
                'weather' in subsession_dict and 'weather_var_ongoing' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['allow_fog'] if (
                'weather' in subsession_dict and 'allow_fog' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['track_water'] if (
                'weather' in subsession_dict and 'track_water' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['precip_option'] if (
                'weather' in subsession_dict and 'precip_option' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['time_of_day'] if (
                'weather' in subsession_dict and 'time_of_day' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['simulated_start_utc_time'] if (
                'weather' in subsession_dict and 'simulated_start_utc_time' in subsession_dict['weather']
            ) else None,
            subsession_dict['weather']['simulated_start_utc_offset'] if (
                'weather' in subsession_dict and 'simulated_start_utc_offset' in subsession_dict['weather']
            ) else None,
            subsession_dict['track_state']['leave_marbles'] if (
                'track_state' in subsession_dict and 'leave_marbles' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['practice_rubber'] if (
                'track_state' in subsession_dict and 'practice_rubber' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['qualify_rubber'] if (
                'track_state' in subsession_dict and 'qualify_rubber' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['warmup_rubber'] if (
                'track_state' in subsession_dict and 'warmup_rubber' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['race_rubber'] if (
                'track_state' in subsession_dict and 'race_rubber' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['practice_grip_compound'] if (
                'track_state' in subsession_dict and 'practice_grip_compound' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['qualify_grip_compound'] if (
                'track_state' in subsession_dict and 'qualify_grip_compound' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['warmup_grip_compound'] if (
                'track_state' in subsession_dict and 'warmup_grip_compound' in subsession_dict['track_state']
            ) else None,
            subsession_dict['track_state']['race_grip_compound'] if (
                'track_state' in subsession_dict and 'race_grip_compound' in subsession_dict['track_state']
            ) else None,
            subsession_dict['race_summary']['num_opt_laps'] if (
                'race_summary' in subsession_dict and 'num_opt_laps' in subsession_dict['race_summary']
            ) else None,
            subsession_dict['race_summary']['has_opt_path'] if (
                'race_summary' in subsession_dict and 'has_opt_path' in subsession_dict['race_summary']
            ) else None,
            subsession_dict['race_summary']['special_event_type'] if (
                'race_summary' in subsession_dict and 'special_event_type' in subsession_dict['race_summary']
            ) else None,
            subsession_dict['race_summary']['special_event_type_text'] if (
                'race_summary' in subsession_dict and 'special_event_type_text' in subsession_dict['race_summary']
            ) else None,
            subsession_dict['results_restricted'] if 'results_restricted' in subsession_dict else None
        ))

        for session_result_dict in subsession_dict['session_results']:
            for result_dict in session_result_dict['results']:
                result_parameters.append((
                    subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                    session_result_dict['simsession_number'] if 'simsession_number' in session_result_dict else None,
                    session_result_dict['simsession_type'] if 'simsession_type' in session_result_dict else None,
                    session_result_dict['simsession_type_name'] if (
                        'simsession_type_name' in session_result_dict
                    ) else None,
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
                    result_dict['livery']['car_id'] if (
                        'livery' in result_dict and 'car_id' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['pattern'] if (
                        'livery' in result_dict and 'pattern' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['color1'] if (
                        'livery' in result_dict and 'color1' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['color2'] if (
                        'livery' in result_dict and 'color2' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['color3'] if (
                        'livery' in result_dict and 'color3' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['number_font'] if (
                        'livery' in result_dict and 'number_font' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['number_color1'] if (
                        'livery' in result_dict and 'number_color1' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['number_color2'] if (
                        'livery' in result_dict and 'number_color2' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['number_color3'] if (
                        'livery' in result_dict and 'number_color3' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['number_slant'] if (
                        'livery' in result_dict and 'number_slant' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['sponsor1'] if (
                        'livery' in result_dict and 'sponsor1' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['sponsor2'] if (
                        'livery' in result_dict and 'sponsor2' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['car_number'] if (
                        'livery' in result_dict and 'car_number' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['wheel_color'] if (
                        'livery' in result_dict and 'wheel_color' in result_dict['livery']
                    ) else None,
                    result_dict['livery']['rim_type'] if (
                        'livery' in result_dict and 'rim_type' in result_dict['livery']
                    ) else None,
                    result_dict['suit']['pattern'] if (
                        'suit' in result_dict and 'pattern' in result_dict['suit']
                    ) else None,
                    result_dict['suit']['color1'] if (
                        'suit' in result_dict and 'color1' in result_dict['suit']
                    ) else None,
                    result_dict['suit']['color2'] if (
                        'suit' in result_dict and 'color2' in result_dict['suit']
                    ) else None,
                    result_dict['suit']['color3'] if (
                        'suit' in result_dict and 'color3' in result_dict['suit']
                    ) else None,
                    result_dict['helmet']['pattern'] if (
                        'helmet' in result_dict and 'pattern' in result_dict['helmet']
                    ) else None,
                    result_dict['helmet']['color1'] if (
                        'helmet' in result_dict and 'color1' in result_dict['helmet']
                    ) else None,
                    result_dict['helmet']['color2'] if (
                        'helmet' in result_dict and 'color2' in result_dict['helmet']
                    ) else None,
                    result_dict['helmet']['color3'] if (
                        'helmet' in result_dict and 'color3' in result_dict['helmet']
                    ) else None,
                    result_dict['helmet']['face_type'] if (
                        'helmet' in result_dict and 'face_type' in result_dict['helmet']
                    ) else None,
                    result_dict['helmet']['helmet_type'] if (
                        'helmet' in result_dict and 'helmet_type' in result_dict['helmet']
                    ) else None,
                    result_dict['ai'] if 'ai' in result_dict else None
                ))

                if 'team_id' in result_dict and 'driver_results' in result_dict:
                    for driver_result in result_dict['driver_results']:
                        result_parameters.append((
                            subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                            session_result_dict['simsession_number'] if (
                                'simsession_number' in session_result_dict
                            ) else None,
                            session_result_dict['simsession_type'] if (
                                'simsession_type' in session_result_dict
                            ) else None,
                            session_result_dict['simsession_type_name'] if (
                                'simsession_type_name' in session_result_dict
                            ) else None,
                            session_result_dict['simsession_subtype'] if (
                                'simsession_subtype' in session_result_dict
                            ) else None,
                            session_result_dict['simsession_name'] if (
                                'simsession_name' in session_result_dict
                            ) else None,
                            driver_result['cust_id'] if 'cust_id' in driver_result else None,
                            driver_result['team_id'] if 'team_id' in driver_result else None,
                            driver_result['display_name'] if 'display_name' in driver_result else None,
                            driver_result['finish_position'] if 'finish_position' in driver_result else None,
                            driver_result['finish_position_in_class'] if (
                                'finish_position_in_class' in driver_result
                            ) else None,
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
                            driver_result['starting_position_in_class'] if (
                                'starting_position_in_class' in driver_result
                            ) else None,
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
                            driver_result['aggregate_champ_points'] if (
                                'aggregate_champ_points' in driver_result
                            ) else None,
                            driver_result['livery']['car_id'] if (
                                'livery' in driver_result and 'car_id' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['pattern'] if (
                                'livery' in driver_result and 'pattern' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['color1'] if (
                                'livery' in driver_result and 'color1' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['color2'] if (
                                'livery' in driver_result and 'color2' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['color3'] if (
                                'livery' in driver_result and 'color3' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['number_font'] if (
                                'livery' in driver_result and 'number_font' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['number_color1'] if (
                                'livery' in driver_result and 'number_color1' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['number_color2'] if (
                                'livery' in driver_result and 'number_color2' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['number_color3'] if (
                                'livery' in driver_result and 'number_color3' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['number_slant'] if (
                                'livery' in driver_result and 'number_slant' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['sponsor1'] if (
                                'livery' in driver_result and 'sponsor1' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['sponsor2'] if (
                                'livery' in driver_result and 'sponsor2' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['car_number'] if (
                                'livery' in driver_result and 'car_number' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['wheel_color'] if (
                                'livery' in driver_result and 'wheel_color' in driver_result['livery']
                            ) else None,
                            driver_result['livery']['rim_type'] if (
                                'livery' in driver_result and 'rim_type' in driver_result['livery']
                            ) else None,
                            driver_result['suit']['pattern'] if (
                                'suit' in driver_result and 'pattern' in driver_result['suit']
                            ) else None,
                            driver_result['suit']['color1'] if (
                                'suit' in driver_result and 'color1' in driver_result['suit']
                            ) else None,
                            driver_result['suit']['color2'] if (
                                'suit' in driver_result and 'color2' in driver_result['suit']
                            ) else None,
                            driver_result['suit']['color3'] if (
                                'suit' in driver_result and 'color3' in driver_result['suit']
                            ) else None,
                            driver_result['helmet']['pattern'] if (
                                'helmet' in driver_result and 'pattern' in driver_result['helmet']
                            ) else None,
                            driver_result['helmet']['color1'] if (
                                'helmet' in driver_result and 'color1' in driver_result['helmet']
                            ) else None,
                            driver_result['helmet']['color2'] if (
                                'helmet' in driver_result and 'color2' in driver_result['helmet']
                            ) else None,
                            driver_result['helmet']['color3'] if (
                                'helmet' in driver_result and 'color3' in driver_result['helmet']
                            ) else None,
                            driver_result['helmet']['face_type'] if (
                                'helmet' in driver_result and 'face_type' in driver_result['helmet']
                            ) else None,
                            driver_result['helmet']['helmet_type'] if (
                                'helmet' in driver_result and 'helmet_type' in driver_result['helmet']
                            ) else None,
                            driver_result['ai'] if 'ai' in driver_result else None
                        ))

        if 'car_classes' in subsession_dict:
            for car_class_dict in subsession_dict['car_classes']:
                if 'cars_in_class' not in car_class_dict:
                    continue
                for car_dict in car_class_dict['cars_in_class']:
                    car_class_parameters.append((
                        subsession_dict['subsession_id'] if 'subsession_id' in subsession_dict else None,
                        car_class_dict['car_class_id'] if 'car_class_id' in car_class_dict else None,
                        car_dict['car_id'] if 'car_id' in car_dict else None,
                        car_class_dict['name'] if 'name' in car_class_dict else None,
                        car_class_dict['short_name'] if 'short_name' in car_class_dict else None
                    ))

        try:
            await self._execute_write_query(INSERT_SUBSESSIONS, params=subsession_parameters)
        except Error as e:
            subsessions = []
            for subsession_dict in subsession_dicts:
                subsessions.append(subsession_dict['subsession_id'])
            if e.sqlite_errorcode == 1555:
                logging.getLogger('respobot.database').warning(f"Subsession already in database, ignoring.")
                raise BotDatabaseError(
                    f"Error inserting new race data for subsession {subsessions}", ErrorCodes.insert_collision.value
                )
            else:
                logging.getLogger('respobot.database').error(
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                    f"add subsession(s) {subsessions} to the subsessions table."
                )
                raise BotDatabaseError(
                    f"Error inserting new race data for subsession {subsessions}", ErrorCodes.general_failure.value
                )

        try:
            await self._execute_write_query(INSERT_RESULTS, params=result_parameters)
        except Error as e:
            subsessions = []
            for subsession_dict in subsession_dicts:
                subsessions.append(subsession_dict['subsession_id'])
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                "add a result from subsession(s) {subsessions} to the results table."
            )
            raise BotDatabaseError(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                "add a result from subsession(s) {subsessions} to the results table.",
                ErrorCodes.general_failure.value)

        try:
            await self._execute_write_query(INSERT_SUBSESSION_CAR_CLASSES, params=car_class_parameters)
        except Error as e:
            subsessions = []
            for subsession_dict in subsession_dicts:
                subsessions.append(subsession_dict['subsession_id'])
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                f"add a car class from subsession(s) {subsessions} to the subsession_car_classes table."
            )
            raise BotDatabaseError(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                f"add a car class from subsession(s) {subsessions} to the subsession_car_classes table.",
                ErrorCodes.general_failure.value
            )


async def get_subsession_data(self, subsession_id: int):
    """Returns a dict where each column in the subsession table is a key in the dict.

    Arguments:
        subsession_id (int): The id of the subsession to return.

    Returns:
        A dict of the subsession where each table column is a key in the dict.
    """
    if not isinstance(subsession_id, int):
        assert BotDatabaseError("subsession_id must be an integer type.", ErrorCodes.value_error.value)

    query = f"SELECT * FROM subsessions WHERE subsession_id = {subsession_id}"
    parameters = (subsession_id,)
    parameters = ()

    try:
        subsession_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_subsession_data() for subsession {subsession_id}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_subsession_data() for subsession {subsession_id}."
        )

    subsession_dicts = await self._map_tuples_to_dicts(subsession_tuples, 'subsessions')

    if len(subsession_dicts) > 1:
        logging.getLogger('respobot.database').warning(
            f"More than one tuple returned when selecting subsession_id {subsession_id} from the subsession table."
        )

    return subsession_dicts[0]


async def is_subsession_multiclass(self, subsession_id: int):
    """Determine if a subsession was multiclass.

    Arguments:
        subsession_id (int): The id of the subsession to check.

    Returns:
        A bool which is True if the session was multiclass and False otherwise.
    """
    query = """
        SELECT car_class_id
        FROM subsession_car_classes
        WHERE subsession_id = ?
        GROUP BY car_class_id
    """

    parameters = (subsession_id,)

    try:
        result_tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_subsession_multiclass() for subsession {subsession_id}."
        )
        raise BotDatabaseError(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"is_subsession_multiclass() for subsession {subsession_id}."
        )

        return len(result_tuples) > 1


async def get_subsession_drivers_old_irs(self, subsession_id: int, car_class_id: int = None):
    """Get the starting iRating for all drivers in a subsession.

    Arguments:
        subsession_id (int): The id of the subsession to grab data from.

    Keyword arguments:
        car_class_id (int): The id of the car_class if you only want drivers from a specific class.

    Returns:
        A list of tuples containing (cust_id, livery_car_number, oldi_rating).
    """
    query = """
        SELECT
            cust_id,
            livery_car_number,
            oldi_rating
        FROM results
        WHERE
            subsession_id = ? AND
            simsession_number = 0 AND
            cust_id IS NOT NULL AND
            oldi_rating > 0
    """

    parameters = (subsession_id,)

    if car_class_id is not None:
        query += " AND car_class_id = ?"
        parameters += (car_class_id,)

    try:
        results = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"get_subsession_drivers_old_irs() for subsession: {subsession_id} and car_class_id: {car_class_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"get_subsession_drivers_old_irs() for subsession: {subsession_id} and car_class_id: {car_class_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if results is None or len(results) < 1:
        return []

    return results


async def fetch_member_car_numbers_in_subsession(self, subsession_id: int):
    """Returns a list of car number strings for all cars in a subsession that were driven by a Respo member.

    Arguments:
        subsession_id (int): The id of the subsession to grab data from.

    Returns:
        A list of strings containing the car numbers.
    """
    query = """
        SELECT livery_car_number, car_class_id
        FROM results
        WHERE
            subsession_id = ? AND
            cust_id IN (
                SELECT iracing_custid
                FROM members
                WHERE iracing_custid > 0
            )
        GROUP BY livery_car_number
    """
    parameters = (subsession_id,)

    try:
        tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"fetch_member_car_numbers_in_subsession() for subsession_id {subsession_id}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"fetch_member_car_numbers_in_subsession() for subsession_id {subsession_id}."
            ),
            ErrorCodes.general_failure.value
        )

    if tuples is None or len(tuples) < 1:
        return None

    car_numbers = []

    for result_tuple in tuples:
        car_numbers.append(result_tuple[0])

    return car_numbers


async def fetch_members_in_subsession(self, subsession_id: int, car_number: int = None):
    """Returns a list of member dictionaries for all Respo members in the session.

    Arguments:
        subsession_id (int): The id of the subsession to grab data from.

    Returns:
        A list of member dictionaries of Respo participants. Each column in the members table
        is a key in the dictionary.
    """
    query = """
        SELECT
            members.*
        FROM results
        INNER JOIN members
        ON members.iracing_custid = results.cust_id
        WHERE
            subsession_id = ?
    """
    parameters = (subsession_id,)

    if car_number is not None:
        query += """
            AND livery_car_number = ?
        """
        parameters += (car_number,)

    query += """
        GROUP BY members.iracing_custid
    """

    try:
        tuples = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
            f"fetch_members_in_subsession() for subsession_id {subsession_id} and car_number {car_number}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during "
                f"fetch_members_in_subsession() for subsession_id {subsession_id} and car_number {car_number}."
            ),
            ErrorCodes.general_failure.value
        )

    if tuples is None or len(tuples) < 1:
        return None

    member_dicts = await self._map_tuples_to_dicts(tuples, 'members')

    # Scan through the resulting dicts and convert the graph colours to a list of values
    # and datetimes/dates to appropriate objects.
    for member_dict in member_dicts:
        _update_member_dict_objects(member_dict)

    return member_dicts


async def is_subsession_in_db(self, subsession_id: int):
    """Determines if a subsession is in the subsessions table of the database.

    Arguments:
        subsession_id (int): The id of the subsession of interest.

    Returns:
        A bool that is True if the subsession is in the subsessions table and False otherwise.
    """
    query = """
        SELECT subsession_id
        FROM subsessions
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


async def get_cars_in_class(self, subsession_id, car_class_id, simsession_number: int = 0):
    """Get the number of cars that participated in a specific class in a subsession.

    Arguments:
        subsession_id (int): The subsession to analyze.
        car_class_id (int): The id of the car class to count entries.

    Keyword arguments:
        simsession_number (int): The simsession to count from. This may do nothing since it
        shouldn't be possible for a car to be in one session and not another.

    Returns:
        An int representing the number of entries in the specified car class.
    """
    query = """
        SELECT livery_car_number
        FROM results
        WHERE
            subsession_id = ? AND
            car_class_id = ? AND
            simsession_number = ?
        GROUP BY livery_car_number
    """
    parameters = (subsession_id, car_class_id, simsession_number)

    try:
        result = await self._execute_read_query(query, params=parameters)
    except Error as e:
        logging.getLogger('respobot.database').error(
            f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_cars_in_class() for "
            f"subsession_id {subsession_id}, car_class_id {car_class_id}, simsession_number {simsession_number}, "
            f"simsession_type {simsession_type}."
        )
        raise BotDatabaseError(
            (
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} during get_cars_in_class() for "
                f"subsession_id {subsession_id}, car_class_id {car_class_id}, simsession_number {simsession_number}, "
                f"simsession_type {simsession_type}."
            ),
            ErrorCodes.general_failure.value
        )

    return len(result)

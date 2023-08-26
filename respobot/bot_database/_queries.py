"""
/bot_database/_queries.py

Main queries for initializing and maintaining the database.
The queries for specific features are located directly in the code.
"""

CREATE_TABLE_MEMBERS = """
CREATE TABLE 'members' (
    'uid'   INTEGER NOT NULL UNIQUE,
    'name'  TEXT NOT NULL UNIQUE,
    'iracing_custid'    INTEGER NOT NULL UNIQUE,
    'discord_id'    INTEGER NOT NULL UNIQUE,
    'graph_colour'  TEXT,
    'latest_session_found'   TEXT,
    'ir_member_since'   TEXT,
    'pronoun_type' TEXT,
    PRIMARY KEY('uid' AUTOINCREMENT)
);
"""

CREATE_TABLE_SUBSESSIONS = """
CREATE TABLE 'subsessions' (
    'subsession_id' INTEGER NOT NULL UNIQUE,
    'season_id' INTEGER,
    'season_name'   TEXT,
    'season_short_name' TEXT,
    'season_year'   INTEGER,
    'season_quarter'    INTEGER,
    'series_id' INTEGER,
    'series_name'   TEXT,
    'series_short_name' TEXT,
    'series_logo'   TEXT,
    'race_week_num' INTEGER,
    'session_id'    INTEGER,
    'license_category_id'   INTEGER,
    'license_category'  TEXT,
    'private_session_id'    INTEGER,
    'host_id'   INTEGER,
    'session_name'  TEXT,
    'league_id' INTEGER,
    'league_name'   TEXT,
    'league_season_id'  INTEGER,
    'league_season_name'    TEXT,
    'restrict_results'  INTEGER,
    'start_time'    TEXT,
    'end_time'  TEXT,
    'num_laps_for_qual_average' INTEGER,
    'num_laps_for_solo_average' INTEGER,
    'corners_per_lap'   INTEGER,
    'caution_type'  INTEGER,
    'event_type'    INTEGER,
    'event_type_name'   TEXT,
    'driver_changes'    INTEGER,
    'min_team_drivers'  INTEGER,
    'max_team_drivers'  INTEGER,
    'driver_change_rule'    INTEGER,
    'driver_change_param1'  INTEGER,
    'driver_change_param2'  INTEGER,
    'max_weeks' INTEGER,
    'points_type'   TEXT,
    'event_strength_of_field'   INTEGER,
    'event_average_lap' INTEGER,
    'event_laps_complete'   INTEGER,
    'num_cautions'  INTEGER,
    'num_caution_laps'  INTEGER,
    'num_lead_changes'  INTEGER,
    'official_session'  INTEGER,
    'heat_info_id'  INTEGER,
    'special_event_type'    INTEGER,
    'damage_model'  INTEGER,
    'can_protest'   INTEGER,
    'cooldown_minutes'  INTEGER,
    'limit_minutes' INTEGER,
    'track_id'  INTEGER,
    'track_name'    TEXT,
    'track_config_name' TEXT,
    'track_category_id' INTEGER,
    'track_category'    TEXT,
    'weather_version'   INTEGER,
    'weather_type'  INTEGER,
    'weather_temp_units'    INTEGER,
    'weather_temp_value'    INTEGER,
    'weather_rel_humidity'  INTEGER,
    'weather_fog'   INTEGER,
    'weather_wind_dir'  INTEGER,
    'weather_wind_units'    INTEGER,
    'weather_wind_value'    INTEGER,
    'weather_skies' INTEGER,
    'weather_var_initial'   INTEGER,
    'weather_var_ongoing'   INTEGER,
    'weather_allow_fog' INTEGER,
    'weather_track_water'   INTEGER,
    'weather_precip_option' INTEGER,
    'weather_time_of_day'   INTEGER,
    'weather_simulated_start_utc_time'  TEXT,
    'weather_simulated_start_utc_offset'    INTEGER,
    'track_state_leave_marbles' INTEGER,
    'track_state_practice_rubber'   INTEGER,
    'track_state_qualify_rubber'    INTEGER,
    'track_state_warmup_rubber' INTEGER,
    'track_state_race_rubber'   INTEGER,
    'track_state_practice_grip_compound'    INTEGER,
    'track_state_qualify_grip_compound' INTEGER,
    'track_state_warmup_grip_compound'  INTEGER,
    'track_state_race_grip_compound'    INTEGER,
    'race_summary_num_opt_laps' INTEGER,
    'race_summary_has_opt_path' INTEGER,
    'race_summary_special_event_type'   INTEGER,
    'race_summary_special_event_type_text'  TEXT,
    'results_restricted'    INTEGER,
    PRIMARY KEY('subsession_id')
);
"""

CREATE_INDEX_SUBSESSIONS_EVENTTYPE_ID = """
CREATE INDEX 'index_subsessions_eventtype_id' ON 'subsessions' (
    'event_type' ASC,
    'subsession_id' ASC
);
"""

INSERT_SUBSESSIONS = """
INSERT INTO 'subsessions' (
    'subsession_id',
    'season_id',
    'season_name',
    'season_short_name',
    'season_year',
    'season_quarter',
    'series_id',
    'series_name',
    'series_short_name',
    'series_logo',
    'race_week_num',
    'session_id',
    'license_category_id',
    'license_category',
    'private_session_id',
    'host_id',
    'session_name',
    'league_id',
    'league_name',
    'league_season_id',
    'league_season_name',
    'restrict_results',
    'start_time',
    'end_time',
    'num_laps_for_qual_average',
    'num_laps_for_solo_average',
    'corners_per_lap',
    'caution_type',
    'event_type',
    'event_type_name',
    'driver_changes',
    'min_team_drivers',
    'max_team_drivers',
    'driver_change_rule',
    'driver_change_param1',
    'driver_change_param2',
    'max_weeks',
    'points_type',
    'event_strength_of_field',
    'event_average_lap',
    'event_laps_complete',
    'num_cautions',
    'num_caution_laps',
    'num_lead_changes',
    'official_session',
    'heat_info_id',
    'special_event_type',
    'damage_model',
    'can_protest',
    'cooldown_minutes',
    'limit_minutes',
    'track_id',
    'track_name',
    'track_config_name',
    'track_category_id',
    'track_category',
    'weather_version',
    'weather_type',
    'weather_temp_units',
    'weather_temp_value',
    'weather_rel_humidity',
    'weather_fog',
    'weather_wind_dir',
    'weather_wind_units',
    'weather_wind_value',
    'weather_skies',
    'weather_var_initial',
    'weather_var_ongoing',
    'weather_allow_fog',
    'weather_track_water',
    'weather_precip_option',
    'weather_time_of_day',
    'weather_simulated_start_utc_time',
    'weather_simulated_start_utc_offset',
    'track_state_leave_marbles',
    'track_state_practice_rubber',
    'track_state_qualify_rubber',
    'track_state_warmup_rubber',
    'track_state_race_rubber',
    'track_state_practice_grip_compound',
    'track_state_qualify_grip_compound',
    'track_state_warmup_grip_compound',
    'track_state_race_grip_compound',
    'race_summary_num_opt_laps',
    'race_summary_has_opt_path',
    'race_summary_special_event_type',
    'race_summary_special_event_type_text',
    'results_restricted'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

CREATE_TABLE_RESULTS = """
CREATE TABLE 'results' (
    'uid' INTEGER NOT NULL UNIQUE,
    'subsession_id' INTEGER NOT NULL,
    'simsession_number' INTEGER NOT NULL,
    'simsession_type' INTEGER,
    'simsession_type_name' TEXT,
    'simsession_subtype' INTEGER,
    'simsession_name' TEXT,
    'cust_id' INTEGER,
    'team_id' INTEGER,
    'display_name' TEXT,
    'finish_position' INTEGER,
    'finish_position_in_class' INTEGER,
    'laps_lead' INTEGER,
    'laps_complete' INTEGER,
    'opt_laps_complete' INTEGER,
    'interval' INTEGER,
    'class_interval' INTEGER,
    'average_lap' INTEGER,
    'best_lap_num' INTEGER,
    'best_lap_time' INTEGER,
    'best_nlaps_num' INTEGER,
    'best_nlaps_time' INTEGER,
    'best_qual_lap_at' TEXT,
    'best_qual_lap_num' INTEGER,
    'best_qual_lap_time' INTEGER,
    'reason_out_id' INTEGER,
    'reason_out' TEXT,
    'champ_points' INTEGER,
    'drop_race' INTEGER,
    'club_points' INTEGER,
    'position' INTEGER,
    'qual_lap_time' INTEGER,
    'starting_position' INTEGER,
    'starting_position_in_class' INTEGER,
    'car_class_id' INTEGER,
    'car_class_name' TEXT,
    'car_class_short_name' TEXT,
    'club_id' INTEGER,
    'club_name' TEXT,
    'club_shortname' TEXT,
    'division' INTEGER,
    'division_name' TEXT,
    'old_license_level' INTEGER,
    'old_sub_level' INTEGER,
    'old_cpi' REAL,
    'oldi_rating' INTEGER,
    'old_ttrating' INTEGER,
    'new_license_level' INTEGER,
    'new_sub_level' INTEGER,
    'new_cpi' REAL,
    'newi_rating' INTEGER,
    'new_ttrating' INTEGER,
    'multiplier' INTEGER,
    'license_change_oval' INTEGER,
    'license_change_road' INTEGER,
    'incidents' INTEGER,
    'max_pct_fuel_fill' INTEGER,
    'weight_penalty_kg' INTEGER,
    'league_points' INTEGER,
    'league_agg_points' INTEGER,
    'car_id' INTEGER,
    'car_name' TEXT,
    'aggregate_champ_points' INTEGER,
    'livery_car_id' INTEGER,
    'livery_pattern' INTEGER,
    'livery_color1' TEXT,
    'livery_color2' TEXT,
    'livery_color3' TEXT,
    'livery_number_font' INTEGER,
    'livery_number_color1' TEXT,
    'livery_number_color2' TEXT,
    'livery_number_color3' TEXT,
    'livery_number_slant' INTEGER,
    'livery_sponsor1' INTEGER,
    'livery_sponsor2' INTEGER,
    'livery_car_number' TEXT,
    'livery_wheel_color' TEXT,
    'livery_rim_type' INTEGER,
    'suit_pattern' INTEGER,
    'suit_color1' TEXT,
    'suit_color2' TEXT,
    'suit_color3' TEXT,
    'helmet_pattern' INTEGER,
    'helmet_color1' TEXT,
    'helmet_color2' TEXT,
    'helmet_color3' TEXT,
    'helmet_face_type' INTEGER,
    'helmet_type' INTEGER,
    'ai' INTEGER,
    PRIMARY KEY("uid" AUTOINCREMENT),
    FOREIGN KEY("subsession_id") REFERENCES "subsessions"("subsession_id") ON UPDATE CASCADE ON DELETE CASCADE
);
"""

INDEX_RESULTS_SUBID_SESNUM = """
CREATE INDEX 'index_results_subid_sesnum' ON 'results' (
    'subsession_id' ASC,
    'simsession_number' DESC
);
"""

INDEX_RESULTS_SESNUM_SUBID_CUSTID = """
CREATE INDEX 'index_results_sesnum_subid_custid' ON 'results' (
    'simsession_type' ASC,
    'simsession_number' DESC,
    'subsession_id' ASC,
    'cust_id'   ASC
);
"""

INDEX_RESULTS_IRATING_GRAPH = """
CREATE INDEX 'index_results_irating_graph' ON 'results' (
    'cust_id'   ASC,
    'simsession_type'   ASC
);
"""

INSERT_RESULTS = """
INSERT INTO 'results' (
    'subsession_id',
    'simsession_number',
    'simsession_type',
    'simsession_type_name',
    'simsession_subtype',
    'simsession_name',
    'cust_id',
    'team_id',
    'display_name',
    'finish_position',
    'finish_position_in_class',
    'laps_lead',
    'laps_complete',
    'opt_laps_complete',
    'interval',
    'class_interval',
    'average_lap',
    'best_lap_num',
    'best_lap_time',
    'best_nlaps_num',
    'best_nlaps_time',
    'best_qual_lap_at',
    'best_qual_lap_num',
    'best_qual_lap_time',
    'reason_out_id',
    'reason_out',
    'champ_points',
    'drop_race',
    'club_points',
    'position',
    'qual_lap_time',
    'starting_position',
    'starting_position_in_class',
    'car_class_id',
    'car_class_name',
    'car_class_short_name',
    'club_id',
    'club_name',
    'club_shortname',
    'division',
    'division_name',
    'old_license_level',
    'old_sub_level',
    'old_cpi',
    'oldi_rating',
    'old_ttrating',
    'new_license_level',
    'new_sub_level',
    'new_cpi',
    'newi_rating',
    'new_ttrating',
    'multiplier',
    'license_change_oval',
    'license_change_road',
    'incidents',
    'max_pct_fuel_fill',
    'weight_penalty_kg',
    'league_points',
    'league_agg_points',
    'car_id',
    'car_name',
    'aggregate_champ_points',
    'livery_car_id',
    'livery_pattern',
    'livery_color1',
    'livery_color2',
    'livery_color3',
    'livery_number_font',
    'livery_number_color1',
    'livery_number_color2',
    'livery_number_color3',
    'livery_number_slant',
    'livery_sponsor1',
    'livery_sponsor2',
    'livery_car_number',
    'livery_wheel_color',
    'livery_rim_type',
    'suit_pattern',
    'suit_color1',
    'suit_color2',
    'suit_color3',
    'helmet_pattern',
    'helmet_color1',
    'helmet_color2',
    'helmet_color3',
    'helmet_face_type',
    'helmet_type',
    'ai'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

CREATE_TABLE_SUBSESSION_CAR_CLASSES = """
CREATE TABLE 'subsession_car_classes' (
    'uid' INTEGER NOT NULL UNIQUE,
    'subsession_id' INTEGER NOT NULL,
    'car_class_id' INTEGER,
    'car_id' INTEGER NOT NULL,
    'car_class_name' TEXT,
    'car_class_short_name' TEXT,
    PRIMARY KEY('uid')
);
"""

INDEX_SUBSESSION_CAR_CLASSES_SUBID_CLASSID = """
CREATE INDEX 'index_subsession_car_classes_subid_classid' ON 'subsession_car_classes' (
    'subsession_id' ASC,
    'car_class_id' ASC
);
"""

INSERT_SUBSESSION_CAR_CLASSES = """
INSERT INTO 'subsession_car_classes' (
    'subsession_id',
    'car_class_id',
    'car_id',
    'car_class_name',
    'car_class_short_name'
)
VALUES (
    ?, ?, ?, ?, ?
);
"""

CREATE_TABLE_LAPS = """
CREATE TABLE 'laps' (
    'uid' INTEGER NOT NULL UNIQUE,
    'subsession_id' INTEGER NOT NULL,
    'simsession_number' INTEGER NOT NULL,
    'group_id' INTEGER,
    'name' TEXT,
    'cust_id' INTEGER NOT NULL,
    'display_name' TEXT,
    'lap_number' INTEGER NOT NULL,
    'flags' INTEGER,
    'incident' INTEGER,
    'session_time' INTEGER,
    'session_start_time' INTEGER,
    'lap_time' INTEGER,
    'team_fastest_lap' INTEGER,
    'personal_best_lap' INTEGER,
    'license_level' INTEGER,
    'car_number' TEXT,
    'lap_events' TEXT,
    'lap_position' INTEGER,
    'interval' INTEGER,
    'interval_units' TEXT,
    'fastest_lap' INTEGER,
    'ai' INTEGER,
    PRIMARY KEY('uid')
);
"""

INDEX_LAPS_SUBID_SESSNUM_CUSTID = """
CREATE INDEX 'index_laps_subid_sessnum_custid' ON 'laps' (
    'subsession_id' ASC,
    'simsession_number' ASC,
    'cust_id' ASC
);
"""

INSERT_LAPS = """
INSERT INTO 'laps' (
    'subsession_id',
    'simsession_number',
    'group_id',
    'name',
    'cust_id',
    'display_name',
    'lap_number',
    'flags',
    'incident',
    'session_time',
    'session_start_time',
    'lap_time',
    'team_fastest_lap',
    'personal_best_lap',
    'license_level',
    'car_number',
    'lap_events',
    'lap_position',
    'interval',
    'interval_units',
    'fastest_lap',
    'ai'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

CREATE_TABLE_CURRENT_SEASONS = """
CREATE TABLE 'current_seasons' (
    'season_id' INTEGER NOT NULL UNIQUE,
    'active' INTEGER,
    'allowed_season_members' TEXT,
    'car_class_ids' TEXT,
    'car_types' TEXT,
    'caution_laps_do_not_count' INTEGER,
    'complete' INTEGER,
    'cross_license' INTEGER,
    'driver_change_rule' INTEGER,
    'driver_changes' INTEGER,
    'drops' INTEGER,
    'enable_pitlane_collisions' INTEGER,
    'fixed_setup' INTEGER,
    'green_white_checkered_limit' INTEGER,
    'grid_by_class' INTEGER,
    'hardcore_level' INTEGER,
    'heat_info_id' INTEGER,
    'heat_cust_id' INTEGER,
    'heat_hidden' INTEGER,
    'heat_created' TEXT,
    'heat_heat_info_name' TEXT,
    'heat_description' TEXT,
    'heat_max_entrants' INTEGER,
    'heat_race_style' INTEGER,
    'heat_open_practice' INTEGER,
    'heat_pre_qual_practice_length_minutes' INTEGER,
    'heat_pre_qual_num_to_main' INTEGER,
    'heat_qual_style' INTEGER,
    'heat_qual_length_minutes' INTEGER,
    'heat_qual_laps' INTEGER,
    'heat_qual_num_to_main' INTEGER,
    'heat_qual_scoring' INTEGER,
    'heat_qual_caution_type' INTEGER,
    'heat_qual_open_delay_seconds' INTEGER,
    'heat_qual_scores_champ_points' INTEGER,
    'heat_length_minutes' INTEGER,
    'heat_laps' INTEGER,
    'heat_max_field_size' INTEGER,
    'heat_num_position_to_invert' INTEGER,
    'heat_caution_type' INTEGER,
    'heat_num_from_each_to_main' INTEGER,
    'heat_scores_champ_points' INTEGER,
    'heat_consolation_num_to_consolation' INTEGER,
    'heat_consolation_num_to_main' INTEGER,
    'heat_consolation_first_max_field_size' INTEGER,
    'heat_consolation_first_session_length_minutes' INTEGER,
    'heat_consolation_first_session_laps' INTEGER,
    'heat_consolation_delta_max_field_size' INTEGER,
    'heat_consolation_delta_session_length_minutes' INTEGER,
    'heat_consolation_delta_session_laps' INTEGER,
    'heat_consolation_num_position_to_invert' INTEGER,
    'heat_consolation_scores_champ_points' INTEGER,
    'heat_consolation_run_always' INTEGER,
    'heat_pre_main_practice_length_minutes' INTEGER,
    'heat_main_length_minutes' INTEGER,
    'heat_main_laps' INTEGER,
    'heat_main_max_field_size' INTEGER,
    'heat_main_num_position_to_invert' INTEGER,
    'heat_session_minutes_estimate' INTEGER,
    'ignore_license_for_practice' INTEGER,
    'incident_limit' INTEGER,
    'incident_warn_mode' INTEGER,
    'incident_warn_param1' INTEGER,
    'incident_warn_param2' INTEGER,
    'is_heat_racing' INTEGER,
    'license_group' INTEGER,
    'license_group_types' TEXT,
    'lucky_dog' INTEGER,
    'max_team_drivers' INTEGER,
    'max_weeks' INTEGER,
    'min_team_drivers' INTEGER,
    'multiclass' INTEGER,
    'must_use_diff_tire_types_in_race' INTEGER,
    'next_race_session' TEXT,
    'num_opt_laps' INTEGER,
    'official' INTEGER,
    'op_duration' INTEGER,
    'open_practice_session_type_id' INTEGER,
    'qualifier_must_start_race' INTEGER,
    'race_week' INTEGER,
    'race_week_to_make_divisions' INTEGER,
    'reg_user_count' INTEGER,
    'region_competition' INTEGER,
    'restrict_by_member' INTEGER,
    'restrict_to_car' INTEGER,
    'restrict_viewing' INTEGER,
    'schedule_description' TEXT,
    'season_name' TEXT,
    'season_quarter' INTEGER,
    'season_short_name' TEXT,
    'season_year' INTEGER,
    'send_to_open_practice' INTEGER,
    'series_id' INTEGER,
    'short_parade_lap' INTEGER,
    'start_date' TEXT,
    'start_on_qual_tire' INTEGER,
    'start_zone' INTEGER,
    'track_types' TEXT,
    'unsport_conduct_rule_mode' INTEGER,
    PRIMARY KEY('season_id')
);
"""

INSERT_CURRENT_SEASONS = """
INSERT INTO 'current_seasons' (
    'active',
    'allowed_season_members',
    'car_class_ids',
    'car_types',
    'caution_laps_do_not_count',
    'complete',
    'cross_license',
    'driver_change_rule',
    'driver_changes',
    'drops',
    'enable_pitlane_collisions',
    'fixed_setup',
    'green_white_checkered_limit',
    'grid_by_class',
    'hardcore_level',
    'heat_info_id',
    'heat_cust_id',
    'heat_hidden',
    'heat_created',
    'heat_heat_info_name',
    'heat_description',
    'heat_max_entrants',
    'heat_race_style',
    'heat_open_practice',
    'heat_pre_qual_practice_length_minutes',
    'heat_pre_qual_num_to_main',
    'heat_qual_style',
    'heat_qual_length_minutes',
    'heat_qual_laps',
    'heat_qual_num_to_main',
    'heat_qual_scoring',
    'heat_qual_caution_type',
    'heat_qual_open_delay_seconds',
    'heat_qual_scores_champ_points',
    'heat_length_minutes',
    'heat_laps',
    'heat_max_field_size',
    'heat_num_position_to_invert',
    'heat_caution_type',
    'heat_num_from_each_to_main',
    'heat_scores_champ_points',
    'heat_consolation_num_to_consolation',
    'heat_consolation_num_to_main',
    'heat_consolation_first_max_field_size',
    'heat_consolation_first_session_length_minutes',
    'heat_consolation_first_session_laps',
    'heat_consolation_delta_max_field_size',
    'heat_consolation_delta_session_length_minutes',
    'heat_consolation_delta_session_laps',
    'heat_consolation_num_position_to_invert',
    'heat_consolation_scores_champ_points',
    'heat_consolation_run_always',
    'heat_pre_main_practice_length_minutes',
    'heat_main_length_minutes',
    'heat_main_laps',
    'heat_main_max_field_size',
    'heat_main_num_position_to_invert',
    'heat_session_minutes_estimate',
    'ignore_license_for_practice',
    'incident_limit',
    'incident_warn_mode',
    'incident_warn_param1',
    'incident_warn_param2',
    'is_heat_racing',
    'license_group',
    'license_group_types',
    'lucky_dog',
    'max_team_drivers',
    'max_weeks',
    'min_team_drivers',
    'multiclass',
    'must_use_diff_tire_types_in_race',
    'next_race_session',
    'num_opt_laps',
    'official',
    'op_duration',
    'open_practice_session_type_id',
    'qualifier_must_start_race',
    'race_week',
    'race_week_to_make_divisions',
    'reg_user_count',
    'region_competition',
    'restrict_by_member',
    'restrict_to_car',
    'restrict_viewing',
    'schedule_description',
    'season_name',
    'season_quarter',
    'season_short_name',
    'season_year',
    'send_to_open_practice',
    'series_id',
    'short_parade_lap',
    'start_date',
    'start_on_qual_tire',
    'start_zone',
    'track_types',
    'unsport_conduct_rule_mode',
    'season_id'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

UPDATE_CURRENT_SEASONS = """
UPDATE 'current_seasons'
SET
    active = ?,
    allowed_season_members = ?,
    car_class_ids = ?,
    car_types = ?,
    caution_laps_do_not_count = ?,
    complete = ?,
    cross_license = ?,
    driver_change_rule = ?,
    driver_changes = ?,
    drops = ?,
    enable_pitlane_collisions = ?,
    fixed_setup = ?,
    green_white_checkered_limit = ?,
    grid_by_class = ?,
    hardcore_level = ?,
    heat_info_id = ?,
    heat_cust_id = ?,
    heat_hidden = ?,
    heat_created = ?,
    heat_heat_info_name = ?,
    heat_description = ?,
    heat_max_entrants = ?,
    heat_race_style = ?,
    heat_open_practice = ?,
    heat_pre_qual_practice_length_minutes = ?,
    heat_pre_qual_num_to_main = ?,
    heat_qual_style = ?,
    heat_qual_length_minutes = ?,
    heat_qual_laps = ?,
    heat_qual_num_to_main = ?,
    heat_qual_scoring = ?,
    heat_qual_caution_type = ?,
    heat_qual_open_delay_seconds = ?,
    heat_qual_scores_champ_points = ?,
    heat_length_minutes = ?,
    heat_laps = ?,
    heat_max_field_size = ?,
    heat_num_position_to_invert = ?,
    heat_caution_type = ?,
    heat_num_from_each_to_main = ?,
    heat_scores_champ_points = ?,
    heat_consolation_num_to_consolation = ?,
    heat_consolation_num_to_main = ?,
    heat_consolation_first_max_field_size = ?,
    heat_consolation_first_session_length_minutes = ?,
    heat_consolation_first_session_laps = ?,
    heat_consolation_delta_max_field_size = ?,
    heat_consolation_delta_session_length_minutes = ?,
    heat_consolation_delta_session_laps = ?,
    heat_consolation_num_position_to_invert = ?,
    heat_consolation_scores_champ_points = ?,
    heat_consolation_run_always = ?,
    heat_pre_main_practice_length_minutes = ?,
    heat_main_length_minutes = ?,
    heat_main_laps = ?,
    heat_main_max_field_size = ?,
    heat_main_num_position_to_invert = ?,
    heat_session_minutes_estimate = ?,
    ignore_license_for_practice = ?,
    incident_limit = ?,
    incident_warn_mode = ?,
    incident_warn_param1 = ?,
    incident_warn_param2 = ?,
    is_heat_racing = ?,
    license_group = ?,
    license_group_types = ?,
    lucky_dog = ?,
    max_team_drivers = ?,
    max_weeks = ?,
    min_team_drivers = ?,
    multiclass = ?,
    must_use_diff_tire_types_in_race = ?,
    next_race_session = ?,
    num_opt_laps = ?,
    official = ?,
    op_duration = ?,
    open_practice_session_type_id = ?,
    qualifier_must_start_race = ?,
    race_week = ?,
    race_week_to_make_divisions = ?,
    reg_user_count = ?,
    region_competition = ?,
    restrict_by_member = ?,
    restrict_to_car = ?,
    restrict_viewing = ?,
    schedule_description = ?,
    season_name = ?,
    season_quarter = ?,
    season_short_name = ?,
    season_year = ?,
    send_to_open_practice = ?,
    series_id = ?,
    short_parade_lap = ?,
    start_date = ?,
    start_on_qual_tire = ?,
    start_zone = ?,
    track_types = ?,
    unsport_conduct_rule_mode = ?
WHERE
    season_id = ?
"""

CREATE_TABLE_SERIES = """
CREATE TABLE 'series' (
    'series_id' INTEGER NOT NULL UNIQUE,
    'series_name' TEXT,
    'series_short_name' TEXT,
    'category_id' INTEGER,
    'category' TEXT,
    'active' INTEGER,
    'official' INTEGER,
    'fixed_setup' INTEGER,
    'search_filters' TEXT,
    'logo' TEXT,
    'license_group' INTEGER,
    'license_group_types' TEXT,
    'allowed_licenses' TEXT,
    PRIMARY KEY('series_id')
);
"""

INSERT_SERIES = """
INSERT INTO 'series' (
    'series_name',
    'series_short_name',
    'category_id',
    'category',
    'active',
    'official',
    'fixed_setup',
    'search_filters',
    'logo',
    'license_group',
    'license_group_types',
    'allowed_licenses',
    'series_id'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

UPDATE_SERIES = """
UPDATE 'series'
SET
    series_name = ?,
    series_short_name = ?,
    category_id = ?,
    category = ?,
    active = ?,
    official = ?,
    fixed_setup = ?,
    search_filters = ?,
    logo = ?,
    license_group = ?,
    license_group_types = ?,
    allowed_licenses = ?
WHERE
    series_id = ?
"""

CREATE_TABLE_SEASONS = """
CREATE TABLE 'seasons' (
    'season_id' INTEGER NOT NULL UNIQUE,
    'series_id' INTEGER,
    'season_name' TEXT,
    'season_short_name' TEXT,
    'season_year' INTEGER,
    'season_quarter' INTEGER,
    'active' INTEGER,
    'official' INTEGER,
    'driver_changes' INTEGER,
    'fixed_setup' INTEGER,
    'license_group' INTEGER,
    'license_group_types' TEXT,
    'max_race_week' INTEGER,
    PRIMARY KEY('season_id')
);
"""

INSERT_SEASONS = """
INSERT INTO 'seasons' (
    'series_id',
    'season_name',
    'season_short_name',
    'season_year',
    'season_quarter',
    'active',
    'official',
    'driver_changes',
    'fixed_setup',
    'license_group',
    'license_group_types',
    'max_race_week',
    'season_id'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""

UPDATE_SEASONS = """
UPDATE 'seasons'
SET
    series_id = ?,
    season_name = ?,
    season_short_name = ?,
    season_year = ?,
    season_quarter = ?,
    active = ?,
    official = ?,
    driver_changes = ?,
    fixed_setup = ?,
    license_group = ?,
    license_group_types = ?,
    max_race_week = ?
WHERE
    season_id = ?
"""

CREATE_TABLE_SEASON_CAR_CLASSES = """
CREATE TABLE 'season_car_classes' (
    'uid' INTEGER NOT NULL UNIQUE,
    'season_id' INTEGER NOT NULL,
    'car_class_id' INTEGER NOT NULL,
    'short_name' INTEGER NOT NULL,
    'name' INTEGER,
    'relative_speed' INTEGER,
    PRIMARY KEY('uid')
);
"""

INSERT_SEASON_CAR_CLASSES = """
INSERT INTO 'season_car_classes' (
    'short_name',
    'name',
    'relative_speed',
    'season_id',
    'car_class_id'
)
VALUES (
    ?, ?, ?, ?, ?
)
"""

UPDATE_SEASON_CAR_CLASSES = """
UPDATE 'season_car_classes'
SET
    short_name = ?,
    name = ?,
    relative_speed = ?
WHERE
    season_id = ? AND
    car_class_id = ?
"""

CREATE_TABLE_CURRENT_CAR_CLASSES = """
CREATE TABLE 'current_car_classes' (
    'car_class_id'  INTEGER NOT NULL,
    'car_dirpath'   TEXT,
    'car_id'    INTEGER NOT NULL,
    'retired'   INTEGER,
    'cust_id'   INTEGER,
    'name'  TEXT,
    'relative_speed'    INTEGER,
    'short_name'    TEXT
);
"""

CLEAR_CURRENT_CAR_CLASSES = """
DELETE FROM 'current_car_classes'
"""

INSERT_CURRENT_CAR_CLASSES = """
INSERT INTO 'current_car_classes' (
    'car_dirpath',
    'retired',
    'cust_id',
    'name',
    'relative_speed',
    'short_name',
    'car_class_id',
    'car_id'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?
)
"""

UPDATE_CURRENT_CAR_CLASSES = """
UPDATE current_car_classes
SET
    car_dirpath = ?,
    retired = ?,
    cust_id = ?,
    name = ?,
    relative_speed = ?,
    short_name = ?
WHERE
    car_class_id = ? AND
    car_id = ?
"""

CREATE_TABLE_SEASON_DATES = """
CREATE TABLE 'season_dates' (
    'uid' INTEGER NOT NULL UNIQUE,
    'season_year' INTEGER NOT NULL,
    'season_quarter' INTEGER NOT NULL,
    'start_time' TEXT NOT NULL,
    'end_time' TEXT NOT NULL,
    PRIMARY KEY('uid')
);
"""

INSERT_SEASON_DATES = """
INSERT INTO 'season_dates' (
    'start_time',
    'end_time',
    'season_year',
    'season_quarter'
)
VALUES (
    ?, ?, ?, ?
)
"""

UPDATE_SEASON_DATES = """
UPDATE season_dates
SET
    start_time = ?,
    end_time = ?
WHERE
    season_year = ? AND
    season_quarter = ?
"""

CREATE_TABLE_QUOTES = """
CREATE TABLE 'quotes' (
    'uid'   INTEGER NOT NULL UNIQUE,
    'discord_id'    INTEGER NOT NULL,
    'message_id'    INTEGER NOT NULL UNIQUE,
    'name'  TEXT,
    'quote' TEXT NOT NULL,
    'replied_to_name'   TEXT,
    'replied_to_quote'  TEXT,
    'replied_to_message_id' INTEGER,
    PRIMARY KEY('uid' AUTOINCREMENT)
);
"""

CREATE_INDEX_QUOTES = """
CREATE INDEX 'index_quotes' ON 'quotes' (
    'discord_id'    ASC
);
"""

INSERT_QUOTE = """
INSERT INTO 'quotes' (
    'discord_id',
    'message_id',
    'name',
    'quote',
    'replied_to_name',
    'replied_to_quote',
    'replied_to_message_id'
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?
)
"""

CREATE_TABLE_SPECIAL_EVENTS = """
CREATE TABLE "special_events" (
    "uid"   INTEGER NOT NULL UNIQUE,
    "name"  TEXT NOT NULL,
    "start_date"    TEXT NOT NULL,
    "end_date"  TEXT NOT NULL,
    "track" TEXT NOT NULL,
    "cars"  TEXT NOT NULL,
    "category"  TEXT NOT NULL,
    PRIMARY KEY("uid" AUTOINCREMENT)
);
"""

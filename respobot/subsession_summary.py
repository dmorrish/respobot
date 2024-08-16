import logging
import traceback
import discord
import math

import constants
import helpers
from bot_database import BotDatabase, BotDatabaseError
from irslashdata import constants as irConstants


class CarResultSummary():
    def __init__(self):
        self.results_url = None  # DONE
        self.series_name = None  # DONE
        self.season_id = None  # DONE
        self.league_name = None  # DONE
        self.session_name = None  # DONE
        self.car_name = None
        self.car_class_id = None
        self.car_class_name = None  # DONE
        self.track_name = None  # DONE
        self.track_config_name = None  # DONE
        self.track_category_id = None  # DONE
        self.license_category_id = None  # DONE
        self.cars_in_event = None  # DONE
        self.cars_in_class = None  # DONE
        self.event_strength_of_field = None  # DONE
        self.class_strength_of_field = None  # DONE
        self.max_team_drivers = None  # DONE
        self.is_multiclass = None  # DONE

        self.checkered_flag_lap_num = None  # DONE
        self.green_flag_lap_num = None  # DONE

        self.tow_laps = None  # DONE
        self.car_contact_laps = None  # DONE
        self.contact_laps = None  # DONE
        self.lost_control_laps = None  # DONE
        self.black_flag_laps = None  # DONE

        self.race_incidents = None  # DONE
        self.heat_incidents = None  # DONE

        self.got_fastest_race_lap = None  # DONE
        self.fastest_race_lap_time = None  # DONE
        self.got_fastest_heat_lap = None  # DONE
        self.fastest_heat_lap_time = None  # DONE
        self.got_fastest_qual_lap = None  # DONE
        self.fastest_qual_lap_time = None  # DONE
        self.fastest_qual_lap_driver_cust_id = None  # DONE

        self.close_finishers = None  # DONE
        self.laps_down = None  # DONE

        self.race_starting_position_in_class = None  # DONE
        self.race_finish_position_in_class = None  # DONE
        self.race_finish_position_relative_to_car_num = None  # DONE

        self.heat_starting_position_in_class = None  # DONE
        self.heat_finish_position_in_class = None  # DONE
        self.heat_finish_position_relative_to_car_num = None  # DONE

        self.car_number_in_class = None  # DONE

        self.laps_led = None  # DONE
        self.did_not_finish = None  # DONE
        self.disqualified = None  # DONE

        self.driver_race_results = None  # DONE
        self.driver_heat_results = None  # DONE

    def from_dict(self, data_dict):
        self.results_url = data_dict['results_url'] if (
            'results_url' in data_dict
        ) else None
        self.series_name = data_dict['series_name'] if (
            'series_name' in data_dict
        ) else None
        self.season_id = data_dict['season_id'] if (
            'season_id' in data_dict
        ) else None
        self.league_name = data_dict['league_name'] if (
            'league_name' in data_dict
        ) else None
        self.session_name = data_dict['session_name'] if (
            'session_name' in data_dict
        ) else None
        self.car_name = data_dict['car_name'] if (
            'car_name' in data_dict
        ) else None
        self.car_class_id = data_dict['car_class_id'] if (
            'car_class_id' in data_dict
        ) else None
        self.car_class_name = data_dict['car_class_name'] if (
            'car_class_name' in data_dict
        ) else None
        self.track_name = data_dict['track_name'] if (
            'track_name' in data_dict
        ) else None
        self.track_config_name = data_dict['track_config_name'] if (
            'track_config_name' in data_dict
        ) else None
        self.track_category_id = data_dict['track_category_id'] if (
            'track_category_id' in data_dict
        ) else None
        self.license_category_id = data_dict['license_category_id'] if (
            'license_category_id' in data_dict
        ) else None
        self.cars_in_event = data_dict['cars_in_event'] if (
            'cars_in_event' in data_dict
        ) else None
        self.cars_in_class = data_dict['cars_in_class'] if (
            'cars_in_class' in data_dict
        ) else None
        self.event_strength_of_field = data_dict['event_strength_of_field'] if (
            'event_strength_of_field' in data_dict
        ) else None
        self.class_strength_of_field = data_dict['class_strength_of_field'] if (
            'class_strength_of_field' in data_dict
        ) else None
        self.max_team_drivers = data_dict['max_team_drivers'] if (
            'max_team_drivers' in data_dict
        ) else None
        self.is_multiclass = data_dict['is_multiclass'] if (
            'is_multiclass' in data_dict
        ) else None

        self.checkered_flag_lap_num = data_dict['checkered_flag_lap_num'] if (
            'checkered_flag_lap_num' in data_dict
        ) else None
        self.green_flag_lap_num = data_dict['green_flag_lap_num'] if (
            'green_flag_lap_num' in data_dict
        ) else None

        self.tow_laps = data_dict['tow_laps'] if (
            'tow_laps' in data_dict
        ) else None
        self.car_contact_laps = data_dict['car_contact_laps'] if (
            'car_contact_laps' in data_dict
        ) else None
        self.contact_laps = data_dict['contact_laps'] if (
            'contact_laps' in data_dict
        ) else None
        self.lost_control_laps = data_dict['lost_control_laps'] if (
            'lost_control_laps' in data_dict
        ) else None
        self.black_flag_laps = data_dict['black_flag_laps'] if (
            'black_flag_laps' in data_dict
        ) else None

        self.race_incidents = data_dict['race_incidents'] if (
            'race_incidents' in data_dict
        ) else None
        self.heat_incidents = data_dict['heat_incidents'] if (
            'heat_incidents' in data_dict
        ) else None

        self.got_fastest_race_lap = data_dict['got_fastest_race_lap'] if (
            'got_fastest_race_lap' in data_dict
        ) else None
        self.fastest_race_lap_time = data_dict['fastest_race_lap_time'] if (
            'fastest_race_lap_time' in data_dict
        ) else None
        self.got_fastest_heat_lap = data_dict['got_fastest_heat_lap'] if (
            'got_fastest_heat_lap' in data_dict
        ) else None
        self.fastest_heat_lap_time = data_dict['fastest_heat_lap_time'] if (
            'fastest_heat_lap_time' in data_dict
        ) else None
        self.got_fastest_qual_lap = data_dict['got_fastest_qual_lap'] if (
            'got_fastest_qual_lap' in data_dict
        ) else None
        self.fastest_qual_lap_time = data_dict['fastest_qual_lap_time'] if (
            'fastest_qual_lap_time' in data_dict
        ) else None
        self.fastest_qual_lap_driver_cust_id = data_dict['fastest_qual_lap_driver_cust_id'] if (
            'fastest_qual_lap_driver_cust_id' in data_dict
        ) else None

        self.close_finishers = data_dict['close_finishers'] if (
            'close_finishers' in data_dict
        ) else None
        self.laps_down = data_dict['laps_down'] if (
            'laps_down' in data_dict
        ) else None

        self.race_starting_position_in_class = data_dict['race_starting_position_in_class'] if (
            'race_starting_position_in_class' in data_dict
        ) else None
        self.race_finish_position_in_class = data_dict['race_finish_position_in_class'] if (
            'race_finish_position_in_class' in data_dict
        ) else None
        self.race_finish_position_relative_to_car_num = data_dict['race_finish_position_relative_to_car_num'] if (
            'race_finish_position_relative_to_car_num' in data_dict
        ) else None

        self.heat_starting_position_in_class = data_dict['heat_starting_position_in_class'] if (
            'heat_starting_position_in_class' in data_dict
        ) else None
        self.heat_finish_position_in_class = data_dict['heat_finish_position_in_class'] if (
            'heat_finish_position_in_class' in data_dict
        ) else None
        self.heat_finish_position_relative_to_car_num = data_dict['heat_finish_position_relative_to_car_num'] if (
            'heat_finish_position_relative_to_car_num' in data_dict
        ) else None

        self.car_number_in_class = data_dict['car_number_in_class'] if (
            'car_number_in_class' in data_dict
        ) else None

        self.laps_led = data_dict['laps_led'] if (
            'laps_led' in data_dict
        ) else None
        self.did_not_finish = data_dict['did_not_finish'] if (
            'did_not_finish' in data_dict
        ) else None
        self.disqualified = data_dict['disqualified'] if (
            'disqualified' in data_dict
        ) else None

        if 'driver_race_results' in data_dict:
            self.driver_race_results = []
            for driver_race_result in data_dict['driver_race_results']:
                driver_race_result_obj = DriverResultSummary()
                driver_race_result_obj.cust_id = driver_race_result['cust_id'] if (
                    'cust_id' in driver_race_result
                ) else None
                driver_race_result_obj.display_name = driver_race_result['display_name'] if (
                    'display_name' in driver_race_result
                ) else None
                driver_race_result_obj.irating_new = driver_race_result['irating_new'] if (
                    'irating_new' in driver_race_result
                ) else None
                driver_race_result_obj.irating_old = driver_race_result['irating_old'] if (
                    'irating_old' in driver_race_result
                ) else None
                driver_race_result_obj.license_level_new = driver_race_result['license_level_new'] if (
                    'license_level_new' in driver_race_result
                ) else None
                driver_race_result_obj.license_level_old = driver_race_result['license_level_old'] if (
                    'license_level_old' in driver_race_result
                ) else None
                driver_race_result_obj.license_sub_level_new = driver_race_result['license_sub_level_new'] if (
                    'license_sub_level_new' in driver_race_result
                ) else None
                driver_race_result_obj.license_sub_level_old = driver_race_result['license_sub_level_old'] if (
                    'license_sub_level_old' in driver_race_result
                ) else None
                driver_race_result_obj.incidents = driver_race_result['incidents'] if (
                    'incidents' in driver_race_result
                ) else None
                driver_race_result_obj.laps_complete = driver_race_result['laps_complete'] if (
                    'laps_complete' in driver_race_result
                ) else None
                driver_race_result_obj.laps_led = driver_race_result['laps_led'] if (
                    'laps_led' in driver_race_result
                ) else None
                driver_race_result_obj.champ_points = driver_race_result['champ_points'] if (
                    'champ_points' in driver_race_result
                ) else None

                self.driver_race_results.append(driver_race_result_obj)
        else:
            self.driver_race_results = None

        if 'driver_heat_results' in data_dict:
            self.driver_heat_results = []
            for driver_heat_result in data_dict['driver_heat_results']:
                driver_heat_result_obj = DriverResultSummary()
                driver_heat_result_obj.cust_id = driver_heat_result['cust_id'] if (
                    'cust_id' in driver_heat_result
                ) else None
                driver_heat_result_obj.display_name = driver_heat_result['display_name'] if (
                    'display_name' in driver_heat_result
                ) else None
                driver_heat_result_obj.irating_new = driver_heat_result['irating_new'] if (
                    'irating_new' in driver_heat_result
                ) else None
                driver_heat_result_obj.irating_old = driver_heat_result['irating_old'] if (
                    'irating_old' in driver_heat_result
                ) else None
                driver_heat_result_obj.license_level_new = driver_heat_result['license_level_new'] if (
                    'license_level_new' in driver_heat_result
                ) else None
                driver_heat_result_obj.license_level_old = driver_heat_result['license_level_old'] if (
                    'license_level_old' in driver_heat_result
                ) else None
                driver_heat_result_obj.license_sub_level_new = driver_heat_result['license_sub_level_new'] if (
                    'license_sub_level_new' in driver_heat_result
                ) else None
                driver_heat_result_obj.license_sub_level_old = driver_heat_result['license_sub_level_old'] if (
                    'license_sub_level_old' in driver_heat_result
                ) else None
                driver_heat_result_obj.incidents = driver_heat_result['incidents'] if (
                    'incidents' in driver_heat_result
                ) else None
                driver_heat_result_obj.laps_complete = driver_heat_result['laps_complete'] if (
                    'laps_complete' in driver_heat_result
                ) else None
                driver_heat_result_obj.laps_led = driver_heat_result['laps_led'] if (
                    'laps_led' in driver_heat_result
                ) else None
                driver_heat_result_obj.champ_points = driver_heat_result['champ_points'] if (
                    'champ_points' in driver_heat_result
                ) else None

                self.driver_heat_results.append(driver_heat_result_obj)
        else:
            self.driver_heat_results = None


class DriverResultSummary():
    def __init__(self):
        self.cust_id = None  # DONE
        self.display_name = None  # DONE
        self.irating_new = None  # DONE
        self.irating_old = None  # DONE
        self.license_level_new = None  # DONE
        self.license_level_old = None  # DONE
        self.license_sub_level_new = None  # DONE
        self.license_sub_level_old = None  # DONE
        self.incidents = None  # DONE
        self.laps_complete = None
        self.laps_led = None  # DONE
        self.champ_points = None


async def generate_subsession_summary(bot: discord.Bot, db: BotDatabase, subsession_id: int, car_number: str):

    car_results = CarResultSummary()

    car_results.results_url = (
        f"https://members-ng.iracing.com/racing/results-stats/results?subsessionid={subsession_id}"
    )

    try:
        subsession_data = await db.get_subsession_data(subsession_id)
        subsession_result_dicts = await db.get_subsession_results(subsession_id)

        if subsession_result_dicts is None or len(subsession_result_dicts) < 1:
            # Main event is not a race or no results for some other reason
            logging.getLogger('respobot.bot').warning(
                f"During generate_subsession_summary() no race results were returned by "
                f"db.get_subsession_results() for subsession {subsession_id}."
            )
            return None

        car_results.series_name = subsession_data['series_name']
        car_results.season_id = subsession_data['season_id']
        car_results.league_name = subsession_data['league_name']
        car_results.session_name = subsession_data['session_name']
        car_results.track_name = subsession_data['track_name']
        car_results.track_config_name = subsession_data['track_config_name']
        car_results.track_category_id = subsession_data['track_category_id']
        car_results.license_category_id = subsession_data['license_category_id']
        car_results.event_strength_of_field = subsession_data['event_strength_of_field']
        car_results.max_team_drivers = subsession_data['max_team_drivers']
        car_results.is_multiclass = await db.is_subsession_multiclass(subsession_id)

        driver_race_result_dicts = []
        driver_heat_result_dicts = []
        car_race_result_dict = None
        car_heat_result_dict = None
        is_team_race = False
        is_hosted = False

        fastest_race_lap_time = None
        fastest_race_lap_car_number = None

        fastest_heat_lap_time = None
        fastest_heat_lap_car_number = None

        fastest_qual_lap_time = None
        fastest_qual_lap_car_number = None
        fastest_qual_lap_driver_cust_id = -1

        race_simsession_numbers = []
        event_car_numbers = []

        if (
            subsession_data['private_session_id'] is not None
            and subsession_data['private_session_id'] > 0
        ):
            is_hosted = True

        # Scan results once to get the results for all who drove this car
        # and also find the car number of the car with the fastest lap
        for subsession_result_dict in subsession_result_dicts:
            # Skip any results that are missing a car number
            # This shouldn't ever happen.
            if subsession_result_dict['livery_car_number'] is None:
                logging.getLogger('respobot.bot').warning(
                    f"A result for subsession {subsession_id} is missing a car number."
                )
                continue

            # Keep track of all car numbers in the race
            if subsession_result_dict['livery_car_number'] not in event_car_numbers:
                event_car_numbers.append(subsession_result_dict['livery_car_number'])

            # Keep track of which simsessions are races
            if subsession_result_dict['simsession_type'] == irConstants.SimSessionType.race.value:
                if subsession_result_dict['simsession_number'] not in race_simsession_numbers:
                    race_simsession_numbers.append(subsession_result_dict['simsession_number'])

            if subsession_result_dict['simsession_type'] == irConstants.SimSessionType.race.value:
                if (
                    subsession_result_dict['best_lap_time'] is not None
                    and subsession_result_dict['best_lap_time'] > 0
                    and subsession_result_dict['livery_car_number'] is not None
                ):
                    result_best_lap_time = subsession_result_dict['best_lap_time']
                    if subsession_result_dict['simsession_number'] == 0:
                        if fastest_race_lap_time is None or result_best_lap_time < fastest_race_lap_time:
                            fastest_race_lap_time = result_best_lap_time
                            fastest_race_lap_car_number = subsession_result_dict['livery_car_number']
                    else:
                        if fastest_heat_lap_time is None or result_best_lap_time < fastest_heat_lap_time:
                            fastest_heat_lap_time = result_best_lap_time
                            fastest_heat_lap_car_number = subsession_result_dict['livery_car_number']
            elif (
                subsession_result_dict['simsession_type'] == irConstants.SimSessionType.lone_qualifying.value
                or subsession_result_dict['simsession_type'] == irConstants.SimSessionType.open_qualifying.value
            ):
                if (
                    subsession_result_dict['best_qual_lap_time'] is not None
                    and subsession_result_dict['best_qual_lap_time'] > 0
                    and subsession_result_dict['livery_car_number'] is not None
                ):
                    result_best_qual_lap_time = subsession_result_dict['best_qual_lap_time']
                    if fastest_qual_lap_time is None or result_best_qual_lap_time < fastest_qual_lap_time:
                        fastest_qual_lap_time = result_best_qual_lap_time
                        fastest_qual_lap_car_number = subsession_result_dict['livery_car_number']
                        fastest_qual_lap_driver_cust_id = subsession_result_dict['cust_id']

            if subsession_result_dict['livery_car_number'] != car_number:
                continue

            if subsession_result_dict['simsession_type'] == irConstants.SimSessionType.race.value:
                if subsession_result_dict['simsession_number'] == 0:
                    driver_race_result_dicts.append(subsession_result_dict)
                else:
                    driver_heat_result_dicts.append(subsession_result_dict)

            # If it hasn't been done yet, record the car_class_id for the car number being analysed.
            if (
                car_results.car_class_id is None
                and 'car_class_id' in subsession_result_dict
                and subsession_result_dict['car_class_id'] is not None
            ):
                car_results.car_class_id = subsession_result_dict['car_class_id']
                car_results.car_class_name = subsession_result_dict['car_class_name']
                car_results.car_name = subsession_result_dict['car_name']

        car_results.cars_in_event = len(event_car_numbers)

        if len(race_simsession_numbers) < 1:
            # Not a race
            return None

        # Scan results again to get all the car numbers in the same class
        car_numbers_in_class = []
        for subsession_result_dict in subsession_result_dicts:
            if 'livery_car_number' not in subsession_result_dict:
                continue
            if 'car_class_id' not in subsession_result_dict:
                continue

            if (
                subsession_result_dict['car_class_id'] == car_results.car_class_id
                and subsession_result_dict['livery_car_number'] not in car_numbers_in_class
            ):
                car_numbers_in_class.append(subsession_result_dict['livery_car_number'])

        car_results.cars_in_class = len(car_numbers_in_class)

        # If more than one race result dict was found for this car number then it's a team race
        # Fetch the race result dict for the team
        if len(driver_race_result_dicts) > 1:
            # This was a team race. Find the result dict for the team.
            is_team_race = True
            for member_race_result_dict in driver_race_result_dicts:
                if 'cust_id' in member_race_result_dict and member_race_result_dict['cust_id'] is None:
                    car_race_result_dict = member_race_result_dict
                    break
        elif len(driver_race_result_dicts) > 0:
            car_race_result_dict = driver_race_result_dicts[0]
        else:
            return None

        # If more than one heat result dict was found for this car number then it's a team race
        # Fetch the heat result dict for the team
        if len(driver_heat_result_dicts) > 1:
            for member_heat_result_dict in driver_heat_result_dicts:
                if 'cust_id' in member_heat_result_dict and member_heat_result_dict['cust_id'] is None:
                    car_heat_result_dict = member_heat_result_dict
                    break
        elif len(driver_heat_result_dicts) > 0:
            car_heat_result_dict = driver_heat_result_dicts[0]

        if car_race_result_dict is None:
            logging.getLogger('respobot.bot').warning(
                "During generate_subsession_summary() no car_race_result_dict was found."
            )
            return None

        if fastest_race_lap_car_number == car_number:
            car_results.got_fastest_race_lap = True
            car_results.fastest_race_lap_time = fastest_race_lap_time

        if fastest_heat_lap_car_number == car_number:
            car_results.got_fastest_heat_lap = True
            car_results.fastest_heat_lap_time = fastest_heat_lap_time

        if fastest_qual_lap_car_number == car_number:
            car_results.got_fastest_qual_lap = True
            car_results.fastest_qual_lap_time = fastest_qual_lap_time
            car_results.fastest_qual_lap_driver_cust_id = fastest_qual_lap_driver_cust_id

        car_results.race_starting_position_in_class = car_race_result_dict['starting_position_in_class']
        car_results.race_finish_position_in_class = car_race_result_dict['finish_position_in_class']

        if car_heat_result_dict is not None:
            car_results.heat_starting_position_in_class = car_heat_result_dict['starting_position_in_class']
            car_results.heat_finish_position_in_class = car_heat_result_dict['finish_position_in_class']

        car_results.race_incidents = car_race_result_dict['incidents']
        if car_heat_result_dict is not None:
            car_results.heat_incidents = car_heat_result_dict['incidents']

        if (
            car_race_result_dict['reason_out_id'] == irConstants.ReasonOutIds.disqualified.value
            or car_race_result_dict['reason_out_id'] == irConstants.ReasonOutIds.dq_scoring_invalidated.value
        ):
            car_results.disqualified = True

        if not is_team_race and not is_hosted:
            int_car_numbers_in_class = [int(car_num) for car_num in car_numbers_in_class]
            int_car_numbers_in_class.sort()
            car_number_in_class = int_car_numbers_in_class.index(int(car_number))
            car_results.car_number_in_class = car_number_in_class
            race_finish_position_relative_to_car_num = (
                car_number_in_class - car_race_result_dict['finish_position_in_class']
            )
            car_results.race_finish_position_relative_to_car_num = race_finish_position_relative_to_car_num

            if car_heat_result_dict is not None:
                heat_finish_position_relative_to_car_num = (
                    car_number_in_class - car_heat_result_dict['finish_position_in_class']
                )
                car_results.heat_finish_position_relative_to_car_num = heat_finish_position_relative_to_car_num

        # Get all race laps for this subsession
        race_laps = await db.get_laps(subsession_id, simsession_number=0)

        if race_laps is None:
            logging.getLogger('respobot.bot').warning(
                f"During generate_subsession_summary() no race laps were returned by "
                f"db.get_laps() for simsession_number=0, in subsession {subsession_id}."
            )
            return None

        # We'll keep track of how many people actually drove the car in the race.
        drivers_who_completed_a_lap = []

        invalid_laps = []
        pitted_laps = []
        off_track_laps = []
        black_flag_laps = []
        car_reset_laps = []
        contact_laps = []
        car_contact_laps = []
        lost_control_laps = []
        discontinuity_laps = []
        interpolated_crossing_laps = []
        clock_smash_laps = []
        tow_laps = []
        driver_change_laps = []
        green_flag_lap_num = None
        checkered_flag_lap_num = None
        optional_path_laps = []
        car_laps_led = []
        car_position = [(-1, -1)] * (subsession_data['event_laps_complete'] + 10)
        best_competitor_car_position = [-1] * (subsession_data['event_laps_complete'] + 10)

        team_finish_interval = None
        team_finish_interval_in_ms = False
        checkered_flag_laps = []
        car_reached_checkered = False

        for race_lap in race_laps:
            if race_lap['flags'] & irConstants.IncFlags.checkered.value != 0:
                # Gather all checkered flag lap info for other cars to find close
                # results later
                checkered_flag_laps.append(race_lap)

                if race_lap['car_number'] == car_number:
                    car_reached_checkered = True
                    checkered_flag_lap_num = race_lap['lap_number']
                    car_results.checkered_flag_lap_num = checkered_flag_lap_num
                    team_finish_interval = race_lap['interval']
                    if team_finish_interval is None:
                        # The winner has an interval and interval unit of None. Set it to 0 ms.
                        team_finish_interval = 0
                        team_finish_interval_in_ms = True
                    elif race_lap['interval_units'] == 'ms':
                        team_finish_interval_in_ms = True

            if race_lap['car_number'] == car_number:
                # Keep track of the car's position at every lap
                position_tuple = (race_lap['lap_position'], race_lap['cust_id'])
                car_position[race_lap['lap_number']] = position_tuple

                # Add new cust_ids to the driver list
                if race_lap['cust_id'] not in drivers_who_completed_a_lap:
                    drivers_who_completed_a_lap.append(race_lap['cust_id'])

                # Mark the green flag lap number
                if race_lap['flags'] & irConstants.IncFlags.first_lap.value != 0:
                    green_flag_lap_num = race_lap['lap_number']
                    car_results.green_flag_lap_num = green_flag_lap_num

            elif race_lap['car_number'] in car_numbers_in_class:
                # Keep track of the best in-class competitor position at every lap
                if (
                    race_lap['lap_position'] > 0 and (
                        best_competitor_car_position[race_lap['lap_number']] < 0
                        or race_lap['lap_position'] < best_competitor_car_position[race_lap['lap_number']]
                    )
                ):
                    best_competitor_car_position[race_lap['lap_number']] = race_lap['lap_position']

            # Skip the remaining analysis if this lap is a different car
            if race_lap['car_number'] != car_number:
                continue

            if race_lap['flags'] & irConstants.IncFlags.invalid.value != 0:
                invalid_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.pitted.value != 0:
                pitted_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.off_track.value != 0:
                off_track_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.black_flag.value != 0:
                black_flag_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.car_reset.value != 0:
                car_reset_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.contact.value != 0:
                contact_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.car_contact.value != 0:
                car_contact_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.lost_control.value != 0:
                lost_control_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.discontinuity.value != 0:
                discontinuity_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.interpolated_crossing.value != 0:
                interpolated_crossing_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.clock_smash.value != 0:
                clock_smash_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.tow.value != 0:
                tow_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.driver_change.value != 0:
                driver_change_laps.append(race_lap['lap_number'])
            if race_lap['flags'] & irConstants.IncFlags.optional_path.value != 0:
                optional_path_laps.append(race_lap['lap_number'])

        # Keep track of how many laps each driver led.
        driver_laps_led = {}
        for result_dict in driver_race_result_dicts:
            driver_laps_led[str(result_dict['cust_id'])] = []

        # If the car reached the green flag, scan through laps to find if any were led
        if green_flag_lap_num is not None:
            for i in range(len(car_position)):
                if (
                    car_position[i][0] < best_competitor_car_position[i]
                    and car_position[i][0] >= 0
                    and i >= green_flag_lap_num
                    and (
                        car_reached_checkered and i <= checkered_flag_lap_num
                        or car_position[i][0] > 0
                    )
                ):
                    car_laps_led.append(i)
                    driver_laps_led[str(car_position[i][1])].append(i)

        car_results.laps_led = car_laps_led

        if team_finish_interval_in_ms is True:
            # Car finished on the lead lap. See if it finished close to anyone else
            for checkered_flag_lap in checkered_flag_laps:
                if checkered_flag_lap['car_number'] == car_number:
                    continue

                if checkered_flag_lap['car_number'] not in car_numbers_in_class:
                    continue

                if checkered_flag_lap['interval_units'] != 'ms':
                    continue

                comparison_interval = checkered_flag_lap['interval']

                if comparison_interval is None:
                    # The winner of the race will have an interval/interval_units of None
                    comparison_interval = 0

                interval = comparison_interval - team_finish_interval

                if abs(interval) < constants.CLOSE_FINISH_INTERVAL_MS:
                    if car_results.close_finishers is None:
                        car_results.close_finishers = []
                    car_results.close_finishers.append((checkered_flag_lap['car_number'], interval))
            # Sort the close finishers by interval
            if car_results.close_finishers is not None:
                car_results.close_finishers = sorted(car_results.close_finishers, key=lambda tup: tup[1], reverse=True)
        else:
            if car_reached_checkered is True:
                # Check all other cars in class and if this class finished on the lead lap, then
                # condider reporting on laps down interval.
                for checkered_flag_lap in checkered_flag_laps:
                    if (
                        checkered_flag_lap['car_number'] in car_numbers_in_class
                        and checkered_flag_lap['interval_units'] == 'ms'
                    ):
                        car_results.laps_down = team_finish_interval
                        break
            else:
                if (
                    car_race_result_dict['reason_out_id'] != irConstants.ReasonOutIds.running.value
                    and car_race_result_dict['reason_out_id'] != irConstants.ReasonOutIds.dq_scoring_invalidated.value
                ):
                    car_results.did_not_finish = True

        car_results.black_flag_laps = black_flag_laps
        car_results.tow_laps = tow_laps
        car_results.car_contact_laps = car_contact_laps
        car_results.contact_laps = contact_laps
        car_results.lost_control_laps = lost_control_laps

        # Iterate through all the race/heat results dicts and create DriverResultSumary() objects
        # and attach to the CarResultSummary() object
        for result_dict in driver_race_result_dicts:
            if result_dict['cust_id'] is None or result_dict['cust_id'] < 0:
                continue
            new_result = DriverResultSummary()
            new_result.cust_id = result_dict['cust_id']
            new_result.display_name = result_dict['display_name']
            new_result.irating_new = result_dict['newi_rating']
            new_result.irating_old = result_dict['oldi_rating']
            new_result.license_level_new = result_dict['new_license_level']
            new_result.license_level_old = result_dict['old_license_level']
            new_result.license_sub_level_new = result_dict['new_sub_level']
            new_result.license_sub_level_old = result_dict['old_sub_level']
            new_result.incidents = result_dict['incidents']
            new_result.laps_complete = result_dict['laps_complete']
            new_result.laps_led = driver_laps_led[str(result_dict['cust_id'])]
            new_result.champ_points = result_dict['champ_points']

            if car_results.driver_race_results is None:
                car_results.driver_race_results = []
            car_results.driver_race_results.append(new_result)

        for result_dict in driver_heat_result_dicts:
            if result_dict['cust_id'] is None or result_dict['cust_id'] < 0:
                continue
            new_result = DriverResultSummary()
            new_result.cust_id = result_dict['cust_id']
            new_result.display_name = result_dict['display_name']
            new_result.irating_new = result_dict['newi_rating']
            new_result.irating_change = result_dict['oldi_rating']
            new_result.license_level_new = result_dict['new_license_level']
            new_result.license_level_old = result_dict['old_license_level']
            new_result.license_sub_level_new = result_dict['new_sub_level']
            new_result.license_sub_level_old = result_dict['old_sub_level']
            new_result.incidents = result_dict['incidents']
            new_result.laps_complete = result_dict['laps_complete']
            new_result.laps_led = driver_laps_led[str(result_dict['cust_id'])]
            new_result.champ_points = result_dict['champ_points']

            if car_results.driver_heat_results is None:
                car_results.driver_heat_results = []
            car_results.driver_heat_results.append(new_result)

        # Calculate the SoF as the average based on each individual team's average IR.
        class_sof_data = await db.get_subsession_drivers_old_irs(
            subsession_data['subsession_id'],
            car_class_id=car_results.car_class_id
        )
        sof_dict = {}
        for driver_tuple in class_sof_data:
            car_num = driver_tuple[1]
            ir = driver_tuple[2]

            if car_num not in sof_dict:
                sof_dict[car_num] = [ir]
            else:
                sof_dict[car_num].append(ir)

        total_teams_in_class = len(sof_dict)
        total_exponents = 0
        for car_num in sof_dict:
            total_team_exponents = 0
            for irating in sof_dict[car_num]:
                car_exponent = math.exp(-1 * irating / (1600 / math.log(2)))
                total_team_exponents += car_exponent
            team_sof = (1600 / math.log(2)) * math.log(len(sof_dict[car_num]) / total_team_exponents)
            team_exponent = math.exp(-1 * team_sof / (1600 / math.log(2)))
            total_exponents += team_exponent
        class_sof = (1600 / math.log(2)) * math.log(total_teams_in_class / total_exponents)

        car_results.class_strength_of_field = int(class_sof)

    except BotDatabaseError as exc:
        exception_string = (
            f"The error '{exc}' occurred with code {exc.error_code} during generate_subsession_summary() "
            f"for subsession {subsession_id} and car_number {car_number}."
        )
        logging.getLogger('respobot.database').error(exception_string)
        await helpers.send_bot_failure_dm(bot, exception_string)
    except KeyError as exc:
        exception_lines = traceback.format_exception(exc)
        exception_string = ""
        for line in exception_lines:
            exception_string += line

        logging.getLogger('respobot.bot').error(exception_string)
        await helpers.send_bot_failure_dm(bot, exception_string)

    return car_results

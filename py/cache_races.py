import global_vars
import asyncio
from pyracing import constants as pyracingConstants


async def cache_races(iracing_id):
    if str(iracing_id) not in global_vars.race_cache:
        while global_vars.race_cache_locks > 0:
            asyncio.sleep(1)
        global_vars.race_cache[str(iracing_id)] = {}

    first_year = 3000
    yearly_stats_list = await global_vars.ir.yearly_stats(iracing_id)
    for year_stats in yearly_stats_list:
        if int(year_stats.year) < first_year:
            first_year = int(year_stats.year)

    print("Caching races for " + str(iracing_id) + " back to " + str(first_year))

    year = global_vars.series_info['misc']['current_year']
    quarter = global_vars.series_info['misc']['current_quarter']

    global_vars.members_locks += 1
    for member in global_vars.members:
        if global_vars.members[member]['iracingCustID'] == iracing_id:
            global_vars.members[member]['last_race_check'] = 0
            break
    global_vars.members_locks -= 1

    while year >= first_year:
        races = await global_vars.ir.search_results(iracing_id, quarter=quarter, year=year)
        if len(races) > 0:
            if str(year) not in global_vars.race_cache[str(iracing_id)]:
                while global_vars.race_cache_locks > 0:
                    asyncio.sleep(1)
                global_vars.race_cache[str(iracing_id)][str(year)] = {}
            if str(quarter) not in global_vars.race_cache[str(iracing_id)][str(year)]:
                while global_vars.race_cache_locks > 0:
                    asyncio.sleep(1)
                global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)] = {}

        for race in races:
            if str(race.series_id) not in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)]:
                while global_vars.race_cache_locks > 0:
                    asyncio.sleep(1)
                global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(race.series_id)] = {}

            subsession = await global_vars.ir.subsession_data(race.subsession_id)
            driver_found = False

            # Need to do a preliminary scan because you can have a race in your results where you never drove a lap. Team races?
            for driver in subsession.drivers:
                if driver.cust_id == race.cust_id and driver.sim_ses_type_name == "Race":
                    driver_found = True

            if driver_found:
                while global_vars.race_cache_locks > 0:
                    asyncio.sleep(1)

                global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(race.series_id)][str(race.subsession_id)] = {}
                new_race_dict = global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(race.series_id)][str(race.subsession_id)]
                new_race_dict["official"] = race.official_session
                new_race_dict['time_start_raw'] = race.time_start_raw
                new_race_dict["category"] = race.category_id
                new_race_dict["points_champ"] = race.points_champ
                new_race_dict["race_week"] = race.race_week
                new_race_dict["car_class_id"] = race.car_class_id
                new_race_dict["pos_start_class"] = race.pos_start_class
                new_race_dict["pos_finish_class"] = race.pos_finish_class

                if subsession.team_drivers_max > 1:
                    team_event = True
                else:
                    team_event = False

                class_count = 0

                # Prelim scan drivers to get class count
                for driver in subsession.drivers:
                    if driver.car_class_id == race.car_class_id and driver.sim_ses_type_name == 'Race':
                        if team_event is True:
                            if driver.cust_id < 0:  # Teams have a negative customer ID, so count the teams
                                class_count += 1
                        else:
                            class_count += 1  # If not a team event, count every driver in the race

                for driver in subsession.drivers:
                    if driver.cust_id == race.cust_id and driver.sim_ses_type_name == "Race":
                        new_race_dict['incidents'] = driver.incidents
                        new_race_dict['laps'] = driver.laps_comp
                        new_race_dict['laps_led'] = driver.laps_led
                        new_race_dict['irating_old'] = driver.irating_old
                        new_race_dict['irating_new'] = driver.irating_new
                        new_race_dict['drivers_in_class'] = class_count
                        new_race_dict['team_drivers_max'] = subsession.team_drivers_max

                        if 'last_race_check' not in global_vars.members[member]:
                            global_vars.members[member]['last_race_check'] = 0

                        if race.category_id == pyracingConstants.Category.road.value and race.time_start_raw > global_vars.members[member]['last_race_check']:
                            print('New road race ' + str(race.subsession_id) + ' at: ' + str(race.time_start_raw) + ' which is newer than: ' + str(global_vars.members[member]['last_race_check']))
                            global_vars.members[member]['last_race_check'] = race.time_start_raw

                            if race.official_session == 1:
                                global_vars.members[member]['last_known_ir'] = driver.irating_new
                                print("New road ir is: " + str(driver.irating_new))

        print("Driver: " + str(iracing_id) + "  Year: " + str(year) + "  Season: " + str(quarter) + "  Races found: " + str(len(races)))

        quarter -= 1
        if quarter <= 0:
            quarter = 4
            year -= 1

    global_vars.dump_json()

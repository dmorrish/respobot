import global_vars
import math


# Pass in -1 for the series ID to get the current week based on Rookie Mazda
async def get_current_iracing_week(series_id):
    seasons = await global_vars.ir.current_seasons(only_active=True)

    for season in seasons:
        if season.series_id == series_id or series_id < 0 and season.series_id == 139:
            return season.race_week

    return -1


async def populate_head2head_stats(iracing_id, year=None, quarter=None, category=None, series=None, car_class=None):

    stats_dict = {
        'total_races': 0,
        'wins': 0,
        'podiums': 0,
        'total_champ_points': 0,
        'highest_champ_points': 0,
        'total_incidents': 0,
        'total_laps': 0,
        'total_poles': 0,
        'total_laps_led': 0,
        'top_half': 0,
        'highest_ir_gain': 0,
        'highest_ir_loss': 0,
        'total_ir_change': 0,
        'highest_ir': -1,
        'lowest_ir': -1
    }

    global_vars.race_cache_locks += 1
    if str(iracing_id) in global_vars.race_cache:
        for year_key in global_vars.race_cache[str(iracing_id)]:
            if year_key == str(year) or year is None:
                for quarter_key in global_vars.race_cache[str(iracing_id)][year_key]:
                    if quarter_key == str(quarter) or quarter is None:
                        for series_key in global_vars.race_cache[str(iracing_id)][year_key][quarter_key]:
                            if series_key == str(series) or series is None:
                                for subsession_key in global_vars.race_cache[str(iracing_id)][year_key][quarter_key][series_key]:
                                    if category is None or ('category' in global_vars.race_cache[str(iracing_id)][year_key][quarter_key][series_key][subsession_key] and global_vars.race_cache[str(iracing_id)][year_key][quarter_key][series_key][subsession_key]['category'] == category):
                                        race = global_vars.race_cache[str(iracing_id)][year_key][quarter_key][series_key][subsession_key]
                                        if 'official' in race and race['official'] == 1:
                                            stats_dict['total_races'] += 1
                                            stats_dict['total_champ_points'] += race['points_champ']

                                            if race['points_champ'] > stats_dict['highest_champ_points']:
                                                stats_dict['highest_champ_points'] = race['points_champ']

                                            if race['pos_finish_class'] == 1:
                                                stats_dict['wins'] += 1
                                            if 1 <= race['pos_finish_class'] <= 3:
                                                stats_dict['podiums'] += 1

                                            if race['pos_start_class'] == 1:
                                                stats_dict['total_poles'] += 1

                                            stats_dict['total_incidents'] += race['incidents']
                                            stats_dict['total_laps'] += race['laps']
                                            stats_dict['total_laps_led'] += race['laps_led']

                                            irating_change = race['irating_new'] - race['irating_old']
                                            stats_dict['total_ir_change'] += irating_change

                                            if irating_change > stats_dict['highest_ir_gain']:
                                                stats_dict['highest_ir_gain'] = irating_change

                                            if irating_change < stats_dict['highest_ir_loss']:
                                                stats_dict['highest_ir_loss'] = irating_change

                                            if race['pos_finish_class'] <= int(math.ceil(race['drivers_in_class'] / 2)):
                                                stats_dict['top_half'] += 1

                                            if race['irating_new'] > stats_dict['highest_ir'] or stats_dict['highest_ir'] < 0:
                                                stats_dict['highest_ir'] = race['irating_new']

                                            if race['irating_new'] < stats_dict['lowest_ir'] and race['irating_new'] > 0 or stats_dict['lowest_ir'] < 0:
                                                stats_dict['lowest_ir'] = race['irating_new']

    global_vars.race_cache_locks -= 1

    if stats_dict['total_champ_points'] > 0:
        stats_dict['avg_champ_points'] = stats_dict['total_champ_points'] / stats_dict['total_races']
    else:
        stats_dict['avg_champ_points'] = 0
    if stats_dict['total_incidents'] > 0:
        stats_dict['laps_per_inc'] = stats_dict['total_laps'] / stats_dict['total_incidents']
    else:
        stats_dict['laps_per_inc'] = math.inf

    return stats_dict


def get_respo_champ_points(year, quarter, up_to_week):

    leaderboard_best_weeks = {}
    series_list = []
    series_leaderboards = {}
    # Make a list of all series Respo members ran
    global_vars.race_cache_locks += 1
    for member in global_vars.race_cache:
        if str(year) in global_vars.race_cache[member]:
            if str(quarter) in global_vars.race_cache[member][str(year)]:
                for series in global_vars.race_cache[member][str(year)][str(quarter)]:
                    series_list.append(int(series))
            # NEC hard coding bullshit
            if quarter != 2 and "2" in global_vars.race_cache[member][str(year)]:
                if "275" in global_vars.race_cache[member][str(year)]["2"]:
                    series_list.append(275)
    global_vars.race_cache_locks -= 1

    # Generate weekly points breakdown for each series
    for series in series_list:
        series_leaderboards[series] = get_champ_points(series, -1, year, quarter, up_to_week)

    if len(series_list) < 1:
        return leaderboard_best_weeks

    for member in series_leaderboards[series]:
        # leaderboard_best_weeks[member] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        leaderboard_best_weeks[member] = {'weeks': {}}

    # Iterate through week by week and pick each member's best series for that week
    for series in series_leaderboards:
        for member in series_leaderboards[series]:
            for week_key in series_leaderboards[series][member]['weeks']:
                if week_key in leaderboard_best_weeks[member]['weeks']:
                    if series_leaderboards[series][member]['weeks'][week_key] > leaderboard_best_weeks[member]['weeks'][week_key]:
                        leaderboard_best_weeks[member]['weeks'][week_key] = series_leaderboards[series][member]['weeks'][week_key]
                else:
                    leaderboard_best_weeks[member]['weeks'][week_key] = series_leaderboards[series][member]['weeks'][week_key]

    return leaderboard_best_weeks


def get_ir_data_from_cache(iracing_id, category):
    ir_dict = []
    iracing_id = str(iracing_id)
    if iracing_id in global_vars.race_cache:
        global_vars.race_cache_locks += 1
        for year in global_vars.race_cache[iracing_id]:
            for quarter in global_vars.race_cache[iracing_id][year]:
                for series in global_vars.race_cache[iracing_id][year][quarter]:
                    for subsession in global_vars.race_cache[iracing_id][year][quarter][series]:
                        race = global_vars.race_cache[iracing_id][year][quarter][series][subsession]
                        if race['category'] == category and race['irating_new'] > 0:
                            ir_dict.append((race['time_start_raw'], race['irating_new']))
        global_vars.race_cache_locks -= 1

    ir_dict.sort(key=lambda tup: tup[0])

    return ir_dict


def calc_total_champ_points(leaderboard_dict, weeks_to_count):

    for member in leaderboard_dict:
        leaderboard_dict[member]['weeks'] = dict(sorted(leaderboard_dict[member]['weeks'].items(), key=lambda item: item[0], reverse=False))
        leaderboard_dict[member]['weeks'] = dict(sorted(leaderboard_dict[member]['weeks'].items(), key=lambda item: item[1], reverse=True))

        total_points = 0
        weeks_counted = 0
        for week in leaderboard_dict[member]['weeks']:
            total_points += leaderboard_dict[member]['weeks'][week]
            weeks_counted += 1

            if weeks_counted >= weeks_to_count:
                break

        leaderboard_dict[member]['total_points'] = total_points


def calc_projected_champ_points(leaderboard_dict, max_week, weeks_to_count, active_season):
    for member in leaderboard_dict:
        leaderboard_dict[member]['weeks'] = dict(sorted(leaderboard_dict[member]['weeks'].items(), key=lambda item: item[0], reverse=False))
        leaderboard_dict[member]['weeks'] = dict(sorted(leaderboard_dict[member]['weeks'].items(), key=lambda item: item[1], reverse=True))

        num_weeks_raced = len(leaderboard_dict[member]['weeks'])
        projected_weeks_raced = num_weeks_raced / max_week * 12
        if projected_weeks_raced > 0:
            inclusion_rate = 6 / projected_weeks_raced
        else:
            inclusion_rate = 1
        projected_points = 0

        weeks_to_project = math.ceil(num_weeks_raced * inclusion_rate)

        # If they haven't raced in the current week in an active series
        if active_season:
            if str(max_week) not in leaderboard_dict[member]["weeks"]:
                if weeks_to_project >= weeks_to_count:
                    weeks_to_project -= 1

        weeks_counted = 0
        for week in leaderboard_dict[member]['weeks']:
            projected_points += leaderboard_dict[member]['weeks'][week]
            weeks_counted += 1
            if weeks_counted >= weeks_to_project:
                break
        if weeks_to_project > 0:
            leaderboard_dict[member]['projected_points'] = int(projected_points / weeks_to_project * weeks_to_count)
        else:
            leaderboard_dict[member]['projected_points'] = 0


def get_champ_points(series_id, car_class_id, year, quarter, up_to_week):
    leaderboard = {}

    # Hard coding bullshit to handle NEC
    actual_quarter = -1

    if series_id == 275:
        actual_quarter = quarter
        quarter = 2

    global_vars.members_locks += 1
    for member in global_vars.members:
        iracing_id = global_vars.members[member]["iracingCustID"]
        points = {}
        for i in range(0, 12):
            points[str(i)] = []

        if str(iracing_id) in global_vars.race_cache:
            if str(year) in global_vars.race_cache[str(iracing_id)]:
                if str(quarter) in global_vars.race_cache[str(iracing_id)][str(year)]:
                    if str(series_id) in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)]:
                        global_vars.race_cache_locks += 1
                        for race in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)]:
                            if car_class_id < 0 or 'car_class_id' in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]:
                                if car_class_id < 0 or global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]['car_class_id'] == car_class_id:
                                    if 'race_week' in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]:
                                        if global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]["race_week"] <= up_to_week:
                                            if 'points_champ' in global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]:
                                                race_week = global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]["race_week"]

                                                # Adjust for IMSA Endurance being on week 1, 3, 5, 7, 9, and 11
                                                # and ESS being on week 2, 4, 6, 8, 10, and 12
                                                if series_id == 419:
                                                    race_week *= 2
                                                elif series_id == 331:
                                                    race_week = race_week * 2 + 1

                                                if global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]["points_champ"] > 0:
                                                    # More NEC bullshit
                                                    use_race = False
                                                    if series_id == 275:
                                                        nec_week = race_week
                                                        if actual_quarter == 2:
                                                            if nec_week == 0:
                                                                race_week = 5
                                                                use_race = True
                                                            elif nec_week == 1:
                                                                race_week = 7
                                                                use_race = True
                                                            elif nec_week == 2:
                                                                race_week = 10
                                                                use_race = True
                                                        elif actual_quarter == 3:
                                                            if nec_week == 3:
                                                                race_week = 2
                                                                use_race = True
                                                            elif nec_week == 4:
                                                                race_week = 4
                                                                use_race = True
                                                            elif nec_week == 5:
                                                                race_week = 7
                                                                use_race = True
                                                            elif nec_week == 6:
                                                                race_week = 11
                                                                use_race = True
                                                        elif actual_quarter == 3:
                                                            if nec_week == 7:
                                                                race_week = 1
                                                                use_race = True
                                                            elif nec_week == 8:
                                                                race_week = 4
                                                                use_race = True

                                                        if use_race is True:
                                                            points[str(race_week)].append(global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]["points_champ"])
                                                    else:
                                                        points[str(race_week)].append(global_vars.race_cache[str(iracing_id)][str(year)][str(quarter)][str(series_id)][race]["points_champ"])
                                                else:
                                                    if race_week < 12:
                                                        points[str(race_week)].append(0)
                        global_vars.race_cache_locks -= 1

        # weekly_points = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        weekly_points = {}
        for week in points:
            num_to_grab = math.ceil(len(points[week]) / 4)
            points[week].sort(reverse=True)
            if points[week]:
                points[week] = points[week][0:num_to_grab]
                weekly_points[week] = int(sum(points[week]) / num_to_grab)
        leaderboard[global_vars.members[member]['leaderboardName']] = {'weeks': weekly_points}

    global_vars.members_locks -= 1
    return leaderboard

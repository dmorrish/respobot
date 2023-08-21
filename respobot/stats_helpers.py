import math
from datetime import datetime
from bot_database import BotDatabase


async def populate_head2head_stats(db: BotDatabase, iracing_custid, year=None, quarter=None, category=None, series=None, car_class=None):

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

    race_dicts = await db.get_member_race_results(iracing_custid, series_id=series, car_class_id=car_class, season_year=year, season_quarter=quarter, license_category_id=category, official_session=1, simsession_type=6)

    for race_dict in race_dicts:
        stats_dict['total_races'] += 1
        stats_dict['total_champ_points'] += race_dict['champ_points']

        if race_dict['champ_points'] > stats_dict['highest_champ_points']:
            stats_dict['highest_champ_points'] = race_dict['champ_points']

        if race_dict['finish_position_in_class'] == 0:
            stats_dict['wins'] += 1
        if 0 <= race_dict['finish_position_in_class'] <= 2:
            stats_dict['podiums'] += 1

        if race_dict['starting_position_in_class'] == 0:
            stats_dict['total_poles'] += 1

        stats_dict['total_incidents'] += race_dict['incidents']
        stats_dict['total_laps'] += race_dict['laps_complete']
        stats_dict['total_laps_led'] += race_dict['laps_led']

        irating_change = race_dict['newi_rating'] - race_dict['oldi_rating']
        stats_dict['total_ir_change'] += irating_change

        if irating_change > stats_dict['highest_ir_gain']:
            stats_dict['highest_ir_gain'] = irating_change

        if irating_change < stats_dict['highest_ir_loss']:
            stats_dict['highest_ir_loss'] = irating_change

        drivers_in_class = await db.get_drivers_in_class(race_dict['subsession_id'], race_dict['car_class_id'], simsession_type=6)

        if race_dict['finish_position_in_class'] <= int(math.ceil(drivers_in_class / 2)):
            stats_dict['top_half'] += 1

        if race_dict['newi_rating'] > stats_dict['highest_ir'] or stats_dict['highest_ir'] < 0:
            stats_dict['highest_ir'] = race_dict['newi_rating']

        if race_dict['newi_rating'] < stats_dict['lowest_ir'] and race_dict['newi_rating'] > 0 or stats_dict['lowest_ir'] < 0:
            stats_dict['lowest_ir'] = race_dict['newi_rating']

    if stats_dict['total_champ_points'] > 0:
        stats_dict['avg_champ_points'] = stats_dict['total_champ_points'] / stats_dict['total_races']
    else:
        stats_dict['avg_champ_points'] = 0
    if stats_dict['total_incidents'] > 0:
        stats_dict['laps_per_inc'] = stats_dict['total_laps'] / stats_dict['total_incidents']
    else:
        stats_dict['laps_per_inc'] = math.inf

    return stats_dict


##################
# TODO: VALIDATE #
##################
async def get_respo_race_week(db: BotDatabase, time_start: str):
    start_datetime = datetime.fromisoformat(time_start)
    season_year = -1
    season_quarter = -1
    race_week = -1
    season_found = False

    season_date_tuples = await db.get_season_dates()

    if season_date_tuples is None or len(season_date_tuples) < 1:
        return None

    for season_date_tuple in season_date_tuples:
        (_, season_year, season_quarter, str_start_time, str_end_time) = season_date_tuple
        season_start = datetime.fromisoformat(str_start_time)
        season_end = datetime.fromisoformat(str_end_time)

        if start_datetime >= season_start and start_datetime < season_end:
            time_diff = (start_datetime - season_start).total_seconds()
            race_week = int(time_diff / (7 * 24 * 60 * 60))
            season_found = True
            break

    if season_found:
        return (season_year, season_quarter, race_week)
    else:
        return (None, None, None)


async def get_number_of_race_weeks(db: BotDatabase, time_start: str):
    start_datetime = datetime.fromisoformat(time_start)
    season_year = -1
    season_quarter = -1
    race_weeks = -1
    season_found = False

    season_date_tuples = await db.get_season_dates()

    if season_date_tuples is None or len(season_date_tuples) < 1:
        return None

    for season_date_tuple in season_date_tuples:
        (_, season_year, season_quarter, str_start_time, str_end_time) = season_date_tuple
        season_start = datetime.fromisoformat(str_start_time)
        season_end = datetime.fromisoformat(str_end_time)

        if start_datetime >= season_start:
            time_diff = (season_end - season_start).total_seconds()
            race_weeks = int(time_diff / (7 * 24 * 60 * 60))
            season_found = True
            break

    if season_found:
        return race_weeks
    else:
        return None


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


async def get_member_weekly_points_dict(db: BotDatabase, iracing_custid, series_id, car_class_id, season_year, season_quarter, up_to_week, adjust_race_weeks, subsession_to_ignore: int = None):
    points = {}
    for i in range(0, 12):
        points[str(i)] = []

    race_dicts = await db.get_member_race_results(iracing_custid, series_id=series_id, car_class_id=car_class_id, season_year=season_year, season_quarter=season_quarter, official_session=1, simsession_type=6)

    for race_dict in race_dicts:
        if subsession_to_ignore is not None and race_dict['subsession_id'] == subsession_to_ignore:
            continue
        race_week = None
        if adjust_race_weeks and 'start_time' in race_dict:
            (adjusted_season_year, adjusted_season_quarter, adjusted_race_week) = await get_respo_race_week(db, race_dict['start_time'])

            if adjusted_race_week is not None and adjusted_season_year == season_year and adjusted_season_quarter == season_quarter:
                race_week = adjusted_race_week
        elif 'race_week_num' in race_dict:
            race_week = race_dict['race_week_num']

        if race_week is None:
            continue

        if race_week <= up_to_week:
            if 'champ_points' in race_dict and 'official_session' in race_dict and race_dict['official_session'] == 1:
                points[str(race_week)].append(race_dict['champ_points'])

    weekly_points = {}
    for week in points:
        num_to_grab = math.ceil(len(points[week]) / 4)
        points[week].sort(reverse=True)
        if points[week]:
            points[week] = points[week][0:num_to_grab]
            weekly_points[week] = int(sum(points[week]) / num_to_grab)

    return weekly_points


async def get_champ_points(db: BotDatabase, member_dicts, series_id, car_class_id, season_year, season_quarter, up_to_week):
    leaderboard = {}

    for member_dict in member_dicts:
        weekly_points = await get_member_weekly_points_dict(db, member_dict['iracing_custid'], series_id, car_class_id, season_year, season_quarter, up_to_week, False)
        leaderboard[member_dict['name']] = {'weeks': weekly_points}

    return leaderboard


async def get_respo_champ_points(db: BotDatabase, member_dicts, season_year, season_quarter, up_to_week, subsession_to_ignore: int = None):
    leaderboard = {}

    for member_dict in member_dicts:
        weekly_points_best = {}
        series_list = await db.get_member_series_raced(member_dict['iracing_custid'], season_year=season_year, season_quarter=season_quarter, official_session=1, simsession_type=6)

        for series_id in series_list:
            weekly_points = await get_member_weekly_points_dict(db, member_dict['iracing_custid'], series_id, None, season_year, season_quarter, up_to_week, True, subsession_to_ignore=subsession_to_ignore)

            if weekly_points is None or len(weekly_points) < 1:
                continue

            for week in weekly_points:
                if week not in weekly_points_best or weekly_points[week] > weekly_points_best[week]:
                    weekly_points_best[week] = weekly_points[week]
        leaderboard[member_dict['name']] = {'weeks': weekly_points_best}

    return leaderboard

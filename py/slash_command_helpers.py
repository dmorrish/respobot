import discord
import constants
from bot_database import BotDatabase

db = None


def init(db_: BotDatabase):
    global db
    db = db_


async def get_member_list(ctx: discord.AutocompleteContext):
    global db
    member_name_list = []

    member_dicts = await db.fetch_member_dicts()

    if member_dicts is None or len(member_dicts) < 1:
        return []

    for member_dict in member_dicts:
        member_name_list.append(member_dict['name'].split()[0])

    member_name_list.sort()

    return [member_string for member_string in member_name_list if member_string.lower().startswith(ctx.value.lower())]


async def get_iracing_seasons(ctx: discord.AutocompleteContext):
    global db
    season_list = []
    (year, quarter, _, _, _) = await db.get_current_iracing_week()

    if year is None or quarter is None:
        return []

    while year > 2007:
        season_string = str(year) + 's' + str(quarter)
        season_list.append(season_string)

        quarter -= 1

        if quarter < 1:
            quarter = 4
            year -= 1

    return [season for season in season_list if season.startswith(ctx.value.lower())]


async def get_series_list(ctx: discord.AutocompleteContext):
    global db
    series_list = []
    series_keyword_list = []

    if 'season' in ctx.options:
        season_selected = ctx.options['season']
    else:
        season_selected = None

    if season_selected is None or season_selected == '':
        if ctx.command.name == 'champ':
            return ["Please select a season first."]
        else:
            (season_year, season_quarter, _, _, _) = await db.get_current_iracing_week()
            if season_year is None or season_quarter is None:
                return []
    else:
        season_year, season_quarter = parse_season_string(season_selected)

    series_tuples = await db.get_season_basic_info(season_year=season_year, season_quarter=season_quarter)

    if series_tuples is None or len(series_tuples) < 1:
        return []

    for series_tuple in series_tuples:
        series_keyword_list.append(series_tuple[1])

    series_keyword_list.sort()

    if ctx.command.name == 'champ':
        series_keyword_list = [constants.respo_series_name] + series_keyword_list

    return [series for series in series_keyword_list if (series.lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]


async def get_series_classes(ctx: discord.AutocompleteContext):
    if 'season' in ctx.options:
        season_selected = ctx.options['season']
    else:
        season_selected = None

    if 'series' in ctx.options:
        series_selected = ctx.options['series']
    else:
        series_selected = None

    if season_selected is None or season_selected == '' or series_selected is None or series_selected == '':
        return ["Please slect a season and series first."]

    season_year, season_quarter = parse_season_string(season_selected)

    if season_year is None or season_quarter is None:
        return ["Please select a season and series first."]

    if series_selected == constants.respo_series_name:
        return ["Literally any fucking car at all."]

    series_id = await db.get_series_id_from_season_name(series_selected, season_year=season_year, season_quarter=season_quarter)
    season_id = await db.get_season_id(series_id, season_year, season_quarter)

    class_tuples = await db.get_season_car_classes(season_id=season_id)

    if class_tuples is None or len(class_tuples) < 1:
        return []

    return [class_tuple[1] for class_tuple in class_tuples if (class_tuple[1].lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]


async def get_quote_ids(ctx: discord.AutocompleteContext):
    global db
    quote_ids = await db.get_quote_ids()
    return [str(x) for x in quote_ids if (str(x).lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]


def parse_season_string(season_string):
    tmp = season_string[0:4]
    if tmp.isnumeric():
        year = int(tmp)
    else:
        return None, None

    tmp = season_string[-1]
    if tmp.isnumeric():
        quarter = int(tmp)
    else:
        return None, None

    return year, quarter

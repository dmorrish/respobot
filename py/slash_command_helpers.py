import discord
import global_vars


async def get_member_list(ctx: discord.AutocompleteContext):
    member_name_list = []
    global_vars.members_locks += 1
    for member in global_vars.members:
        member_name_list.append(global_vars.members[member]['leaderboardName'].split()[0])
    global_vars.members_locks -= 1
    member_name_list.sort()

    return [member_string for member_string in member_name_list if member_string.lower().startswith(ctx.value.lower())]


async def get_iracing_seasons(ctx: discord.AutocompleteContext):
    season_list = []
    year = global_vars.series_info['misc']['current_year']
    quarter = global_vars.series_info['misc']['current_quarter']

    while year > 2007:
        season_string = str(year) + 's' + str(quarter)
        season_list.append(season_string)

        quarter -= 1

        if quarter < 1:
            quarter = 4
            year -= 1

    return [season for season in season_list if season.startswith(ctx.value.lower())]


async def get_series_list(ctx: discord.AutocompleteContext):
    series_list = []
    series_keyword_list = []

    if ctx.command.name == 'champ':
        series_list.append('respo')

    for series_key in global_vars.series_info:
        if 'keywords' in global_vars.series_info[series_key]:
            for keyword in global_vars.series_info[series_key]['keywords']:
                series_keyword_list.append(keyword)
    series_keyword_list.sort()

    series_list.extend(series_keyword_list)

    return [series for series in series_list if series.startswith(ctx.value.lower())]


async def get_series_classes(ctx: discord.AutocompleteContext):
    class_list = []
    series_selected = ctx.options["series"]

    for series_key in global_vars.series_info:
        if 'keywords' in global_vars.series_info[series_key] and series_selected in global_vars.series_info[series_key]['keywords']:
            if 'classes' in global_vars.series_info[series_key]:
                for class_key in global_vars.series_info[series_key]['classes']:
                    for class_keyword in global_vars.series_info[series_key]['classes'][class_key]:
                        class_list.append(class_keyword)

    return [class_keyword for class_keyword in class_list if class_keyword.startswith(ctx.value.lower())]


def parse_season_string(season_string):
    tmp = season_string[0:4]
    if tmp.isnumeric():
        year = int(tmp)
    else:
        return -1, -1

    tmp = season_string[-1]
    if tmp.isnumeric():
        quarter = int(tmp)
    else:
        return -1, -1

    return year, quarter


def get_member_dict_from_first_name(member_name_from_list):
    global_vars.members_locks += 1
    for member_key in global_vars.members:
        if "leaderboardName" in global_vars.members[member_key]:
            name_split = global_vars.members[member_key]["leaderboardName"].split()
            if len(name_split) > 0 and name_split[0].lower() == member_name_from_list.lower():
                global_vars.members_locks -= 1
                return global_vars.members[member_key]

    global_vars.members_locks -= 1

    return {}


def get_member_key(member_name_from_list):
    global_vars.members_locks += 1
    for member_key in global_vars.members:
        if "leaderboardName" in global_vars.members[member_key]:
            name_split = global_vars.members[member_key]["leaderboardName"].split()
            if len(name_split) > 0 and name_split[0].lower() == member_name_from_list.lower():
                global_vars.members_locks -= 1
                return member_key

    global_vars.members_locks -= 1

    return ""


# async def get_member_dict(member: str):
#     member_dict = {}

#     if not member.isnumeric():
#         if len(member.split()) == 1:
#             member_name_list = []
#             for tmp_member in global_vars.members:
#                 member_name_list.append(global_vars.members[tmp_member]['leaderboardName'].split()[0])

#             if member in member_name_list:
#                 member_dict = get_member_dict_from_first_name(member)
#                 if member_dict:
#                     return member_dict
#             else:
#                 return {}

#         driver_name = ""
#         if (member[0] == '"' or member[0] == "“") and (member[-1] == '"' or member[-1] == '”'):
#             # Adding by quoted name.
#             driver_name = member[1:-1]
#         else:
#             # Adding by unquoted name
#             driver_name = member

#         driver_list = await global_vars.ir.driver_stats(search=driver_name)  # This returns a list of drivers, but we only want exact matches.
#         driver_found = False
#         for driver in driver_list:
#             if driver.display_name.lower() == driver_name.lower():
#                 member_dict['leaderboardName'] = driver.display_name
#                 member_dict['iracingCustID'] = driver.cust_id
#                 return member_dict
#         if not driver_found:
#             return {}
#     else:
#         iracing_id = int(member)
#         races_list = await global_vars.ir.last_races_stats(iracing_id)
#         if len(races_list) < 1:
#             return {}

#         subsession = await global_vars.ir.subsession_data(races_list[0].subsession_id)
#         for driver in subsession.drivers:
#             if driver.cust_id == int(member):
#                 member_dict['leaderboardName'] = driver.display_name
#                 member_dict['iracingCustID'] = driver.cust_id
#                 return member_dict

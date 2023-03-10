# discord imports
import discord
from discord.ext import commands
from discord.commands import Option

# import all RespoBot modules
import slash_command_helpers as slash_helpers
import stats_helpers as stats
import environment_variables as env
import image_generators as image_gen
import global_vars

# other imports
import os
import random
import math
from datetime import datetime


class ChampCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='champ',
        description="Show the championship points for a series (or the Respo 'race whatever the fuck' series)."
    )
    async def champ(
        self,
        ctx,
        series: Option(str, "Select a series", required=True, autocomplete=slash_helpers.get_series_list),
        car: Option(str, "Select a car class", required=False, autocomplete=slash_helpers.get_series_classes),
        season: Option(str, "Select a season", required=False, autocomplete=slash_helpers.get_iracing_seasons)
    ):
        await ctx.respond("Working on it...")

        season_name = ""
        year = -1
        quarter = -1
        last_run_year = -1
        last_run_quarter = -1
        series_id = -1
        car_class_id = -1

        if series == "respo":
            season_name = "Respo Racing Whatever the Fuck You Want Series"
            last_run_year = global_vars.series_info['misc']['current_year']
            last_run_quarter = global_vars.series_info['misc']['current_quarter']
        else:
            for series_key in global_vars.series_info:
                if 'keywords' in global_vars.series_info[series_key] and series in global_vars.series_info[series_key]['keywords']:
                    series_id = int(series_key)
                    last_run_year = global_vars.series_info[series_key]['last_run_year']
                    last_run_quarter = global_vars.series_info[series_key]['last_run_quarter']
                    season_name = global_vars.series_info[series_key]['name']
                    if 'classes' in global_vars.series_info[series_key] and len(global_vars.series_info[series_key]['classes']) > 1:
                        if car is None:
                            await ctx.edit(content="You need to specify a car class for this series.")
                            return
                        else:
                            for car_class_key in global_vars.series_info[series_key]['classes']:
                                for keyword in global_vars.series_info[series_key]['classes'][car_class_key]:
                                    if car == keyword:
                                        car_class_id = int(car_class_key)
                                        break
                            if car_class_id == "":
                                await ctx.edit(content="The provided car class is not valid for this series.")
                                return
                    break
            if series_id < 0:
                await ctx.edit(content="Series not found. Did you use the correct series keyword? Based on your track record, I would say no.")
                return

        if season is not None:
            tmp = season[0:4]
            if tmp.isnumeric():
                year = int(tmp)
            else:
                await ctx.edit(content="You've entered an invalid season year: " + tmp)

            tmp = season[-1]
            if tmp.isnumeric():
                quarter = int(tmp)

            if quarter > 4 or quarter < 1:
                await ctx.edit(content="Valid iRacing seasons are 1, 2, 3, or 4.")
                return
            if year > global_vars.series_info['misc']['current_year'] or year == global_vars.series_info['misc']['current_year'] and quarter > global_vars.series_info['misc']['current_quarter']:
                await ctx.edit(content="Just like Nostradamus, I can't predict the future.")
                return
            if year < 2008:
                await ctx.edit(content="iRacing was launched in 2008.")
                return
        else:
            year = last_run_year
            quarter = last_run_quarter

        max_week = 12
        if year == global_vars.series_info["misc"]["current_year"] and quarter == global_vars.series_info["misc"]["current_quarter"]:
            max_week = await stats.get_current_iracing_week(series_id)

        overall_leaderboard = {}
        global_vars.members_locks += 1
        for member in global_vars.members:
            if 'graph_colour' in global_vars.members[member]:
                overall_leaderboard[global_vars.members[member]['leaderboardName']] = {"data": [0], "colour": global_vars.members[member]['graph_colour']}
            else:
                overall_leaderboard[global_vars.members[member]['leaderboardName']] = {"data": [0], "colour": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]}
        global_vars.members_locks -= 1

        week_data = {}
        if series_id < 0:
            week_data = stats.get_respo_champ_points(year, quarter, max_week)
            if week_data == {}:
                await ctx.edit(content="You idiot. Didn't you know? No on in Respo actually races.")
                return
        else:
            week_data = stats.get_champ_points(series_id, car_class_id, year, quarter, max_week)

        someone_racing = False
        for member in week_data:
            if len(week_data[member]) > 0:
                someone_racing = True
                break

        weeks_to_count = 8
        if series == 'respo':
            weeks_to_count = 6

        # Sort weeks, calculate totals, and project totals
        for member in week_data:
            week_data[member]['weeks'] = dict(sorted(week_data[member]['weeks'].items(), key=lambda item: item[0], reverse=False))
            week_data[member]['weeks'] = dict(sorted(week_data[member]['weeks'].items(), key=lambda item: item[1], reverse=True))

            week_data[member]['total_points'] = stats.calc_total_champ_points(week_data[member]['weeks'], weeks_to_count)

            num_weeks_raced = len(week_data[member]['weeks'])
            projected_weeks_raced = num_weeks_raced / max_week * 12
            if projected_weeks_raced > 0:
                inclusion_rate = 6 / projected_weeks_raced
            else:
                inclusion_rate = 1
            projected_points = 0

            weeks_to_project = math.ceil(num_weeks_raced * inclusion_rate)

            # If they haven't raced in the current week in an active series
            if year == global_vars.series_info["misc"]["current_year"] and quarter == global_vars.series_info["misc"]["current_quarter"]:
                if str(max_week) not in week_data[member]["weeks"]:
                    if weeks_to_project >= weeks_to_count:
                        weeks_to_project -= 1

            weeks_counted = 0
            for week in week_data[member]['weeks']:
                projected_points += week_data[member]['weeks'][week]
                weeks_counted += 1
                if weeks_counted >= weeks_to_project:
                    break
            if weeks_to_project > 0:
                week_data[member]['projected_points'] = int(projected_points / weeks_to_project * weeks_to_count)
            else:
                week_data[member]['projected_points'] = 0

        if someone_racing:
            title_text = "Championship Points for " + season_name
            if car_class_id > 0:
                title_text += " class " + global_vars.series_info[str(series_id)]['classes'][str(car_class_id)][0]
            title_text += " for " + str(year) + "s" + str(quarter)

            if year == global_vars.series_info['misc']['current_year'] and quarter == global_vars.series_info['misc']['current_quarter']:
                ongoing = True
            else:
                ongoing = False

            graph = image_gen.generate_champ_graph(week_data, title_text, weeks_to_count, ongoing)

            filepath = env.BOT_DIRECTORY + "media/tmp_champ_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

            graph.save(filepath, format=None)

            with open(filepath, "rb") as f_graph:
                picture = discord.File(f_graph)
                await ctx.edit(content='', file=picture)
                picture.close()

            if os.path.exists(filepath):
                os.remove(filepath)

            return
        else:
            await ctx.edit(content="No one is racing this series because it sucks ass.")
            return

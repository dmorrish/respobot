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
from datetime import datetime
import asyncio


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
        week_13_active = False

        if year == global_vars.series_info['misc']['current_year'] and quarter == global_vars.series_info['misc']['current_quarter'] and not week_13_active:
            ongoing = True
        else:
            ongoing = False

        if ongoing:
            max_week = await stats.get_current_iracing_week(series_id)
            if max_week < 0:
                max_week = 12
                week_13_active = True

        if ongoing and week_13_active:
            ongoing = False

        overall_leaderboard = {}
        global_vars.members_locks += 1
        for member in global_vars.members:
            if 'graph_colour' in global_vars.members[member]:
                overall_leaderboard[global_vars.members[member]['leaderboardName']] = {"data": [0], "colour": global_vars.members[member]['graph_colour']}
            else:
                overall_leaderboard[global_vars.members[member]['leaderboardName']] = {"data": [0], "colour": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]}
        global_vars.members_locks -= 1

        weeks_to_count = 8
        if series == 'respo':
            weeks_to_count = 6

        week_data = {}
        if series_id < 0:
            week_data = stats.get_respo_champ_points(year, quarter, max_week)
            if week_data == {}:
                await ctx.edit(content="You idiot. Didn't you know? No on in Respo actually races.")
                return
        else:
            week_data = stats.get_champ_points(series_id, car_class_id, year, quarter, max_week)

        stats.calc_total_champ_points(week_data, weeks_to_count)
        stats.calc_projected_champ_points(week_data, max_week, weeks_to_count, ongoing)

        someone_racing = False
        for member in week_data:
            if len(week_data[member]['weeks']) > 0:
                someone_racing = True
                break

        if someone_racing:
            title_text = "Championship Points for " + season_name
            if car_class_id > 0:
                title_text += " class " + global_vars.series_info[str(series_id)]['classes'][str(car_class_id)][0]
            title_text += " for " + str(year) + "s" + str(quarter)

            graph = image_gen.generate_champ_graph(week_data, title_text, weeks_to_count, ongoing)

            filepath = env.BOT_DIRECTORY + "media/tmp_champ_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

            graph.save(filepath, format=None)

            with open(filepath, "rb") as f_graph:
                picture = discord.File(f_graph)
                await ctx.edit(content='', file=picture)
                picture.close()

            if os.path.exists(filepath):
                await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
                os.remove(filepath)

            return
        else:
            await ctx.edit(content="This query generated no results, kinda like you.")
            return

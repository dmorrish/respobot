# discord imports
import discord
from discord.ext import commands
from discord.commands import Option

# import all RespoBot modules
import slash_command_helpers as slash_helpers
import stats_helpers as stats
import environment_variables as env
import image_generators as image_gen
import constants

# other imports
import os
import random
from datetime import datetime
import asyncio


class ChampCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='champ',
        description="Show the championship points for a series (or the Respo 'race whatever the fuck' series)."
    )
    async def champ(
        self,
        ctx,
        season: Option(str, "Select a season", required=True, autocomplete=slash_helpers.get_iracing_seasons),
        series: Option(str, "Select a series", required=True, autocomplete=slash_helpers.get_series_list),
        car: Option(str, "Select a car class", required=False, autocomplete=slash_helpers.get_series_classes)
    ):
        await ctx.respond("Working on it...")

        selected_year = None
        selected_quarter = None
        series_id = None
        car_class_id = None

        (current_standard_year, current_standard_quarter, current_standard_race_week, current_standard_max_weeks, current_standard_season_active) = await self.db.get_current_iracing_week(series_id=139)

        if current_standard_year is None:
            await ctx.edit("Something catastrophically bad happened while trying to figure out the current iRacing season. I'm not even a little bit sorry.")

        tmp = season[0:4]
        if tmp.isnumeric():
            selected_year = int(tmp)
        else:
            await ctx.edit(content="You've entered an invalid season year: " + tmp)

        tmp = season[-1]
        if tmp.isnumeric():
            selected_quarter = int(tmp)

        if selected_quarter > 4 or selected_quarter < 1:
            await ctx.edit(content="Valid iRacing seasons are 1, 2, 3, or 4.")
            return
        if selected_year > current_standard_year or selected_year == current_standard_year and selected_quarter > current_standard_quarter:
            await ctx.edit(content="Just like Nostradamus, I can't predict the future.")
            return
        if selected_year < 2008:
            await ctx.edit(content="iRacing was launched in 2008.")
            return

        if series == constants.respo_series_name:
            series_id = -1
        else:
            series_id = await self.db.get_series_id_from_season_name(series, season_year=selected_year, season_quarter=selected_quarter)

            if series_id is None:
                await ctx.edit(content="Series not found. Make sure you select a series from the autocomplete list.")
                return

        if car is not None:
            season_id = await self.db.get_season_id(series_id, selected_year, selected_quarter)
            car_class_id = await self.db.get_car_class_id_from_car_class_name(car, season_id=season_id)

        if series_id > 0:
            (current_season_year, current_season_quarter, current_season_race_week, current_season_max_weeks, current_season_active) = await self.db.get_current_iracing_week(series_id=series_id)
            (_, _, _, _, selected_season_max_week) = await self.db.get_season_basic_info(series_id=series_id, season_year=selected_year, season_quarter=selected_quarter)[0]
        else:
            (current_season_year, current_season_quarter, current_season_race_week, current_season_max_weeks, current_season_active) = await self.db.get_current_iracing_week(series_id=139)
            (_, _, _, _, selected_season_max_week) = await self.db.get_season_basic_info(series_id=139, season_year=selected_year, season_quarter=selected_quarter)[0]

        if selected_year == current_season_year and selected_quarter == current_season_quarter and current_season_active:
            ongoing = True
        else:
            ongoing = False

        if ongoing:
            max_week = current_season_race_week
        else:
            max_week = selected_season_max_week

        if max_week is None:
            max_week = 12

        overall_leaderboard = {}
        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is None or len(member_dicts) < 1:
            await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
            return

        for member_dict in member_dicts:
            if 'name' in member_dict:
                if 'graph_colour' in member_dict:
                    overall_leaderboard[member_dict['name']] = {"data": [0], "colour": member_dict['graph_colour']}
                else:
                    overall_leaderboard[member_dict['name']] = {"data": [0], "colour": [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]}

        weeks_to_count = 8
        if series == constants.respo_series_name:
            weeks_to_count = constants.respo_weeks_to_count

        week_data = {}
        if series_id is not None and series_id > 0:
            week_data = await stats.get_champ_points(self.db, member_dicts, series_id, car_class_id, selected_year, selected_quarter, max_week)
        elif series_id is not None and series_id == -1:
            week_data = await stats.get_respo_champ_points(self.db, member_dicts, selected_year, selected_quarter, max_week)

        if series_id is not None and series_id == -1 and week_data == {}:
            await ctx.edit(content="You idiot. Didn't you know? No on in Respo actually races.")
            return

        stats.calc_total_champ_points(week_data, weeks_to_count)
        stats.calc_projected_champ_points(week_data, max_week, weeks_to_count, ongoing)

        someone_racing = False
        for member in week_data:
            if len(week_data[member]['weeks']) > 0:
                someone_racing = True
                break

        if someone_racing:
            title_text = "Championship Points for " + series
            if car_class_id is not None and car_class_id > 0:
                title_text += " class " + car
            title_text += " for " + str(selected_year) + "s" + str(selected_quarter)

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

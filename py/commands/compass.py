import os
import discord
import math
import asyncio
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import slash_command_helpers as slash_helpers
import stats_helpers as stats
import image_generators as image_gen
from pyracing import constants as pyracingConstants


class CompassCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name="compass",
        description="Plot the iRacing compass for all Respo members."
    )
    async def iracing_compass_meme(
        self,
        ctx,
        season: Option(str, "The season to compare. If left blank, the full driver careers are compared.", required=False, autocomplete=slash_helpers.get_iracing_seasons)
    ):
        await ctx.respond("Working on it...")
        member_stats = {}
        compass_data = {}
        max_laps_per_inc = 0
        max_avg_champ_points = 0

        year = -1
        quarter = -1

        (current_year, current_quarter, _, _, _) = await self.db.get_current_iracing_week()

        if season is None:
            year = None
            quarter = None
        else:
            year, quarter = slash_helpers.parse_season_string(season)

            if year < 0 or quarter < 0:
                await ctx.edit(content="The season string must be in the format: 2018s2")
                return

            if quarter > 4 or quarter < 1:
                await ctx.edit(content="Valid iRacing seasons are 1, 2, 3, or 4.")
                return
            if year > current_year or year == current_year and quarter > current_quarter:
                await ctx.edit(content="Just like Nostradamus, I can't predict the future.")
                return
            if year < 2008:
                await ctx.edit(content="iRacing was launched in 2008.")
                return

        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is None or len(member_dicts) < 1:
            await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
            return

        for member_dict in member_dicts:
            if 'iracing_custid' in member_dict and 'name' in member_dict and 'discord_id' in member_dict:
                name = member_dict['name']
                member_stats[name] = await stats.populate_head2head_stats(self.db, member_dict['iracing_custid'], year=year, quarter=quarter, category=pyracingConstants.Category.road.value, series=None, car_class=None)
                if member_stats[name]['laps_per_inc'] != math.inf:
                    compass_data[name] = {}
                    compass_data[name]['point'] = (member_stats[name]['laps_per_inc'], member_stats[name]['avg_champ_points'])
                    compass_data[name]['discordID'] = member_dict['discord_id']
                    if member_stats[name]['laps_per_inc'] > max_laps_per_inc:
                        max_laps_per_inc = member_stats[name]['laps_per_inc']
                    if member_stats[name]['avg_champ_points'] > max_avg_champ_points:
                        max_avg_champ_points = member_stats[name]['avg_champ_points']

        if season is None:
            time_span_text = "Full Career"
        else:
            time_span_text = season

        image = await image_gen.generate_compass_image(ctx.guild, compass_data, time_span_text)

        filepath = env.BOT_DIRECTORY + "media/tmp_compass_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

        image.save(filepath, format=None)

        with open(filepath, "r+b") as f_compass:
            picture = discord.File(f_compass)
            await ctx.edit(content='', file=picture)
            picture.close()

        if os.path.exists(filepath):
            await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
            os.remove(filepath)

        return

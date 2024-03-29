import io
import discord
import math
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import constants
import helpers
import environment_variables as env
from slash_command_helpers import SlashCommandHelpers, SeasonStringError
import stats_helpers as stats
import image_generators as image_gen
from bot_database import BotDatabaseError


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
        category: Option(
            str,
            "Select a racing category.",
            required=True,
            choices=constants.IRACING_CATEGORIES
        ),
        season: Option(
            str,
            "The season to compare. If left blank, the full driver careers are compared.",
            required=False,
            autocomplete=SlashCommandHelpers.get_iracing_seasons
        )
    ):
        try:
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
                (year, quarter) = SlashCommandHelpers.parse_season_string(season)

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

            member_dicts = await self.db.fetch_member_dicts(ignore_smurfs=True)

            if member_dicts is None or len(member_dicts) < 1:
                await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
                return

            for member_dict in member_dicts:
                if 'iracing_custid' in member_dict and 'name' in member_dict and 'discord_id' in member_dict:
                    name = member_dict['name']
                    member_stats[name] = await stats.calculate_compass_point(
                        self.db,
                        member_dict['iracing_custid'],
                        year=year,
                        quarter=quarter,
                        category=helpers.get_category_from_option(category),
                        series=None,
                        car_class=None
                    )
                    if member_stats[name]['laps_per_inc'] != math.inf:
                        compass_data[name] = {}
                        compass_data[name]['point'] = (
                            member_stats[name]['laps_per_inc'],
                            member_stats[name]['avg_champ_points']
                        )
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

            image_memory_file = io.BytesIO()
            image.save(image_memory_file, format='png')
            image_memory_file.seek(0)

            picture = discord.File(
                image_memory_file,
                filename=f"RespoCompass_{str(datetime.now().strftime('%Y%m%d%H%M%S%f'))}.png"
            )
            await ctx.edit(content='', file=picture)
            image_memory_file.close()
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return
        except SeasonStringError as e:
            await ctx.edit(content=f"Error: {e}")
            return

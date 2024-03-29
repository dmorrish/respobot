import io
import discord
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import constants
import helpers
import environment_variables as env
from slash_command_helpers import SlashCommandHelpers, SeasonStringError
import stats_helpers as stats
import image_generators as image_gen
from irslashdata import constants as irConstants
from bot_database import BotDatabaseError


class Head2HeadCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name="head2head",
        description="Compare two Respo racers over their full career or, optionally, a particular season."
    )
    async def head_2_head(
        self,
        ctx,
        racer1: Option(
            str,
            "The first person in the comparison.",
            required=True,
            autocomplete=SlashCommandHelpers.get_member_list
        ),
        racer2: Option(
            str,
            "The second person in the comparison.",
            required=True,
            autocomplete=SlashCommandHelpers.get_member_list
        ),
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
            if racer1 is None or racer2 is None:
                ctx.respond("You must supply two people to compare.", ephemeral=True)
                return

            await ctx.respond("Working on it...")

            racer1_dict = await self.db.fetch_member_dict(name=racer1)
            if not racer1_dict:
                await ctx.edit(
                    content="I didn't find " + racer1 + " as a Respo member. Make sure you pick someone from the list."
                )
                return

            racer2_dict = await self.db.fetch_member_dict(name=racer2)
            if not racer2_dict:
                await ctx.edit(
                    content="I didn't find " + racer2 + " as a Respo member. Make sure you pick someone from the list."
                )
                return

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

            racer1_stats = await stats.populate_head2head_stats(
                self.db,
                racer1_dict['iracing_custid'],
                year=year,
                quarter=quarter,
                category=helpers.get_category_from_option(category),
                series=None,
                car_class=None
            )

            racer2_stats = await stats.populate_head2head_stats(
                self.db,
                racer2_dict['iracing_custid'],
                year=year,
                quarter=quarter,
                category=helpers.get_category_from_option(category),
                series=None,
                car_class=None
            )

            if racer1_stats['total_races'] < 1:
                await ctx.edit(content=racer1_dict['name'] + " has no races for the selected options.")
                return

            if racer2_stats['total_races'] < 1:
                await ctx.edit(content=racer2_dict['name'] + " has no races for the selected options.")
                return

            if season is not None:
                title = season
            else:
                title = "Full Career"

            image = await image_gen.generate_head2head_image(
                ctx.guild,
                title,
                racer1_dict,
                racer1_stats,
                racer2_dict,
                racer2_stats
            )

            image_memory_file = io.BytesIO()
            image.save(image_memory_file, format='png')
            image_memory_file.seek(0)

            picture = discord.File(
                image_memory_file,
                filename=f"RespoHead2Head_{str(datetime.now().strftime('%Y%m%d%H%M%S%f'))}.png"
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

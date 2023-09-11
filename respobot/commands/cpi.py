# discord imports
import discord
from discord.ext import commands
from discord.commands import Option

# import all RespoBot modules
from slash_command_helpers import SlashCommandHelpers
import environment_variables as env
import image_generators as image_gen
import constants
import stats_helpers as stats
from bot_database import BotDatabaseError

# other imports
import os
from datetime import datetime


class CornersPerIncidentCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='cpi',
        description=(
            f"Generate a graph of corners per incident averaged over your previous "
            f"{constants.CPI_CORNERS_INCLUDED} corners."
        )
    )
    async def cpi(
        self,
        ctx,
        member: Option(str, "Select a season", required=True, autocomplete=SlashCommandHelpers.get_member_list),
        series: Option(str, "Select a series", required=False, autocomplete=SlashCommandHelpers.get_all_series_list)
    ):
        try:
            await ctx.respond("Working on it...")

            series_id = None

            series_name = ""

            if series is not None:
                id_start = series.rfind("(") + 1
                id_end = series.rfind(")")
                series_id = int(series[id_start:id_end])

                if series_id is None:
                    await ctx.edit(
                        content="Series not found. Make sure you select a series from the autocomplete list."
                    )
                    return

                series_name = await self.db.get_series_name_from_id(series_id)

            member_dict = await self.db.fetch_member_dict(name=member)

            cpi_graph_data = await stats.generate_cpi_graph_data(
                self.db,
                member_dict['iracing_custid'],
                series_id=series_id
            )

            if len(cpi_graph_data) < 1:
                await ctx.edit(content="This member has not raced this series.")
                return

            total_corners = cpi_graph_data[-1][1]
            if total_corners < constants.CPI_CORNERS_INCLUDED:
                await ctx.edit(
                    content=(
                        f"This member has not completed {constants.CPI_CORNERS_INCLUDED} corners "
                        f"that match the selected options."
                    )
                )
                return

            member_dict["cpi_data"] = cpi_graph_data

            title_text = f"Corners per Incident Graph for {member_dict['name']} ({cpi_graph_data[-1][2]:.1f})"
            if series is not None:
                title_text += f"\n{series_name}"
            else:
                title_text += f"\nAll Series"
            graph = image_gen.generate_cpi_graph(member_dict, title_text, False)

            filename = f"tmp_cpi_{str(datetime.now().strftime('%Y%m%d%H%M%S%f'))}.png"
            filepath = env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + filename

            graph.save(filepath, format=None)

            with open(filepath, "rb") as f_graph:
                picture = discord.File(f_graph)
                await ctx.edit(content='', file=picture)
                picture.close()

            if os.path.exists(filepath):
                os.remove(filepath)

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

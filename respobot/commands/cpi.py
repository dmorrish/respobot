# discord imports
import discord
from discord.ext import commands
from discord.commands import Option

# import all RespoBot modules
from slash_command_helpers import SlashCommandHelpers
import environment_variables as env
import image_generators as image_gen
import constants

# other imports
import os
from datetime import datetime
import asyncio


class CornersPerIncidentCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='cpi',
        description=f"Generate a graph of corners per incident averaged over your previous {constants.CPI_CORNERS_INCLUDED} corners."
    )
    async def cpi(
        self,
        ctx,
        member: Option(str, "Select a season", required=True, autocomplete=SlashCommandHelpers.get_member_list),
        series: Option(str, "Select a series", required=False, autocomplete=SlashCommandHelpers.get_all_series_list)
    ):
        await ctx.respond("Working on it...")

        series_id = None

        series_name = ""

        (current_year, current_quarter, _, _, _) = await self.db.get_current_iracing_week(series_id=139)

        if series is not None:
            id_start = series.rfind("(") + 1
            id_end = series.rfind(")")
            series_id = int(series[id_start:id_end])

            if series_id is None:
                await ctx.edit(content="Series not found. Make sure you select a series from the autocomplete list.")
                return

            series_name = await self.db.get_series_name_from_id(series_id)

        member_dict = await self.db.fetch_member_dict(name=member)

        cpi_tuples = await self.db.get_cpi_data(member_dict['iracing_custid'], series_id=series_id)
        member_dict['cpi_data'] = []
        total_corners = 0

        for i in range(len(cpi_tuples)):
            total_corners += cpi_tuples[i][2]
            previous_races_needed = 1
            corners_counted = cpi_tuples[i][2]
            total_incidents = cpi_tuples[i][1]

            # The current race has enough corners all on its own. Scale CPI based on this race.
            if corners_counted > constants.CPI_CORNERS_INCLUDED:
                total_incidents = total_incidents * constants.CPI_CORNERS_INCLUDED / corners_counted
                corners_counted = constants.CPI_CORNERS_INCLUDED

            while corners_counted < constants.CPI_CORNERS_INCLUDED and i - previous_races_needed >= 0:
                if corners_counted + cpi_tuples[i - previous_races_needed][2] < constants.CPI_CORNERS_INCLUDED:
                    # All corners in this race are needed. Simply grab the incidents and laps.
                    corners_counted += cpi_tuples[i - previous_races_needed][2]
                    total_incidents += cpi_tuples[i - previous_races_needed][1]
                else:
                    # Only a fraction of the corners in this race are needed.
                    # Weight the incidents by the proportion of total laps that are needed
                    corners_needed = constants.CPI_CORNERS_INCLUDED - corners_counted
                    corners_counted = constants.CPI_CORNERS_INCLUDED
                    total_incidents += cpi_tuples[i - previous_races_needed][1] * corners_needed / cpi_tuples[i - previous_races_needed][2]
                previous_races_needed += 1

            if total_incidents == 0:
                new_cpi = constants.CPI_CORNERS_INCLUDED
            else:
                new_cpi = corners_counted / total_incidents

            if new_cpi > constants.CPI_CORNERS_INCLUDED:
                new_cpi = constants.CPI_CORNERS_INCLUDED

            cpi_timestamp = datetime.fromisoformat(cpi_tuples[i][0]).timestamp() * 1000
            member_dict['cpi_data'].append((cpi_timestamp, total_corners, new_cpi))

        if len(member_dict['cpi_data']) < 1:
            await ctx.edit(content="This member has not raced this series.")
            return

        if total_corners < constants.CPI_CORNERS_INCLUDED:
            await ctx.edit(content=f"This member has not completed {constants.CPI_CORNERS_INCLUDED} laps that match the selected options.")
            return

        title_text = f"Corners per Incident Graph for {member_dict['name']} ({member_dict['cpi_data'][-1][2]:.1f})"
        if series is not None:
            title_text += f"\n{series_name}"
        else:
            title_text += f"\nAll Series"
        graph = image_gen.generate_cpi_graph([member_dict], title_text, False)

        filepath = env.BOT_DIRECTORY + "media/tmp_cpi_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

        graph.save(filepath, format=None)

        with open(filepath, "rb") as f_graph:
            picture = discord.File(f_graph)
            await ctx.edit(content='', file=picture)
            picture.close()

        if os.path.exists(filepath):
            await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
            os.remove(filepath)

        return

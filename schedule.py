import discord
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import slash_command_helpers as slash_helpers
import global_vars


class ScheduleCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='schedule',
        description="Show the current season schedule for a series."
    )
    async def schedule(
        self,
        ctx,
        series: Option(str, "Select a series", autocomplete=slash_helpers.get_series_list)
    ):
        seasons = await global_vars.ir.current_seasons(only_active=True)

        if not seasons:
            await ctx.respond("Something went horribly wrong! There are no active seasons!")
            return

        series_found = False

        for series_key in global_vars.series_info:
            if "keywords" in global_vars.series_info[series_key]:
                for keyword in global_vars.series_info[series_key]['keywords']:
                    if keyword == series.lower():
                        series_id = int(series_key)
                        series_found = True

        if series_found is not True:
            await ctx.respond(f"What the fuck series is \"{series}\"")
            return

        for season in seasons:
            if season.series_id == series_id:
                title = "Schedule for " + global_vars.series_info[str(series_id)]["name"]
                embedVar = discord.Embed(title=title, description="", color=0xff0000)
                # message_text = "Schedule for " + global_vars.series_info[str(series_id)]["name"] + ":\n\n"
                for track in season.tracks:
                    week_text = "  Week " + str(track.race_week + 1)
                    if track.race_week + 1 == season.race_week:
                        week_text += " (current)"
                    track_text = " " + track.name
                    if track.config and track.config != "N/A":
                        track_text += " (" + track.config + ")"
                    embedVar.add_field(name=week_text, value=track_text, inline=False)
                await ctx.respond(embed=embedVar)
                return

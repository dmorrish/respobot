from datetime import datetime, timezone
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import helpers
from slash_command_helpers import SlashCommandHelpers
from irslashdata.exceptions import AuthenticationError, ServerDownError


class NextRaceCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='nextrace',
        description="Show the next race time for a particular series."
    )
    async def nextrace(
        self,
        ctx,
        series: Option(str, "Select a series.", required=True, autocomplete=SlashCommandHelpers.get_series_list)
    ):
        await ctx.respond("On it...", ephemeral=False)

        (season_year, season_quarter) = SlashCommandHelpers.get_current_season()

        series_id = await self.db.get_series_id_from_season_name(series, season_year=season_year, season_quarter=season_quarter)

        if series_id is None:
            await ctx.edit(content="I didn't find that series, just like your dignity.")
            return

        if series_id > 0:
            try:
                race_guide = await self.ir.race_guide_new()
            except AuthenticationError:
                await ctx.edit(content=f"Authentication failed when trying to log in to the iRacing server. Deryk has been DMed.")
                await helpers.send_bot_failure_dm(self.bot, "Authentication to the iRacing server failed.")
                return
            except ServerDownError:
                await ctx.edit(content=f"iRacing is down for maintenance and this command relies on the stats server. Try again later.")
                return

        if race_guide is None:
            await ctx.edit(content="I think I shit myself. Sorry.")
            return

        race_found = False
        time_start = datetime(year=3000, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        for session in race_guide['sessions']:
            if 'series_id' in session and session['series_id'] == series_id:
                if 'start_time' in session:
                    race_found = True
                    session_start_time = datetime.fromisoformat(session['start_time'])
                    if session_start_time < time_start:
                        time_start = session_start_time

        if race_found is False:
            await ctx.edit(content=f"There aren't any races scheduled for **{series}** in the next three hours which is as far ahead that iRacing will let me see.")
            return

        message_text = f"The next race in **{series}** is scheduled for <t:{str(int(time_start.timestamp()))}>"

        time_until_next = time_start - datetime.now(timezone.utc)

        if time_until_next.days < 1:
            hours = int(time_until_next.seconds / (60 * 60))
            minutes = int((time_until_next.seconds % (60 * 60)) / 60)
            message_text += " (in "
            if hours > 0:
                message_text += str(hours) + " hour"
                if hours > 1:
                    message_text += "s"
                message_text += " and "
            message_text += str(minutes) + " minute"
            if minutes != 1:
                message_text += "s"
            message_text += ")"
        message_text += "."

        await ctx.edit(content=message_text)
        return

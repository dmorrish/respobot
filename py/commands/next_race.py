from datetime import datetime, timedelta, timezone
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import slash_command_helpers as slash_helpers


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
        series: Option(str, "Select a series.", required=True, autocomplete=slash_helpers.get_series_list)
    ):
        await ctx.respond("On it...", ephemeral=False)

        # Default is RespoBot's timezone.
        respobot_time_offset = datetime.now() - datetime.utcnow()
        user_time_offset = respobot_time_offset

        timezone_name = "eastern"

        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is not None and len(member_dicts) > 0:
            for member_dict in member_dicts:
                if 'discord_id' in member_dict and member_dict['discord_id'] == ctx.author.id and 'timezone' in member_dict:
                    timezone_name = member_dict['timezone']

        if timezone_name == "eastern":
            user_time_offset += timedelta(hours=0)
        elif timezone_name == "central":
            user_time_offset += timedelta(hours=-1)
        elif timezone_name == "mountain":
            user_time_offset += timedelta(hours=-2)
        elif timezone_name == "pacific":
            user_time_offset += timedelta(hours=-3)
        else:
            timezone_name = 'eastern'
            user_time_offset += timedelta(hours=0)

        series_id = await self.db.get_series_id_from_season_name(series)

        if series_id is None:
            await ctx.edit(content="I didn't find that series, just like your dignity.")
            return

        if series_id > 0:
            race_guide = await self.ir.race_guide_new()

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

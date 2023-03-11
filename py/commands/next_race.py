from datetime import datetime, timedelta
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import slash_command_helpers as slash_helpers
import global_vars
from pyracing import constants as pyracingConstants


class NextRaceCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

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

        global_vars.members_locks += 1
        for member in global_vars.members:
            if 'discordID' in global_vars.members[member] and global_vars.members[member]['discordID'] == ctx.author.id and 'timezone' in global_vars.members[member]:
                timezone_name = global_vars.members[member]['timezone']
        global_vars.members_locks -= 1

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

        series_id = -1
        series_found = False

        for series_key in global_vars.series_info:
            if "keywords" in global_vars.series_info[series_key]:
                for keyword in global_vars.series_info[series_key]['keywords']:
                    if keyword == series:
                        series_id = int(series_key)
                        series_found = True

        if series_found is False:
            await ctx.edit(content="I didn't find that series, just like your dignity.")
            return

        if series_id > 0:
            race_guide = await global_vars.ir.race_guide()

        if race_guide is None:
            await ctx.edit(content="I think I shit myself. Sorry.")
            return

        race_found = False
        time_start = datetime(year=3000, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        for series in race_guide:
            if series.series_id == series_id:
                for schedule in series.season_schedule:
                    for race in schedule.race:
                        if race.event_type == pyracingConstants.EventType.race.value:
                            if race.time_start < time_start and race.time_start + respobot_time_offset > datetime.now():
                                # Keep the earliest race that starts after now.
                                time_start = race.time_start + respobot_time_offset
                                # Round minutes due to getting times just a few microseconds below the minute mark.
                                minutes = int(time_start.minute + round((time_start.second + time_start.microsecond / 1000000) / 60, 0))
                                time_added = timedelta(minutes=minutes)
                                time_start = time_start.replace(microsecond=0, second=0, minute=0)
                                time_start += time_added
                                race_found = True

        if race_found is False:
            await ctx.edit(content="There aren't any races scheduled for that series at the moment.")
            return

        # if time_start.date() == (datetime.now() + user_time_offset).date():
        #     message_text = "The next race in **" + global_vars.series_info[str(series_id)]['name'] + "** is today at " + time_start.strftime("%I:%M%p") + " (" + timezone_name + ")."
        # else:
        #     message_text = "The next race in **" + global_vars.series_info[str(series_id)]['name'] + "** is on " + time_start.strftime("%Y-%b-%d at %I:%M%p") + " (" + timezone_name + ")."

        message_text = "The next race in **" + global_vars.series_info[str(series_id)]['name'] + "** is scheduled for <t:" + str(int(time_start.timestamp())) + ">."

        time_until_next = time_start - datetime.now()

        if time_until_next.days < 1:
            hours = int(time_until_next.seconds / (68 * 60))
            minutes = int((time_until_next.seconds % (60 * 60)) / 60)
            message_text += "\n(in "
            if hours > 0:
                message_text += str(hours) + " hour"
                if hours > 1:
                    message_text += "s"
                message_text += " and "
            message_text += str(minutes) + " minute"
            if minutes != 1:
                message_text += "s"
            message_text += ")"

        await ctx.edit(content=message_text)
        return

import discord
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
from slash_command_helpers import SlashCommandHelpers
from bot_database import BotDatabaseError
from irslashdata.exceptions import AuthenticationError, ServerDownError


class ScheduleCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='schedule',
        description="Show the current season schedule for a series."
    )
    async def schedule(
        self,
        ctx,
        series: Option(str, "Select a series", required=True, autocomplete=SlashCommandHelpers.get_series_list)
    ):
        try:
            await ctx.respond("Working on it...")
            season_dicts = await self.ir.current_seasons()

            if season_dicts is None:
                await ctx.edit(content="Something went horribly wrong! There are no active seasons!")
                return

            series_found = False
            schedule = None
            race_week = None

            for season_dict in season_dicts:
                if 'season_name' in season_dict and season_dict['season_name'] == series:
                    series_found = True
                    if 'schedules' in season_dict and len(season_dict['schedules']) > 1:
                        schedule = season_dict['schedules']
                    if 'race_week' in season_dict:
                        race_week = season_dict['race_week']

            if series_found is not True:
                await ctx.edit(content=f"What the fuck series is \"{series}\"?")
                return

            title = "Schedule for " + series
            embedVar = discord.Embed(title=title, description="", color=0xff0000)

            if schedule is not None and len(schedule) > 0:
                schedule = sorted(schedule, key=lambda d: d['race_week_num'])
                for race_week_dict in schedule:
                    week_text = "  Week " + str(race_week_dict['race_week_num'] + 1)
                    if race_week_dict['race_week_num'] == race_week:
                        week_text += " (current)"
                    if 'track' in race_week_dict and 'track_name' in race_week_dict['track']:
                        track_text = " " + race_week_dict['track']['track_name']
                    if 'track' in race_week_dict and 'config_name' in race_week_dict['track']:
                        track_text += " (" + race_week_dict['track']['config_name'] + ")"
                    embedVar.add_field(name=week_text, value=track_text, inline=False)
                await ctx.edit(content="", embed=embedVar)
            else:
                await ctx.edit(content=f"No schedule was found for {series}")
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except AuthenticationError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Authentication failed when trying to log in to the iRacing server.",
                exc
            )
            return
        except ServerDownError:
            await ctx.edit(
                content=(
                    f"iRacing is down for maintenance and this command relies on the stats server. "
                    f"Try again later."
                )
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

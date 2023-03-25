import discord
from discord.ext import commands
from discord.commands import Option
import global_vars
import environment_variables as env
import json
from datetime import date


class SpecialEventsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name='special_events',
        description='Show the iRacing special events calendar.'
    )
    async def special_events(
        self,
        ctx,
        show: Option(str, "Select a racing category.", required=False, choices=['all', 'upcoming', 'next']),
        category: Option(str, "Select a racing category.", required=False, choices=['road', 'oval', 'dirt_road', 'dirt_oval'])
    ):
        with open(env.BOT_DIRECTORY + "json/special_events.json", "r") as f_schedule:
            schedule = json.load(f_schedule)

        if schedule:
            year_string = str(date.today().year)
            title_text = ""

            if not show or (show == 'all'):
                title_text = "Special Events Calendar for " + year_string
            elif show == 'upcoming':
                title_text = "Upcoming Special Events for " + year_string
            else:
                title_text = "Next Special Event"

            if category:
                if category == 'road':
                    title_text += " - Road"
                elif category == 'oval':
                    title_text += " - Oval"
                elif category == 'dirt_road':
                    title_text += " - Dirt Road"
                elif category == 'dirt_oval':
                    title_text += " - Dirt Oval"

            embedVar = discord.Embed(title=title_text, description="", color=0xff0000)

            if year_string not in schedule:
                await ctx.respond("Deryk hasn't entered any special event dates for " + year_string + " yet. Go tell him to get off his lazy ass and fix it.")
            else:
                event_count = 0
                for event in schedule[year_string]:

                    start_date = None
                    end_date = None

                    if schedule[year_string][event]['start'] != {}:
                        start_date = date(schedule[year_string][event]['start']['year'], schedule[year_string][event]['start']['month'], schedule[year_string][event]['start']['day'])
                    if schedule[year_string][event]['end'] != {}:
                        end_date = date(schedule[year_string][event]['end']['year'], schedule[year_string][event]['end']['month'], schedule[year_string][event]['end']['day'])

                    if (start_date is not None) and (end_date is not None):
                        if start_date == end_date:
                            event_details = start_date.strftime("%b %d, %Y") + "\n"
                        elif start_date.month == end_date.month:
                            event_details = start_date.strftime("%b %d") + "-" + end_date.strftime("%d, %Y") + "\n"
                        else:
                            event_details = start_date.strftime("%b %d") + " - " + end_date.strftime("%b %d, %Y") + "\n"
                    else:
                        event_details = "Dates TBD \n"

                    event_details += schedule[year_string][event]['track'] + "\n"
                    event_details += schedule[year_string][event]['cars'] + "\n"

                    if category and category != schedule[year_string][event]['category']:
                        continue

                    if not show or (show == 'all') or event_count > 13:
                        embedVar.add_field(name=schedule[year_string][event]['name'], value=event_details, inline=False)
                        event_count += 1
                    elif (start_date is None) or (end_date is None) or (end_date >= date.today()):
                        embedVar.add_field(name=schedule[year_string][event]['name'], value=event_details, inline=False)
                        event_count += 1

                        if show == 'next':
                            break

                if event_count == 0:
                    await ctx.respond("There are no more events scheduled this year.")
                elif not show and not category:
                    await ctx.respond(embed=embedVar, ephemeral=True)
                else:
                    await ctx.respond(embed=embedVar, ephemeral=False)

        else:
            await ctx.respond("I couldn't load the schedule. Tell Deryk he sucks.")

import discord
from discord.ext import commands
from discord.commands import Option
from datetime import date


class SpecialEventsCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        name='special_events',
        description='Show the iRacing special events calendar.'
    )
    async def special_events(
        self,
        ctx,
        show: Option(str, "Select what to return. 'all' includes any races from the current year forward.", required=False, choices=['all', 'upcoming', 'next']),
        category: Option(str, "Select a racing category.", required=False, choices=['road', 'oval', 'dirt_road', 'dirt_oval'])
    ):
        year_string = str(date.today().year)
        title_text = ""
        earliest_date = date.today()

        if not show or (show == 'all'):
            title_text = "Special Events Calendar for " + year_string + " and Onward"
            earliest_date = date(date.today().year, 1, 1)
        elif show == 'upcoming':
            title_text = "Upcoming Special Events"
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

        event_dicts = await self.db.get_special_events(earliest_date=earliest_date.isoformat())

        if event_dicts is None or len(event_dicts) < 1:
            await ctx.respond(f"Deryk hasn't entered any special event dates after {earliest_date} yet. Go tell him to get off his lazy ass and fix it.")
        else:
            event_count = 0
            for event_dict in event_dicts:

                try:
                    start_date = date.fromisoformat(event_dict['start_date'])
                except ValueError:
                    start_date = None

                try:
                    end_date = date.fromisoformat(event_dict['end_date'])
                except ValueError:
                    end_date = None

                if (start_date is not None) and (end_date is not None):
                    if start_date == end_date:
                        event_details = start_date.strftime("%b %d, %Y") + "\n"
                    elif start_date.month == end_date.month:
                        event_details = start_date.strftime("%b %d") + "-" + end_date.strftime("%d, %Y") + "\n"
                    else:
                        event_details = start_date.strftime("%b %d") + " - " + end_date.strftime("%b %d, %Y") + "\n"
                else:
                    event_details = "Dates TBD \n"

                event_details += event_dict['track'] + "\n"
                event_details += event_dict['cars'] + "\n"

                if category and category != event_dict['category']:
                    continue

                if not show or (show == 'all'):
                    embedVar.add_field(name=event_dict['name'], value=event_details, inline=False)
                    event_count += 1
                elif (start_date is None) or (end_date is None) or (end_date >= date.today()):
                    embedVar.add_field(name=event_dict['name'], value=event_details, inline=False)
                    event_count += 1

                    if show == 'next':
                        break

            if event_count == 0:
                await ctx.respond(f"There are no events scheduled after {earliest_date}.")
            elif not show and not category:
                await ctx.respond(embed=embedVar, ephemeral=True)
            else:
                await ctx.respond(embed=embedVar, ephemeral=False)

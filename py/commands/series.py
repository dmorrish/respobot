import discord
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import global_vars
from pyracing import constants as pyracingConstants


class SeriesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='series',
        description="Generate a list of all the series keywords for use in other commands."
    )
    async def series(
        self,
        ctx,
        category: Option(str, "Select a racing category.", required=False, choices=['road', 'oval', 'dirt_road', 'dirt_oval'])
    ):
        if category is None:
            category = 'road'

        title_text = ""
        message_text = ""
        if category.lower() == 'road':
            category_id = pyracingConstants.Category.road.value
            title_text = "Road Series Keywords:\n\n"
        elif category.lower() == 'dirt_road':
            category_id = pyracingConstants.Category.dirt_road.value
            title_text = "Dirt Road Series Keywords:\n\n"
        elif category.lower() == 'oval':
            category_id = pyracingConstants.Category.oval.value
            title_text = "Oval Series Keywords:\n\n"
        elif category.lower() == 'dirt_oval':
            category_id = pyracingConstants.Category.dirt_oval.value
            title_text = "Dirt Oval Series Keywords:\n\n"
        else:
            category_id = pyracingConstants.Category.road.value
            title_text = "Road Series Keywords:\n\n"

        embedVar = discord.Embed(title=title_text, description="", color=0xff0000)

        for series in global_vars.series_info:
            if 'keywords' in global_vars.series_info[series] and len(global_vars.series_info[series]['keywords']) > 0 and 'category' in global_vars.series_info[series] and global_vars.series_info[series]['category'] == category_id and global_vars.series_info[series]['last_run_year'] == global_vars.series_info['misc']['current_year'] and global_vars.series_info[series]['last_run_quarter'] == global_vars.series_info['misc']['current_quarter']:
                keyword_length = len(global_vars.series_info[series]['keywords'][0])
                for i in range(0, 10 - keyword_length):
                    message_text += " "
                field_title = ""
                first_keyword = True
                for keyword in global_vars.series_info[series]['keywords']:
                    if first_keyword:
                        field_title += keyword
                        first_keyword = False
                        if len(global_vars.series_info[series]['keywords']) > 1:
                            field_title += " ("
                    else:
                        field_title += keyword + ", "
                if len(global_vars.series_info[series]['keywords']) > 1:
                    field_title = field_title[0:-2]
                    field_title += ")"

                field_text = global_vars.series_info[series]['name']
                if 'classes' in global_vars.series_info[series] and len(global_vars.series_info[series]['classes']) > 1:
                    field_text += " ("
                    first_class = True
                    for car_class in global_vars.series_info[series]['classes']:
                        if len(global_vars.series_info[series]['classes'][car_class]) > 0:
                            if first_class is True:
                                field_text += global_vars.series_info[series]['classes'][car_class][0]
                                first_class = False
                            else:
                                field_text += ", " + global_vars.series_info[series]['classes'][car_class][0]
                    field_text += ")"
                embedVar.add_field(name=field_title, value=field_text, inline=False)

        await ctx.respond(embed=embedVar, ephemeral=True)

        return

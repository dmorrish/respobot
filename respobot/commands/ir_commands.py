import os
import random
import discord
import asyncio
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import constants
import environment_variables as env
import helpers
import slash_command_helpers as slash_helpers
from slash_command_helpers import SlashCommandHelpers
import image_generators as image_gen
from pyracing import constants as pyracingConstants
from discord.commands import SlashCommandGroup


class IrCommandsCog(commands.Cog):

    def __init__(self, bot_, db, ir):
        self.bot = bot_
        self.db = db
        self.ir = ir

    ir_command_group = SlashCommandGroup("ir", "Commands related to iRating.")

    @ir_command_group.command(
        name='graph',
        description="Graph all Respo Racing members' iRating. Alternatively, plot a specific person by name or iRacing ID"
    )
    async def ir_graph(
        self,
        ctx,
        member: Option(str, "Plot iRating for a specific person. Can be a Respo member, or by full name or iRacing ID.", required=False, autocomplete=SlashCommandHelpers.get_member_list)
    ):
        member_dicts = []
        if member is not None:
            member_dict = await self.db.fetch_member_dict(first_name=member)

            if member_dict:
                await ctx.respond("Plotting iRating for " + member)

                if 'graph_colour' not in member_dict:
                    member_dict['graph_colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]

                member_dicts.append(member_dict)
            else:
                if not member.isnumeric():
                    driver_name = ""
                    if (member[0] == '"' or member[0] == "“") and (member[-1] == '"' or member[-1] == '”'):
                        # Adding by quoted name. Quoted and unquoted are now functionally equivalent since I stopped trying to clean up the command input.
                        driver_name = member[1:-1]
                    else:
                        # Adding by unquoted name
                        driver_name = member

                    await ctx.respond("Checking iRacing servers for " + member)

                    driver_dict_list = await self.ir.lookup_drivers_new(driver_name)

                    driver_found = False
                    for driver_dict in driver_dict_list:
                        if driver_dict['display_name'].lower() == driver_name.lower():
                            member_dict = {}
                            member_dict['name'] = driver_dict['display_name']
                            member_dict['iracing_custid'] = driver_dict['cust_id']
                            member_dict['graph_colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]
                            member_dicts.append(member_dict)
                            driver_found = True
                    if not driver_found:
                        await ctx.edit(content="Just like your dignity, the driver named " + driver_name + " is nowhere to be found on iRacing.")
                        return
                else:
                    iracing_custid = int(member)
                    await ctx.respond("Checking iRacing servers for ID: " + member)
                    member_info_dict_list = await self.ir.get_member_info_new([iracing_custid])
                    if len(member_info_dict_list) < 1:
                        await ctx.edit(content="Just like your dignity, the driver with the iRacing ID " + member + " is nowhere to be found on iRacing.")
                        return
                    else:
                        member_dict = {}
                        member_dict['name'] = member_info_dict_list[0]['display_name']
                        member_dict['iracing_custid'] = iracing_custid
                        member_dict['graph_colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]
                        member_dicts.append(member_dict)
        else:
            await ctx.respond("Generating iR graph for all Respo members.")

            member_dicts = await self.db.fetch_member_dicts()

            if member_dicts is None or len(member_dicts) < 1:
                await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
                return

            for member_dict in member_dicts:
                if 'graph_colour' not in member_dict:
                    member_dict['colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]

        if len(member_dicts) < 1:
            await ctx.edit(content="Something went wrong. No one was found and an error wasn't thrown. Deryk sucks at programming.")
            return

        for member_dict in member_dicts:
            member_dict['ir_data'] = []
            if 'discord_id' not in member_dict:
                irating_data = await self.ir.chart_data_new(member_dict['iracing_custid'], category_id=2, chart_type=1)
                for point_dict in irating_data:
                    time_point = datetime.fromisoformat(point_dict['when'])
                    timestamp = time_point.timestamp() * 1000
                    member_dict['ir_data'].append((timestamp, point_dict['value']))
            else:
                member_dict['ir_data'] = await self.db.get_ir_data(iracing_custid=member_dict['iracing_custid'], category_id=pyracingConstants.Category.road.value)

        temp_member_dicts = []

        for member_dict in member_dicts:
            if len(member_dict['ir_data']) > 0:
                temp_member_dicts.append(member_dict)

        sorted_member_dicts = sorted(temp_member_dicts, key=lambda item: item['ir_data'][-1][1], reverse=True)

        if len(sorted_member_dicts) > 1:
            title_text = "Respo Racing iRating Graph"
            graph = image_gen.generate_ir_graph(sorted_member_dicts, title_text, True)
        else:
            irating = sorted_member_dicts[0]['ir_data'][-1][1]
            title_text = "iRating Graph for " + sorted_member_dicts[0]['name'] + " (" + str(irating) + ")"
            graph = image_gen.generate_ir_graph(sorted_member_dicts, title_text, False)

        filepath = env.BOT_DIRECTORY + "media/tmp_ir_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

        graph.save(filepath, format=None)

        with open(filepath, "rb") as f_graph:
            picture = discord.File(f_graph)
            await ctx.edit(content='', file=picture)
            picture.close()

        if os.path.exists(filepath):
            await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
            os.remove(filepath)

        return

    @ir_command_group.command(
        name='leaderboard',
        description='Show the iRating leaderboard.'
    )
    async def ir_leaderboard(
        self,
        ctx
    ):
        ir_dict = {}
        pleb_line_printed = False
        response = "```\nNAME                        IR\n"
        response += "--------------------------------\n"
        response += "rEsPo BoT                  " + str(random.randint(12401, 12990)) + "\n"

        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is None or len(member_dicts) < 1:
            await ctx.respond("There aren't any members entered into the database yet. Go yell at Deryk.")
            return

        for member_dict in member_dicts:
            latest_road_ir_in_db = await self.db.get_member_ir(member_dict['iracing_custid'], category_id=pyracingConstants.Category.road.value)
            if latest_road_ir_in_db is None or latest_road_ir_in_db < 0:
                continue
            ir_dict[helpers.spongify(member_dict['name'])] = member_dict['last_known_ir']

        sorted_ir_dict = dict(sorted(ir_dict.items(), key=lambda item: item[1], reverse=True))

        print(sorted_ir_dict)

        for key in sorted_ir_dict:
            if pleb_line_printed is False and sorted_ir_dict[key] is not None and sorted_ir_dict[key] < constants.pleb_line:
                response += "----------(pleb line)-----------\n"
                pleb_line_printed = True
            response += key
            for i in range(28 - len(key)):
                response += " "
            response += str(sorted_ir_dict[key]) + "\n"
        response += "\n```"
        await ctx.respond(response)
        return

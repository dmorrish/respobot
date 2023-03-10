import os
import random
import discord
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import slash_command_helpers as slash_helpers
import stats_helpers as stats
import image_generators as image_gen
import global_vars
from pyracing import constants as pyracingConstants


class IrGraphCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.ir_command_group.command(
        name='graph',
        description="Graph all Respo Racing members' iRating. Alternatively, plot a specific person by name or iRacing ID"
    )
    async def ir_graph(
        ctx,
        member: Option(str, "Plot iRating for a specific person. Can be a Respo member, or by full name or iRacing ID.", required=False, autocomplete=slash_helpers.get_member_list)
    ):
        ir_dict = {}
        if member is not None:
            member_dict = slash_helpers.get_member_details(member)
            if member_dict:
                await ctx.respond("Plotting iRating for " + member)
                ir_dict[member_dict["iracingCustID"]] = {}
                ir_dict[member_dict["iracingCustID"]]['name'] = member_dict['leaderboardName']
                ir_dict[member_dict["iracingCustID"]]['last_known_ir'] = member_dict['last_known_ir']
                ir_dict[member_dict["iracingCustID"]]['is_respo'] = True

                if 'graph_colour' in member_dict:
                    ir_dict[member_dict["iracingCustID"]]['colour'] = member_dict['graph_colour']
                else:
                    ir_dict[member_dict["iracingCustID"]]['colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]
            else:
                if not member.isnumeric():
                    driver_name = ""
                    if (member[0] == '"' or member[0] == "“") and (member[-1] == '"' or member[-1] == '”'):
                        # Adding by quoted name. Quoted and unquoted $add are now functionally equivalent since I stopped trying to clean up the command input.
                        driver_name = member[1:-1]
                    else:
                        # Adding by unquoted name
                        driver_name = member

                    await ctx.respond("Checking iRacing servers for " + member)
                    driver_list = await global_vars.ir.driver_stats(search=driver_name)  # This returns a list of drivers, but we only want exact matches.
                    driver_found = False
                    for driver in driver_list:
                        if driver.display_name.lower() == driver_name.lower():
                            ir_dict[driver.cust_id] = {}
                            ir_dict[driver.cust_id]['name'] = driver.display_name
                            ir_dict[driver.cust_id]['last_known_ir'] = -1
                            ir_dict[driver.cust_id]['is_respo'] = False
                            ir_dict[driver.cust_id]['colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]
                            driver_found = True
                    if not driver_found:
                        await ctx.edit(content="Just like your dignity, the driver named " + driver_name + " is nowhere to be found on iRacing.")
                        return
                else:
                    iracing_id = int(member)
                    await ctx.respond("Checking iRacing servers for ID: " + member)
                    races_list = await global_vars.ir.last_races_stats(iracing_id)
                    if len(races_list) < 1:
                        await ctx.edit(content="Just like your dignity, the driver with the iRacing ID " + member + " is nowhere to be found on iRacing.")
                        return

                    subsession = await global_vars.ir.subsession_data(races_list[0].subsession_id)
                    for driver in subsession.drivers:
                        if driver.cust_id == int(member):
                            ir_dict[iracing_id] = {}
                            ir_dict[iracing_id]['name'] = driver.display_name
                            ir_dict[iracing_id]['last_known_ir'] = -1
                            ir_dict[iracing_id]['is_respo'] = False
                            ir_dict[iracing_id]['colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]

        else:
            await ctx.respond("Generating iR graph for all Respo members.")
            global_vars.members_locks += 1
            for member in global_vars.members:
                if "iracingCustID" in global_vars.members[member]:
                    ir_dict[global_vars.members[member]["iracingCustID"]] = {}
                    ir_dict[global_vars.members[member]["iracingCustID"]]['name'] = global_vars.members[member]['leaderboardName']
                    ir_dict[global_vars.members[member]["iracingCustID"]]['last_known_ir'] = global_vars.members[member]['last_known_ir']
                    ir_dict[global_vars.members[member]["iracingCustID"]]['is_respo'] = True
                    if 'graph_colour' in global_vars.members[member]:
                        ir_dict[global_vars.members[member]["iracingCustID"]]['colour'] = global_vars.members[member]['graph_colour']
                    else:
                        ir_dict[global_vars.members[member]["iracingCustID"]]['colour'] = [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255]
            global_vars.members_locks -= 1

        if len(ir_dict) < 1:
            await ctx.edit(content="Something went wrong. No one was found and an error wasn't thrown. Deryk sucks at programming.")
            return

        for iracing_id in ir_dict:
            ir_dict[iracing_id]["ir_data"] = []
            if ir_dict[iracing_id]['is_respo'] is not True:
                irating_data = await global_vars.ir.irating(int(iracing_id), pyracingConstants.Category.road.value)

                for point in irating_data.content:
                    ir_dict[iracing_id]["ir_data"].append((point.timestamp, point.value))
            else:
                ir_dict[iracing_id]["ir_data"] = stats.get_ir_data_from_cache(iracing_id, pyracingConstants.Category.road.value)

            if ir_dict[iracing_id]['last_known_ir'] > 0:
                new_tuple = (ir_dict[iracing_id]["ir_data"][-1][0], ir_dict[iracing_id]['last_known_ir'])
                ir_dict[iracing_id]["ir_data"][-1] = new_tuple
            ir_dict[iracing_id]["last_known_ir"] = ir_dict[iracing_id]["ir_data"][-1][1]

        sorted_ir_dict = dict(sorted(ir_dict.items(), key=lambda item: item[1]['last_known_ir'], reverse=True))

        if len(sorted_ir_dict) > 1:
            title_text = "Respo Racing iRating Graph"
            graph = image_gen.generate_ir_graph(sorted_ir_dict, title_text, True)
        else:
            key = list(ir_dict)[0]
            irating = ir_dict[key]['ir_data'][-1][1]
            title_text = "iRating Graph for " + ir_dict[key]['name'] + " (" + str(irating) + ")"
            graph = image_gen.generate_ir_graph(sorted_ir_dict, title_text, False)

        filepath = env.BOT_DIRECTORY + "media/tmp_ir_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

        graph.save(filepath, format=None)

        with open(filepath, "rb") as f_graph:
            picture = discord.File(f_graph)
            await ctx.edit(content='', file=picture)
            picture.close()

        if os.path.exists(filepath):
            os.remove(filepath)

        return

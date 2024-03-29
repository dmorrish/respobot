import io
import random
import discord
from datetime import datetime
from discord.ext import commands
from discord.commands import Option
import constants
import helpers
from slash_command_helpers import SlashCommandHelpers
import image_generators as image_gen
from irslashdata import constants as irConstants
from irslashdata.exceptions import AuthenticationError, ServerDownError
from discord.commands import SlashCommandGroup
from bot_database import BotDatabaseError


class IrCommandsCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    ir_command_group = SlashCommandGroup("ir", "Commands related to iRating.")

    @ir_command_group.command(
        name='graph',
        description=(
            "Graph all Respo Racing members' iRating. Or plot a specific person by name or iRacing ID."
        )
    )
    async def ir_graph(
        self,
        ctx,
        category: Option(
            str,
            "Select a racing category.",
            required=True,
            choices=constants.IRACING_CATEGORIES
        ),
        member: Option(
            str,
            "Plot iRating for a specific person. Can be a Respo member, or by full name or iRacing ID.",
            required=False,
            autocomplete=SlashCommandHelpers.get_member_list
        )
    ):
        try:
            member_dicts = []
            if member is not None:
                member_dict = await self.db.fetch_member_dict(name=member)

                if member_dict:
                    await ctx.respond("Plotting iRating for " + member)

                    if 'graph_colour' not in member_dict:
                        member_dict['graph_colour'] = [
                            random.randint(0, 255),
                            random.randint(0, 255),
                            random.randint(0, 255),
                            255
                        ]

                    member_dicts.append(member_dict)
                else:
                    if not member.isnumeric():
                        driver_name = ""
                        if (member[0] == '"' or member[0] == "“") and (member[-1] == '"' or member[-1] == '”'):
                            # Adding by quoted name. Quoted and unquoted are now functionally
                            # equivalent since I stopped trying to clean up the command input.
                            driver_name = member[1:-1]
                        else:
                            # Adding by unquoted name
                            driver_name = member

                        await ctx.respond("Checking iRacing servers for " + member)

                        driver_dict_list = await self.ir.lookup_drivers(driver_name)

                        driver_found = False
                        for driver_dict in driver_dict_list:
                            if driver_dict['display_name'].lower() == driver_name.lower():
                                member_dict = {}
                                member_dict['name'] = driver_dict['display_name']
                                member_dict['iracing_custid'] = driver_dict['cust_id']
                                member_dict['graph_colour'] = [
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                    random.randint(0, 255),
                                    255
                                ]
                                member_dicts.append(member_dict)
                                driver_found = True
                        if not driver_found:
                            await ctx.edit(
                                content=(
                                    f"Just like your dignity, the driver named {driver_name} "
                                    f"is nowhere to be found on iRacing."
                                )
                            )
                            return
                    else:
                        iracing_custid = int(member)
                        await ctx.respond("Checking iRacing servers for ID: " + member)
                        member_info_dict_list = await self.ir.get_member_info([iracing_custid])
                        if len(member_info_dict_list) < 1:
                            await ctx.edit(
                                content=(
                                    f"Just like your dignity, the driver with the iRacing ID {member} "
                                    f"is nowhere to be found on iRacing."
                                )
                            )
                            return
                        else:
                            member_dict = {}
                            member_dict['name'] = member_info_dict_list[0]['display_name']
                            member_dict['iracing_custid'] = iracing_custid
                            member_dict['graph_colour'] = [
                                random.randint(48, 207),
                                random.randint(48, 207),
                                random.randint(48, 207),
                                255
                            ]
                            member_dicts.append(member_dict)
            else:
                await ctx.respond("Generating iR graph for all Respo members.")

                member_dicts = await self.db.fetch_member_dicts(ignore_smurfs=True)

                if member_dicts is None or len(member_dicts) < 1:
                    await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
                    return

                for member_dict in member_dicts:
                    if 'graph_colour' not in member_dict:
                        member_dict['colour'] = [
                            random.randint(48, 207),
                            random.randint(48, 207),
                            random.randint(48, 207),
                            255
                        ]

            if len(member_dicts) < 1:
                await ctx.edit(
                    content=(
                        "Something went wrong. No one was found and an error "
                        "wasn't thrown. Deryk sucks at programming."
                    )
                )
                return

            category_id = helpers.get_category_from_option(category)
            draw_license_split_line = False
            if (
                category_id == irConstants.Category.road.value
                or category_id == irConstants.Category.sports_car.value
                or category_id == irConstants.Category.formula_car.value
            ):
                draw_license_split_line = True

            for member_dict in member_dicts:
                member_dict['ir_data'] = []
                if 'discord_id' not in member_dict:
                    irating_data = None
                    irating_data2 = None
                    if (
                        category_id == irConstants.Category.road.value
                        or category_id == irConstants.Category.sports_car.value
                        or category_id == irConstants.Category.formula_car.value
                    ):
                        irating_data = await self.ir.chart_data(
                            member_dict['iracing_custid'],
                            category_id=irConstants.Category.road.value,
                            chart_type=1
                        )
                        irating_data_sports = await self.ir.chart_data(
                            member_dict['iracing_custid'],
                            category_id=irConstants.Category.sports_car.value,
                            chart_type=1
                        )
                        irating_data_formula = await self.ir.chart_data(
                            member_dict['iracing_custid'],
                            category_id=irConstants.Category.formula_car.value,
                            chart_type=1
                        )

                        if category_id == irConstants.Category.road.value:
                            irating_data2 = irating_data + irating_data_formula
                            irating_data += irating_data_sports
                            member_dict['ir_data2'] = []
                        elif category_id == irConstants.Category.sports_car:
                            irating_data += irating_data_sports
                        else:
                            irating_data += irating_data_formula
                    else:
                        irating_data = await self.ir.chart_data(
                            member_dict['iracing_custid'],
                            category_id=category_id,
                            chart_type=1
                        )
                    for point_dict in irating_data:
                        time_point = datetime.fromisoformat(point_dict['when'])
                        member_dict['ir_data'].append((time_point, point_dict['value']))
                    if irating_data2 is not None:
                        for point_dict in irating_data2:
                            time_point = datetime.fromisoformat(point_dict['when'])
                            member_dict['ir_data2'].append((time_point, point_dict['value']))
                else:
                    if(category_id == irConstants.Category.road.value):
                        member_dict['ir_data'] = await self.db.get_ir_data(
                            iracing_custid=member_dict['iracing_custid'],
                            category_id=irConstants.Category.sports_car.value
                        )
                        member_dict['ir_data2'] = await self.db.get_ir_data(
                            iracing_custid=member_dict['iracing_custid'],
                            category_id=irConstants.Category.formula_car.value
                        )
                    else:
                        member_dict['ir_data'] = await self.db.get_ir_data(
                            iracing_custid=member_dict['iracing_custid'],
                            category_id=category_id
                        )

            temp_member_dicts = []

            for member_dict in member_dicts:
                if len(member_dict['ir_data']) > 0:
                    temp_member_dicts.append(member_dict)

            sorted_member_dicts = sorted(temp_member_dicts, key=lambda item: item['ir_data'][-1][1], reverse=True)

            if len(sorted_member_dicts) > 1:
                title_text = f"Respo Racing {category} iRating Graph"
                graph = image_gen.generate_ir_graph(
                    sorted_member_dicts,
                    title_text,
                    True,
                    draw_license_split_line=draw_license_split_line
                )
            elif len(sorted_member_dicts) > 0:
                irating = sorted_member_dicts[0]['ir_data'][-1][1]
                if(category_id == irConstants.Category.road.value):
                    title_text = f"{category} iRating Graph for {sorted_member_dicts[0]['name']}"
                else:
                    title_text = f"{category} iRating Graph for {sorted_member_dicts[0]['name']} ({str(irating)})"
                graph = image_gen.generate_ir_graph(
                    sorted_member_dicts,
                    title_text,
                    False,
                    draw_license_split_line=draw_license_split_line
                )
            else:
                if(len(member_dicts) > 1):
                    await ctx.edit(content="No one has at least two races in this category yet.")
                else:
                    await ctx.edit(
                        content=f"{member_dicts[0]['name']} doesn't have at least two races in this category yet."
                    )
                return

            graph_memory_file = io.BytesIO()
            graph.save(graph_memory_file, format='png')
            graph_memory_file.seek(0)

            picture = discord.File(
                graph_memory_file,
                filename=f"RespoIRGraph_{str(datetime.now().strftime('%Y%m%d%H%M%S%f'))}.png"
            )
            await ctx.edit(content='', file=picture)
            graph_memory_file.close()
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

    @ir_command_group.command(
        name='leaderboard',
        description='Show the iRating leaderboard.'
    )
    async def ir_leaderboard(
        self,
        ctx,
        category: Option(
            str,
            "Select a racing category.",
            required=True,
            choices=constants.IRACING_CATEGORIES
        )
    ):
        try:
            await ctx.respond("Generating leaderboard...")

            ir_dict = {}
            pleb_line_printed = False
            response = "```\nNAME                        IR\n"
            response += "--------------------------------\n"
            response += "rEsPo BoT                  " + str(random.randint(12401, 12990)) + "\n"

            member_dicts = await self.db.fetch_member_dicts(ignore_smurfs=True)

            if member_dicts is None or len(member_dicts) < 1:
                await ctx.edit(content="There aren't any members entered into the database yet. Go yell at Deryk.")
                return

            for member_dict in member_dicts:
                latest_road_ir_in_db = await self.db.get_member_ir(
                    member_dict['iracing_custid'],
                    category_id=helpers.get_category_from_option(category),
                )
                if latest_road_ir_in_db is None or latest_road_ir_in_db < 0:
                    continue
                ir_dict[helpers.spongify(member_dict['name'])] = latest_road_ir_in_db

            sorted_ir_dict = dict(sorted(ir_dict.items(), key=lambda item: item[1], reverse=True))

            for key in sorted_ir_dict:
                if (
                    pleb_line_printed is False
                    and sorted_ir_dict[key] is not None
                    and sorted_ir_dict[key] < constants.PLEB_LINE
                ):
                    response += "----------(pleb line)-----------\n"
                    pleb_line_printed = True
                response += key
                for i in range(28 - len(key)):
                    response += " "
                response += str(sorted_ir_dict[key]) + "\n"
            response += "\n```"
            await ctx.edit(content=response)
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

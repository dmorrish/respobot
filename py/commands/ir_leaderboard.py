import random
from discord.ext import commands
import helpers
import global_vars


class IrLeaderboardCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.ir_command_group.command(
        name='leaderboard',
        description='Show the iRating leaderboard.'
    )
    async def ir_leaderboard(
        ctx
    ):
        ir_dict = {}
        pleb_line_printed = False
        response = "```\nNAME                        IR\n"
        response += "--------------------------------\n"
        response += "rEsPo BoT                  " + str(random.randint(12401, 12990)) + "\n"
        list_of_shame = "\n\nThe following asswipes have not done a road race in their previous 10 races: \n"
        list_of_shame_populated = False

        global_vars.members_locks += 1
        for member in global_vars.members:
            if "last_known_ir" in global_vars.members[member]:
                if global_vars.members[member]["last_known_ir"] > 0:
                    ir_dict[helpers.spongify(global_vars.members[member]["leaderboardName"])] = global_vars.members[member]["last_known_ir"]
                else:
                    list_of_shame += global_vars.members[member]['leaderboardName'] + "\n"
                    list_of_shame_populated = True
        global_vars.members_locks -= 1
        sorted_ir_dict = dict(sorted(ir_dict.items(), key=lambda item: item[1], reverse=True))
        for key in sorted_ir_dict:
            if pleb_line_printed is False and sorted_ir_dict[key] < global_vars.pleb_line:
                response += "----------(pleb line)-----------\n"
                pleb_line_printed = True
            response += key
            for i in range(28 - len(key)):
                response += " "
            response += str(sorted_ir_dict[key]) + "\n"
        if list_of_shame_populated is True:
            response += list_of_shame + "."
        response += "\n```"
        await ctx.respond(response)
        return

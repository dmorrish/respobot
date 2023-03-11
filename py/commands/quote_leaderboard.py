from discord.ext import commands
import global_vars


class QuoteLeaderboardCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.quote_command_group.command(
        name='leaderboard',
        description="Show how many times each member has been quoted."
    )
    async def quote_leaderboard(
        ctx
    ):

        quote_count_dict = {}
        global_vars.members_locks += 1
        for member in global_vars.members:
            if 'discordID' in global_vars.members[member] and 'leaderboardName' in global_vars.members[member]:
                if str(global_vars.members[member]['discordID']) in global_vars.quotes:
                    quote_count_dict[global_vars.members[member]['leaderboardName']] = len(global_vars.quotes[str(global_vars.members[member]['discordID'])])
                else:
                    quote_count_dict[global_vars.members[member]['leaderboardName']] = 0
        global_vars.members_locks -= 1

        sorted_quote_count_dict = dict(sorted(quote_count_dict.items(), key=lambda item: item[1], reverse=True))

        response = "```\nNAME                TIMES QUOTED\n"
        response += "--------------------------------\n"

        for member in sorted_quote_count_dict:
            response += member
            for i in range(32 - len(member) - len(str(sorted_quote_count_dict[member]))):
                response += " "
            response += str(sorted_quote_count_dict[member]) + "\n"
        response += "\n```"
        await ctx.respond(response)
        return

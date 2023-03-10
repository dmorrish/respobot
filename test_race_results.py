from discord.ext import commands
from discord.commands import Option
import slash_command_helpers as slash_helpers
import global_vars
import race_results


class TestRaceResultsCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[775866381946060820],
        name="test_race_results",
        description="Display the results for a specific race."
    )
    async def test_race_results(
        self,
        ctx,
        racer: Option(str, "The Respo member.", required=True, autocomplete=slash_helpers.get_member_list),
        subsession_id: Option(int, "The subsession id.", required=True)
    ):

        await ctx.respond("Working on it...")

        member_dict = slash_helpers.get_member_details(racer)
        results_dict = await race_results.get_results_summary(member_dict['iracingCustID'], subsession_id)

        if results_dict is not None:
            await race_results.results.send_results_embed(ctx.channel, results_dict, member_dict)
            await ctx.edit(content="Done!")
        else:
            await ctx.edit(content='Error! This driver was not found in the provided subsession.')
        return

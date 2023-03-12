from discord.ext import commands
from discord.commands import Option
import global_vars
import slash_command_helpers as slash_helpers
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

        member = slash_helpers.get_member_key(racer)

        if 'iracingCustID' in global_vars.members[member]:
            subsession = await global_vars.ir.subsession_data(subsession_id)

        if subsession:
            await race_results.process_race_result(member, subsession)
            await ctx.edit(content='Done!')
        else:
            await ctx.edit(content='Error! This driver was not found in the provided subsession.')
        return

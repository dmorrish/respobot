from discord.ext import commands
from discord.commands import Option
import race_results
import helpers
import slash_command_helpers as slash_helpers


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
        racer: Option(str, "The Respo member to test.", required=True, autocomplete=slash_helpers.get_member_list),
        subsession_id: Option(int, "The subsession id.", required=True),
        embed_type: Option(str, "standard, compact, or auto.", required=False)
    ):

        await ctx.respond("Working on it...")

        # subsession = await global_vars.ir.subsession_data(subsession_id)

        racer_dict = helpers.get_member_dict_from_first_name(racer)

        if "iracingCustID" in racer_dict:
            iracing_id = racer_dict["iracingCustID"]
        else:
            await ctx.respond("This didn't work because I'm an idiot.")
            return

        if embed_type:
            await race_results.process_race_result(iracing_id, subsession_id, embed_type=embed_type)
        else:
            await race_results.process_race_result(iracing_id, subsession_id)
        await ctx.edit(content='Done!')

        return

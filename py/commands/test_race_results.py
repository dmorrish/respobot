from discord.ext import commands
from discord.commands import Option
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
        subsession_id: Option(int, "The subsession id.", required=True),
        embed_type: Option(str, "standard, compact, or auto.", required=False)
    ):

        await ctx.respond("Working on it...")

        # subsession = await global_vars.ir.subsession_data(subsession_id)

        if embed_type:
            await race_results.process_race_result(subsession_id, embed_type=embed_type)
        else:
            await race_results.process_race_result(subsession_id)
        await ctx.edit(content='Done!')

        return

from discord.ext import commands
from discord.commands import Option
import race_results


class TestRaceResultsCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

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

        try:
            subsession_data = await self.ir.subsession_data_new(subsession_id)
            if subsession_data is None or len(subsession_data) < 1:
                await ctx.edit(content="Race not found.")
                return
        except Exception as e:
            print(e.response.url)

        if not embed_type:
            embed_type = 'auto'

        await race_results.generate_race_report(self.bot, self.db, subsession_id, embed_type=embed_type)

        await ctx.edit(content='Done!')

        return

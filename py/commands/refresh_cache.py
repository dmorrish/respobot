from discord.ext import commands
from discord.commands import Option
from discord.errors import HTTPException
import environment_variables as env
import cache_races


class RefreshCacheCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='refresh_cache',
        description="Rebuild the race cache for all users or, optionally, a single user by iRacing ID."
    )
    # @permissions.is_user(173613324666273792)
    async def refresh_cache(
        self,
        ctx,
        iracing_custid: Option(int, "iRacing id.", required=False)
    ):
        if ctx.user.id == 173613324666273792:
            await ctx.respond("Working on it...", ephemeral=True)
            if iracing_custid is None:
                await cache_races.cache_races(self.db, self.ir, await self.db.fetch_iracing_cust_ids())
            else:
                await cache_races.cache_races(self.db, self.ir, [iracing_custid])
            try:
                await ctx.edit(content="Done!")
            except HTTPException:
                # Sometimes caching takes long enough to run that the webhook expires and editing the message fails.
                return
        else:
            await ctx.respond("Sorry, you're not nearly cool enough to do that.", ephemeral=True)

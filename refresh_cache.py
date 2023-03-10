from discord.ext import commands
from discord.commands import Option
import environment_variables as env
import global_vars
import cache_races


class RefreshCacheCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='refresh_cache',
        description="Rebuild the race cache for all users or, optionally, a single user by iRacing ID."
    )
    # @permissions.is_user(173613324666273792)
    async def refresh_cache(
        self,
        ctx,
        iracing_id: Option(int, "iRacing id.", required=False)
    ):
        if ctx.user.id == 173613324666273792:
            await ctx.respond("Working on it...", ephemeral=True)
            if iracing_id is None:

                global_vars.members_locks += 1
                for member in global_vars.members:
                    await cache_races.cache_races(global_vars.members[member]["iracingCustID"])
                global_vars.members_locks -= 1
            else:
                await cache_races.cache_races(iracing_id)
            await ctx.edit(content="Done!")
        else:
            await ctx.respond("Sorry, you're not nearly cool enough to do that.", ephemeral=True)

import random
import discord
from discord.ext import commands
import environment_variables as env
from slash_command_helpers import SlashCommandHelpers


class SendNudesCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        guild_ids=[env.GUILD],
        name='sendnudes',
        description="For when you're feeling lonely."
    )
    async def sendnudes(
        self,
        ctx
    ):
        try:
            filename = f"RespoBot{str(random.randint(0, 6))}.jpeg"
            with open(env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + filename, 'rb') as f_image:
                picture = discord.File(f_image)
                await ctx.respond(file=picture)
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

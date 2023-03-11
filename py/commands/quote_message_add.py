import discord
from discord.ext import commands
import global_vars


class QuoteMessageAddCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(
        name='Add Quote',
        description="Add this message to the Respo Racing quotes database."
    )
    async def quote_add_message_command(
        ctx,
        message: discord.Message
    ):
        if message.author == global_vars.bot.user:
            await ctx.respond("I know you love every little thing that comes out of my mouth, but sorry you can't quote me.", ephemeral=True)
            return

        # Check to see if it's already in there.
        if str(message.author.id) in global_vars.quotes:
            if str(message.id) in global_vars.quotes[str(message.author.id)]:
                await ctx.respond("This quote is already in the database.", ephemeral=True)
                return

        # Only quoting text. I'm not going to write some stupid image handling code.
        if message.content == "" or (len(message.content.split()) == 1 and "http" in message.content):
            await ctx.respond("How about quoting someone that actually said something?", ephemeral=True)
            return

        # Don't quote commands.
        if message.content[0] == "$" or message.content[0] == "!":
            await ctx.respond("Why the fuck would you want to quote a bot command? Yeah, that will _totally_ be hilarious 6 months from now.", ephemeral=True)
            return

        global pendingQuotes
        for pending_quote in pendingQuotes:
            if pendingQuotes[pending_quote] == message.id:
                await ctx.respond("Someone already suggested this, you slow ass.", ephemeral=True)
                return

        # Ok, we're actually going to add this thing.
        quoted_user = await ctx.guild.fetch_member(message.author.id)
        if quoted_user is None:
            quoted_user = message.author
        quote_text = ""
        if(message.reference):
            replied_message = await ctx.fetch_message(message.reference.message_id)
            replied_user = await ctx.guild.fetch_member(replied_message.author.id)
            if replied_user is None:
                replied_user = replied_message.author
            quote_text += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
            quote_text += quoted_user.display_name + ": " + message.content
        else:
            quote_text += "> " + message.content + "\n> - " + quoted_user.display_name
        await ctx.respond("Should the following quote be added?")
        sentMessage = await ctx.channel.send(quote_text)
        await sentMessage.add_reaction('👍')
        pendingQuotes[str(sentMessage.id)] = message.id

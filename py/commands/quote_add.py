from discord.ext import commands
from discord.commands import Option
from discord.errors import NotFound
import global_vars


class QuoteAddCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.quote_command_group.command(
        name="add",
        description="Add a quote to the database by ID or message link."
    )
    async def quote_add(
        ctx,
        message: Option(str, "The ID or the link of the message you wish to quote.", required=True)
    ):
        if message.isnumeric():
            try:
                message_object = await ctx.fetch_message(int(message))
            except NotFound:
                ctx.respond("The message with ID " + message + " was not found.", ephemeral=True)
                return
        elif "https://discord.com/channels/" in message.lower():
            # Adding a quote by link
            message_id_pos = message.rfind("/") + 1
            message_id = int(message[message_id_pos:])
            try:
                message_object = await ctx.fetch_message(message_id)
            except NotFound:
                await ctx.respond("The URL " + message + " doesn't point to a valid message in this channel.", ephemeral=True)
                return
        else:
            await ctx.respond("I'm not Silvia Brown for fuck's sake, I can't read your mind. I need a numeric message ID or a valid message URL in order to find it.")
            return

        if message_object and message_object.author == global_vars.client.user:
            await ctx.respond("I know you love every little thing that comes out of my mouth, but sorry you can't quote me.", ephemeral=True)
            return

        # Check to see if it's already in there.
        if str(message_object.author.id) in global_vars.quotes:
            if str(message_object.id) in global_vars.quotes[str(message_object.author.id)]:
                await ctx.respond("This quote is already in the database.", ephemeral=True)
                return

        # Only quoting text. I'm not going to write some stupid image handling code.
        if message_object.content == "" or (len(message_object.content.split()) == 1 and "http" in message_object.content):
            await ctx.respond("How about quoting someone that actually said something?", ephemeral=True)
            return

        # Don't quote commands.
        if message_object.content[0] == "$" or message_object.content[0] == "!":
            await ctx.respond("Why the fuck would you want to quote a bot command? Yeah, that will _totally_ be hilarious 6 months from now.", ephemeral=True)
            return

        for pending_quote in global_vars.pending_quotes:
            if global_vars.pending_quotes[pending_quote] == message_object.id:
                await ctx.respond("Someone already suggested this, you slow ass.", ephemeral=True)
                return

        # Ok, we're actually going to add this thing.
        quoted_user = await ctx.guild.fetch_member(message_object.author.id)
        if quoted_user is None:
            quoted_user = message_object.author
        quote_text = ""
        if(message_object.reference):
            replied_message = await ctx.fetch_message(message_object.reference.message_id)
            replied_user = await ctx.guild.fetch_member(replied_message.author.id)
            if replied_user is None:
                replied_user = replied_message.author
            quote_text += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
            quote_text += quoted_user.display_name + ": " + message_object.content
        else:
            quote_text += "> " + message_object.content + "\n> - " + quoted_user.display_name
        await ctx.respond("Should the following quote be added?")
        sentMessage = await ctx.channel.send(quote_text)
        await sentMessage.add_reaction('👍')
        global_vars.pending_quotes[str(sentMessage.id)] = message_object.id

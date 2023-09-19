import random
import discord
from discord.ext import commands
from discord.commands import Option
from discord.errors import NotFound
from discord import Message
from slash_command_helpers import SlashCommandHelpers
from discord.commands import SlashCommandGroup
import helpers
from bot_database import BotDatabaseError


class QuoteCommandsCog(commands.Cog):

    def __init__(self, bot, db, ir, bot_state):
        self.bot = bot
        self.db = db
        self.ir = ir
        self.bot_state = bot_state

    quote_command_group = SlashCommandGroup("quote", "Commands related to server quotes.")

    @quote_command_group.command(
        name="add",
        description="Add a quote to the database by ID or message link."
    )
    async def quote_add(
        self,
        ctx,
        message: Option(str, "The ID or the link of the message you wish to quote.", required=True)
    ):
        try:
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
                    await ctx.respond(
                        "The URL " + message + " doesn't point to a valid message in this channel.",
                        ephemeral=True
                    )
                    return
            else:
                await ctx.respond(
                    "I'm not Silvia Brown for fuck's sake, I can't read your mind. "
                    "I need a numeric message ID or a valid message URL in order to find it."
                )
                return

            if message_object is None:
                await ctx.respond("Something went wrong when trying to fetch the message from the Discord server.")
                return

            await self.process_quote_add(ctx, message_object)
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

    @quote_command_group.command(
        name='leaderboard',
        description="Show how many times each member has been quoted."
    )
    async def quote_leaderboard(
        self,
        ctx
    ):
        try:
            quote_leaderboard = await self.db.get_quote_leaderboard()

            response = "```\nNAME                TIMES QUOTED\n"
            response += "--------------------------------\n"

            for member in quote_leaderboard:
                name = member[0]
                quote_count = member[2]
                response += name
                for i in range(32 - len(name) - len(str(quote_count))):
                    response += " "
                response += str(quote_count) + "\n"
            response += "\n```"
            await ctx.respond(response)
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

    @quote_command_group.command(
        name='list',
        description="Show a listing of all the quotes for a member."
    )
    async def quote_list(
        self,
        ctx,
        member: Option(str, "The member to list.", required=True, autocomplete=SlashCommandHelpers.get_member_list)
    ):
        try:
            await ctx.respond("Working on it...", ephemeral=True)
            message_chunks = []

            message_chunk = ""

            member_dict = await self.db.fetch_member_dict(name=member)

            if member_dict is None:
                await ctx.edit(content="Who the fuck is " + member + "?")
                return

            message_chunk = "Here's a summary of all the times " + member + " has been quoted, you creep.\n\n"

            quote_dicts = await self.db.get_quotes(discord_id=member_dict['discord_id'])

            if quote_dicts is None or len(quote_dicts) < 1:
                await ctx.edit(content="No one has quoted " + member + " and that makes me a sad panda :(")
                return

            for quote_dict in quote_dicts:
                new_quote_text = ""
                new_quote_text += f"id: {quote_dict['uid']}\n"
                quote_text = await self.generate_quote_text(ctx, quote_dict)
                new_quote_text += quote_text + "\n\n"

                if len(message_chunk) + len(new_quote_text) > 2000:
                    message_chunks.append(message_chunk)
                    message_chunk = new_quote_text
                else:
                    message_chunk += new_quote_text

            message_chunks.append(message_chunk)

            for message_chunk in message_chunks:
                await ctx.respond(message_chunk, ephemeral=True)
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

    @commands.message_command(
        name='Add Quote',
        description="Add this message to the Respo Racing quotes database."
    )
    async def quote_add_message_command(
        self,
        ctx,
        message: Message
    ):
        try:
            await self.process_quote_add(ctx, message)
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

    @quote_command_group.command(
        name='show',
        description="Show a random quote. Optionally choose a specific member."
    )
    async def quote_show(
        self,
        ctx,
        member: Option(
            str,
            "Quote a specific person.",
            required=False,
            autocomplete=SlashCommandHelpers.get_member_list
        ),
        quote_id: Option(int, "Show a specific quote.", required=False, autocomplete=SlashCommandHelpers.get_quote_ids)
    ):
        try:
            quote_dict = {}
            id_to_quote = None
            if quote_id is not None:
                quote_dicts = await self.db.get_quotes(quote_id=int(quote_id))

                if quote_dicts is None or len(quote_dicts) < 1:
                    await ctx.respond("This quote doesn't exist. Autocomplete is there for a reason...")

                quote_dict = quote_dicts[0]

            else:
                if member is not None:
                    member_dict = await self.db.fetch_member_dict(name=member)
                    if 'discord_id' in member_dict:
                        id_to_quote = member_dict['discord_id']
                    else:
                        await ctx.respond("Who the fuck is " + member + "?", ephemeral=True)
                        return

                if id_to_quote is not None:
                    quote_dicts = await self.db.get_quotes(discord_id=id_to_quote)

                    if quote_dicts is None:
                        await ctx.respond(
                            helpers.spongify("This person has never said anything notable. Not even once."),
                            ephemeral=True
                        )
                        return

                    quote_dict = random.choice(quote_dicts)
                else:
                    # Non-linear selection!
                    # Proportions are doled out as an exponential rising to a final value.
                    # Initial value is 10, final value is 50. Tau (28.85) is selected so that you get
                    # a proportion of 30 when you've been quoted 20 times.
                    leaderboard = await self.db.get_quote_leaderboard()
                    trimmed_leaderboard = []

                    for member_tuple in leaderboard:
                        if member_tuple[2] > 0:
                            trimmed_leaderboard.append(member_tuple)

                    proportions = []
                    for person_tuple in trimmed_leaderboard:
                        proportions.append(int(10.0 + 40.0 * (1.0 - 2.71828**(-float(person_tuple[2]) / 28.85))))

                    # Produce thresholds for the draw based on each person's proportion of the total.
                    thresholds = [proportions[0]]
                    for i in range(1, len(proportions)):
                        thresholds.append(proportions[i] + thresholds[i - 1])

                    # Draw the winning number.
                    pick = random.randint(0, thresholds[-1] - 1)

                    # Determine who won.
                    selected_person = 0
                    for threshold in thresholds:
                        if pick < thresholds[selected_person]:
                            break
                        else:
                            selected_person += 1

                    id_to_quote = trimmed_leaderboard[selected_person][1]
                    quote_dicts = await self.db.get_quotes(id_to_quote)

                    if quote_dicts is None:
                        await ctx.respond(
                            helpers.spongify("This person has never said anything notable. Not even once."),
                            ephemeral=True
                        )
                        return

                    quote_dict = random.choice(quote_dicts)

            quote_text = await self.generate_quote_text(ctx, quote_dict)
            await ctx.respond(quote_text)
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

    async def generate_quote_text(self, ctx: commands.Context, quote_dict: dict):
        try:
            discord_member = await ctx.guild.fetch_member(quote_dict['discord_id'])
        except NotFound:
            discord_member = None

        quoted_name = ""
        replied_to_name = ""

        if discord_member is None:
            quoted_name = quote_dict['name']
        else:
            quoted_name = discord_member.display_name

        if quote_dict['replied_to_quote'] is not None and quote_dict['replied_to_name'] is not None:
            try:
                replied_to_discord_member = await ctx.guild.fetch_member(quote_dict["replied_to_message_id"])
            except NotFound:
                replied_to_discord_member = None
            if replied_to_discord_member is None:
                replied_to_name = quote_dict['replied_to_name']
            else:
                replied_to_name = replied_to_discord_member.display_name

        quote_text = ""
        if quote_dict["replied_to_quote"] is not None:
            quote_text += "> " + replied_to_name + ": " + quote_dict["replied_to_quote"] + "\n> "
            quote_text += quoted_name + ": " + quote_dict["quote"]
        else:
            quote_text += "> " + quote_dict["quote"] + "\n> \\- " + quoted_name

        return quote_text

    async def process_quote_add(self, ctx: commands.Context, message_object: Message):
        try:
            if message_object and message_object.author == self.bot.user:
                await ctx.respond(
                    "I know you love every little thing that comes out of my mouth, but sorry you can't quote me.",
                    ephemeral=True
                )
                return

            if message_object and message_object.author.id == 905283876346265710:
                await ctx.respond(
                    "Fuck that noise. @WhoTheFuckBot has never said a single quotable thing once.",
                    ephemeral=True
                )
                return

            if message_object and message_object.author.id == ctx.author.id:
                await ctx.respond(
                    "Really? You're quoting yourself? That's a little embarrassing, don't you think?",
                    ephemeral=True
                )
                return

            # Check to see if it's already in there.
            if await self.db.is_quote_in_db(message_object.id):
                await ctx.respond("This quote is already in the database.", ephemeral=True)
                return

            # Only quoting text. I'm not going to write some stupid image handling code.
            if (
                message_object.content == ""
                or (len(message_object.content.split()) == 1 and "http" in message_object.content)
            ):
                await ctx.respond("How about quoting someone that actually said something?", ephemeral=True)
                return

            for pending_quote in self.bot_state.data['pending_quotes']:
                if pending_quote['quoted_message_id'] == message_object.id:
                    await ctx.respond("Someone already suggested this, you slow ass.", ephemeral=False)
                    return

            # Ok, we're actually going to add this thing.
            quoted_user = message_object.author
            quote_text = ""
            if(message_object.reference):
                replied_message = await ctx.fetch_message(message_object.reference.message_id)
                replied_user = replied_message.author
                quote_text += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
                quote_text += quoted_user.display_name + ": " + message_object.content
            else:
                quote_text += "> " + message_object.content + "\n> \\- " + quoted_user.display_name
            await ctx.respond("Should the following quote be added?")
            sentMessage = await ctx.channel.send(quote_text)
            await sentMessage.add_reaction('👍')
            new_pending_quote = {
                "vote_message_id": sentMessage.id,
                "quoted_message_id": message_object.id,
                "quote_added_by_id": ctx.author.id,
                "person_quoted_id": message_object.author.id,
                "has_been_voted_by_adder": False,
                "has_been_voted_by_person_quoted": False
            }
            self.bot_state.data['pending_quotes'].append(new_pending_quote)
            self.bot_state.dump_state()
            return
        except BotDatabaseError as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Error interfacing with the database.",
                exc
            )
            return
        except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
            await SlashCommandHelpers.process_command_failure(
                self.bot,
                ctx,
                "Discord error.",
                exc
            )
            return

import random
import discord
from discord.ext import commands
import helpers
from bot_database import BotDatabaseError
from slash_command_helpers import SlashCommandHelpers


class OnReactionAddCog(commands.Cog):

    def __init__(self, bot, db, ir, bot_state):
        self.bot = bot
        self.db = db
        self.ir = ir
        self.bot_state = bot_state

    async def get_reaction(self, payload: discord.RawReactionActionEvent):
        try:
            guild = helpers.fetch_guild(self.bot)
            channel = await guild.fetch_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            for reaction in message.reactions:
                if str(reaction.emoji) == str(payload.emoji):
                    return reaction
            return None
        except discord.HTTPException:
            return None

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        reaction = await self.get_reaction(payload)
        if reaction is None:
            return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        reaction = await self.get_reaction(payload)
        if reaction is None:
            return

        users = await reaction.users().flatten()

        pending_quote = None
        for quote in self.bot_state.data['pending_quotes']:
            if quote["vote_message_id"] == reaction.message.id:
                pending_quote = quote

        if pending_quote is not None and reaction.emoji == '👍':

            quoter_voted = False
            quoted_voted = False
            extra_votes_required = 0
            for user in users:
                if user.id == pending_quote['quote_added_by_id']:
                    quoter_voted = True
                    extra_votes_required += 1
                if user.id == pending_quote['person_quoted_id']:
                    quoted_voted = True
                    # This check is redundant because the bot prevents people from quoting themselves.
                    if pending_quote['person_quoted_id'] != pending_quote['quote_added_by_id']:
                        extra_votes_required += 1

            if pending_quote["has_been_voted_by_person_quoted"] is False and quoted_voted is True:
                pending_quote["has_been_voted_by_person_quoted"] = True
                self.bot_state.dump_state()
                channel = helpers.fetch_channel(self.bot)
                await channel.send(
                    f"<@{user.id}>, maybe we'll let the others decide if the bullshit you spew is quote worthy."
                )
                return

            if pending_quote["has_been_voted_by_adder"] is False and quoter_voted is True:
                pending_quote["has_been_voted_by_adder"] = True
                self.bot_state.dump_state()
                channel = helpers.fetch_channel(self.bot)
                await channel.send(
                    f"<@{user.id}>, the idea is to let *other people* decide if the quote should be added."
                )
                return

            if reaction.count > (1 + extra_votes_required):
                quote_dict = {}

                quoted_message = await reaction.message.channel.fetch_message(pending_quote["quoted_message_id"])
                quoted_user = await quoted_message.guild.fetch_member(quoted_message.author.id)

                if quoted_user is None:
                    quoted_user = quoted_message.author

                quote_dict['discord_id'] = quoted_user.id
                quote_dict['message_id'] = quoted_message.id
                quote_dict['name'] = quoted_user.display_name
                quote_dict['quote'] = quoted_message.content

                if quoted_message.reference:
                    replied_message = await quoted_message.channel.fetch_message(quoted_message.reference.message_id)
                    replied_user = await replied_message.guild.fetch_member(replied_message.author.id)

                    if replied_user is None:
                        replied_user = replied_message.author

                    quote_dict['replied_to_name'] = replied_user.display_name
                    quote_dict['replied_to_quote'] = replied_message.content
                    quote_dict['replied_to_message_id'] = replied_message.id

                try:
                    await self.db.add_quote(quote_dict)
                    await SlashCommandHelpers.refresh_quotes()
                except BotDatabaseError as exc:
                    await helpers.send_bot_failure_dm(
                        self.bot,
                        f"During on_reaction_add() the following exception was encountered: {exc}"
                    )

                self.bot_state.data['pending_quotes'].remove(pending_quote)
                self.bot_state.dump_state()
                await reaction.message.add_reaction('✅')
                await reaction.message.channel.send("New quote added:")
                quote_text = ""
                if "replied_message" in locals():
                    quote_text += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
                    quote_text += quoted_user.display_name + ": " + quoted_message.content
                else:
                    quote_text += "> " + quoted_message.content + "\n> \\- " + quoted_user.display_name
                await reaction.message.channel.send(quote_text)

        elif random.randint(0, 3) == 3:
            if (
                str(reaction.emoji) == "<:KEKLEO:875757285329240114>"
                or str(reaction.emoji) == "<:mike:808815425269137498>"
                or str(reaction.emoji) == "<:humblebrag:893615755424317450>"
                or str(reaction.emoji) == "<a:nonplebbragging:893616042448932875>"
            ):
                await reaction.message.add_reaction(reaction.emoji)

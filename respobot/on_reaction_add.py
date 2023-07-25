import random
from discord.ext import commands


class OnReactionAddCog(commands.Cog):

    def __init__(self, bot, db, ir, bot_state):
        self.bot = bot
        self.db = db
        self.ir = ir
        self.bot_state = bot_state

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        if str(reaction.message.id) in self.bot_state.data['pending_quotes'] and reaction.emoji == '👍' and reaction.count >= 2:
            quote_dict = {}

            quoted_message = await reaction.message.channel.fetch_message(self.bot_state.data['pending_quotes'][str(reaction.message.id)])
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

            await self.db.add_quote(quote_dict)

            del self.bot_state.data['pending_quotes'][str(reaction.message.id)]
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
            if str(reaction.emoji) == "<:KEKLEO:875757285329240114>" or str(reaction.emoji) == "<:mike:808815425269137498>" or str(reaction.emoji) == "<:humblebrag:893615755424317450>" or str(reaction.emoji) == "<a:nonplebbragging:893616042448932875>":
                await reaction.message.add_reaction(reaction.emoji)
import random
import asyncio
from discord.ext import commands
import global_vars


class OnReactionAddCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):

        if str(reaction.message.id) in global_vars.pending_quotes and reaction.emoji == '👍' and reaction.count >= 2:
            quoted_message = await reaction.message.channel.fetch_message(global_vars.pending_quotes[str(reaction.message.id)])
            quoted_user = await quoted_message.guild.fetch_member(quoted_message.author.id)

            if quoted_user is None:
                quoted_user = quoted_message.author

            if quoted_message.reference:
                replied_message = await quoted_message.channel.fetch_message(quoted_message.reference.message_id)
                replied_user = await replied_message.guild.fetch_member(replied_message.author.id)

                if replied_user is None:
                    replied_user = replied_message.author

            if str(quoted_user.id) not in global_vars.quotes:
                global_vars.quotes[str(quoted_user.id)] = {}

            while global_vars.quotes_locks > 0:
                await asyncio.sleep(1)
            global_vars.quotes[str(quoted_user.id)][str(quoted_message.id)] = {"name": quoted_user.display_name, "quote": quoted_message.content}

            if "replied_message" in locals():
                global_vars.quotes[str(quoted_user.id)][str(quoted_message.id)]["replied_to_name"] = replied_user.display_name
                global_vars.quotes[str(quoted_user.id)][str(quoted_message.id)]["replied_to_quote"] = replied_message.content
                global_vars.quotes[str(quoted_user.id)][str(quoted_message.id)]["replied_to_id"] = replied_user.id
            del global_vars.pending_quotes[str(reaction.message.id)]
            await reaction.message.add_reaction('✅')
            await reaction.message.channel.send("New quote added:")
            quote_text = ""
            if "replied_message" in locals():
                quote_text += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
                quote_text += quoted_user.display_name + ": " + quoted_message.content
            else:
                quote_text += "> " + quoted_message.content + "\n> - " + quoted_user.display_name
            await reaction.message.channel.send(quote_text)
            global_vars.dump_json()
        elif random.randint(0, 3) == 3:
            if str(reaction.emoji) == "<:KEKLEO:875757285329240114>" or str(reaction.emoji) == "<:mike:808815425269137498>" or str(reaction.emoji) == "<:humblebrag:893615755424317450>" or str(reaction.emoji) == "<a:nonplebbragging:893616042448932875>":
                await reaction.message.add_reaction(reaction.emoji)

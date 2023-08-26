import random
import discord
from discord.ext import commands
import helpers
import environment_variables as env


class OnMessageCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        elif isinstance(message.channel, discord.DMChannel):
            if message.author.id == 173613324666273792:
                arguments = message.content.split()
                argument_count = len(arguments)

                if argument_count < 1:
                    return

                if arguments[0].lower() == "$puppetmaster":
                    if argument_count > 1:
                        response = message.content[14:]
                        if response != "":
                            channel = helpers.fetch_channel(self.bot)
                            if channel is not None:
                                await channel.send(helpers.spongify(response))
                elif arguments[0].lower() == "$seriouspuppet":
                    if argument_count > 1:
                        response = message.content[15:]
                        if response != "":
                            channel = helpers.fetch_channel(self.bot)
                            if channel is not None:
                                await channel.send(response)

            return
        elif message.channel.guild.id != env.GUILD:
            return

        random_number = random.randint(0, 299)

        if random_number == 34:
            await message.add_reaction(random.choice(message.channel.guild.emojis))

        if "i got wrecked" in message.content.lower() or "i was wrecked" in message.content.lower():
            await message.add_reaction('🇫')

        if "holler" in message.content.lower():
            await message.add_reaction('🥩')

        if "a dime a dozen" in message.content.lower():
            await message.channel.send(
                helpers.spongify("A dime a dozen? Are you talking about your favourite worker's handjob rates?")
            )

        if "speak of the devil" in message.content.lower():
            await message.channel.send(helpers.spongify("Did someone mention me?"))

        if "i need to get over" in message.content.lower():
            await message.channel.send(helpers.spongify(
                "Before you get over that, maybe you should get over yourself.")
            )

        return

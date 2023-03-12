import random
import discord
from discord.ext import commands
import helpers
import environment_variables as env
import global_vars


class OnMessageCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == global_vars.bot.user:
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
                            for guild in global_vars.bot.guilds:
                                if guild.id == env.GUILD:
                                    for channel in guild.channels:
                                        if channel.id == env.CHANNEL:
                                            await channel.send(helpers.spongify(response))
                elif arguments[0].lower() == "$seriouspuppet":
                    if argument_count > 1:
                        response = message.content[15:]
                        if response != "":
                            for guild in global_vars.bot.guilds:
                                if guild.id == env.GUILD:
                                    for channel in guild.channels:
                                        if channel.id == env.CHANNEL:
                                            await channel.send(response)

            return
        elif message.channel.guild.id != env.GUILD:
            return

        random_number = random.randint(0, 299)

        if random_number == 34:
            await message.add_reaction(random.choice(message.channel.guild.emojis))

        if random_number == 69 or random_number == 138 or random_number == 207:
            random_number_2 = random.randint(0, 19)
            if random_number_2 == 0:
                await global_vars.bot.change_presence(activity=discord.Game(name="Daikatana"))
            elif random_number_2 == 1:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Alinity"))
            elif random_number_2 == 2:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Whip It by Devo"))
            elif random_number_2 == 3:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Ghost"))
            elif random_number_2 == 4:
                await global_vars.bot.change_presence(activity=discord.Game(name="Sonic 2006"))
            elif random_number_2 == 5:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Amouranth"))
            elif random_number_2 == 6:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Tainted Love by Soft Cell"))
            elif random_number_2 == 7:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="10 Things I Hate About You"))
            elif random_number_2 == 8:
                await global_vars.bot.change_presence(activity=discord.Game(name="E.T. on Atari"))
            elif random_number_2 == 9:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Mia Malkova"))
            elif random_number_2 == 10:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Blue Monday by New Order"))
            elif random_number_2 == 11:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Gigli"))
            elif random_number_2 == 12:
                await global_vars.bot.change_presence(activity=discord.Game(name="Shaq Fu"))
            elif random_number_2 == 13:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Faith"))
            elif random_number_2 == 14:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="M.E. by Gary Numan"))
            elif random_number_2 == 15:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Sleepless in Seattle"))
            elif random_number_2 == 16:
                await global_vars.bot.change_presence(activity=discord.Game(name="Superman 64"))
            elif random_number_2 == 17:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Leynainu"))
            elif random_number_2 == 18:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="The Safety Dance by Men Without Hats"))
            elif random_number_2 == 19:
                await global_vars.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Bridget Jones's Diary"))

        if "i got wrecked" in message.content.lower() or "i was wrecked" in message.content.lower():
            await message.add_reaction('🇫')

        if "holler" in message.content.lower():
            await message.add_reaction('🥩')

        if "a dime a dozen" in message.content.lower():
            await message.channel.send(helpers.spongify("A dime a dozen? Are you talking about your favourite worker's handjob rates?"))

        if "speak of the devil" in message.content.lower():
            await message.channel.send(helpers.spongify("Did someone mention me?"))

        if "i need to get over" in message.content.lower():
            await message.channel.send(helpers.spongify("Before you get over that, maybe you should get over yourself."))

        return

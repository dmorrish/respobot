import discord
import environment_variables as env
import json

members = None
sass_talk = None
quotes = None
series_info = None
race_cache = None
hosted_cache = None
ir = None

intents = discord.Intents.all()
intents.message_content = True

bot = discord.Bot(intents=intents)
quote_command_group = bot.create_group("quote", "Commands related to server quotes.", [env.GUILD])
ir_command_group = bot.create_group("ir", "Commands related to iRating.", [env.GUILD])

members_locks = 0
race_cache_locks = 0
quotes_locks = 0

pleb_line = 2500

pending_quotes = {}


def load_json():
    with open(env.BOT_DIRECTORY + "json/members.json", "r") as f_members:
        global members
        members = json.load(f_members)

    with open(env.BOT_DIRECTORY + "json/sass_talk.json", "r") as f_sass_talk:
        global sass_talk
        sass_talk = json.load(f_sass_talk)

    with open(env.BOT_DIRECTORY + "json/quotes.json", "r") as f_quotes:
        global quotes
        quotes = json.load(f_quotes)

    with open(env.BOT_DIRECTORY + "json/series_info.json", "r") as f_series_info:
        global series_info
        series_info = json.load(f_series_info)

    with open(env.BOT_DIRECTORY + "json/race_cache.json", "r") as f_race_cache:
        global race_cache
        race_cache = json.load(f_race_cache)

    with open(env.BOT_DIRECTORY + "json/hosted_cache.json", "r") as f_hosted_cache:
        global hosted_cache
        hosted_cache = json.load(f_hosted_cache)


def dump_json():
    with open(env.BOT_DIRECTORY + "json/members.json", "w") as f_members:
        json.dump(members, f_members, indent=4)

    with open(env.BOT_DIRECTORY + "json/quotes.json", "w") as f_quotes:
        json.dump(quotes, f_quotes, indent=4)

    with open(env.BOT_DIRECTORY + "json/race_cache.json", "w") as f_race_cache:
        json.dump(race_cache, f_race_cache, indent=4)

    with open(env.BOT_DIRECTORY + "json/hosted_cache.json", "w") as f_hosted_cache:
        json.dump(hosted_cache, f_hosted_cache, indent=4)

    with open(env.BOT_DIRECTORY + "json/series_info.json", "w") as f_series_info:
        json.dump(series_info, f_series_info, indent=4)

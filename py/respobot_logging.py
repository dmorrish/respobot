import logging
import environment_variables as env

logger_discord = logging.getLogger('discord')
logger_discord.propagate = False
logger_discord.setLevel(logging.INFO)
handler = logging.FileHandler(filename=env.BOT_DIRECTORY + 'log/discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger_discord.addHandler(handler)

logger_pyracing = logging.getLogger('pyracing')
logger_pyracing.propagate = False
logger_pyracing.setLevel(logging.INFO)
handler2 = logging.FileHandler(filename=env.BOT_DIRECTORY + 'log/pyracing.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger_pyracing.addHandler(handler2)

logger_respobot = logging.getLogger('respobot')
logger_respobot.propagate = False
logger_respobot.setLevel(logging.INFO)
handler3 = logging.FileHandler(filename=env.BOT_DIRECTORY + 'log/respobot.log', encoding='utf-8', mode='a')
handler3.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger_respobot.addHandler(handler3)

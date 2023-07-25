import logging
from logging.handlers import SocketHandler
import environment_variables as env
import os

# Init data folder if does not exist.
if not os.path.exists(env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY):
    os.mkdir(env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY)

file_handler_formatter = logging.Formatter(
    '{'
    '+*!*+args+*!*+: +*!*+%(args)s+*!*+, '
    '+*!*+created+*!*+: %(created)f, '
    '+*!*+exc_text+*!*+: +*!*+%(exc_text)s+*!*+, '
    '+*!*+filename+*!*+: +*!*+%(filename)s+*!*+, '
    '+*!*+funcName+*!*+: +*!*+%(funcName)s+*!*+, '
    '+*!*+levelname+*!*+: +*!*+%(levelname)s+*!*+, '
    '+*!*+levelno+*!*+: %(levelno)d, '
    '+*!*+lineno+*!*+: %(lineno)d, '
    '+*!*+module+*!*+: +*!*+%(module)s+*!*+, '
    '+*!*+msecs+*!*+: %(msecs)d, '
    '+*!*+msg+*!*+: +*!*+%(message)s+*!*+, '
    '+*!*+name+*!*+: +*!*+%(name)s+*!*+, '
    '+*!*+pathname+*!*+: +*!*+%(pathname)s+*!*+, '
    '+*!*+process+*!*+: %(process)d, '
    '+*!*+processName+*!*+: +*!*+%(processName)s+*!*+, '
    '+*!*+relativeCreated+*!*+: %(relativeCreated)d, '
    '+*!*+stack_info+*!*+: +*!*+%(stack_info)s+*!*+, '
    '+*!*+thread+*!*+: %(thread)d, '
    '+*!*+threadName+*!*+: +*!*+%(threadName)s+*!*+'
    '},')

logger_discord = logging.getLogger('discord')
logger_discord.propagate = False
logger_discord.setLevel(logging.DEBUG)
file_handler_discord = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'discord.log', encoding='utf-8', mode='a')
file_handler_discord.setFormatter(file_handler_formatter)
logger_discord.addHandler(file_handler_discord)
socket_handler = SocketHandler('192.168.1.43', 19996)  # default listening address
logger_discord.addHandler(socket_handler)

logger_pyracing = logging.getLogger('pyracing')
logger_pyracing.propagate = False
logger_pyracing.setLevel(logging.DEBUG)
file_handler_pyracing = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'pyracing.log', encoding='utf-8', mode='a')
file_handler_pyracing.setFormatter(file_handler_formatter)
logger_pyracing.addHandler(file_handler_pyracing)
logger_pyracing.addHandler(socket_handler)

logger_respobot = logging.getLogger('respobot')
logger_respobot.propagate = False
logger_respobot.setLevel(logging.DEBUG)
file_handler_respobot = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'respobot.log', encoding='utf-8', mode='a')
file_handler_respobot.setFormatter(file_handler_formatter)
logger_respobot.addHandler(file_handler_respobot)
logger_respobot.addHandler(socket_handler)
logger_respobot_commands = logger_respobot.getChild('commands')
logger_respobot_commands.propagate = False
logger_respobot_commands.addHandler(file_handler_respobot)
logger_respobot_commands.addHandler(socket_handler)
logger_respobot_database = logger_respobot.getChild('database')
logger_respobot_database.propagate = False
logger_respobot_database.addHandler(file_handler_respobot)
logger_respobot_database.addHandler(socket_handler)
logger_respobot_iracing = logger_respobot.getChild('iracing')
logger_respobot_iracing.propagate = False
logger_respobot_iracing.addHandler(file_handler_respobot)
logger_respobot_iracing.addHandler(socket_handler)
logger_respobot_bot = logger_respobot.getChild('bot')
logger_respobot_bot.propagate = False
logger_respobot_bot.addHandler(file_handler_respobot)
logger_respobot_bot.addHandler(socket_handler)

import logging
import environment_variables as env
import os

# Init data folder if does not exist.
if not os.path.exists(env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY):
    os.mkdir(env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY)

logger_discord = logging.getLogger('discord')
logger_discord.propagate = False
logger_discord.setLevel(logging.INFO)
handler = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'discord.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('{"args": "%(args)s", "created": %(created)f, "exc_text": "", "filename": "%(filename)s", "funcName": "%(funcName)s", "levelname": "%(levelname)s", "levelno": %(levelno)d, "lineno": %(lineno)d, "module": "%(module)s", "msecs": %(msecs)d, "msg": "%(message)s", "name": "%(name)s", "pathname": "", "process": %(process)d, "processName": "%(processName)s", "relativeCreated": %(relativeCreated)d, "stack_info": "%(stack_info)s", "thread": %(thread)d, "threadName": "%(threadName)s", "extra_column": ""},'))
logger_discord.addHandler(handler)

logger_pyracing = logging.getLogger('pyracing')
logger_pyracing.propagate = False
logger_pyracing.setLevel(logging.INFO)
handler2 = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'pyracing.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter('{"args": "%(args)s", "created": %(created)f, "exc_text": "", "filename": "%(filename)s", "funcName": "%(funcName)s", "levelname": "%(levelname)s", "levelno": %(levelno)d, "lineno": %(lineno)d, "module": "%(module)s", "msecs": %(msecs)d, "msg": "%(message)s", "name": "%(name)s", "pathname": "", "process": %(process)d, "processName": "%(processName)s", "relativeCreated": %(relativeCreated)d, "stack_info": "%(stack_info)s", "thread": %(thread)d, "threadName": "%(threadName)s", "extra_column": ""},'))
logger_pyracing.addHandler(handler2)

logger_respobot = logging.getLogger('respobot')
logger_respobot.propagate = False
logger_respobot.setLevel(logging.INFO)
handler3 = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'respobot.log', encoding='utf-8', mode='a')
handler3.setFormatter(logging.Formatter('{"args": "%(args)s", "created": %(created)f, "exc_text": "", "filename": "%(filename)s", "funcName": "%(funcName)s", "levelname": "%(levelname)s", "levelno": %(levelno)d, "lineno": %(lineno)d, "module": "%(module)s", "msecs": %(msecs)d, "msg": "%(message)s", "name": "%(name)s", "pathname": "", "process": %(process)d, "processName": "%(processName)s", "relativeCreated": %(relativeCreated)d, "stack_info": "%(stack_info)s", "thread": %(thread)d, "threadName": "%(threadName)s", "extra_column": ""},'))
logger_respobot.addHandler(handler3)

logger_test = logging.getLogger('logtest')
logger_test.propagate = False
logger_test.setLevel(logging.INFO)
handler4 = logging.FileHandler(filename=env.BOT_DIRECTORY + env.LOG_SUBDIRECTORY + 'logtest.log', encoding='utf-8', mode='a')
handler4.setFormatter(logging.Formatter('{"args": "%(args)s", "created": %(created)f, "exc_text": "", "filename": "%(filename)s", "funcName": "%(funcName)s", "levelname": "%(levelname)s", "levelno": %(levelno)d, "lineno": %(lineno)d, "module": "%(module)s", "msecs": %(msecs)d, "msg": "%(message)s", "name": "%(name)s", "pathname": "", "process": %(process)d, "processName": "%(processName)s", "relativeCreated": %(relativeCreated)d, "stack_info": "%(stack_info)s", "thread": %(thread)d, "threadName": "%(threadName)s", "extra_column": ""},'))
logger_test.addHandler(handler4)

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
IRACING_USERNAME = os.getenv('IRACING_USERNAME')
IRACING_PASSWORD = os.getenv('IRACING_PASSWORD')
BOT_DIRECTORY = os.getenv('BOT_DIRECTORY')
DATA_SUBDIRECTORY = os.getenv('DATA_SUBDIRECTORY')
LOG_SUBDIRECTORY = os.getenv('LOG_SUBDIRECTORY')
ROLE_GOD = int(os.getenv('ROLE_GOD'))
ROLE_PLEB = int(os.getenv('ROLE_PLEB'))
IS_PRODUCTION = os.getenv('IS_PRODUCTION')
SUPPRESS_RACE_RESULTS = os.getenv('SUPPRESS_RACE_RESULTS')
DATABASE_FILENAME = os.getenv('DATABASE_FILENAME')
BOT_STATE_FILENAME = os.getenv('BOT_STATE_FILENAME')

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
ADMIN_ID = int(os.getenv('ADMIN_ID'))
IRACING_USERNAME = os.getenv('IRACING_USERNAME')
IRACING_PASSWORD = os.getenv('IRACING_PASSWORD')
BOT_DIRECTORY = os.getenv('BOT_DIRECTORY')
DATA_SUBDIRECTORY = os.getenv('DATA_SUBDIRECTORY')
MEDIA_SUBDIRECTORY = os.getenv('MEDIA_SUBDIRECTORY')
LOG_SUBDIRECTORY = os.getenv('LOG_SUBDIRECTORY')
ROLE_GOD = int(os.getenv('ROLE_GOD'))
ROLE_PLEB = int(os.getenv('ROLE_PLEB'))
SUPPRESS_RACE_RESULTS = True if os.getenv('SUPPRESS_RACE_RESULTS').lower() == "true" else False
IS_DEV_INSTANCE = True if os.getenv('IS_DEV_INSTANCE').lower() == "true" else False
DATABASE_FILENAME = os.getenv('DATABASE_FILENAME')
BOT_STATE_FILENAME = os.getenv('BOT_STATE_FILENAME')
LOG_SERVER_ADDRESS = os.getenv('LOG_SERVER_ADDRESS')
LOG_SERVER_PORT = os.getenv('LOG_SERVER_PORT')
OPEN_AI_TOKEN = os.getenv('OPEN_AI_TOKEN')

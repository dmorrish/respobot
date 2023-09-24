import environment_variables as env
import logging
import json
from json.decoder import JSONDecodeError


class BotState:
    def __init__(self, filepath):
        self.filepath = filepath
        self.write_lock = False
        self.data = {}
        self.load_state()

    def load_state(self):
        try:
            with open(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.BOT_STATE_FILENAME, "r") as f_bot_state:
                try:
                    self.data = json.load(f_bot_state)
                    logging.getLogger('respobot.bot').info(
                        f"Successfully loaded {env.BOT_STATE_FILENAME} as "
                        f"{json.dumps(self.data)}"
                    )

                except JSONDecodeError:
                    logging.getLogger('respobot.bot').error(
                        f"{env.BOT_STATE_FILENAME} did not contain valid JSON data, initializing as {{}}"
                    )
                    self.data = {}
        except FileNotFoundError:
            logging.getLogger('respobot.bot').error("bot_state.json does not exist, initializing as {}")
            self.data = {}

        if 'last_weekly_report_week' not in self.data:
            logging.getLogger('respobot.bot').info("'last_weekly_report_week' missing from bot_state, setting to -1.")
            self.data['last_weekly_report_week'] = -1
            self.dump_state()

        if 'pending_quotes' not in self.data:
            logging.getLogger('respobot.bot').info("'pending_quotes' missing from bot_state, setting to {}.")
            self.data['pending_quotes'] = []
            self.dump_state()

        if 'anniversary_flip_flop' not in self.data:
            logging.getLogger('respobot.bot').info("'anniversary_flip_flop' missing from bot_state, setting to True.")
            self.data['anniversary_flip_flop'] = True
            self.dump_state()

        if 'server_icon_angle' not in self.data:
            logging.getLogger('respobot.bot').info("'server_icon_angle' missing from bot_state, setting to 0.")
            self.data['server_icon_angle'] = 0
            self.dump_state()

    def dump_state(self):
        self.write_lock = True
        with open(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.BOT_STATE_FILENAME, "w") as f_bot_state:
            json.dump(self.data, f_bot_state, indent=4)
        self.write_lock = False

    def is_write_locked(self):
        return self.write_lock

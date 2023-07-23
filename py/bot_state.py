import environment_variables as env
import respobot_logging as log
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
                except JSONDecodeError:
                    log.logger_respobot.error("bot_state.json did not contain valid JSON data, initializing as {}")
                    self.data = {}
        except FileNotFoundError:
            log.logger_respobot.error("bot_state.json does not exist, initializing as {}")
            self.data = {}

        if 'last_weekly_report_week' not in self.data:
            log.logger_respobot.info("'last_weekly_report_week' missing from bot_state, setting to -1.")
            self.data['last_weekly_report_week'] = -1
            self.dump_state()

        if 'pending_quotes' not in self.data:
            log.logger_respobot.info("'pending_quotes' missing from bot_state, setting to {}.")
            self.data['pending_quotes'] = {}
            self.dump_state()

        if 'birthday_flip_flop' not in self.data:
            log.logger_respobot.info("'birthday_flip_flop' missing from bot_state, setting to True.")
            self.data['birthday_flip_flop'] = True
            self.dump_state()

    def dump_state(self):
        self.write_lock = True
        with open(env.BOT_DIRECTORY + "json/bot_state.json", "w") as f_bot_state:
            json.dump(self.data, f_bot_state, indent=4)
        self.write_lock = False

    def is_write_locked(self):
        return self.write_lock

import logging
import discord
import constants
from bot_database import BotDatabase, BotDatabaseError


class SeasonStringError(Exception):
    """Raised when someone enters an invalid season string."""

    def __init__(self, message):
        super(SeasonStringError, self).__init__(message)


class SlashCommandHelpers:
    db = None
    member_name_list = []
    admin_member_name_list = []
    iracing_season_strings = []
    iracing_series_dict = {}
    current_season_string = ""
    quote_ids = []

    @classmethod
    async def init(self, db: BotDatabase):
        self.db = db
        await self.refresh_series()
        await self.refresh_quotes()
        await self.refresh_members()

    @classmethod
    async def refresh_quotes(self):
        new_quote_ids = await self.db.get_quote_ids()
        self.quote_ids = []
        for quote_id in new_quote_ids:
            self.quote_ids.append(str(quote_id))

    @classmethod
    async def refresh_members(self):
        new_member_name_list = []
        new_admin_member_name_list = []

        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is not None and len(member_dicts) > 0:
            for member_dict in member_dicts:
                new_member_name_list.append(member_dict['name'])
                new_admin_member_name_list.append(f"{member_dict['uid']} : {member_dict['name']}")

            split_list = []
            for name in new_member_name_list:
                split_list.append(name.split())

            admin_split_list = []
            for name in new_admin_member_name_list:
                admin_split_list.append(name.split())

            new_member_name_list = []
            new_admin_member_name_list = []

            for name in sorted(split_list, key=lambda x: x[-1]):
                new_member_name_list.append(' '.join(name))

            for name in sorted(admin_split_list, key=lambda x: x[-1]):
                new_admin_member_name_list.append(' '.join(name))

        self.member_name_list = new_member_name_list
        self.admin_member_name_list = new_admin_member_name_list

    @classmethod
    async def refresh_series(self):
        new_iracing_season_strings = []
        (year, quarter, _, _, _) = await self.db.get_current_iracing_week()
        new_current_season_string = str(year) + 's' + str(quarter)
        if year is not None and quarter is not None:
            while (
                year > constants.IRACING_FIRST_YEAR
                or (year == constants.IRACING_FIRST_YEAR and quarter >= constants.IRACING_FIRST_QUARTER)
            ):
                season_string = str(year) + 's' + str(quarter)
                new_iracing_season_strings.append(season_string)

                quarter -= 1

                if quarter < 1:
                    quarter = 4
                    year -= 1

        new_iracing_series_dict = {}
        new_iracing_series_dict['all_series'] = []

        series_tuples = await self.db.get_all_series()

        for series_tuple in series_tuples:
            new_series_dict = {
                "series_id": series_tuple["series_id"],
                "series_name": series_tuple["series_name"]
            }
            new_iracing_series_dict['all_series'].append(new_series_dict)

        if new_iracing_season_strings is not None and len(new_iracing_season_strings) > 0:
            for season in new_iracing_season_strings:
                (season_year, season_quarter) = self.parse_season_string(season)

                new_iracing_series_dict[season] = {}
                new_iracing_series_dict[season]['season_name_strings'] = []
                new_iracing_series_dict[season]['season_class_dict'] = {}

                series_info_tuples = await self.db.get_season_basic_info(
                    season_year=season_year,
                    season_quarter=season_quarter
                )
                car_class_tuples = await self.db.get_season_car_classes(
                    season_year=season_year,
                    season_quarter=season_quarter
                )

                if series_info_tuples is not None and len(series_info_tuples) > 0:
                    for series_info_tuple in series_info_tuples:
                        season_id = series_info_tuple[0]
                        season_name = series_info_tuple[2]
                        new_iracing_series_dict[season]['season_name_strings'].append(season_name)
                        new_iracing_series_dict[season]['season_class_dict'][season_name] = []

                        for car_class_tuple in car_class_tuples:
                            car_class_season_id = car_class_tuple[0]
                            car_class_short_name = car_class_tuple[2]

                            if car_class_season_id == season_id:
                                new_iracing_series_dict[season]['season_class_dict'][season_name].append(
                                    car_class_short_name
                                )

        self.current_season_string = new_current_season_string
        self.iracing_season_strings = new_iracing_season_strings
        self.iracing_series_dict = new_iracing_series_dict

    @classmethod
    def parse_season_string(self, season_string):
        current_year = None
        current_quarter = None
        if self.current_season_string != "":
            current_year = int(self.current_season_string[0:4])
            current_quarter = int(self.current_season_string[-1])
        tmp = season_string[0:4]

        if tmp.isnumeric():
            selected_year = int(tmp)
        else:
            raise SeasonStringError(
                "The first four characters of the season field must be numbers representing the season year."
            )

        tmp = season_string[-1]
        if tmp.isnumeric():
            selected_quarter = int(tmp)
        else:
            raise SeasonStringError(
                "The last character of the season field must be a number representing the "
                "season quarter: 1, 2, 3, or 4."
            )

        if selected_quarter > 4 or selected_quarter < 1:
            raise SeasonStringError("Valid quarters are 1, 2, 3, or 4.")
        if (
            current_year is not None
            and current_quarter is not None
            and (
                selected_year > current_year
                or (selected_year == current_year and selected_quarter > current_quarter)
            )
        ):
            raise SeasonStringError("Selected season is in the future.")
        if (
            selected_year < constants.IRACING_FIRST_YEAR
            or (selected_year == constants.IRACING_FIRST_YEAR and selected_quarter < constants.IRACING_FIRST_QUARTER)
        ):
            raise SeasonStringError(
                f"Selected season is before the very first iRacing season, "
                f"{constants.IRACING_FIRST_YEAR}s{constants.IRACING_FIRST_QUARTER}."
            )

        return (selected_year, selected_quarter)

    @classmethod
    def get_current_season(self):
        return self.parse_season_string(self.current_season_string)

    @classmethod
    def get_member_list(self, ctx: discord.AutocompleteContext):
        return [
            member_string for member_string in self.member_name_list if (
                member_string.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    def get_admin_member_list(self, ctx: discord.AutocompleteContext):
        return [
            member_string for member_string in self.admin_member_name_list if (
                member_string.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    async def get_iracing_seasons(self, ctx: discord.AutocompleteContext):
        return [
            season for season in self.iracing_season_strings if (
                season.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    def get_series_list(self, ctx: discord.AutocompleteContext):

        if 'season' in ctx.options:
            if ctx.options['season'] not in self.iracing_season_strings:
                return["Invalid season entered. Please go back and correct it."]
            season_selected = ctx.options['season']
        else:
            if ctx.command.name == 'champ':
                return ["Please select a season first."]
            season_selected = self.current_season_string

        if season_selected not in self.iracing_series_dict:
            return ["Selected season not found in the series list. Let Deryk know because it means he sucks."]

        series_keyword_list = self.iracing_series_dict[season_selected]['season_name_strings']

        if ctx.command.name == 'champ':
            series_keyword_list = [constants.RESPO_SERIES_NAME] + series_keyword_list

        return [
            series for series in series_keyword_list if (
                series.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    def get_all_series_list(self, ctx: discord.AutocompleteContext):

        series_keyword_list = [
            f"{series['series_name']} ({series['series_id']})" for series in self.iracing_series_dict['all_series']
        ]

        return [
            series_keyword for series_keyword in series_keyword_list if (
                series_keyword.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    async def get_series_classes(self, ctx: discord.AutocompleteContext):
        if 'season' in ctx.options:
            season_selected = ctx.options['season']
        else:
            season_selected = self.current_season_string

        if 'series' in ctx.options:
            series_selected = ctx.options['series']
        else:
            series_selected = None

        if season_selected is None or season_selected == '':
            season_selected = self.current_season_string
        else:
            if season_selected not in self.iracing_series_dict:
                return ["Selected season not found in the series list. Let Deryk know because it means he sucks."]

        if series_selected is None or series_selected == '':
            return ["Please slect a series first."]

        if series_selected == constants.RESPO_SERIES_NAME:
            return ["Literally any fucking car at all."]

        series_classes_dict = self.iracing_series_dict[season_selected]['season_class_dict'][series_selected]

        return [
            class_name for class_name in series_classes_dict if (
                class_name.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    async def get_quote_ids(self, ctx: discord.AutocompleteContext):
        return [
            quote_id for quote_id in self.quote_ids if (
                quote_id.lower().find(ctx.value.lower()) > -1
                or ctx.value == ''
                or ctx.value is None
            )
        ]

    @classmethod
    async def get_special_events(self, ctx: discord.AutocompleteContext):
        try:
            event_dicts = await self.db.get_special_events()

            if event_dicts is None or len(event_dicts) < 1:
                return ["No special events found in the database."]

            event_list = []
            for event_dict in event_dicts:
                if 'uid' in event_dict and 'name' in event_dict and 'start_date' in event_dict:
                    event_list.append(f"{event_dict['uid']} : {event_dict['start_date']} - {event_dict['name']}")
            return [
                event_name for event_name in event_list if (
                    event_name.lower().find(ctx.value.lower()) > -1
                    or ctx.value == ''
                    or ctx.value is None
                )
            ]

        except BotDatabaseError as exc:
            logging.getLogger('respobot.database').warning(
                f"The following error occured when trying to add the special event to the database: {exc}"
            )
            return ["Database error when fetching special events."]

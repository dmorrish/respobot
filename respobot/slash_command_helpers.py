import discord
import constants
from bot_database import BotDatabase


class SeasonStringError(Exception):
    """Raised when someone enters an invalid season string."""

    def __init__(self, message):
        super(SeasonStringError, self).__init__(message)


class SlashCommandHelpers:
    db = None
    member_name_list = []
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
        self.quote_ids = []
        new_quote_ids = await self.db.get_quote_ids()
        for quote_id in new_quote_ids:
            self.quote_ids.append(str(quote_id))

    @classmethod
    async def refresh_members(self):
        new_member_name_list = []

        member_dicts = await self.db.fetch_member_dicts()

        if member_dicts is not None and len(member_dicts) > 0:
            for member_dict in member_dicts:
                new_member_name_list.append(member_dict['name'].split()[0])

            new_member_name_list.sort()

        self.member_name_list = new_member_name_list

    @classmethod
    async def refresh_series(self):
        new_iracing_season_strings = []
        (year, quarter, _, _, _) = await self.db.get_current_iracing_week()
        new_current_season_string = str(year) + 's' + str(quarter)
        if year is not None and quarter is not None:
            while year > constants.iracing_first_year or year == constants.iracing_first_year and quarter >= constants.iracing_first_quarter:
                season_string = str(year) + 's' + str(quarter)
                new_iracing_season_strings.append(season_string)

                quarter -= 1

                if quarter < 1:
                    quarter = 4
                    year -= 1

        new_iracing_series_dict = {}

        if new_iracing_season_strings is not None and len(new_iracing_season_strings) > 0:
            for season in new_iracing_season_strings:
                (season_year, season_quarter) = self.parse_season_string(season)

                new_iracing_series_dict[season] = {}
                new_iracing_series_dict[season]['season_name_strings'] = []
                new_iracing_series_dict[season]['season_class_dict'] = {}

                series_info_tuples = await self.db.get_season_basic_info(season_year=season_year, season_quarter=season_quarter)
                car_class_tuples = await self.db.get_season_car_classes_for_all_series(season_year, season_quarter)

                if series_info_tuples is not None and len(series_info_tuples) > 0:
                    for series_info_tuple in series_info_tuples:
                        series_name = series_info_tuple[2]
                        new_iracing_series_dict[season]['season_name_strings'].append(series_name)
                        new_iracing_series_dict[season]['season_class_dict'][series_name] = []
                        # series_id = await self.db.get_series_id_from_season_name(series_name, season_year=season_year, season_quarter=season_quarter)
                        # season_id = await self.db.get_season_id(series_id, season_year, season_quarter)
                        season_id = series_info_tuple[0]

                        for car_class_tuple in car_class_tuples:
                            car_class_season_id = car_class_tuple[0]
                            car_class_short_name = car_class_tuple[2]

                            if car_class_season_id == season_id:
                                new_iracing_series_dict[season]['season_class_dict'][series_name].append(car_class_short_name)

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
            raise SeasonStringError("The first four characters of the season field must be numbers representing the season year.")

        tmp = season_string[-1]
        if tmp.isnumeric():
            selected_quarter = int(tmp)
        else:
            raise SeasonStringError("The last character of the season field must be a number representing the season quarter: 1, 2, 3, or 4.")

        if selected_quarter > 4 or selected_quarter < 1:
            raise SeasonStringError("Valid quarters are 1, 2, 3, or 4.")
        if current_year is not None and current_quarter is not None and (selected_year > current_year or (selected_year == current_year and selected_quarter > current_quarter)):
            raise SeasonStringError("Selected season is in the future.")
        if selected_year < constants.iracing_first_year or (selected_year == constants.iracing_first_year and selected_quarter < constants.iracing_first_quarter):
            raise SeasonStringError(f"Selected season is before the very first iRacing season, {constants.iracing_first_year}s{constants.iracing_first_quarter}.")

        return (selected_year, selected_quarter)

    @classmethod
    def get_member_list(self, ctx: discord.AutocompleteContext):
        return [member_string for member_string in self.member_name_list if member_string.lower().startswith(ctx.value.lower())]

    @classmethod
    async def get_iracing_seasons(self, ctx: discord.AutocompleteContext):
        return [season for season in self.iracing_season_strings if season.startswith(ctx.value.lower())]

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
            series_keyword_list = [constants.respo_series_name] + series_keyword_list

        return [series for series in series_keyword_list if (series.lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]

    @classmethod
    async def get_series_classes(self, ctx: discord.AutocompleteContext):
        if 'season' in ctx.options:
            season_selected = ctx.options['season']
        else:
            season_selected = None

        if 'series' in ctx.options:
            series_selected = ctx.options['series']
        else:
            series_selected = None

        if season_selected is None or season_selected == '' or series_selected is None or series_selected == '':
            return ["Please slect a season and series first."]

        if season_selected not in self.iracing_series_dict:
            return ["Selected season not found in the series list. Let Deryk know because it means he sucks."]

        if series_selected == constants.respo_series_name:
            return ["Literally any fucking car at all."]

        return [class_name for class_name in self.iracing_series_dict[season_selected]['season_class_dict'][series_selected] if (class_name.lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]

    @classmethod
    async def get_quote_ids(self, ctx: discord.AutocompleteContext):
        return [x for x in self.quote_ids if (x.lower().find(ctx.value.lower()) > -1 or ctx.value == '' or ctx.value is None)]

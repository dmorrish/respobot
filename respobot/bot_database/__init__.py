# import respobot_logging as log
import logging
import aiosqlite
from aiosqlite import Error, OperationalError
from ._queries import *
from enum import Enum


class ErrorCodes(Enum):
    """Defined error codes for BotDatabaseError."""
    insert_collision = 100
    insufficient_info = 101
    general_failure = 102
    value_error = 103
    max_retries_exceeded = 104


class BotDatabaseError(Exception):
    """Raised when there is any issue communicating with the database."""

    error_code = None

    def __init__(self, message, error_code: int = None):
        self.error_code = error_code
        super(BotDatabaseError, self).__init__(message)


class BotDatabase:
    """Class for interfacing with the RespoBot database."""

    def __init__(self, filename, max_retries: int = 0):
        self.filename = filename
        self.max_retries = max_retries

    async def init_tables(self):
        """Initializes the database tables, creating them and their
        indices if they don't exist.

        Arguments:
            None

        Returns:
            None

        Raises:
            aiosqlite.Error: Raised for any Error during table/index creation.
        """
        try:
            if not await self._table_exists('members'):
                logging.getLogger('respobot.database').info("creating table: members")
                await self._execute_write_query(CREATE_TABLE_MEMBERS)

            if not await self._table_exists('quotes'):
                logging.getLogger('respobot.database').info("creating table: quotes")
                await self._execute_write_query(CREATE_TABLE_QUOTES)
                await self._execute_write_query(CREATE_INDEX_QUOTES)

            if not await self._table_exists('subsessions'):
                logging.getLogger('respobot.database').info("creating table: subsessions")
                await self._execute_write_query(CREATE_TABLE_SUBSESSIONS)
                await self._execute_write_query(CREATE_INDEX_SUBSESSIONS_EVENTTYPE_ID)

            if not await self._table_exists('results'):
                logging.getLogger('respobot.database').info("creating table: results")
                await self._execute_write_query(CREATE_TABLE_RESULTS)
                await self._execute_write_query(CREATE_INDEX_RESULTS_SUBID_SESNUM)
                await self._execute_write_query(CREATE_INDEX_RESULTS_SESNUM_SUBID_CUSTID)
                await self._execute_write_query(CREATE_INDEX_RESULTS_IRATING_GRAPH)

            if not await self._table_exists('subsession_car_classes'):
                logging.getLogger('respobot.database').info("creating table: subsession_car_classes")
                await self._execute_write_query(CREATE_TABLE_SUBSESSION_CAR_CLASSES)
                await self._execute_write_query(CREATE_INDEX_SUBSESSION_CAR_CLASSES_SUBID_CLASSID)

            if not await self._table_exists('laps'):
                logging.getLogger('respobot.database').info("creating table: laps")
                await self._execute_write_query(CREATE_TABLE_LAPS)
                await self._execute_write_query(CREATE_INDEX_LAPS_SUBID_SESSNUM_CUSTID)

            if not await self._table_exists('current_seasons'):
                logging.getLogger('respobot.database').info("creating table: current_seasons")
                await self._execute_write_query(CREATE_TABLE_CURRENT_SEASONS)

            if not await self._table_exists('series'):
                logging.getLogger('respobot.database').info("creating table: series")
                await self._execute_write_query(CREATE_TABLE_SERIES)

            if not await self._table_exists('seasons'):
                logging.getLogger('respobot.database').info("creating table: seasons")
                await self._execute_write_query(CREATE_TABLE_SEASONS)

            if not await self._table_exists('season_car_classes'):
                logging.getLogger('respobot.database').info("creating table: season_car_classes")
                await self._execute_write_query(CREATE_TABLE_SEASON_CAR_CLASSES)

            if not await self._table_exists('current_car_classes'):
                logging.getLogger('respobot.database').info("creating table: current_car_classes")
                await self._execute_write_query(CREATE_TABLE_CURRENT_CAR_CLASSES)

            if not await self._table_exists('season_dates'):
                logging.getLogger('respobot.database').info("creating table: season_dates")
                await self._execute_write_query(CREATE_TABLE_SEASON_DATES)

            if not await self._table_exists('special_events'):
                logging.getLogger('respobot.database').info("creating table: special_events")
                await self._execute_write_query(CREATE_TABLE_SPECIAL_EVENTS)
        except Error:
            logging.getLogger('respobot.database').error("Error initializing database tables.")
            raise
        else:
            logging.getLogger('respobot.database').info("Successfully initialized the database tables.")

        return self

    async def _table_exists(self, table_name: str):
        """Returns a bool which is True if the table given by table_name exists and False otherwise.

        Arguments:
            table_name (str): The name of the database table.

        Returns:
            A bool indicating if the table exists.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        parameters = (table_name,)
        async with aiosqlite.connect(self.filename) as connection:
            async with connection.execute(query, parameters) as cursor:
                try:
                    result = await cursor.fetchall()
                    return len(result) > 0
                except Error as e:
                    logging.getLogger('respobot.database').error(
                        f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when running "
                        "_table_exists() with query:\n{query}\nwith params:\n{parameters}"
                    )

    async def _execute_write_query(self, query, params=None):
        """Executes the provided query. Used for queries that make changes to the database.

        Arguments:
            query (str): The query to execute.

        Keyword arguments:
            params (tuple): An optional tuple of values for any ? placeholders in the query. len(params) must equal
                            the number of ? placeholders in the query string.

        Returns:
            None.

        Raises:
            BotDatabaseError: Raised for max_retries exceeded.
            aiosqlite.OperationalError: Raised for any sqlite OperationalError except 5 (BUSY) or 6 (LOCKED).
            aiosqlite.Error: Raised for any sqlite Error.
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            retry_count += 1

            try:
                async with aiosqlite.connect(self.filename) as connection:
                    async with connection.cursor() as cursor:
                        if params is None:
                            await cursor.execute(query)
                        elif isinstance(params, tuple):
                            await cursor.execute(query, params)
                        elif isinstance(params, list):
                            await cursor.executemany(query, params)
                        else:
                            raise Error(
                                "If you pass params into _execute_write_query() they must be a tuple "
                                "or a list of tuples."
                            )
                        await connection.commit()
                        return
            except OperationalError as exc:
                if exc.sqlite_errorcode == 5 or exc.sqlite_errorcode == 6:
                    logging.getLogger('respobot.database').warning(
                        f"sqlite query failed due to sqlite error code {exc.sqlite_errorcode}: {exc.sqlite_errorname}"
                    )
                else:
                    logging.getLogger('respobot.database').error(
                        f"The sqlite3 error '{exc}' occurred with code {exc.sqlite_errorcode} when running "
                        f"_execute_write_query() with query:\n{query}\nwith params:\n{params}"
                    )
                    raise exc
            except Error as exc:
                logging.getLogger('respobot.database').error(
                    f"The sqlite3 error '{exc}' occurred with code {exc.sqlite_errorcode} when running "
                    f"_execute_write_query() with query:\n{query}\nwith params:\n{params}"
                )
                raise exc
        raise BotDatabaseError(
            "_execute_write_query() hit the max_retries count. Query abandoned.",
            ErrorCodes.max_retries_exceeded.value
        )

    async def _execute_read_query(self, query, params=None):
        """Executes the provided query. Used for SELECT queries.

        Arguments:
            query (str): The query to execute.

        Keyword arguments:
            params (tuple): An optional tuple of values for any ? placeholders in the query. len(params) must equal
                            the number of ? placeholders in the query string.

        Returns:
            A list of tuples where each tuple is one row in the query result. The length of the tuples is determined
            by the columns chosen in the SELECT query.

        Raises:
            BotDatabaseError: Raised for max_retries exceeded.
            aiosqlite.OperationalError: Raised for any sqlite OperationalError except 5 (BUSY) or 6 (LOCKED).
            aiosqlite.Error: Raised for any sqlite Error.
        """
        retry_count = 0

        while retry_count <= self.max_retries:
            retry_count += 1
            try:
                async with aiosqlite.connect(self.filename) as connection:
                    async with connection.cursor() as cursor:
                        result = None
                        if params is None:
                            await cursor.execute(query)
                        elif isinstance(params, tuple):
                            await cursor.execute(query, params)
                        elif isinstance(params, list):
                            await cursor.executemany(query, params)
                        else:
                            raise Error(
                                "If you pass params into _execute_read_query() they must be a tuple "
                                "or a list of tuples."
                            )
                        result = await cursor.fetchall()
                        return result
            except OperationalError as exc:
                if exc.sqlite_errorcode == 5 or exc.sqlite_errorcode == 6:
                    logging.getLogger('respobot.database').warning(
                        f"sqlite query failed due to sqlite error code {exc.sqlite_errorcode}: {exc.sqlite_errorname}"
                    )
                else:
                    logging.getLogger('respobot.database').error(
                        f"The sqlite3 error '{exc}' occurred with code {exc.sqlite_errorcode} when running "
                        f"_execute_read_query() with query:\n{query}\nwith params:\n{params}"
                    )
                    raise exc
            except Error as e:
                logging.getLogger('respobot.database').error(
                    f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when running "
                    f"_execute_read_query() with query:\n{query}\nwith params:\n{params}"
                )
                raise e
        raise BotDatabaseError(
            "_execute_read_query() hit the max_retries count. Query abandoned.",
            ErrorCodes.max_retries_exceeded.value
        )

    async def _map_tuples_to_dicts(self, query_result_tuples: list, table_name: str, extra_columns: list = []):
        """Maps row tuples returned from a SELECT query to a dict object where each key-value pair
        is of the form: "table_column_name": value

        Note: This will only work if the tuples are a result of selecting ALL columns in the table.
              SELECT * FROM table_name ...

        Arguments:
            query_result_tuples (list): A list of tuples returned from a "SELECT * FROM ..." query.
            table_name (str): The name of the table from which query_result_tuples came from.

        Returns:
            A dict where each key-value pair is of the form: "table_column_name": value

        Raises:
            BotDatabaseError: Raised if checking the database for table_name fails or if the length of a
                              tuple in query_result_tuples does not match the number of columns in the table.
        """
        query = f"PRAGMA table_info({table_name})"

        if query_result_tuples is None or len(query_result_tuples) < 1:
            return None

        try:
            table_column_tuples = await self._execute_read_query(query)
        except Error as e:
            logging.getLogger('respobot.database').error(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                f"get the table info for {table_name} during map_tuples_to_dict()"
            )
            raise BotDatabaseError(
                f"The sqlite3 error '{e}' occurred with code {e.sqlite_errorcode} when trying to "
                f"get the table info for {table_name} during map_tuples_to_dict()"
            )

        query_result_dicts = []
        for query_result_tuple in query_result_tuples:
            if len(table_column_tuples) != len(query_result_tuple) - len(extra_columns):
                raise BotDatabaseError(
                    f"Error mapping tuple to dict, tuple length does not match number of columns in {table_name}."
                )

            new_query_result_dict = {}
            columns_mapped = 0
            for table_column_tuple in table_column_tuples:
                index = table_column_tuple[1]
                new_query_result_dict[index] = query_result_tuple[columns_mapped]
                columns_mapped += 1
            for extra_column in extra_columns:
                new_query_result_dict[extra_column] = query_result_tuple[columns_mapped]
                columns_mapped += 1
            query_result_dicts.append(new_query_result_dict)

        return query_result_dicts

    from ._subsessions import (
        add_subsessions,
        get_subsession_data,
        is_subsession_multiclass,
        get_subsession_drivers_old_irs,
        fetch_member_car_numbers_in_subsession,
        fetch_members_in_subsession,
        is_subsession_in_db,
        get_cars_in_class,
        get_last_official_race_time
    )

    from ._laps import (
        add_laps,
        get_laps,
        is_subsession_in_laps_table
    )

    from ._results import (
        get_subsession_results,
        get_champ_points_data
    )

    from ._seasons import (
        is_season_in_seasons_table,
        is_car_class_in_season_car_classes_table,
        is_season_in_season_dates_table,
        is_car_class_car_in_current_car_classes,
        update_current_seasons,
        update_seasons,
        update_season_dates,
        update_current_car_classes,
        is_season_active,
        get_current_series_week,
        get_current_iracing_week,
        get_season_basic_info,
        get_series_last_run_season,
        get_series_id_from_season_name,
        get_car_class_id_from_car_class_name,
        get_season_car_classes,
        get_season_car_classes_for_all_series,
        get_season_id,
        get_season_dates
    )

    from ._series import (
        is_series_in_series_table,
        get_all_series,
        get_series_name_from_id
    )

    from ._members import (
        fetch_guild_member_ids,
        fetch_iracing_cust_ids,
        fetch_name,
        get_member_latest_session_found,
        set_member_latest_session_found,
        set_member_latest_race_report,
        get_member_ir,
        fetch_member_dict,
        fetch_member_dicts,
        add_member,
        remove_member,
        edit_member,
        fetch_graph_colour,
        set_graph_colour
    )

    from ._stats import (
        get_latest_ir,
        get_ir_data,
        get_race_incidents_and_corners,
        get_member_race_results,
        get_member_official_race_subsession_ids,
        get_member_series_raced
    )

    from ._quotes import (
        get_quotes,
        is_quote_in_db,
        get_quote_leaderboard,
        get_quote_ids,
        add_quote
    )

    from ._special_events import (
        get_special_events,
        add_special_event,
        remove_special_event,
        edit_special_event
    )

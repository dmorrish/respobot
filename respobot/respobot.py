# RespoBot.py
# Hold on to your butts.

import os
import signal
import discord
import discord.commands
from discord.ext import tasks
import random
import math
from irslashdata.client import Client as IracingClient
from irslashdata.exceptions import AuthenticationError, ServerDownError
from datetime import datetime, timezone
import logging
import io

# RespoBot modules
import respobot_logging
import image_generators
import constants
import environment_variables as env
import race_results as results
import update_series
import stats_helpers as stats
from slash_command_helpers import SlashCommandHelpers
import helpers
import image_generators as image_gen
from bot_database import BotDatabase, BotDatabaseError
from bot_state import BotState

# Import all bot command cogs
from commands.admin_commands import AdminCommandsCog
from commands.champ import ChampCog
from commands.cpi import CornersPerIncidentCog
from commands.compass import CompassCog
from commands.head2head import Head2HeadCog
from commands.ir_commands import IrCommandsCog
from commands.next_race import NextRaceCog
from commands.quote_commands import QuoteCommandsCog
from commands.schedule import ScheduleCog
from commands.send_nudes import SendNudesCog
from commands.special_events import SpecialEventsCog
from commands.test_race_results import TestRaceResultsCog

# Import all bot event handlers
from on_message import OnMessageCog
from on_reaction_add import OnReactionAddCog

# Init data and folder if does not exist.
if not os.path.exists(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY):
    os.mkdir(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY)

# Init Bot, IracingClient, BotDatabase, and BotState
intents = discord.Intents.all()
intents.message_content = True
bot = discord.Bot(intents=intents)

ir = IracingClient(env.IRACING_USERNAME, env.IRACING_PASSWORD)

db = BotDatabase(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.DATABASE_FILENAME, max_retries=5)
# slash_helpers.init(db)

bot_state = BotState(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.BOT_STATE_FILENAME)

# Attach all bot command cogs
bot.add_cog(AdminCommandsCog(bot, db, ir))
bot.add_cog(ChampCog(bot, db, ir))
bot.add_cog(CornersPerIncidentCog(bot, db, ir))
bot.add_cog(CompassCog(bot, db, ir))
bot.add_cog(Head2HeadCog(bot, db, ir))
bot.add_cog(IrCommandsCog(bot, db, ir))
bot.add_cog(NextRaceCog(bot, db, ir))
bot.add_cog(QuoteCommandsCog(bot, db, ir, bot_state))
bot.add_cog(ScheduleCog(bot, db, ir))
bot.add_cog(SendNudesCog(bot))
bot.add_cog(SpecialEventsCog(bot, db, ir))
if env.IS_DEV_INSTANCE:
    bot.add_cog(TestRaceResultsCog(bot, db, ir))

# Attach all bot event handlers
bot.add_cog(OnMessageCog(bot, db, ir))
bot.add_cog(OnReactionAddCog(bot, db, ir, bot_state))


@bot.event
async def on_ready():
    logging.getLogger('respobot.bot').info("I'm alive!")
    print("I'm alive!")

    try:
        await db.init_tables()
    except BotDatabaseError as exc:
        logging.getLogger('respobot.bot').error(
            f"The following exception was raised when initializing the database: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"The following exception was raised when initializing the database: {exc}"
        )
        return

    await helpers.change_bot_presence(bot)

    try:
        season_dates = await db.get_season_dates()
        if season_dates is None:
            await update_series.update_season_dates(db, ir)

        if not await db.is_series_in_series_table(constants.REFERENCE_SERIES):
            # series and seasons tables have not been populated. Update them now.
            ir_results = await ir.stats_series()
            await db.update_seasons(ir_results)

            ir_results = await ir.current_seasons()
            await db.update_current_seasons(ir_results)

        if not await db.is_car_class_car_in_current_car_classes(0, 34):
            car_class_dicts = await ir.current_car_classes()
            await db.update_current_car_classes(car_class_dicts)
    except AuthenticationError:
        logging.getLogger('respobot.iracing').warning(
            "Authentication to the iRacing server failed. "
            "Could not initialize the seasons, current_seasons, car_classes, and current_car_classes tables."
        )
        await helpers.send_bot_failure_dm(
            bot,
            "Authentication to the iRacing server failed. "
            "Could not initialize the seasons, current_seasons, car_classes, and current_car_classes tables."
        )
    except ServerDownError:
        logging.getLogger('respobot.iracing').warning(
            "The iRacing servers are down for maintenance. "
            "Could not initialize the seasons, current_seasons, car_classes, and current_car_classes tables."
        )
    except BotDatabaseError as exc:
        logging.getLogger('respobot.database').warning(
            "The following exception occured when initializing the seasons, current_seasons, car_classes, "
            f"and current_car_classes tables: {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            "The following exception occured when initializing the seasons, current_seasons, car_classes, "
            f"and current_car_classes tables: {exc}"
        )

    await SlashCommandHelpers.init(db)

    await helpers.promote_demote_members(bot, db)

    fast_task_loop.start()
    slow_task_loop.start()


@bot.event
async def on_guild_channel_create(channel):
    guild = helpers.fetch_guild(bot)

    if guild.id == channel.guild.id:
        await channel.send("#TwoManyChannels")


@tasks.loop(seconds=constants.SLOW_LOOP_INTERVAL, reconnect=True)
async def slow_task_loop():
    logging.getLogger('respobot.bot').debug(f"Running slow_task_loop().")
    try:
        (old_current_year, old_current_quarter, _, _, _) = await db.get_current_iracing_week()

        # Update 'current_seasons' and 'current_car_classes' tables.
        ir_results = await ir.current_car_classes()
        await db.update_current_car_classes(ir_results)

        ir_results = await ir.current_seasons()
        await db.update_current_seasons(ir_results)

        (current_year, current_quarter, _, _, _) = await db.get_current_iracing_week()

        # Check if there is a new season. If yes, update 'seasons' and 'season_dates' tables.
        if (
            current_year is not None and current_quarter is not None
            and (
                current_year > old_current_year
                or (current_year == old_current_year and current_quarter > old_current_quarter)
            )
        ):
            ir_results = await ir.stats_series()
            await db.update_seasons(ir_results)

            await update_series.update_season_dates(db, ir, season_year=current_year, season_quarter=current_quarter)
            # Since there's a new season, we need to refresh the autocomplete cache
            await SlashCommandHelpers.refresh_series()
    except AuthenticationError:
        logging.getLogger('respobot.iracing').warning(
            "Authentication to the iRacing server failed. "
            "Could not update season data in slow_task_loop()"
        )
        await helpers.send_bot_failure_dm(
            bot,
            "Authentication to the iRacing server failed. "
            "Could not update season data in slow_task_loop()"
        )
    except ServerDownError:
        logging.getLogger('respobot.iracing').warning(
            "The iRacing servers are down for maintenance. "
            "Could not update season data in slow_task_loop()"
        )
    except BotDatabaseError as exc:
        logging.getLogger('respobot.database').warning(
            f"The following exception occured when updating season data in slow_task_loop(): {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"The following exception occured when updating season data in slow_task_loop(): {exc}"
        )
    logging.getLogger('respobot.bot').debug(f"Done running slow_task_loop().")


@tasks.loop(seconds=constants.FAST_LOOP_INTERVAL, reconnect=True)
async def fast_task_loop():
    logging.getLogger('respobot.bot').debug(f"Running fast_task_loop().")

    logging.getLogger('respobot.bot').debug(f"fast_task_loop(): Fetching Discord Member objects.")
    # Update colours
    guild = helpers.fetch_guild(bot)
    member_objects = await helpers.fetch_guild_member_objects(bot, guild, db)

    if member_objects is not None:
        logging.getLogger('respobot.bot').debug(f"fast_task_loop(): Updating colours.")
        for member_obj in member_objects:
            brightness = math.sqrt(member_obj.colour.r ** 2 + member_obj.colour.g ** 2 + member_obj.colour.b ** 2)
            if brightness == 0:
                new_colour = [64, 64, 64, 255]
            elif brightness < 110:
                factor = 83 / brightness
                new_colour = [
                    member_obj.colour.r * factor,
                    member_obj.colour.g * factor,
                    member_obj.colour.b * factor,
                    255
                ]
            else:
                new_colour = [
                    member_obj.colour.r,
                    member_obj.colour.g,
                    member_obj.colour.b,
                    255
                ]

            try:
                await db.set_graph_colour(new_colour, discord_id=member_obj.id)
            except BotDatabaseError:
                logging.getLogger('respobot.bot').warning(
                    f"Unable to set graph color for Discord user {member_obj.display_name} "
                    f"({member_obj.id}). Skipping."
                )

    # Potentially update bot presence
    if random.randint(0, 19) == 0:
        logging.getLogger('respobot.bot').debug(f"fast_task_loop(): Updating bot presence.")
        await helpers.change_bot_presence(bot)

    if 'last_weekly_report_week' not in bot_state.data:
        bot_state.data['last_weekly_report_week'] = -1
        bot_state.dump_state()

    # From 1am to 2am UTC every Tuesday, check if we need to post an end-of-week update.
    now = datetime.now(timezone.utc)
    if now.hour == 1 and now.weekday() == 1:
        logging.getLogger('respobot.bot').debug(f"fast_task_loop(): Weekly report check.")
        try:
            (
                current_year,
                current_quarter,
                current_race_week,
                current_season_max_weeks,
                current_season_active
            ) = await db.get_current_iracing_week()

            logging.getLogger('respobot.bot').debug(
                f"get_current_iracing_week() returned ({current_year}, {current_quarter}, "
                f"{current_race_week}, {current_season_max_weeks}, {current_season_active})"
            )

            if current_race_week is None:
                current_race_week = -1

            post_update = False
            update_message = ""

            if (
                current_race_week > 0
                and current_race_week < current_season_max_weeks
                and current_race_week > bot_state.data['last_weekly_report_week']
            ):
                # Post the end of week Respo update when week 2 or later begins and the season is still active
                logging.getLogger('respobot.bot').debug(f"Posting end-of-week championship points update.")
                post_update = True
                report_up_to = current_race_week
                update_message = (
                    f"We've reached the end of week {current_race_week} so let's see who's "
                    f"racing well, who's racing like shit, and who's not even racing at all!"
                )
                bot_state.data['last_weekly_report_week'] = current_race_week
                bot_state.dump_state()
            elif (
                (current_race_week >= current_season_max_weeks or current_season_active != 1)
                and bot_state.data['last_weekly_report_week'] > 0
            ):
                # Post an end-of season Respo update if the season is not active
                # and the previously reported week was an active week.
                logging.getLogger('respobot.bot').debug(f"Posting end-of-season championship points update.")
                post_update = True
                report_up_to = current_season_max_weeks
                update_message = (
                    "Wow, I can't believe another season has passed. "
                    "Let's see how you shitheels stack up."
                )
                bot_state.data['last_weekly_report_week'] = -1
                bot_state.dump_state()

            if post_update:
                channel = helpers.fetch_channel(bot)
                member_dicts = await db.fetch_member_dicts()
                week_data = await stats.get_respo_champ_points(
                    db,
                    member_dicts,
                    current_year,
                    current_quarter,
                    report_up_to
                )
                stats.calc_total_champ_points(week_data, constants.RESPO_WEEKS_TO_COUNT)
                stats.calc_projected_champ_points(week_data, current_race_week, constants.RESPO_WEEKS_TO_COUNT, False)

                someone_racing = False
                for member in week_data:
                    if len(week_data[member]['weeks']) > 0:
                        someone_racing = True
                        break

                if someone_racing and channel is not None:
                    title_text = "Championship Points for Respo Racing Whatever the Fuck You Want Series"

                    title_text += " for " + str(current_year) + "s" + str(current_quarter)

                    if current_season_active == 1:
                        graph = image_gen.generate_champ_graph_compact(
                            week_data,
                            title_text,
                            constants.RESPO_WEEKS_TO_COUNT,
                            current_race_week
                        )
                    else:
                        graph = image_gen.generate_champ_graph(
                            week_data,
                            title_text,
                            constants.RESPO_WEEKS_TO_COUNT,
                            False
                        )

                    filename = f"tmp_champ_{str(datetime.now().strftime('%Y%m%d%H%M%S%f'))}.png"
                    filepath = env.BOT_DIRECTORY + env.MEDIA_SUBDIRECTORY + filename
                    graph.save(filepath, format=None)

                    with open(filepath, "rb") as f_graph:
                        picture = discord.File(f_graph)
                        await channel.send(content=update_message, file=picture)
                        picture.close()

                    if os.path.exists(filepath):
                        os.remove(filepath)
        except BotDatabaseError as exc:
            logging.getLogger('respobot.database').warning(
                f"The following exception occured when preparing the "
                f"end-of-week/season update post in fast_task_loop(): {exc}"
            )
            await helpers.send_bot_failure_dm(
                bot,
                f"The following exception occured when preparing the "
                f"end-of-week/season update post in fast_task_loop(): {exc}"
            )

    logging.getLogger('respobot.bot').debug(f"fast_task_loop(): iRacing anniversaries.")
    try:
        # iRacing anniversaries!
        if now.hour == 16 and bot_state.data['anniversary_flip_flop'] is False:
            bot_state.data['anniversary_flip_flop'] = True
            bot_state.dump_state()
            member_dicts = await db.fetch_member_dicts()

            if member_dicts is not None and len(member_dicts) > 0:
                channel = helpers.fetch_channel(bot)
                for member_dict in member_dicts:
                    # Join date anniversary check
                    if (
                        member_dict['ir_member_since'] is not None
                        and now.day == member_dict['ir_member_since'].day
                        and now.month == member_dict['ir_member_since'].month
                    ):
                        anniversary_messages = []
                        anniversary_messages.append(
                            f"iRacing used to be a respectable simracing service with a talented user base, "
                            f" but that all changed {now.year - member_dict['ir_member_since'].year} years ago "
                            f"when {member_dict['name']} joined. Happy iRacing anniversary!"
                        )
                        anniversary_messages.append(
                            f"{member_dict['name']} has been on iRacing for "
                            f"{now.year - member_dict['ir_member_since'].year} years "
                            f"and has spent ${random.randint(3400,8000)}.{random.randint(4,99):02d} on content. "
                            f"Happy iRacing anniversary!"
                        )
                        anniversary_messages.append(
                            f"{now.year - member_dict['ir_member_since'].year} years ago to this day "
                            f"the average skill level on iRacing dropped drastically when "
                            f"{member_dict['name']} signed up for the service. Happy iRacing anniversary!"
                        )
                        await channel.send(random.choice(anniversary_messages))
                    # Last official race anniversary check
                    last_race = await db.get_last_official_race_time(member_dict['iracing_custid'])
                    if last_race is not None:
                        if last_race.year != now.year and last_race.month == now.month and last_race.day == now.day:
                            years_since = now.year - last_race.year
                            one_year_x_years = f"{years_since} years" if years_since > 1 else "one year"
                            him_her_them = "them"
                            if member_dict['pronoun_type'] == 'male':
                                him_her_them = "him"
                            elif member_dict['pronoun_type'] == 'female':
                                him_her_them = "her"
                            await channel.send("<:Hmm:1039933625644355678>")
                            await channel.send(
                                f"It's been exactly {one_year_x_years} since {member_dict['name']} signed up for "
                                f"an official race. Please join me in shaming {him_her_them}."
                            )

            # Server icon rotation (take advantage of the once-per-day setup for anniversaries).
            # Rotate 1 degree every Thursday at 16:00 UTC.
            if now.weekday() == 3:
                bot_state.data['server_icon_angle'] += 1
                bot_state.dump_state()
                guild = helpers.fetch_guild(bot)
                new_icon = await image_generators.generate_guild_icon(bot_state.data['server_icon_angle'])

                img_byte_arr = io.BytesIO()
                new_icon.save(img_byte_arr, format='PNG')
                img_byte_arr = img_byte_arr.getvalue()
                await guild.edit(icon=img_byte_arr)

        elif now.hour != 16:
            bot_state.data['anniversary_flip_flop'] = False
            bot_state.dump_state()

        # Check if anyone raced.
        logging.getLogger('respobot.bot').debug(f"fast_task_loop(): get_race_results()")
        await results.get_race_results(bot, db, ir)
    except BotDatabaseError as exc:
        logging.getLogger('respobot.database').warning(
            f"The following exception occured when preparing the "
            f"iRacing anniversaries post in in slow_task_loop(): {exc}"
        )
        await helpers.send_bot_failure_dm(
            bot,
            f"The following exception occured when preparing the "
            f"iRacing anniversaries post in in slow_task_loop(): {exc}"
        )
    logging.getLogger('respobot.bot').debug(f"Done running fast_task_loop().")


def exit_handler(signum, frame):
    if bot_state.write_lock:
        logging.getLogger('respobot.bot').info('Exit delayed: Writing json files.')
        print("Exit delayed: Writing json files.")

    while bot_state.write_lock:
        pass

    logging.getLogger('respobot.bot').info('Done writing json files. Exiting...')
    print("\nDone writing json files. Exiting...")
    exit(0)


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

bot.run(env.TOKEN)

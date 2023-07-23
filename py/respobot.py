# RespoBot.py
# Hold on to your butts.

import os
import signal
import asyncio
import discord
import discord.commands
from discord.ext import tasks
import math
from pyracing.client import Client as IracingClient
from datetime import datetime, timezone
import httpx
import traceback

# RespoBot modules
import constants
import environment_variables as env
import race_results as results
import respobot_logging as log
import update_series
import stats_helpers as stats
import slash_command_helpers as slash_helpers
import helpers
import image_generators as image_gen
from bot_database import BotDatabase
from bot_state import BotState

# Import all bot command cogs
from commands.champ import ChampCog
from commands.compass import CompassCog
from commands.head2head import Head2HeadCog
from commands.ir_commands import IrCommandsCog
from commands.next_race import NextRaceCog
from commands.quote_commands import QuoteCommandsCog
from commands.refresh_cache import RefreshCacheCog
from commands.schedule import ScheduleCog
from commands.send_nudes import SendNudesCog
from commands.special_events import SpecialEventsCog
from commands.test_race_results import TestRaceResultsCog

# Import all bot event handlers
from on_message import OnMessageCog
from on_reaction_add import OnReactionAddCog

# Init Bot, IracingClient, BotDatabase, and BotState
intents = discord.Intents.all()
intents.message_content = True
bot = discord.Bot(intents=intents)

ir = IracingClient(env.IRACING_USERNAME, env.IRACING_PASSWORD)

db = BotDatabase(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.DATABASE_FILENAME)
slash_helpers.init(db)

bot_state = BotState(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.BOT_STATE_FILENAME)

first_run = True

# Attach all bot command cogs
bot.add_cog(ChampCog(bot, db, ir))
bot.add_cog(CompassCog(bot, db, ir))
bot.add_cog(Head2HeadCog(bot, db, ir))
bot.add_cog(IrCommandsCog(bot, db, ir))
bot.add_cog(NextRaceCog(bot, db, ir))
bot.add_cog(QuoteCommandsCog(bot, db, ir, bot_state))
bot.add_cog(RefreshCacheCog(bot, db, ir))
bot.add_cog(ScheduleCog(bot, db, ir))
bot.add_cog(SendNudesCog(bot))
bot.add_cog(SpecialEventsCog(bot, db, ir))
bot.add_cog(TestRaceResultsCog(bot, db, ir))

# Attach all bot event handlers
bot.add_cog(OnMessageCog(bot, db, ir))
bot.add_cog(OnReactionAddCog(bot, db, ir, bot_state))


@bot.event
async def on_ready():
    await db.init()
    await bot.change_presence(activity=discord.Game(name="50 Cent: Bulletproof"))

    print("I'm alive!")

    season_dates = await db.get_season_dates()
    if season_dates is None:
        await update_series.update_season_dates(db, ir)

    if not await db.is_series_in_series_table(139):
        # series and seasons tables have not been populated. Update them now.
        ir_results = await ir.stats_series_new()
        await db.update_seasons(ir_results)

        ir_results = await ir.current_seasons_new()
        await db.update_current_seasons(ir_results)

    if not await db.is_car_class_car_in_db(0, 34):
        car_class_dicts = await ir.current_car_classes_new()
        await db.update_car_classes(car_class_dicts)

    guild = helpers.fetch_guild(bot)
    await helpers.promote_demote_members(guild, db)

    fast_task_loop.start()
    slow_task_loop.start()


@bot.event
async def on_guild_channel_create(channel):
    guild = helpers.fetch_guild(bot)

    if guild.id == channel.guild.id:
        await channel.send("#TwoManyChannels")


@bot.event
async def on_raw_message_delete(payload):
    if payload.cached_message:
        message = payload.cached_message
    else:
        channel = helpers.fetch_channel(bot)
        await channel.send("Someone just deleted an old ass message. I tried to retrieve")
        return

    response = f"Here's what {message.author.display_name} doesn't want you to see:\n"
    if message.reference:
        replied_message_channel = await message.guild.fetch_channel(message.reference.channel_id)
        replied_message = await replied_message_channel.fetch_message(message.reference.message_id)
        replied_user = replied_message.author
        response += "> " + replied_user.display_name + ": " + replied_message.content + "\n> "
        response += message.author.display_name + ": " + message.content
    else:
        response += "> " + message.content + "\n> \\- " + message.author.display_name
    await message.channel.send(response)


@tasks.loop(seconds=3600)
async def slow_task_loop():
    # Don't run on startup.
    global first_run
    if first_run:
        first_run = False
        return

    (old_current_year, old_current_quarter, old_current_race_week, old_current_season_max_weeks, old_current_season_active) = await db.get_current_iracing_week()

    # Update current_series, current_car_classes, and seasons
    ir_results = await ir.stats_series_new()
    await db.update_seasons(ir_results)

    ir_results = await ir.current_car_classes_new()
    await db.update_car_classes(ir_results)

    ir_results = await ir.current_seasons_new()
    await db.update_current_seasons(ir_results)

    (current_year, current_quarter, current_race_week, current_season_max_weeks, current_season_active) = await db.get_current_iracing_week()

    if current_race_week is None:
        current_race_week = -1

    # Check if there is a new season. If yes, add it to the season_dates table.
    if current_year > old_current_year or (current_year == old_current_year and current_quarter > old_current_quarter):
        # A new season has been detected. Update season dates
        await update_series.update_season_dates(db, ir, season_year=current_year, season_quarter=current_quarter)


@tasks.loop(seconds=120)
async def fast_task_loop():
    (current_year, current_quarter, current_race_week, current_season_max_weeks, current_season_active) = await db.get_current_iracing_week()

    if current_race_week is None:
        current_race_week = -1

    # Update colours
    guild = helpers.fetch_guild(bot)
    member_objects = await helpers.fetch_guild_member_objects(guild, db)

    for member_obj in member_objects:
        brightness = math.sqrt(member_obj.colour.r ** 2 + member_obj.colour.g ** 2 + member_obj.colour.b ** 2)
        if brightness == 0:
            new_colour = [64, 64, 64, 255]
        elif brightness < 110:
            factor = 83 / brightness
            new_colour = [member_obj.colour.r * factor, member_obj.colour.g * factor, member_obj.colour.b * factor, 255]
        else:
            new_colour = [member_obj.colour.r, member_obj.colour.g, member_obj.colour.b, 255]

        await db.set_graph_colour(new_colour, discord_id=member_obj.id)

    if 'last_weekly_report_week' not in bot_state.data:
        bot_state.data['last_weekly_report_week'] = -1
        bot_state.dump_state()

    post_update = False
    update_message = ""

    now = datetime.now(timezone.utc)

    # From 1am to 2am UTC every Tuesday, check if we need to post an end-of-week update.
    if now.hour == 1 and now.weekday() == 1:
        if current_race_week > 0 and current_race_week > bot_state.data['last_weekly_report_week']:
            # Post the end of week Respo update when week 2 or later begins and the season is still active
            post_update = True
            report_up_to = current_race_week
            update_message = "We've reached the end of week " + str(current_race_week) + ", so let's see who's racing well, who's racing like shit, and who's not even racing at all!"
            bot_state.data['last_weekly_report_week'] = current_race_week
            bot_state.dump_state()
        elif (current_race_week < 0 or current_season_active != 1) and bot_state.data['last_weekly_report_week'] > 0:
            # Post an end-of season Respo update if the season is not active and the previously reported week was an active week.
            post_update = True
            report_up_to = current_season_max_weeks
            update_message = "Wow, I can't believe another season has passed. Let's see how you shitheels stack up."
            bot_state.data['last_weekly_report_week'] = -1
            bot_state.dump_state()

        if post_update:
            channel = helpers.fetch_channel(bot)
            member_dicts = await db.fetch_member_dicts()
            week_data = await stats.get_respo_champ_points(db, member_dicts, current_year, current_quarter, report_up_to)
            stats.calc_total_champ_points(week_data, constants.respo_weeks_to_count)
            stats.calc_projected_champ_points(week_data, current_race_week, constants.respo_weeks_to_count, False)

            someone_racing = False
            for member in week_data:
                if len(week_data[member]['weeks']) > 0:
                    someone_racing = True
                    break

            if someone_racing and channel is not None:
                title_text = "Championship Points for Respo Racing Whatever the Fuck You Want Series"

                title_text += " for " + str(current_year) + "s" + str(current_quarter)

                if current_season_active == 1:
                    graph = image_gen.generate_champ_graph_compact(week_data, title_text, constants.respo_weeks_to_count, current_race_week)
                else:
                    graph = image_gen.generate_champ_graph(week_data, title_text, constants.respo_weeks_to_count, False)

                filepath = env.BOT_DIRECTORY + "media/tmp_champ_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

                graph.save(filepath, format=None)

                with open(filepath, "rb") as f_graph:
                    picture = discord.File(f_graph)
                    await channel.send(content=update_message, file=picture)
                    picture.close()

                if os.path.exists(filepath):
                    await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
                    os.remove(filepath)

    # iRacing Birthdays!
    if now.hour == 16 and bot_state.data['birthday_flip_flop'] is False:
        bot_state.data['birthday_flip_flop'] = True
        bot_state.dump_state()
        member_dicts = await db.fetch_member_dicts()

        if member_dicts is not None and len(member_dicts) > 0:
            for member_dict in member_dicts:
                if now.day == member_dict['ir_member_since'].day and now.month == member_dict['ir_member_since'].month:
                    channel = helpers.fetch_channel(bot)
                    await channel.send(f"Happy iRacing birthday, {member_dict['name']}! 🥳🎉🎊")
    elif now.hour != 16:
        bot_state.data['birthday_flip_flop'] = False
        bot_state.dump_state()

    # Check if anyone raced.
    try:
        await results.get_race_results(bot, db, ir)
        # print('Finished scanning for new races. Sleeping until next check.')
        log.logger_respobot.info('Finished scanning for new races. Sleeping until next check.')
    except httpx.HTTPError:
        log.logger_respobot.warning('pyracing timed out when fetching race results.')
        # ir = IracingClient(env.IRACING_USERNAME, env.IRACING_PASSWORD)
    except RecursionError:
        log.logger_respobot.warning('pyracing hit the recursion limit when fetching race results.')
        # ir = IracingClient(env.IRACING_USERNAME, env.IRACING_PASSWORD)
    except Exception as ex:
        print(traceback.format_exc())
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        # print(message)
        log.logger_respobot.error(message)


def exit_handler(signum, frame):
    if bot_state.write_lock:
        log.logger_respobot.info('Exit delayed: Writing json files.')
        print("Exit delayed: Writing json files.")

    while bot_state.write_lock:
        pass

    log.logger_respobot.info('Done writing json files. Exiting...')
    print("\nDone writing json files. Exiting...")
    exit(0)


signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

bot.run(env.TOKEN)

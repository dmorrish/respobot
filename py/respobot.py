# RespoBot.py
# Hold on to your butts.

import os
import asyncio
import discord
import discord.commands
from discord.errors import NotFound, HTTPException
from discord.ext import tasks
import math
from pyracing.client import Client
from datetime import datetime
import httpx
import traceback

# RespoBot modules
import global_vars
import environment_variables as env
import race_results as results
import respobot_logging as log
import roles
import update_series
import stats_helpers as stats
import image_generators as image_gen

# Import all bot command cogs
from commands.champ import ChampCog
from commands.compass import CompassCog
from commands.head2head import Head2HeadCog
from commands.ir_graph import IrGraphCog
from commands.ir_leaderboard import IrLeaderboardCog
from commands.next_race import NextRaceCog
from commands.quote_add import QuoteAddCog
from commands.quote_leaderboard import QuoteLeaderboardCog
from commands.quote_list import QuoteListCog
from commands.quote_message_add import QuoteMessageAddCog
from commands.quote_show import QuoteShowCog
from commands.refresh_cache import RefreshCacheCog
from commands.schedule import ScheduleCog
from commands.send_nudes import SendNudesCog
from commands.series import SeriesCog
from commands.test_race_results import TestRaceResultsCog

# Import all bot event handlers
from on_message import OnMessageCog
from on_reaction_add import OnReactionAddCog

# Attach all bot command cogs
global_vars.bot.add_cog(ChampCog(global_vars.bot))
global_vars.bot.add_cog(CompassCog(global_vars.bot))
global_vars.bot.add_cog(Head2HeadCog(global_vars.bot))
global_vars.bot.add_cog(IrGraphCog(global_vars.bot))
global_vars.bot.add_cog(IrLeaderboardCog(global_vars.bot))
global_vars.bot.add_cog(NextRaceCog(global_vars.bot))
global_vars.bot.add_cog(QuoteAddCog(global_vars.bot))
global_vars.bot.add_cog(QuoteLeaderboardCog(global_vars.bot))
global_vars.bot.add_cog(QuoteListCog(global_vars.bot))
global_vars.bot.add_cog(QuoteMessageAddCog(global_vars.bot))
global_vars.bot.add_cog(QuoteShowCog(global_vars.bot))
global_vars.bot.add_cog(RefreshCacheCog(global_vars.bot))
global_vars.bot.add_cog(ScheduleCog(global_vars.bot))
global_vars.bot.add_cog(SendNudesCog(global_vars.bot))
global_vars.bot.add_cog(SeriesCog(global_vars.bot))
global_vars.bot.add_cog(TestRaceResultsCog(global_vars.bot))

# Attach all bot event handlers
global_vars.bot.add_cog(OnMessageCog(global_vars.bot))
global_vars.bot.add_cog(OnReactionAddCog(global_vars.bot))

global_vars.ir = Client(env.IRACING_USERNAME, env.IRACING_PASSWORD)

first_run = True
kill_switch = False


@global_vars.bot.event
async def on_ready():

    global_vars.load_json()
    await global_vars.bot.change_presence(activity=discord.Game(name="50 Cent: Bulletproof"))

    print("I'm alive!")

    await update_series.run()

    for guild in global_vars.bot.guilds:
        if guild.id == env.GUILD:
            global_vars.members_locks += 1
            for member in global_vars.members:
                if 'last_known_ir' in global_vars.members[member] and 'discordID' in global_vars.members[member]:
                    if global_vars.members[member]['last_known_ir'] < global_vars.pleb_line:
                        await roles.demote_driver(global_vars.members[member]['discordID'])
                    else:
                        await roles.promote_driver(global_vars.members[member]['discordID'])

    task_loop.start()


@tasks.loop(seconds=180)
async def task_loop():

    # Update colours
    for guild in global_vars.bot.guilds:
        if guild.id == env.GUILD:
            global_vars.members_locks += 1
            for member in global_vars.members:
                try:
                    member_obj = await guild.fetch_member(global_vars.members[member]['discordID'])
                    brightness = math.sqrt(member_obj.colour.r ** 2 + member_obj.colour.g ** 2 + member_obj.colour.b ** 2)
                    if brightness == 0:
                        global_vars.members[member]['graph_colour'] = [64, 64, 64, 255]
                    elif brightness < 110:
                        factor = 83 / brightness
                        global_vars.members[member]['graph_colour'] = [member_obj.colour.r * factor, member_obj.colour.g * factor, member_obj.colour.b * factor, 255]
                    else:
                        global_vars.members[member]['graph_colour'] = [member_obj.colour.r, member_obj.colour.g, member_obj.colour.b, 255]
                except NotFound:
                    log.logger_discord.warning("Member: " + member + " not found in the guild.")
                except HTTPException:
                    log.logger_discord.warning("HTTPException while fetching users for graph colours.")
                except Exception:
                    log.logger_discord.warning("Something went wrong when updating member colours.")
            global_vars.members_locks -= 1

            # Delete old Race Report threads
            threads = await guild.active_threads()

            for thread in threads:
                age = int(datetime.timestamp(datetime.now())) - int(datetime.timestamp(thread.created_at))

                if thread.owner_id == global_vars.bot.user.id and age > 7 * 24 * 60 * 60:
                    await thread.delete()

    # await results.get_race_results()
    # logger_pyracing.info('Finished scanning for new races. Sleeping until next check.')

    try:
        await results.get_race_results()
        # print('Finished scanning for new races. Sleeping until next check.')
        log.logger_pyracing.info('Finished scanning for new races. Sleeping until next check.')
    except httpx.HTTPError:
        print("pyracing timed out. Reinitializing client...")
        global_vars.ir = Client(env.IRACING_USERNAME, env.IRACING_PASSWORD)
    except RecursionError:
        print("pyracing hit the recursion limit. Reinitializing client...")
        global_vars.ir = Client(env.IRACING_USERNAME, env.IRACING_PASSWORD)
    except Exception as ex:
        print(traceback.format_exc())
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        # print(message)
        log.logger_pyracing.error(message)

    current_seasons = await global_vars.ir.current_seasons(only_active=1)

    season_active = False
    current_race_week = -1

    for season in current_seasons:
        if season.series_id == 139:
            season_active = True
            current_race_week = season.race_week

    post_update = False
    update_message = ""

    if 'current_race_week' not in global_vars.series_info['misc']:
        global_vars.series_info['misc']['current_race_week'] = -1

    if season_active:
        if current_race_week != global_vars.series_info['misc']['current_race_week']:
            if current_race_week != 1:
                # Post the end of week Respo Update
                post_update = True
                update_message = "We've reached the end of week " + str(current_race_week - 1) + ", so let's see who's racing well, who's racing like shit, and who's not even racing at all!"
    else:
        if global_vars.series_info['misc']['current_race_week'] == 12:
            post_update = True
            update_message = "Wow, I can't believe another season has passed. Let's see how you shitheels stack up."

    if post_update:
        week_data = stats.get_respo_champ_points(global_vars.series_info['misc']['current_year'], global_vars.series_info['misc']['current_quarter'], global_vars.series_info['misc']['current_race_week'])
        stats.calc_total_champ_points(week_data, 6)
        stats.calc_projected_champ_points(week_data, global_vars.series_info['misc']['current_race_week'], 6, False)

        someone_racing = False
        for member in week_data:
            if len(week_data[member]['weeks']) > 0:
                someone_racing = True
                break

        if someone_racing:
            for guild in global_vars.bot.guilds:
                if guild.id == env.GUILD:
                    for channel in guild.channels:
                        if channel.id == env.CHANNEL:
                            title_text = "Championship Points for Respo Racing Whatever the Fuck You Want Series"

                            title_text += " for " + str(global_vars.series_info['misc']['current_year']) + "s" + str(global_vars.series_info['misc']['current_quarter'])

                            graph = image_gen.generate_champ_graph_compact(week_data, title_text, 6, global_vars.series_info['misc']['current_race_week'])

                            filepath = env.BOT_DIRECTORY + "media/tmp_champ_" + str(datetime.now().strftime("%Y%m%d%H%M%S%f")) + ".png"

                            graph.save(filepath, format=None)

                            with open(filepath, "rb") as f_graph:
                                picture = discord.File(f_graph)
                                await channel.send(content=update_message, file=picture)
                                picture.close()

                            if os.path.exists(filepath):
                                await asyncio.sleep(5)  # Give discord some time to upload the image before deleting it. I'm not sure why this is needed since ctx.edit() is awaited, but here we are.
                                os.remove(filepath)

    global_vars.series_info['misc']['current_race_week'] = current_race_week
    global_vars.dump_json()

global_vars.bot.run(env.TOKEN)

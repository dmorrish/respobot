# RespoBot.py
# Hold on to your butts.

import discord
import discord.commands
from discord.errors import NotFound, HTTPException
from discord.ext import tasks
import math
from pyracing.client import Client

import httpx
import traceback

# RespoBot modules
import global_vars
import environment_variables as env
import race_results as results
import respobot_logging as log

# Import all bot command cogs
from champ import ChampCog
from compass import CompassCog
from head2head import Head2HeadCog
from ir_graph import IrGraphCog
from ir_leaderboard import IrLeaderboardCog
from next_race import NextRaceCog
from on_message import OnMessageCog
from on_reaction_add import OnReactionAddCog
from quote_add import QuoteAddCog
from quote_leaderboard import QuoteLeaderboardCog
from quote_list import QuoteListCog
from quote_message_add import QuoteMessageAddCog
from quote_show import QuoteShowCog
from refresh_cache import RefreshCacheCog
from schedule import ScheduleCog
from send_nudes import SendNudesCog
from series import SeriesCog
from test_race_results import TestRaceResultsCog

# Attach all bot command cogs
global_vars.client.add_cog(ChampCog(global_vars.client))
global_vars.client.add_cog(CompassCog(global_vars.client))
global_vars.client.add_cog(Head2HeadCog(global_vars.client))
global_vars.client.add_cog(IrGraphCog(global_vars.client))
global_vars.client.add_cog(IrLeaderboardCog(global_vars.client))
global_vars.client.add_cog(NextRaceCog(global_vars.client))
global_vars.client.add_cog(OnMessageCog(global_vars.client))
global_vars.client.add_cog(OnReactionAddCog(global_vars.client))
global_vars.client.add_cog(QuoteAddCog(global_vars.client))
global_vars.client.add_cog(QuoteLeaderboardCog(global_vars.client))
global_vars.client.add_cog(QuoteListCog(global_vars.client))
global_vars.client.add_cog(QuoteMessageAddCog(global_vars.client))
global_vars.client.add_cog(QuoteShowCog(global_vars.client))
global_vars.client.add_cog(RefreshCacheCog(global_vars.client))
global_vars.client.add_cog(ScheduleCog(global_vars.client))
global_vars.client.add_cog(SendNudesCog(global_vars.client))
global_vars.client.add_cog(SeriesCog(global_vars.client))
global_vars.client.add_cog(TestRaceResultsCog(global_vars.client))

global_vars.ir = Client(env.IRACING_USERNAME, env.IRACING_PASSWORD)

first_run = True
kill_switch = False


# @global_vars.client.slash_command(
#     guild_ids=[env.GUILD],
#     name='puppetmaster'
# )
# @permissions.is_user(173613324666273792)
# async def puppetmaster(
#     ctx,
#     display: Option(str, "Should the text be spongified?", required=True, choices=['Spongify', 'Normal']),
#     message: Option(str, "What do you want RespoBot to say?", required=True)
# ):
#     if display == 'Spongify':
#         response = spongify(message)
#     else:
#         response = message

#     await ctx.respond("Done.", ephemeral=True)
#     await ctx.channel.send(response)
#     return


@global_vars.client.event
async def on_ready():

    global_vars.load_json()
    await global_vars.client.change_presence(activity=discord.Game(name="50 Cent: Bulletproof"))

    print("I'm alive!")
    # task_loop.start()


@tasks.loop(seconds=180)
async def task_loop():

    print("Oh, hi there!")

    # Update colours
    for guild in global_vars.client.guilds:
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
                except:
                    log.logger_discord.warning("Something went wrong when updating member colours.")
            global_vars.members_locks -= 1

    # await get_race_results()
    # logger_pyracing.info('Finished scanning for new races. Sleeping until next check.')

    try:
        await results.get_race_results()
        print('Finished scanning for new races. Sleeping until next check.')
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

    # Next update in 3 minutes
    # await asyncio.sleep(180)

global_vars.client.run(env.TOKEN)

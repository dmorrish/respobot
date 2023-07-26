import constants
import environment_variables as env
import logging
import roles
import discord
from discord.errors import NotFound, HTTPException
from bot_database import BotDatabase
from irslashdata import constants as irConstants


# mAkE iT sPeAk LiKe ThIs
def spongify(message):
    flip_flop = True
    response = ""
    for char in message:
        if char.isalpha():
            if flip_flop is False:
                response += char.upper()
                flip_flop = True
            else:
                response += char.lower()
                flip_flop = False
        else:
            response += char
    return response


def fetch_guild(bot: discord.Bot):
    for guild in bot.guilds:
        if guild.id == env.GUILD:
            return guild
    logging.getLogger('respobot.discord').warning("Could not fetch RespoBot guild from the bot instance.")
    return None


def fetch_channel(bot: discord.Bot):
    for guild in bot.guilds:
        if guild.id == env.GUILD:
            for channel in guild.channels:
                if channel.id == env.CHANNEL:
                    return channel
    logging.getLogger('respobot.discord').warning("Could not fetch default channel from the bot instance.")
    return None


async def promote_demote_members(guild: discord.Guild, db: BotDatabase):

    member_dicts = await db.fetch_member_dicts()

    if member_dicts is None or len(member_dicts) < 1:
        return

    for member_dict in member_dicts:
        latest_road_ir_in_db = await db.get_member_ir(member_dict['iracing_custid'], category_id=irConstants.Category.road.value)
        if latest_road_ir_in_db is None or latest_road_ir_in_db < 0:
            continue

        if latest_road_ir_in_db < constants.pleb_line:
            await roles.demote_driver(guild, member_dict['discord_id'])
        else:
            await roles.promote_driver(guild, member_dict['discord_id'])


async def fetch_guild_member_objects(guild: discord.Guild, db: BotDatabase):

    guild_member_ids = await db.fetch_guild_member_ids()

    member_objects = []

    for member_id in guild_member_ids:
        try:
            new_member_object = await guild.fetch_member(member_id)
            member_objects.append(new_member_object)
        except NotFound:
            logging.getLogger('respobot.bot').warning(f"fetch_guild_member_objects() failed due to: Member {member_id} not found in the guild.")
        except HTTPException:
            logging.getLogger('respobot.bot').warning(f"fetch_guild_member_objects() failed due to: HTTPException while fetching member {member_id}.")
        except Exception as e:
            logging.getLogger('respobot.bot').warning(f"fetch_guild_member_objects() failed due to: {e}")

    return member_objects


async def send_bot_failure_dm(bot: discord.Bot, message: str):
    guild = fetch_guild(bot)

    if guild is not None:
        try:
            admin_object = await guild.fetch_member(env.ADMIN_ID)
            if admin_object is not None:
                try:
                    await admin_object.send(message)
                except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
                    logging.getLogger('respobot.discord').warning(f"Could not send failure DM to admin {admin_object.display_name}. Exception: {exc}")
        except (discord.HTTPException, discord.Forbidden) as exc:
            logging.getLogger('respobot.discord').warning(f"Could not fetch admin Member object to send failure DM. Exception {exc}")
            return

from discord.errors import NotFound
import discord

import helpers
import respobot_logging as log
import environment_variables as env


async def promote_driver(guild: discord.Guild, discord_id: int):
    try:
        discord_member = await guild.fetch_member(discord_id)
        if discord_member is not None:
            role_god = guild.get_role(env.ROLE_GOD)
            role_pleb = guild.get_role(env.ROLE_PLEB)
            if role_god is not None and role_pleb is not None:
                role_change_reason = helpers.spongify(discord_member.display_name + " has proven themself worthy of the title God Among Men.")
                await discord_member.add_roles(role_god, reason=role_change_reason)
                await discord_member.remove_roles(role_pleb, reason=role_change_reason)
            else:
                log.logger_respobot.warning(f"Role(s) not found. Can not promote role for user {discord_id}")
        else:
            log.logger_respobot.warning(f"User: {discord_id} not found. Can not promote role.")
    except NotFound:
        log.logger_respobot.warning(f"User: {discord_id} not found. Can not promote role.")


async def demote_driver(guild: discord.Guild, discord_id: int):
    try:
        discord_member = await guild.fetch_member(discord_id)
        if discord_member is not None:
            role_god = guild.get_role(env.ROLE_GOD)
            role_pleb = guild.get_role(env.ROLE_PLEB)
            if role_god is not None and role_pleb is not None:
                role_change_reason = helpers.spongify(discord_member.display_name + " has been banished from Mount Olypmus and must carry out the rest of their days among the peasants.")
                await discord_member.add_roles(role_pleb, reason=role_change_reason)
                await discord_member.remove_roles(role_god, reason=role_change_reason)
            else:
                log.logger_respobot.warning(f"Role(s) not found. Can not promote role for user {discord_id}")
        else:
            log.logger_respobot.warning(f"User: {discord_id} not found. Can not promote role.")
    except NotFound:
        log.logger_respobot.warning(f"User: {discord_id} not found. Can not promote role.")

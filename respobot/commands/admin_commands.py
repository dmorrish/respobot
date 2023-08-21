import discord
from discord.ext import commands
from discord.commands import Option
import environment_variables as env
from slash_command_helpers import SlashCommandHelpers
from discord.commands import SlashCommandGroup
from irslashdata.exceptions import AuthenticationError, ServerDownError
from bot_database import BotDatabaseError

import asyncio


class AdminCommandsCog(commands.Cog):

    def __init__(self, bot, db, ir):
        self.bot = bot
        self.db = db
        self.ir = ir

    admin_command_group = SlashCommandGroup("admin", "Admin commands for Deryk.")

    @admin_command_group.command(
        name='add_member',
        description="Used by Deryk to add a new member to the bot."
    )
    async def admin_add_member(
        self,
        ctx,
        name: Option(str, "Member's full name as it will appear in command results. Do not surround in quotes.", required=True),
        iracing_custid: Option(int, "iRacing customer id.", required=True),
        discord_id: Option(str, "Discord id.", required=True),
        pronoun_type: Option(str, "male, female, or neutral.", required=True, choices=['male', 'female', 'neutral'])
    ):
        if not self.is_admin(ctx.user.id):
            await ctx.respond("https://tenor.com/view/you-didnt-say-the-magic-word-ah-ah-nope-wagging-finger-gif-17646607")
            return

        await ctx.respond("Working on it...")

        discord_id = int(discord_id)

        try:
            ir_member_dicts = await self.ir.get_member_info_new([iracing_custid])
        except AuthenticationError:
            await ctx.edit(content="Auth error. Fix yo shit!")
            return
        except ServerDownError:
            await ctx.edit(content="iRacing is down for maintenance. Try again later.")
            return

        if ir_member_dicts is None or len(ir_member_dicts) < 1:
            await ctx.edit(content="Not a valid iRacing cust_id. Member not added.")
            return

        if len(ir_member_dicts) > 1:
            await ctx.edit(content="More than one member dict was returned for some unknown reason. Member not added.")
            return

        ir_member_since = ""
        if 'member_since' in ir_member_dicts[0]:
            ir_member_since = ir_member_dicts[0]['member_since']

        member = None
        try:
            member = await ctx.guild.fetch_member(discord_id)
        except (discord.HTTPException, discord.Forbidden) as exc:
            await ctx.edit(content=f"The following exception occured when trying to fetch the discord Member object: {exc}")

        if member is None:
            await ctx.edit(content=f"This discord_id was not found in this server. Member not added.")

        # We have finally passed all the checks. Add the member to the db.
        try:
            await self.db.add_member(name, iracing_custid, discord_id, ir_member_since, pronoun_type)
        except BotDatabaseError as exc:
            await ctx.edit(content=f"The following error occured when trying to add the member to the database: {exc}")
            return
        else:
            await SlashCommandHelpers.refresh_members()
            await ctx.edit(content="Success.")

    @admin_command_group.command(
        name='edit_member',
        description="Used by Deryk to edit/remove a member from the bot."
    )
    async def admin_edit_member(
        self,
        ctx,
        member: Option(str, "Member name.", required=True, autocomplete=SlashCommandHelpers.get_admin_member_list),
        remove: Option(bool, "Set to true to remove the event completely.", required=False),
        name: Option(str, "New name.", required=False),
        iracing_custid: Option(int, "New iRacing customer id.", required=False),
        discord_id: Option(str, "New Discord id.", required=False),
        pronoun_type: Option(str, "male, female, or neutral.", required=False, choices=['male', 'female', 'neutral'])
    ):
        if not self.is_admin(ctx.user.id):
            await ctx.respond("https://tenor.com/view/you-didnt-say-the-magic-word-ah-ah-nope-wagging-finger-gif-17646607")
            return

        await ctx.respond("Working on it...")

        member_split = member.split()
        if member_split[0].isnumeric():
            uid = int(member_split[0])
        else:
            await ctx.edit(content="Failed to parse the member uid from the member string.")
            return

        if remove is True:
            try:
                await self.db.remove_member(uid)
                await ctx.edit(content=f"{member} successfully removed from the database.")
            except BotDatabaseError as exc:
                await ctx.edit(content=f"The following error occured when trying to remove {member} from the database: {exc}")
                return
        else:

            try:
                # Get existing member info
                existing_member_dict = await self.db.fetch_member_dict(uid=uid)

                refresh_ir_info = iracing_custid is not None and iracing_custid != existing_member_dict['iracing_custid']
                ir_member_since = None

                if refresh_ir_info:
                    try:
                        ir_member_dicts = await self.ir.get_member_info_new([iracing_custid])
                    except AuthenticationError:
                        await ctx.edit(content="Auth error. Fix yo shit!")
                        return
                    except ServerDownError:
                        await ctx.edit(content="iRacing is down for maintenance. Try again later.")
                        return

                    if ir_member_dicts is None or len(ir_member_dicts) < 1:
                        await ctx.edit(content="Not a valid iRacing cust_id. Member not edited.")
                        return

                    if len(ir_member_dicts) > 1:
                        await ctx.edit(content="More than one member dict was returned for some unknown reason. Member not edited.")
                        return

                    ir_member_since = ""
                    if 'member_since' in ir_member_dicts[0]:
                        ir_member_since = ir_member_dicts[0]['member_since']

                try:
                    await self.db.edit_member(uid, name=name, iracing_custid=iracing_custid, discord_id=discord_id, ir_member_since=ir_member_since, pronoun_type=pronoun_type)
                except BotDatabaseError as exc:
                    await ctx.edit(content=f"The following error occured when trying to edit {member} in the database: {exc}")
                    return
                else:
                    if refresh_ir_info:
                        try:
                            await self.db.set_member_latest_session_found(iracing_custid, None)
                        except BotDatabaseError as exc:
                            await ctx.edit(content=f"The following error occured when trying to clear latest_session_foun for {member} in the database: {exc}")
                            return

                    if name is not None:
                        await SlashCommandHelpers.refresh_members()

                await ctx.edit(content=f"{member} successfully edited in the database.")
            except BotDatabaseError as exc:
                await ctx.edit(content=f"The following error occured when trying to edit {member} in the database: {exc}")
                return

    @admin_command_group.command(
        name='add_special_event',
        description="Used by Deryk to add a new iRacing special event."
    )
    async def admin_add_special_event(
        self,
        ctx,
        name: Option(str, "Event name.", required=True),
        start_date: Option(str, "YYYY-mm-dd format.", required=True),
        end_date: Option(str, "YYYY-mm-dd format.", required=True),
        track: Option(str, "Event track", required=True),
        cars: Option(str, "Cars in race in comma separated list.", required=True),
        category: Option(str, "road, oval, dirt_road, or dirt_oval", required=True, choices=['road', 'oval', 'dirt_road', 'dirt_oval'])
    ):
        if not self.is_admin(ctx.user.id):
            await ctx.respond("https://tenor.com/view/you-didnt-say-the-magic-word-ah-ah-nope-wagging-finger-gif-17646607")
            return

        await ctx.respond("Working on it...")

        try:
            await self.db.add_special_event(name, start_date, end_date, track, cars, category)
            await ctx.edit(content=f"Success. {name} added to the database.")
        except BotDatabaseError as exc:
            await ctx.edit(content=f"The following error occured when trying to add the special event to the database: {exc}")
            return

    @admin_command_group.command(
        name='edit_special_event',
        description="Used by Deryk to edit an iRacing special event."
    )
    async def admin_edit_special_event(
        self,
        ctx,
        event: Option(str, "The event you wish to edit.", required=True, autocomplete=SlashCommandHelpers.get_special_events),
        remove: Option(bool, "Set to true to remove the event completely.", required=False),
        name: Option(str, "The new name for the event.", required=False),
        start_date: Option(str, "The new start_date for the event in YYYY-mm-dd format.", required=False),
        end_date: Option(str, "The new end_date for the event in YYYY-mm-dd format.", required=False),
        track: Option(str, "The new track for the event.", required=False),
        cars: Option(str, "The new comma separated car list for the event.", required=False),
        category: Option(str, "The new category for the event.", required=False, choices=['road', 'oval', 'dirt_road', 'dirt_oval'])
    ):
        if not self.is_admin(ctx.user.id):
            await ctx.respond("https://tenor.com/view/you-didnt-say-the-magic-word-ah-ah-nope-wagging-finger-gif-17646607")
            return

        await ctx.respond("Working on it...")

        event_split = event.split()
        if event_split[0].isnumeric():
            uid = int(event_split[0])
        else:
            await ctx.edit(content="Failed to parse the event uid from the event string.")
            return

        if remove is True:
            try:
                await self.db.remove_special_event(uid)
                await ctx.edit(content=f"{event} successfully removed from the database.")
            except BotDatabaseError as exc:
                await ctx.edit(content=f"The following error occured when trying to remove the special event {event} from the database: {exc}")
                return
        else:
            try:
                await self.db.edit_special_event(uid, name=name, start_date=start_date, end_date=end_date, track=track, cars=cars, category=category)
                await ctx.edit(content=f"{event} successfully edited in the database.")
            except BotDatabaseError as exc:
                await ctx.edit(content=f"The following error occured when trying to edit the special event {event} in the database: {exc}")
                return

    def is_admin(self, discord_id):
        return discord_id == env.ADMIN_ID

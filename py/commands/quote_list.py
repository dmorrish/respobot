from discord.ext import commands
from discord.commands import Option
from discord.errors import NotFound
import helpers
import slash_command_helpers as slash_helpers
import global_vars


class QuoteListCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.quote_command_group.command(
        name='list',
        description="Show a listing of all the quotes for a member."
    )
    async def quote_list(
        ctx,
        member: Option(str, "The member to list.", required=True, autocomplete=slash_helpers.get_member_list)
    ):
        member_key = ""
        member_name = ""
        message_text = ""

        member_dict = helpers.get_member_dict_from_first_name(member)

        if 'discordID' in member_dict:
            id_to_list = member_dict['discordID']
        else:
            await ctx.respond("Who the fuck is " + member + "?", ephemeral=True)
            return

        message_text = "Here's a summary of all the times " + member + " has been quoted, you creep.\n\n"
        member_key = str(id_to_list)
        try:
            member_object = await ctx.guild.fetch_member(id_to_list)
            member_name = member_object.display_name
        except NotFound:
            if 'leaderboardName' in member_dict:
                member_name = member_dict['leaderboardName']
            else:
                member_name = member

        if member_key in global_vars.quotes and len(global_vars.quotes[member_key]) > 0:
            for quote in global_vars.quotes[member_key]:
                if "replied_to_quote" in global_vars.quotes[member_key][quote] and "replied_to_id" in global_vars.quotes[member_key][quote]:
                    try:
                        replied_to_member = await ctx.guild.fetch_member(global_vars.quotes[member_key][quote]["replied_to_id"])
                        message_text += "> " + replied_to_member.display_name + ": " + global_vars.quotes[member_key][quote]["replied_to_quote"] + "\n"
                    except NotFound:
                        message_text += "> " + global_vars.quotes[member_key][quote]['replied_to_name'] + ": " + global_vars.quotes[member_key][quote]["replied_to_quote"] + "\n"

                    message_text += "> " + member_name + ": " + global_vars.quotes[member_key][quote]['quote'] + "\n\n"
                else:
                    message_text += "> " + global_vars.quotes[member_key][quote]['quote'] + "\n> - " + member_name + "\n\n"

            await ctx.respond(message_text, ephemeral=True)
        else:
            await ctx.respond("No one has quoted " + member + " and that makes me a sad panda :(", ephemeral=True)

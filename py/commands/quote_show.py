import random
from discord.ext import commands
from discord.commands import Option
from discord.errors import NotFound
import helpers
import slash_command_helpers as slash_helpers
import global_vars


class QuoteShowCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @global_vars.quote_command_group.command(
        name='show',
        description="Show a random quote. Optionally choose a specific member."
    )
    async def quote_show(
        ctx,
        member: Option(str, "Quote a specific person.", required=False, autocomplete=slash_helpers.get_member_list)
    ):
        quote_dict = {}
        id_to_quote = -1
        if member is not None:
            member_dict = helpers.get_member_dict_from_first_name(member)
            if 'discordID' in member_dict:
                id_to_quote = member_dict['discordID']
            else:
                await ctx.respond("Who the fuck is " + member + "?", ephemeral=True)
                return

        if global_vars.quotes:
            if id_to_quote > 0:
                if str(id_to_quote) in global_vars.quotes and len(global_vars.quotes[str(id_to_quote)]) > 0:
                    # First check to make sure they've been quoted.
                    key = random.choice(list(global_vars.quotes[str(id_to_quote)]))
                    quote_dict = global_vars.quotes[str(id_to_quote)][key]
                else:
                    await ctx.respond(helpers.spongify("This person has never said anything notable. Not even once."), ephemeral=True)
                    return
            else:
                # Non-linear selection!
                # Proportions are doled out as an exponential rising to a final value.
                # Initial value is 10, final value is 50. Tau (28.85) is selected so that you get
                # a proportion of 30 when you've been quoted 20 times.
                proportions = []
                for person in global_vars.quotes:
                    proportions.append(int(10.0 + 40.0 * (1.0 - 2.71828**(-float(len(global_vars.quotes[person])) / 28.85))))

                # Produce thresholds for the draw based on each person's proportion of the total.
                thresholds = [proportions[0]]
                for i in range(1, len(proportions)):
                    thresholds.append(proportions[i] + thresholds[i - 1])

                # Draw the winning number.
                pick = random.randint(0, thresholds[-1] - 1)

                # Determine who won.
                selected_person = 0
                for threshold in thresholds:
                    if pick < thresholds[selected_person]:
                        break
                    else:
                        selected_person += 1

                id_to_quote = list(global_vars.quotes)[selected_person]
                key = random.choice(list(global_vars.quotes[str(id_to_quote)]))
                quote_dict = global_vars.quotes[str(id_to_quote)][key]

            try:
                discord_member = await ctx.guild.fetch_member(id_to_quote)
            except NotFound:
                discord_member = None

            quoted_name = ""
            replied_to_name = ""

            if discord_member is None:
                quoted_name = quote_dict['name']
            else:
                quoted_name = discord_member.display_name

            if 'replied_to_quote' in quote_dict and 'replied_to_name' in quote_dict:
                try:
                    replied_to_discord_member = await ctx.guild.fetch_member(quote_dict["replied_to_id"])
                except NotFound:
                    replied_to_discord_member = None
                if replied_to_discord_member is None:
                    replied_to_name = quote_dict['replied_to_name']
                else:
                    replied_to_name = replied_to_discord_member.display_name

            quote_text = ""
            if "replied_to_quote" in quote_dict:
                quote_text += "> " + replied_to_name + ": " + quote_dict["replied_to_quote"] + "\n> "
                quote_text += quoted_name + ": " + quote_dict["quote"]
            else:
                quote_text += "> " + quote_dict["quote"] + "\n> - " + quoted_name

            await ctx.respond(quote_text)
            return
        else:
            await ctx.respond("No one has added any quotes yet. Quick, go against your usual instinct and say something interesting for once so someone quotes it.", ephemeral=True)

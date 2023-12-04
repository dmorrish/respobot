import random
import constants
import environment_variables as env
import logging
import roles
import discord
import asyncio
import openai
import functools
from discord.errors import NotFound, HTTPException
from bot_database import BotDatabase, BotDatabaseError
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


async def promote_demote_members(bot: discord.Bot, db: BotDatabase):

    guild = fetch_guild(bot)

    try:
        member_dicts = await db.fetch_member_dicts()

        if member_dicts is None or len(member_dicts) < 1:
            return

        for member_dict in member_dicts:
            latest_road_ir_in_db = await db.get_member_ir(
                member_dict['iracing_custid'],
                category_id=irConstants.Category.road.value
            )
            if latest_road_ir_in_db is None or latest_road_ir_in_db < 0:
                continue

            if latest_road_ir_in_db < constants.PLEB_LINE:
                await roles.demote_driver(guild, member_dict['discord_id'])
            else:
                await roles.promote_driver(guild, member_dict['discord_id'])
    except Exception as exc:
        await send_bot_failure_dm(
            bot,
            f"During promote_demote_members() the following exception was encountered: {exc}"
        )


async def fetch_guild_member_objects(bot: discord.Bot, guild: discord.Guild, db: BotDatabase):

    try:
        guild_member_ids = await db.fetch_guild_member_ids()

        member_objects = []

        for member_id in guild_member_ids:
            try:
                new_member_object = await guild.fetch_member(member_id)
                member_objects.append(new_member_object)
            except NotFound:
                logging.getLogger('respobot.discord').warning(
                    f"During fetch_guild_member_objects(): Member {member_id} not found in the guild."
                )
            except HTTPException:
                logging.getLogger('respobot.discord').warning(
                    f"During fetch_guild_member_objects(): HTTPException while fetching member {member_id}."
                )
            except Exception as e:
                logging.getLogger('respobot.discord').warning(
                    f"During fetch_guild_member_objects(): Error {e} occured while fetching member {member_id}."
                )

        return member_objects
    except BotDatabaseError as exc:
        await send_bot_failure_dm(
            bot,
            (
                f"During fetch_guild_member_objects() the following BotDatabaseError exception "
                f"was encountered: [Errno {exc.error_code}] {exc}"
            )
        )
        logging.getLogger('respobot.database').warning(
            f"During fetch_guild_member_objects() the following BotDatabaseError exception "
            f"was encountered: [Errno {exc.error_code}] {exc}"
        )
        return None
    except Exception as exc:
        await send_bot_failure_dm(
            bot,
            f"During fetch_guild_member_objects() the following exception was encountered: {exc}"
        )
        logging.getLogger('respobot.bot').warning(
            f"During fetch_guild_member_objects() the following exception was encountered: {exc}"
        )
        return None


async def send_bot_failure_dm(bot: discord.Bot, message: str):
    guild = fetch_guild(bot)

    if guild is not None:
        try:
            admin_object = await guild.fetch_member(env.ADMIN_ID)
            if admin_object is not None:
                try:
                    await admin_object.send(message)
                except (discord.HTTPException, discord.Forbidden, discord.InvalidArgument) as exc:
                    logging.getLogger('respobot.discord').warning(
                        f"Could not send failure DM to admin {admin_object.display_name}. Exception: {exc}"
                    )
        except (discord.HTTPException, discord.Forbidden) as exc:
            logging.getLogger('respobot.discord').warning(
                f"Could not fetch admin Member object to send failure DM. Exception {exc}"
            )
            return


async def change_bot_presence(bot: discord.Bot):

    presence_list = [
        discord.Game(name="Daikatana"),
        discord.Game(name="Sonic 2006"),
        discord.Game(name="E.T. the Extra Terrestrial"),
        discord.Game(name="Shaq Fu"),
        discord.Game(name="Superman 64"),
        discord.Game(name="50 Cent: Bulletproof"),
        discord.Game(name="The Legend of Zelda CD-i"),
        discord.Game(name="Fallout 76"),
        discord.Game(name="The Lord of the Rings: Gollum"),

        discord.Activity(type=discord.ActivityType.watching, name="Alinity"),
        discord.Activity(type=discord.ActivityType.watching, name="Amouranth"),
        discord.Activity(type=discord.ActivityType.watching, name="Mia Malkova"),
        discord.Activity(type=discord.ActivityType.watching, name="Faith"),
        discord.Activity(type=discord.ActivityType.watching, name="Leynainu"),
        discord.Activity(type=discord.ActivityType.watching, name="Taylor_Jevaux"),
        discord.Activity(type=discord.ActivityType.watching, name="Jinnytty"),
        discord.Activity(type=discord.ActivityType.watching, name="Melina"),
        discord.Activity(type=discord.ActivityType.watching, name="Evaanna"),

        discord.Activity(type=discord.ActivityType.listening, name="Whip It by Devo"),
        discord.Activity(type=discord.ActivityType.listening, name="Tainted Love by Soft Cell"),
        discord.Activity(type=discord.ActivityType.listening, name="Blue Monday by New Order"),
        discord.Activity(type=discord.ActivityType.listening, name="M.E. by Gary Numan"),
        discord.Activity(type=discord.ActivityType.listening, name="The Safety Dance by Men Without Hats"),
        discord.Activity(type=discord.ActivityType.listening, name="I Ran (So Far Away) by A Flock of Seagulls"),
        discord.Activity(type=discord.ActivityType.listening, name="(I Just) Died in Your Arms by Cutting Crew"),
        discord.Activity(type=discord.ActivityType.listening, name="Hungry Like the Wolf by Duran Duran"),
        discord.Activity(type=discord.ActivityType.listening, name="Sweet Dreams by the Eurythmics"),
        discord.Activity(type=discord.ActivityType.listening, name="Relax by Frankie Goes to Hollywood"),
        discord.Activity(type=discord.ActivityType.listening, name="Video Killed the Radio Start by The Buggles"),
        discord.Activity(type=discord.ActivityType.listening, name="Message in a Bottle by The Police"),
        discord.Activity(type=discord.ActivityType.listening, name="Take on Me by a-ha"),
        discord.Activity(type=discord.ActivityType.listening, name="Down Under by Men at Work"),
        discord.Activity(type=discord.ActivityType.listening, name="Shout by Tears for Fears"),
        discord.Activity(type=discord.ActivityType.listening, name="The Killing Moon by Echo & the Bunnymen"),
        discord.Activity(type=discord.ActivityType.listening, name="Rebel Yell by Billy Idol"),
        discord.Activity(type=discord.ActivityType.listening, name="Talking in Your Sleep by The Romantics"),
        discord.Activity(type=discord.ActivityType.listening, name="Don't  You (Forget About Me) by Simple Minds"),

        discord.Activity(type=discord.ActivityType.watching, name="Ghost"),
        discord.Activity(type=discord.ActivityType.watching, name="10 Things I Hate About You"),
        discord.Activity(type=discord.ActivityType.watching, name="Gigli"),
        discord.Activity(type=discord.ActivityType.watching, name="Sleepless in Seattle"),
        discord.Activity(type=discord.ActivityType.watching, name="Bridget Jones's Diary"),
        discord.Activity(type=discord.ActivityType.watching, name="My Big Fat Greek Wedding"),
        discord.Activity(type=discord.ActivityType.watching, name="How to Lose a Guy in 10 Days"),
        discord.Activity(type=discord.ActivityType.watching, name="Never Been Kissed"),
        discord.Activity(type=discord.ActivityType.watching, name="Annie Hall"),
        discord.Activity(type=discord.ActivityType.watching, name="How Stella Got Her Groove Back"),
        discord.Activity(type=discord.ActivityType.watching, name="Harold and Maude"),
        discord.Activity(type=discord.ActivityType.watching, name="Enchanted"),
        discord.Activity(type=discord.ActivityType.watching, name="Four Weddings and a Funeral"),
        discord.Activity(type=discord.ActivityType.watching, name="Notting Hill"),
        discord.Activity(type=discord.ActivityType.watching, name="You've Got Mail"),
        discord.Activity(type=discord.ActivityType.watching, name="When Harry Met Sally")
    ]

    index = random.randint(0, len(presence_list) - 1)
    await bot.change_presence(activity=presence_list[index])


def format_grammar_for_item_list(items: list):
    if len(items) < 1:
        return ""
    elif len(items) == 1:
        return f"{items[0]}"
    elif len(items) == 2:
        return f"{items[0]} and {items[1]}"
    else:
        item_list = f"{items[0]}, {items[1]}, "
        count = 2
        while count < len(items) - 1:
            item_list += f"{items[count]}, "
            count += 1
        item_list += f"and {items[count]}"
        return item_list


async def gpt_rewrite(message: str, tone: str = "belligerent"):
    logging.getLogger('respobot.bot').debug(
        f"Sending the following message to GPT to be rewritten: {message}"
    )
    loop = asyncio.get_event_loop()
    openai.api_key = env.OPEN_AI_TOKEN
    model = "gpt-4"
    tone_prompt = "Be extra belligerent."
    if tone == "impressed":
        tone_prompt = "You are impressed with this accomplishment."

    messages = [
        {
            "role": "system",
            "content": (
                "You are an overconfident and sarcastic 39 year old man who is an avid motor racing fan. "
                "You never use exclamation points. The only emojis you use are the following two: "
                "<:KEKW:821408061960486992> which is to indicate standard laughter and "
                "<:KEKLEO:875757285329240114> which is to indicate cheeky laughter. However, you don't use them "
                "every message, but rather around 30 percent of the time. You have a good sense of humor and like "
                "to give people a good natured hard time. However, you are quick to acknowledge other peoples' "
                "accomplishments. When you know someone's preferred pronouns you use them instead of neutral ones."
            )
        },
        {
            "role": "user",
            "content": (
                f"Rewrite the message delimited by XML tags in your persona. "
                f"Keep your response to a maximum of two sentences. {tone_prompt}"
                f"<message>{message}</message>"
            )
        },
    ]

    try:
        response = await loop.run_in_executor(
            None,
            functools.partial(
                openai.ChatCompletion.create,
                model=model,
                messages=messages,
                temperature=constants.OPEN_AI_TEMPERATURE
            )
        )
    except openai.error.AuthenticationError:
        logging.getLogger('respobot.bot').warning(
            f"Authentication error with OpenAI server."
        )
        return None
    except Exception as exc:
        logging.getLogger('respobot.bot').warning(
            f"Exception while communicating with OpenAI: {exc}"
        )

    rewritten_message = response['choices'][0]['message']['content']
    logging.getLogger('respobot.bot').debug(
        f"Response from GPT: {rewritten_message} Prompt tokens used: {response['usage']['prompt_tokens']} "
        f" Completion tokens used: {response['usage']['completion_tokens']}."
    )
    return rewritten_message

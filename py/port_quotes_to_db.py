import json
from dotenv import load_dotenv
from bot_database import BotDatabase
import environment_variables as env
import asyncio


def load_json():
    with open(env.BOT_DIRECTORY + "json/quotes.json", "r") as f_quotes:
        global quotes
        quotes = json.load(f_quotes)


async def main():

    load_dotenv()

    quotes = {}
    db = await BotDatabase.init(env.BOT_DIRECTORY + env.DATABASE_FILENAME)
    load_json()

    query = f"""
        INSERT INTO quotes (discord_id, message_id, name, quote, replied_to_name, replied_to_quote, replied_to_message_id)
        VALUES ( ?, ?, ?, ?, ?, ?, ? )
    """
    parameters = []

    for discord_id_str in quotes:
        discord_id = int(discord_id_str)
        for message_id_str in quotes[discord_id_str]:
            quote_dict = quotes[discord_id_str][message_id_str]
            message_id = int(message_id_str)

            parameters.append((
                discord_id,
                message_id,
                quote_dict['name'],
                quote_dict['quote'],
                quote_dict['replied_to_name'] if 'replied_to_name' in quote_dict else None,
                quote_dict['replied_to_quote'] if 'replied_to_quote' in quote_dict else None,
                int(quote_dict['replied_to_id']) if 'replied_to_id' in quote_dict else None
            ))

    await db.execute_query(query, params=parameters)

    print("Done!")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

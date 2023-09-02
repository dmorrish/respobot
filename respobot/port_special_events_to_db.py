import json
from dotenv import load_dotenv
from datetime import date
from bot_database import BotDatabase
import environment_variables as env
import asyncio


def load_json():
    with open(env.BOT_DIRECTORY + "json/special_events.json", "r") as f_special_events:
        return json.load(f_special_events)


async def main():
    load_dotenv()

    special_events = load_json()
    db = BotDatabase(env.BOT_DIRECTORY + env.DATA_SUBDIRECTORY + env.DATABASE_FILENAME, max_retries=5)
    await db.init_tables()
    load_json()

    query = f"""
        INSERT INTO special_events (name, start_date, end_date, track, cars, category)
        VALUES ( ?, ?, ?, ?, ?, ? )
    """
    parameters = []

    for year in special_events:
        for event_key in special_events[year]:
            event_dict = special_events[year][event_key]

            if 'year' in event_dict['start'] and 'month' in event_dict['start'] and 'day' in event_dict['start']:
                event_start_date = date(
                    event_dict['start']['year'],
                    event_dict['start']['month'],
                    event_dict['start']['day']
                ).isoformat()
            else:
                event_start_date = "TBA"
            if 'year' in event_dict['end'] and 'month' in event_dict['end'] and 'day' in event_dict['end']:
                event_end_date = date(
                    event_dict['end']['year'],
                    event_dict['end']['month'],
                    event_dict['end']['day']
                ).isoformat()
            else:
                event_end_date = "TBA"

            parameters.append((
                event_dict['name'],
                event_start_date,
                event_end_date,
                event_dict['track'],
                event_dict['cars'],
                event_dict['category']
            ))

    await db._execute_write_query(query, params=parameters)

    print("Done!")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

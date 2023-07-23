from datetime import date, datetime, timezone, timedelta


async def cache_races(db, ir, iracing_custids):

    member_info = await ir.get_member_info_new(iracing_custids)
    (current_season_year, current_season_quarter, _, _, _) = await db.get_current_iracing_week()

    for member in member_info:
        if 'cust_id' not in member:
            continue
        iracing_custid = member['cust_id']
        date_started = date.fromisoformat(member['member_since'])
        year = date_started.year
        print(str(iracing_custid) + " joined iRacing on " + member['member_since'] + " year: " + str(year))

        print("Caching races for " + member['display_name'] + " back to " + str(year))
        quarter = 1

        caching_done = False
        start_time = datetime(date_started.year, 1, 1, tzinfo=timezone.utc)
        end_time = start_time + timedelta(days=90)
        latest_race = None

        while end_time < datetime.now(timezone.utc):
            print("Caching hosted races for " + str(start_time) + " to " + str(end_time))
            start_range_begin = start_time.isoformat().replace("+00:00", "Z")
            start_range_end = end_time.isoformat().replace("+00:00", "Z")
            hosted_race_dicts = await ir.search_hosted_new(cust_id=iracing_custid, start_range_begin=start_range_begin, start_range_end=start_range_end)
            print(str(len(hosted_race_dicts)) + " races found.")

            race_dicts = []

            for result in hosted_race_dicts:
                new_race = await ir.subsession_data_new(result['subsession_id'])
                if new_race is None:
                    continue
                race_dicts.append(new_race)
                if 'start_time' in new_race:
                    new_race_start_time = datetime.fromisoformat(new_race['start_time'])
                    if latest_race is None or new_race_start_time > latest_race:
                        latest_race = new_race_start_time

            await db.add_subsessions(race_dicts)

            start_time = end_time
            end_time = start_time + timedelta(days=90)
            if end_time > datetime.now(timezone.utc):
                end_time = datetime.now(timezone.utc)

        caching_done = False

        while caching_done is False:
            print("Caching races for " + str(year) + "s" + str(quarter))
            results_dicts = await ir.search_results_new(cust_id=iracing_custid, season_year=year, season_quarter=quarter)
            print(str(len(results_dicts)) + " races found.")

            race_dicts = []

            for result in results_dicts:
                new_race = await ir.subsession_data_new(result['subsession_id'])
                if new_race is None:
                    continue
                race_dicts.append(new_race)
                if 'start_time' in new_race:
                    new_race_start_time = datetime.fromisoformat(new_race['start_time'])
                    if latest_race is None or new_race_start_time > latest_race:
                        latest_race = new_race_start_time

            await db.add_subsessions(race_dicts)

            quarter += 1

            if quarter > 4:
                quarter = 1
                year += 1

            if year > current_season_year or (year == current_season_year and quarter > current_season_quarter):
                caching_done = True

        await db.set_member_last_race_check(iracing_custid, latest_race)
    print("Done caching races!")

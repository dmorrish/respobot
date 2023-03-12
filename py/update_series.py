import json
import global_vars
import environment_variables as env


async def run():

    message = "Updating Series info:\n"

    series_list = await global_vars.ir.current_seasons(only_active=0)

    for series in series_list:

        if str(series.series_id) not in global_vars.series_info:
            message += "New series:\n"
            message += series.series_name_short
            message += series.series_id

            global_vars.series_info[str(series.series_id)] = {}
            global_vars.series_info[str(series.series_id)]["name"] = series.series_name_short
            global_vars.series_info[str(series.series_id)]["category"] = series.category
            global_vars.series_info[str(series.series_id)]["classes"] = {}
        global_vars.series_info[str(series.series_id)]["season_id"] = ""
        if "last_run_year" not in global_vars.series_info[str(series.series_id)]:
            global_vars.series_info[str(series.series_id)]["last_run_year"] = -1
        if "last_run_quarter" not in global_vars.series_info[str(series.series_id)]:
            global_vars.series_info[str(series.series_id)]["last_run_quarter"] = -1
        if "keywords" not in global_vars.series_info[str(series.series_id)]:
            global_vars.series_info[str(series.series_id)]["keywords"] = []
        if series.season_year > global_vars.series_info[str(series.series_id)]["last_run_year"]:
            global_vars.series_info[str(series.series_id)]["last_run_year"] = series.season_year
            global_vars.series_info[str(series.series_id)]["last_run_quarter"] = series.season_quarter
        elif series.season_year == global_vars.series_info[str(series.series_id)]["last_run_year"] and series.season_quarter > global_vars.series_info[str(series.series_id)]["last_run_quarter"]:
            global_vars.series_info[str(series.series_id)]["last_run_year"] = series.season_year
            global_vars.series_info[str(series.series_id)]["last_run_quarter"] = series.season_quarter
        if series.active or (series.season_year == global_vars.series_info[str(series.series_id)]["last_run_year"] and series.season_quarter == global_vars.series_info[str(series.series_id)]["last_run_quarter"]):
            global_vars.series_info[str(series.series_id)]["name"] = series.series_name_short
            global_vars.series_info[str(series.series_id)]["season_id"] = series.season_id
            if "classes" not in global_vars.series_info[str(series.series_id)]:
                global_vars.series_info[str(series.series_id)]["classes"] = {}
            for car_class in series.car_classes:
                if str(car_class.id) not in global_vars.series_info[str(series.series_id)]["classes"]:
                    global_vars.series_info[str(series.series_id)]["classes"][str(car_class.id)] = []

        if "season_history" not in global_vars.series_info[str(series.series_id)]:
            global_vars.series_info[str(series.series_id)]["season_history"] = []
        if series.season_id not in global_vars.series_info[str(series.series_id)]["season_history"]:
            global_vars.series_info[str(series.series_id)]["season_history"].append(series.season_id)

    # Set the current season based off Rookie Mazda
    if "139" in global_vars.series_info:
        global_vars.series_info['misc']['last_run_year'] = global_vars.series_info["139"]["last_run_year"]
        global_vars.series_info['misc']['last_run_quarter'] = global_vars.series_info["139"]["last_run_quarter"]

    with open(env.BOT_DIRECTORY + "json/series_info.json", "w") as f_series_info:
        json.dump(global_vars.series_info, f_series_info, indent=4)

    for guild in global_vars.bot.guilds:
        if guild.id == env.GUILD:
            discord_member = guild.get_member(global_vars.members["Deryk Morrish"]["discordID"])
            await discord_member.send(content=message)

import global_vars
import environment_variables as env
import respobot_logging as log
import httpx
import traceback


async def run():

    try:

        message = "Updating Series info:"

        series_list = await global_vars.ir.current_seasons(only_active=0)

        new_series_found = False

        for series in series_list:

            if str(series.series_id) not in global_vars.series_info:
                new_series_found = True
                message += "\nNew series: "
                message += series.series_name_short + " "
                message += "(" + str(series.series_id) + ")"

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
            global_vars.series_info['misc']['current_year'] = global_vars.series_info["139"]["last_run_year"]
            global_vars.series_info['misc']['current_quarter'] = global_vars.series_info["139"]["last_run_quarter"]

        global_vars.dump_json()

        if new_series_found:
            for guild in global_vars.bot.guilds:
                if guild.id == env.GUILD:
                    discord_member = guild.get_member(global_vars.members["Deryk Morrish"]["discordID"])
                    await discord_member.send(content=message)
    except httpx.HTTPError:
        print("pyracing timed out during the respobot.update_series.run() method.")
    except RecursionError:
        print("pyracing hit the recursion limit during the respobot.update_series.run() method.")
    except Exception as ex:
        print(traceback.format_exc())
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        log.logger_pyracing.error(message)

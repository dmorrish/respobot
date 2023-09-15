# Turn all RespoBot logs into lists so that they can be read by cutelog.

import os
from os import path

log_path = path.join(os.getcwd(), 'logs')

try:
    if not os.path.isdir(log_path):
        os.mkdir(path.join(os.getcwd(), 'logs'))
        print(
            "Created 'logs' directory. Download the RespoBot log files from the server "
            "into this directory and run this program again."
        )
    else:
        try:
            count = 0
            for filename in os.listdir(log_path):
                if filename[-4:] == '.log':
                    with open(path.join(log_path, filename), "r+", encoding="utf8") as f_logfile:
                        content = f_logfile.read()
                        if content is not None and len(content) > 2:
                            content = content.replace('\\', "\\\\")
                            content = content.replace('"', '\\"')
                            content = content.replace("+*!*+None+*!*+", "null")
                            content = content.replace("+*!*+", '"')
                            if content[0] != '[' and content[-2] != ']':
                                new_content = '[' + content[0:-2] + ']\n'
                                f_logfile.seek(0, 0)
                                f_logfile.truncate(0)
                                f_logfile.write(new_content)
                    count += 1
            if count < 1:
                print("No log files found in the logs' directory. Download them from the server first.")
        # except Exception as e:
            # print(e)
        finally:
            pass

except FileNotFoundError:
    print("Error creating the 'logs' directory.")

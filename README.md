# RespoBot

A belligerent Discord bot for iRacing themed Discord servers.

## Required Python Libraries

* ir-slash-data - my fork of pyracing (https://github.com/Esterni/pyracing) that uses iRacing's new /Data stats endpoints and returns information in the original dicts
* httpx - used by ir-slash-data
* py-cord
* python-dotenv
* Pillow
* aiosqlite - asyncio wrapper for sqlite3

## Helpful Python Libraries

* cutelog (RespoBot loggers are set up with a SocketHandler and cutelog is a handy way to view the logs live.)

## Included Utilities

* /logutils contains Windows batch files which can be modified to grab the log files from the server (or a local dev instance), parse them into a format that can be read by cutelog (parsing done by parse_logs.py), and finally open cutelog for viewing.

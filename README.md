# RespoBot

A belligerent Discord bot for iRacing themed Discord servers.

## Required Python libraries

* pyracing-slash-data (my fork of pyracing that uses the new /data endpoints and returns information in the original dicts)
* httpx (used by pyracing-slash-data)
* py-cord
* python-dotenv
* Pillow
* aiosqlite (asyncio wrapper for sqlite3)

## Helpful Python libraries

* cutelog (RespoBot loggers are set up with a SocketHandler and cutelog is a handy way to view the logs live.)
@echo off

:: Set this to point to the folder where the .log files are saved.
:: Do not include a trailing slash.
set remote_folder=/home/user/bot-location/log-folder

del /s /q logs
set /p "ip=Enter RespoBot IP address: "
echo Downloading log files from %ip%.
if not exist "logs" mkdir "logs"
scp deryk@%ip%:%remote_folder%/* ./logs
py -3 parse_logs.py
cutelog
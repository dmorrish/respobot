if not exist "logs" mkdir "logs"
del /s /q logs
@echo off
xcopy /s ..\log logs 
@echo on
py -3 parse_logs.py
cutelog
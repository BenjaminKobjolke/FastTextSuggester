@echo off
call activate_environment.bat
pyinstaller --name FastTextSuggester --onefile --windowed main.py --add-data "data;data" --add-data "settings_example.ini;."
pause

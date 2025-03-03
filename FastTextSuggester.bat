@echo off
echo Starting Screenshot OCR Tool...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the tool
python main.py

REM Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat

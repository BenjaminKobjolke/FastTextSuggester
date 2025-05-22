@echo off
echo Starting Screenshot OCR Tool...

cd /d %~dp0

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the tool
call python main.py


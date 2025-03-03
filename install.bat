@echo off
echo Installing dependencies for Screenshot OCR Tool...


REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    call python -m venv venv
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
call pip install -r requirements.txt

echo.
echo Installation complete!
echo.
echo NOTE: You also need to install Tesseract OCR for Windows.
echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo Make sure to add Tesseract to your PATH or configure the path in settings.
echo.
echo Run the tool using run.bat
pause

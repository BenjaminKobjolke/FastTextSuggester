# FastTestSuggestor - Screenshot OCR Tool

A simple tool that captures screenshots when a hotkey is pressed, processes the image with OCR (Optical Character Recognition), and saves the extracted text to a file. It also provides a suggestion window for quick text insertion.

## Features

- Capture full-screen screenshots with a configurable hotkey (default: Ctrl+Shift+F12)
- Process screenshots with OCR using pytesseract
- Save extracted text to timestamped files in the output directory
- Auto-suggest words from OCR results in a minimalistic input window
- Insert selected text into the active application with a single keypress
- Configurable settings via settings.ini

## Requirements

- Python 3.6+
- Tesseract OCR engine installed on your system
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/BenjaminKobjolke/FastTools/FastTestSuggestor.git
   cd FastTestSuggestor
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required packages:

   ```
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR:
   - Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
   - Make sure the Tesseract executable is in your PATH or set the path in your code

## Configuration

Edit the `settings.ini` file to configure the tool:

```ini
[Hotkey]
combination = ctrl+shift+f12
suggestion_only = ctrl+alt+f12

[OCR]
language = eng
optimize = True

[Output]
directory = output

[Suggestions]
enabled = True
max_results = 10
show_at_startup = False
```

- `combination`: The hotkey combination to trigger the screenshot capture and OCR
- `suggestion_only`: The hotkey to show the suggestion window without capturing a new screenshot
- `language`: The OCR language (default: eng)
- `optimize`: Whether to optimize images for OCR (default: True)
- `directory`: The directory to save OCR output files
- `enabled`: Enable or disable the suggestion window feature
- `max_results`: Maximum number of suggestions to display
- `show_at_startup`: Whether to show the suggestion window when the application starts

## Usage

1. Run the tool:

   ```
   python main.py
   ```

2. Press the configured capture hotkey (default: Ctrl+Shift+F12) to capture a screenshot and perform OCR
3. The extracted text will be saved to a file in the output directory with a timestamp filename (YYYYMMDD\_\_HHMMSS.txt)
4. After OCR processing, a suggestion window will appear
5. Press the suggestion-only hotkey (default: Ctrl+Alt+F12) to show the suggestion window without capturing a new screenshot
6. Start typing to see suggestions from the OCR text
7. Press Enter to insert the selected suggestion into your active application
8. Press the hotkey again to close the suggestion window
9. Press Ctrl+C in the terminal to exit the tool

## License

MIT License - See LICENSE file for details

# FastTestSuggestor - Screenshot OCR Tool

A simple tool that captures screenshots when a hotkey is pressed, processes the image with OCR (Optical Character Recognition), and saves the extracted text to a file. It also provides a suggestion window for quick text insertion.

## Features

- Capture full-screen screenshots with a configurable hotkey (default: Ctrl+Shift+F12)
- Process screenshots with OCR using pytesseract
- Save extracted text to timestamped files in the output directory
- Auto-suggest words from OCR results in a minimalistic input window
- Load text files from the data directory for additional suggestions
- Support for line-based suggestions from files ending with \_line.txt
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
data_directory = data

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
- `data_directory`: The directory containing text files for additional suggestions (files ending with \_line.txt will provide line-based suggestions)
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
6. Start typing to see suggestions from both OCR text and data files
7. Suggestions from files ending with \_line.txt will show complete lines containing your search term
8. Press Enter to insert the selected suggestion into your active application
9. Press the hotkey again to close the suggestion window
10. Press Ctrl+C in the terminal to exit the tool

## Example Files

The `data_example` folder contains example files that demonstrate how the suggestion system works:

- `example_line.txt`: Contains complete lines that will be suggested as-is when a matching term is found
- `example_words.txt`: Contains text that will be processed for individual word and phrase suggestions

To try these examples:

1. Copy the `data_example` folder to a new folder named `data` in the project root:

   ```
   cp -r data_example data
   ```

   or on Windows:

   ```
   xcopy data_example data /E /I
   ```

2. Run the application and press the suggestion hotkey (Ctrl+Alt+F12 by default)
3. Start typing a word like "please" or "meeting" to see line-based suggestions from example_line.txt
4. Try typing words like "programming" or "software" to see word-based suggestions from example_words.txt

This demonstrates the difference between regular word-based suggestions and complete line suggestions.

## License

MIT License - See LICENSE file for details

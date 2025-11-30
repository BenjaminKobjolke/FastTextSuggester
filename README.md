# FastTestSuggestor - Screenshot OCR Tool

A simple tool that captures screenshots when a hotkey is pressed, processes the image with OCR (Optical Character Recognition), and saves the extracted text to a file. It also provides a suggestion window for quick text insertion.

## Features

- Capture full-screen screenshots with a configurable hotkey (default: Ctrl+Shift+F12)
- Process screenshots with OCR using pytesseract
- Save extracted text to timestamped files in the output directory
- Auto-suggest words from OCR results in a minimalistic input window
- Load text files from the data directory for additional suggestions
- Support for line-based suggestions from files ending with \_line.txt
- Support for replacement mappings from files ending with \_replace.txt (e.g., type "umlautu" to insert "ü")
- Support for TSV (tab-separated values) and CSV (comma-separated values) files with individual value suggestions
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

## Special Commands

The suggestion window supports special commands that can be typed in the input field:

- **/reload**: Reloads all data sources without closing the window

  - Refreshes all text files from the data directory
  - Reloads the latest OCR file from the output directory
  - Updates the suggestions displayed in the window
  - Useful when you've added or modified files and want to see the changes immediately

- **/exit**: Exits the application completely
  - Provides a quick way to close the application from the suggestion window

## Example Files

The `data_example` folder contains example files that demonstrate how the suggestion system works:

- `example_line.txt`: Contains complete lines that will be suggested as-is when a matching term is found
- `example_words.txt`: Contains text that will be processed for individual word and phrase suggestions
- `example_data.tsv`: Contains tab-separated values that will be suggested individually
- `example_contacts.csv`: Contains comma-separated values that will be suggested individually
- `templates_separator.txt`: Contains multi-line text blocks separated by `||` - only the first line is shown in suggestions, but the entire block is inserted
- `shortcuts_replace.txt`: Contains key-value replacement mappings (e.g., "umlautu" → "ü", "pipe" → "|")

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
5. Try typing names or email addresses to see suggestions from the example_data.tsv and example_contacts.csv files
6. Try typing "email", "meeting", "support", or "project" to see multi-line template suggestions from templates_separator.txt
7. Try typing "umlaut" or "pipe" to see replacement suggestions from shortcuts_replace.txt

## File Type Support

The application supports different types of files in the data directory:

1. **Regular text files (.txt)**: Processed for individual words and phrases
2. **Line-based text files (\_line.txt)**: Each line is suggested as a complete unit
3. **Separator-based text files (\_separator.txt)**: Multi-line text blocks separated by `||` - shows only the first line in suggestions but inserts the entire block
4. **Replacement text files (\_replace.txt)**: Key-value mappings in format `key|replacement` - type the key and the replacement is inserted. Use `||` for a literal `|` character (e.g., `pipe|||` maps "pipe" to "|")
5. **TSV files (.tsv)**: Each value in the tab-separated file is suggested individually
6. **CSV files (.csv)**: Each value in the comma-separated file is suggested individually

This allows you to organize your suggestions in the most appropriate format for your needs.

## License

MIT License - See LICENSE file for details

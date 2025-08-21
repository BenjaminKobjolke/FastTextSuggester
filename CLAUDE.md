# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastTextSuggester is a Windows desktop application that captures screenshots, performs OCR (Optical Character Recognition) to extract text, and provides an intelligent text suggestion system. The tool uses global hotkeys to capture screenshots and show a suggestion window with auto-complete functionality based on OCR results and pre-loaded data files.

## Development Commands

### Setup and Installation
```bash
# Create virtual environment and install dependencies
install.bat

# Activate virtual environment manually
activate_environment.bat
```

### Running the Application
```bash
# Run the application with virtual environment
FastTextSuggester.bat

# Or run directly with Python (after activating venv)
python main.py

# Run with custom config file
python main.py --config custom_settings.ini
```

### Building Executable
```bash
# Compile to standalone .exe file
compile_exe.bat
```

## Architecture

### Core Components

1. **ScreenshotOCRTool** (src/core/screenshot_ocr_tool.py): Main orchestrator that manages the entire application lifecycle, handles hotkeys, and coordinates between different components.

2. **SuggestionManager** (src/core/suggestion_manager.py): Manages text suggestions from multiple sources (OCR results, data files). Handles loading of different file formats (.txt, _line.txt, .tsv, .csv).

3. **SuggestionWindow** (src/core/suggestion_window.py): Tkinter-based GUI window that displays suggestions and handles user interaction for text insertion.

4. **SelectionWindow** (src/core/selection_window.py): Overlay window for selecting screen regions for OCR processing.

5. **ToolState** (src/core/tool_state.py): Global state management using singleton pattern to coordinate between components.

### Key Design Patterns

- **Singleton State Management**: ToolState class ensures single instance for global state coordination
- **Event-Driven Architecture**: Uses winhotkeys library for global hotkey detection
- **Multi-threaded Processing**: OCR and suggestion loading run in separate threads to maintain UI responsiveness

### External Dependencies

- **winhotkeys**: Custom fork for global hotkey handling (git+https://github.com/BenjaminKobjolke/winhotkeys.git)
- **pytesseract**: OCR engine wrapper requiring Tesseract OCR installation
- **Pillow**: Image processing for screenshot capture and optimization
- **keyboard/pynput**: Keyboard event simulation and monitoring

## Configuration

Settings are managed through `settings.ini` with these key sections:
- **[Hotkey]**: Global hotkey combinations for screenshot capture and suggestion window
- **[OCR]**: Tesseract OCR settings (language, optimization)
- **[Output]**: Directory paths for OCR results and data files
- **[Suggestions]**: Suggestion window behavior and limits

## Data File Formats

The application supports multiple data file formats in the `data` directory:
- **Regular .txt files**: Processed for individual word/phrase suggestions
- **_line.txt files**: Each line is suggested as a complete unit
- **.tsv files**: Tab-separated values, each value suggested individually
- **.csv files**: Comma-separated values, each value suggested individually

## Special Commands in Suggestion Window

- **/reload**: Reloads all data sources without closing the window
- **/exit**: Exits the application completely

## Testing Approach

No formal test framework is configured. Manual testing involves:
1. Running the application with `python main.py`
2. Testing hotkey combinations (Ctrl+Shift+F12 for capture, Ctrl+Alt+F12 for suggestions)
3. Verifying OCR output in the `output` directory
4. Testing suggestion window with example data files from `data_example` directory
"""
FastTestSuggestor - Screenshot OCR Tool

This tool captures screenshots when a hotkey is pressed,
processes the image with OCR, and saves the text to a file.
It also provides a suggestion window for quick text insertion.
"""
import argparse

from src.core.tool_state import ToolState
from src.core.screenshot_ocr_tool import ScreenshotOCRTool


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Screenshot OCR Tool")
    parser.add_argument(
        "--config", 
        type=str, 
        default="settings.ini",
        help="Path to configuration file"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Create and start the Screenshot OCR Tool
    tool = ScreenshotOCRTool()
    tool.start()

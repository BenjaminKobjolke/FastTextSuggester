"""
Screenshot capture functionality for the Screenshot OCR Tool
"""
import os
import shutil
from datetime import datetime
from typing import Optional, Tuple
import tempfile

# We'll use PIL for screenshot capture
from PIL import ImageGrab


class ScreenshotCapture:
    """
    Handles capturing screenshots for the OCR tool.
    """

    def __init__(self, temp_dir: Optional[str] = None, output_dir: Optional[str] = None):
        """
        Initialize the screenshot capture.

        Args:
            temp_dir: Directory to store temporary screenshots (default: system temp dir)
            output_dir: Directory to store permanent screenshots (default: None)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.output_dir = output_dir
        
        # Ensure the temp directory exists
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        # Ensure the output directory exists if provided
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def capture_full_screen(self) -> Tuple[str, datetime]:
        """
        Capture a full-screen screenshot.

        Returns:
            Tuple containing:
                - Path to the saved screenshot
                - Timestamp of the capture
        """
        timestamp = datetime.now()
        filename = f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.temp_dir, filename)
        
        # Capture the full screen
        screenshot = ImageGrab.grab()
        screenshot.save(filepath)
        
        # Save a copy to the output directory if specified
        if self.output_dir:
            output_filepath = os.path.join(self.output_dir, filename)
            try:
                shutil.copy2(filepath, output_filepath)
            except Exception as e:
                # Just log the error, don't raise
                print(f"Error saving screenshot to output directory: {e}")
        
        return filepath, timestamp

    def cleanup_temp_files(self, filepath: str) -> None:
        """
        Clean up temporary screenshot files.

        Args:
            filepath: Path to the file to clean up
        """
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                # Just log the error, don't raise
                print(f"Error cleaning up temporary file {filepath}: {e}")

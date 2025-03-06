"""
FastTestSuggestor - Screenshot OCR Tool

This tool captures screenshots when a hotkey is pressed,
processes the image with OCR, and saves the text to a file.
It also provides a suggestion window for quick text insertion.
"""
import os
import sys
import argparse
from datetime import datetime
import threading

from src.utils.config import Config
from src.utils.logger import Logger
from src.core.screenshot import ScreenshotCapture
from src.core.ocr import OCRProcessor
from src.core.hotkey import HotkeyHandler
from src.core.suggestion_manager import SuggestionManager
from src.core.suggestion_window import SuggestionWindow


class ScreenshotOCRTool:
    """
    Main class for the Screenshot OCR Tool.
    """

    def __init__(self):
        """Initialize the Screenshot OCR Tool."""
        # Initialize configuration
        self.config = Config()
        
        # Initialize logger with config
        self.logger = Logger(self.config)
        
        # Flags for thread-safe operations
        self.stop_ocr = False
        self.ocr_thread = None
        self.hide_suggestion_window = False
        
        # Initialize components
        output_dir = self.config.get_output_directory()
        self.screenshot_capture = ScreenshotCapture(output_dir=output_dir)
        self.ocr_processor = OCRProcessor(self.config.get_ocr_settings())
        
        # Get hotkey combinations from config
        self.hotkey_combinations = self.config.get_hotkey_combinations()
        
        # Get suggestion settings
        self.suggestion_settings = self.config.get_suggestion_settings()
        
        # Initialize suggestion components if enabled
        if self.suggestion_settings["enabled"]:
            self.suggestion_manager = SuggestionManager(
                output_directory=self.config.get_output_directory(),
                data_directory=self.config.get_data_directory()
            )
            self.suggestion_window = SuggestionWindow(self.suggestion_manager, self.logger)
            self.suggestion_window_thread = None
            self.show_suggestion_window = False  # Flag to indicate when to show the window
        else:
            self.suggestion_manager = None
            self.suggestion_window = None
            self.show_suggestion_window = False
        
        # Initialize hotkey handlers
        self.hotkey_handler = HotkeyHandler(
            self.hotkey_combinations["capture"], 
            self.handle_capture_hotkey
        )
        
        self.suggestion_hotkey_handler = HotkeyHandler(
            self.hotkey_combinations["suggestion_only"], 
            self.handle_suggestion_hotkey
        )
        
        self.logger.info(f"Screenshot OCR Tool initialized with hotkeys: capture={self.hotkey_combinations['capture']}, suggestion_only={self.hotkey_combinations['suggestion_only']}")

    def handle_capture_hotkey(self) -> None:
        """
        Handle hotkey press.
        Either capture a screenshot and process it, or toggle the suggestion window.
        """
        # If suggestion window is visible, just hide it
        if self.suggestion_settings["enabled"] and self.suggestion_window and self.suggestion_window.is_visible:
            self.logger.info("Hiding suggestion window")
            
            # If OCR is in progress, try to stop it
            if hasattr(self, 'ocr_thread') and self.ocr_thread and self.ocr_thread.is_alive():
                self.logger.info("Stopping OCR process")
                self.stop_ocr = True
            
            # Set flag to hide window in main thread
            self.hide_suggestion_window = True
            return
            
        # Otherwise, capture and process screenshot
        self.capture_and_process()
        
        # Set flag to show suggestion window in main thread
        if self.suggestion_settings["enabled"] and self.suggestion_window:
            # Reload data files to pick up any changes
            self.suggestion_manager.load_data_files()
            self.logger.info("Data files reloaded for capture")
            
            # Load the latest OCR file
            ocr_loaded = self.suggestion_manager.load_latest_ocr_file()
            
            # Show the suggestion window regardless of OCR file availability
            # since we now have data files as a source of suggestions
            self.show_suggestion_window = True
            
            if ocr_loaded:
                self.logger.info("OCR file loaded, will show suggestion window")
            else:
                self.logger.info("No OCR file found, showing window with data files only")

    def capture_and_process(self) -> None:
        """
        Capture a screenshot, process it with OCR, and save the text.
        Uses threading to improve responsiveness.
        """
        try:
            self.logger.info("Capturing screenshot...")
            
            # Reset stop flag
            self.stop_ocr = False
            
            # Capture screenshot (this must happen first)
            screenshot_path, timestamp = self.screenshot_capture.capture_full_screen()
            self.logger.info(f"Screenshot captured: {screenshot_path}")
            
            # Check if there's a recent OCR file
            has_recent_file = False
            if self.suggestion_settings["enabled"] and self.suggestion_manager:
                has_recent_file = self.suggestion_manager.load_latest_ocr_file()
            
            # Set flag to show suggestion window immediately
            if self.suggestion_settings["enabled"] and self.suggestion_window:
                # Set OCR in progress flag
                self.suggestion_window.set_ocr_in_progress(True)
                
                # Show the window
                self.show_suggestion_window = True
                
                # If we have a recent file, log it
                if has_recent_file:
                    self.logger.info("Recent OCR file loaded, showing suggestions")
                else:
                    self.logger.info("No recent OCR file, showing processing indicator")
            
            # Process with OCR in a separate thread
            self.ocr_thread = threading.Thread(
                target=self._process_ocr_in_background,
                args=(screenshot_path, timestamp)
            )
            self.ocr_thread.daemon = True
            self.ocr_thread.start()
            
        except Exception as e:
            # Clear OCR in progress status on error
            if self.suggestion_settings["enabled"] and self.suggestion_window:
                self.suggestion_window.set_ocr_in_progress(False)
                
            self.logger.error(f"Error in capture and process: {str(e)}")
            
    def _process_ocr_in_background(self, screenshot_path: str, timestamp: datetime) -> None:
        """
        Process OCR in a background thread to improve responsiveness.
        
        Args:
            screenshot_path: Path to the screenshot file
            timestamp: Timestamp of the screenshot
        """
        try:
            self.logger.info("Processing screenshot with OCR in background...")
            
            # Check if we should stop
            if self.stop_ocr:
                self.logger.info("OCR process stopped by user")
                
                # Clear OCR in progress status
                if self.suggestion_settings["enabled"] and self.suggestion_window:
                    self.suggestion_window.set_ocr_in_progress(False)
                
                # Clean up temporary screenshot
                self.screenshot_capture.cleanup_temp_files(screenshot_path)
                return
            
            # Process with OCR
            text = self.ocr_processor.process_image(screenshot_path)
            
            # Save text to file
            output_dir = self.config.get_output_directory()
            output_filename = f"{timestamp.strftime('%Y%m%d__%H%M%S')}.txt"
            output_path = os.path.join(output_dir, output_filename)
            
            self.ocr_processor.save_text_to_file(text, output_path)
            self.logger.info(f"OCR text saved to: {output_path}")
            
            # Clean up old files
            self.ocr_processor.cleanup_old_files(output_dir)
            self.logger.info("Cleaned up old files")
            
            # Update suggestion manager with new text and clear OCR in progress status
            if self.suggestion_settings["enabled"] and self.suggestion_manager:
                self.suggestion_manager.load_latest_ocr_file()
                
                # Clear OCR in progress status
                if self.suggestion_window:
                    self.suggestion_window.set_ocr_in_progress(False)
                    
                self.logger.info("Updated suggestion window with OCR results")
            
            # Clean up temporary screenshot
            self.screenshot_capture.cleanup_temp_files(screenshot_path)
            
        except Exception as e:
            # Clear OCR in progress status on error
            if self.suggestion_settings["enabled"] and self.suggestion_window:
                self.suggestion_window.set_ocr_in_progress(False)
                
            self.logger.error(f"Error in background OCR processing: {str(e)}")

    def handle_suggestion_hotkey(self) -> None:
        """
        Handle suggestion-only hotkey press.
        Show or hide the suggestion window without capturing a new screenshot.
        """
        # If suggestion window is visible, just hide it
        if self.suggestion_settings["enabled"] and self.suggestion_window and self.suggestion_window.is_visible:
            self.logger.info("Hiding suggestion window")
            
            # If OCR is in progress, try to stop it
            if hasattr(self, 'ocr_thread') and self.ocr_thread and self.ocr_thread.is_alive():
                self.logger.info("Stopping OCR process")
                self.stop_ocr = True
            
            # Set flag to hide window in main thread
            self.hide_suggestion_window = True
            return
            
        # Otherwise, try to load the latest OCR file and show the window
        if self.suggestion_settings["enabled"] and self.suggestion_window:
            # Make sure OCR in progress is set to false (no red border)
            self.suggestion_window.set_ocr_in_progress(False)
            
            # Reload data files to pick up any changes
            self.suggestion_manager.load_data_files()
            self.logger.info("Data files reloaded")
            
            # Try to load the latest OCR file
            ocr_loaded = self.suggestion_manager.load_latest_ocr_file()
            if ocr_loaded:
                self.logger.info("OCR file loaded")
            else:
                self.logger.info("No recent OCR file found, using data files only")
            
            # Show the suggestion window regardless of OCR file availability
            # since we now have data files as a source of suggestions
            self.show_suggestion_window = True
            self.logger.info("Showing suggestion window")

    def start(self) -> None:
        """Start the Screenshot OCR Tool."""
        self.logger.info("Starting Screenshot OCR Tool...")
        
        try:
            # Initialize suggestion window if enabled
            if self.suggestion_settings["enabled"] and self.suggestion_window:
                self.logger.info("Initializing suggestion window...")
                
                # Load data files at startup
                self.suggestion_manager.load_data_files()
                self.logger.info("Data files loaded at startup")
                
                # Create the window
                self.suggestion_window.create_window()
                
                # Only show window at startup if configured to do so
                if self.suggestion_settings.get("show_at_startup", False):
                    self.logger.info("Showing suggestion window at startup")
                    self.suggestion_window.show()
            
            # Start the hotkey handlers
            self.hotkey_handler.start()
            self.suggestion_hotkey_handler.start()
            
            # Keep the main thread alive
            print(f"Screenshot OCR Tool is running.")
            print(f"Press {self.hotkey_combinations['capture']} to capture a screenshot and perform OCR.")
            if self.suggestion_settings["enabled"]:
                print(f"Press {self.hotkey_combinations['suggestion_only']} to show the suggestion window without capturing.")
            print("Press Ctrl+C to exit.")
            
            # Wait for keyboard interrupt
            try:
                while True:
                    # Process Tkinter events if window exists
                    if self.suggestion_settings["enabled"] and self.suggestion_window:
                        if hasattr(self.suggestion_window, 'root') and self.suggestion_window.root:
                            try:
                                self.suggestion_window.root.update()
                                
                                # Update OCR status UI in the main thread
                                self.suggestion_window.update_ocr_status_ui()
                            except Exception as e:
                                self.logger.error(f"Error updating Tkinter: {e}")
                    
                    # Check if we need to show or hide the suggestion window
                    if self.show_suggestion_window and self.suggestion_window:
                        self.logger.info("Showing suggestion window from main thread")
                        self.suggestion_window.show()
                        self.show_suggestion_window = False
                    
                    if self.hide_suggestion_window and self.suggestion_window:
                        self.logger.info("Hiding suggestion window from main thread")
                        self.suggestion_window.hide()
                        self.hide_suggestion_window = False
                    
                    import time
                    time.sleep(0.01)  # Short sleep to reduce CPU usage
            except KeyboardInterrupt:
                print("\nExiting...")
                
        except Exception as e:
            self.logger.error(f"Error starting Screenshot OCR Tool: {str(e)}")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the Screenshot OCR Tool."""
        self.logger.info("Stopping Screenshot OCR Tool...")
        
        # Stop hotkey handlers
        self.hotkey_handler.stop()
        self.suggestion_hotkey_handler.stop()
        
        # Hide suggestion window if visible
        if self.suggestion_settings["enabled"] and self.suggestion_window and self.suggestion_window.is_visible:
            self.suggestion_window.hide()
            
        self.logger.info("Screenshot OCR Tool stopped")


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

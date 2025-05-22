"""
Main class for the Screenshot OCR Tool
"""
import os
import threading
import time
from datetime import datetime

from src.utils.config import Config
from src.utils.logger import Logger
from src.core.screenshot import ScreenshotCapture
from src.core.ocr import OCRProcessor
from winhotkeys import HotkeyHandler
from src.core.suggestion_manager import SuggestionManager
from src.core.suggestion_window import SuggestionWindow
from src.core.selection_window import SelectionWindow
from src.core.tool_state import ToolState


class ScreenshotOCRTool:
    """
    Main class for the Screenshot OCR Tool.
    """
    
    # Class variable to track the current selection window
    _selection_window = None

    def __init__(self):
        """Initialize the Screenshot OCR Tool."""
        # Initialize configuration
        self.config = Config()
        
        # Initialize state machine
        self.state = ToolState.IDLE
        
        # Initialize logger with config
        self.logger = Logger(self.config)
        
        # Flags for thread-safe operations
        self.stop_ocr = False
        self.ocr_thread = None
        
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
            # Create suggestion window with escape callback
            self.suggestion_window = SuggestionWindow(
                self.suggestion_manager, 
                self.logger,
                on_escape_callback=self._on_suggestion_window_escape
            )
            self.suggestion_window_thread = None
        else:
            self.suggestion_manager = None
            self.suggestion_window = None
        
        # Initialize hotkey handlers
        self.hotkey_handler = HotkeyHandler(
            self.hotkey_combinations["capture"], 
            self.handle_capture_hotkey,
            suppress=True  # Suppress the hotkey so it doesn't trigger in other applications
        )
        
        self.suggestion_hotkey_handler = HotkeyHandler(
            self.hotkey_combinations["suggestion_only"], 
            self.handle_suggestion_hotkey,
            suppress=True  # Suppress the hotkey so it doesn't trigger in other applications
        )
        
        self.logger.info(f"Screenshot OCR Tool initialized with hotkeys: capture={self.hotkey_combinations['capture']}, suggestion_only={self.hotkey_combinations['suggestion_only']}")

    def handle_capture_hotkey(self) -> None:
        """
        Handle hotkey press.
        Either capture a screenshot and process it, or toggle the suggestion window.
        """
        self.logger.info(f"Capture hotkey pressed. Current state: {self.state}")
        
        # State-based handling
        if self.state == ToolState.IDLE:
            # If we're idle, show the selection window
            self._show_selection_window()
            
        elif self.state == ToolState.SELECTION:
            # If selection window is already open, close it
            self.logger.info("Selection window already open, closing it")
            if ScreenshotOCRTool._selection_window and ScreenshotOCRTool._selection_window.is_open:
                ScreenshotOCRTool._selection_window.close()
                ScreenshotOCRTool._selection_window = None
            self.state = ToolState.IDLE
            
        elif self.state == ToolState.SUGGESTING:
            # If suggestion window is visible, hide it
            self.logger.info("Hiding suggestion window")
            
            # If OCR is in progress, try to stop it
            if hasattr(self, 'ocr_thread') and self.ocr_thread and self.ocr_thread.is_alive():
                self.logger.info("Stopping OCR process")
                self.stop_ocr = True
            
            # Update state to IDLE - window will be hidden in main loop
            self.state = ToolState.IDLE
            
        # In CAPTURING state, do nothing (let the capture complete)
    
    def _show_selection_window(self) -> None:
        """Show the selection window and handle the result."""
        self.logger.info("Preparing to show selection window")
        
        # Make sure suggestion window is hidden first
        if self.suggestion_settings["enabled"] and self.suggestion_window and self.suggestion_window.is_visible:
            self.logger.info("Hiding suggestion window before showing selection window")
            self.suggestion_window.hide()
            # Wait a moment for the window to hide
            time.sleep(0.2)  # Increased delay to ensure window is fully hidden
        
        # Update state
        self.state = ToolState.SELECTION
        self.logger.info(f"State changed to {self.state}")
        
        # Create selection window
        ScreenshotOCRTool._selection_window = SelectionWindow(self.logger)
        
        # Show selection window - this will block until user makes a choice
        self.logger.info("Showing selection window (modal)")
        capture_mode = ScreenshotOCRTool._selection_window.show()
        
        # Clear reference after window is closed
        ScreenshotOCRTool._selection_window = None
        
        # If user canceled, go back to idle
        if not capture_mode:
            self.logger.info("Capture canceled by user")
            self.state = ToolState.IDLE
            return
            
        # Otherwise, capture and process screenshot with the selected mode
        self.logger.info(f"Capture mode selected: {capture_mode}")
        self.state = ToolState.CAPTURING
        self.logger.info(f"State changed to {self.state}")
        self.capture_and_process(capture_mode)

    def capture_and_process(self, capture_mode: str = "whole_screen") -> None:
        """
        Capture a screenshot, process it with OCR, and save the text.
        Uses threading to improve responsiveness.
        
        Args:
            capture_mode: Mode of capture, either 'whole_screen' or 'active_window'
        """
        try:
            self.logger.info(f"Capturing screenshot in {capture_mode} mode...")
            
            # Reset stop flag
            self.stop_ocr = False
            
            # Capture screenshot based on mode
            if capture_mode == "active_window":
                screenshot_path, timestamp = self.screenshot_capture.capture_active_window()
                self.logger.info(f"Active window screenshot captured: {screenshot_path}")
            else:
                screenshot_path, timestamp = self.screenshot_capture.capture_full_screen()
                self.logger.info(f"Full screen screenshot captured: {screenshot_path}")
            
            # Check if there's a recent OCR file
            has_recent_file = False
            if self.suggestion_settings["enabled"] and self.suggestion_manager:
                has_recent_file = self.suggestion_manager.load_latest_ocr_file()
            
            # Only show suggestion window if enabled and we're in the right state
            if self.suggestion_settings["enabled"] and self.suggestion_window:
                # Reload data files to pick up any changes
                self.suggestion_manager.load_data_files()
                self.logger.info("Data files reloaded for capture")
                
                # Set OCR in progress flag
                self.suggestion_window.set_ocr_in_progress(True)
                
                # Update state - window will be shown in main loop
                self.state = ToolState.SUGGESTING
                
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

    def _on_suggestion_window_escape(self) -> None:
        """
        Callback for when the suggestion window is closed by Escape key.
        Updates the state to IDLE.
        """
        self.logger.info("Suggestion window closed by Escape key, updating state to IDLE")
        self.state = ToolState.IDLE
    
    def handle_suggestion_hotkey(self) -> None:
        """
        Handle suggestion-only hotkey press.
        Show or hide the suggestion window without capturing a new screenshot.
        """
        self.logger.info(f"Suggestion hotkey pressed. Current state: {self.state}")
        
        # State-based handling
        if self.state == ToolState.IDLE:
            # If we're idle, show the suggestion window
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
                
                # Update state - window will be shown in main loop
                self.state = ToolState.SUGGESTING
                self.logger.info("Showing suggestion window")
                
        elif self.state == ToolState.SUGGESTING:
            # If suggestion window is visible, hide it
            self.logger.info("Hiding suggestion window")
            
            # If OCR is in progress, try to stop it
            if hasattr(self, 'ocr_thread') and self.ocr_thread and self.ocr_thread.is_alive():
                self.logger.info("Stopping OCR process")
                self.stop_ocr = True
            
            # Update state to IDLE - window will be hidden in main loop
            self.state = ToolState.IDLE
            
        # In other states, do nothing

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
            print(f"  - You will be prompted to choose between whole screen or active window capture.")
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
                    
                    # Handle window visibility based on state
                    if self.suggestion_settings["enabled"] and self.suggestion_window:
                        # Only show suggestion window if we're in SUGGESTING state and it's not visible
                        if self.state == ToolState.SUGGESTING and not self.suggestion_window.is_visible:
                            self.logger.info("Showing suggestion window based on state")
                            self.suggestion_window.show()
                        
                    # Log state changes for debugging
                    if hasattr(self, '_last_state') and self._last_state != self.state:
                        self.logger.info(f"State changed: {self._last_state} -> {self.state}")
                    self._last_state = self.state
                    
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

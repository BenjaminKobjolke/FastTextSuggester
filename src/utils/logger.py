"""
Logging functionality for the Screenshot OCR Tool
"""
import logging
import os
from datetime import datetime


class Logger:
    """
    Logger class for the Screenshot OCR Tool.
    Handles logging to console and file.
    """

    def __init__(self, config=None):
        """
        Initialize the logger.

        Args:
            config: Configuration object (optional)
        """
        # Get logging settings
        self.config = config
        debug_enabled = False
        
        if config:
            logging_settings = config.get_logging_settings()
            debug_enabled = logging_settings.get("debug", False)
        
        # Set log level based on debug setting
        log_level = logging.DEBUG if debug_enabled else logging.INFO
        
        self.logger = logging.getLogger("ScreenshotOCR")
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(
            log_dir, 
            f"screenshot_ocr_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
        """
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
        """
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
        """
        self.logger.debug(message)

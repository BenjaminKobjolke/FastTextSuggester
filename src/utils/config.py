"""
Configuration handling for the Screenshot OCR Tool
"""
import configparser
import logging
import os
from typing import Dict, Any


class Config:
    """
    Configuration manager for the Screenshot OCR Tool.
    Handles reading and parsing settings from the settings.ini file.
    """

    def __init__(self, config_path: str = "settings.ini"):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(config_path):
            self._create_default_config()
        
        self.config.read(config_path)

    def _create_default_config(self) -> None:
        """Create a default configuration file if none exists."""
        self.config["Hotkey"] = {
            "combination": "ctrl+shift+f12"
        }
        self.config["OCR"] = {
            "language": "eng",
            "optimize": "True"
        }
        self.config["Output"] = {
            "directory": "output",
            "data_directory": "data"
        }
        
        with open(self.config_path, "w") as config_file:
            self.config.write(config_file)

    def get_hotkey_combinations(self) -> Dict[str, str]:
        """
        Get the configured hotkey combinations.

        Returns:
            Dictionary with hotkey types and their combinations
        """
        return {
            "capture": self.config.get("Hotkey", "combination", fallback="ctrl+shift+f12"),
            "suggestion_only": self.config.get("Hotkey", "suggestion_only", fallback="ctrl+alt+f12")
        }
        
    def get_hotkey_combination(self) -> str:
        """
        Get the configured capture hotkey combination.
        
        Returns:
            The hotkey combination string
            
        Note:
            This method is kept for backward compatibility.
            New code should use get_hotkey_combinations() instead.
        """
        return self.config.get("Hotkey", "combination", fallback="ctrl+shift+f12")

    def get_ocr_settings(self) -> Dict[str, Any]:
        """
        Get OCR settings.

        Returns:
            Dictionary of OCR settings
        """
        return {
            "language": self.config.get("OCR", "language", fallback="eng"),
            "optimize": self.config.getboolean("OCR", "optimize", fallback=True)
        }

    def get_output_directory(self) -> str:
        """
        Get the configured output directory.

        Returns:
            Path to the output directory
        """
        output_dir = self.config.get("Output", "directory", fallback="output")
        
        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        return output_dir
        
    def get_data_directory(self) -> str:
        """
        Get the configured data directory.

        Returns:
            Path to the data directory
        """
        data_dir = self.config.get("Output", "data_directory", fallback="data")
        
        # Create the data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        return data_dir
        
    def get_suggestion_settings(self) -> Dict[str, Any]:
        """
        Get suggestion settings.

        Returns:
            Dictionary of suggestion settings
        """
        return {
            "enabled": self.config.getboolean("Suggestions", "enabled", fallback=True),
            "max_results": self.config.getint("Suggestions", "max_results", fallback=10),
            "show_at_startup": self.config.getboolean("Suggestions", "show_at_startup", fallback=False)
        }
        
    def get_logging_settings(self) -> Dict[str, Any]:
        """
        Get logging settings.

        Returns:
            Dictionary of logging settings
        """
        # Get log level from config
        log_level_str = self.config.get("Logging", "log_level", fallback="INFO").upper()
        
        # Map string to logging level
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        # Default to INFO if invalid level specified
        log_level = log_level_map.get(log_level_str, logging.INFO)
        
        return {
            "debug": self.config.getboolean("Logging", "debug", fallback=False),
            "log_level": log_level
        }

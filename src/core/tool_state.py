"""
Tool state enum for the Screenshot OCR Tool
"""
import enum


class ToolState(enum.Enum):
    """
    Enum representing the different states of the Screenshot OCR Tool.
    """
    IDLE = 0        # Waiting for user input
    SELECTION = 1   # Selection window is active
    CAPTURING = 2   # Capturing and processing OCR
    SUGGESTING = 3  # Showing suggestion window

"""
Hotkey registration and handling for the Screenshot OCR Tool
"""
from typing import Callable, Optional
import threading
import time

# We'll use keyboard library for hotkey handling
import keyboard


class HotkeyManager:
    """
    Manages hotkey registration and handling.
    """

    def __init__(self):
        """Initialize the hotkey manager."""
        self.registered_hotkeys = {}
        self.running = False
        self.listener_thread = None

    def register_hotkey(self, hotkey_combination: str, callback: Callable) -> None:
        """
        Register a hotkey with a callback function.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'ctrl+shift+f12')
            callback: Function to call when the hotkey is pressed
        """
        self.registered_hotkeys[hotkey_combination] = callback
        
    def start_listening(self) -> None:
        """Start listening for registered hotkeys."""
        if self.running:
            return
            
        self.running = True
        self.listener_thread = threading.Thread(target=self._listener_loop)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        
    def stop_listening(self) -> None:
        """Stop listening for hotkeys."""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1.0)
            self.listener_thread = None
            
    def _listener_loop(self) -> None:
        """Background thread that listens for hotkey presses."""
        # Register all hotkeys with the keyboard library
        for hotkey, callback in self.registered_hotkeys.items():
            keyboard.add_hotkey(hotkey, callback)
            
        # Keep the thread alive while running
        while self.running:
            time.sleep(0.1)
            
        # Unregister all hotkeys when stopping
        for hotkey in self.registered_hotkeys:
            keyboard.remove_hotkey(hotkey)


class HotkeyHandler:
    """
    Handles the screenshot hotkey functionality.
    """

    def __init__(self, hotkey_combination: str, callback: Callable):
        """
        Initialize the hotkey handler.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'ctrl+shift+f12')
            callback: Function to call when the hotkey is pressed
        """
        self.hotkey_manager = HotkeyManager()
        self.hotkey_combination = hotkey_combination
        self.callback = callback
        
    def start(self) -> None:
        """Start the hotkey handler."""
        self.hotkey_manager.register_hotkey(self.hotkey_combination, self.callback)
        self.hotkey_manager.start_listening()
        
    def stop(self) -> None:
        """Stop the hotkey handler."""
        self.hotkey_manager.stop_listening()

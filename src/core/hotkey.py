"""
Hotkey registration and handling for the Screenshot OCR Tool
"""
from typing import Callable, Dict, List, Optional, Set
import threading
import time

# Using global_hotkeys for hotkey handling
from global_hotkeys import *


class HotkeyManager:
    """
    Manages hotkey registration and handling using global_hotkeys.
    """

    def __init__(self):
        """Initialize the hotkey manager."""
        self.registered_hotkeys = {}
        self.running = False
        self._listener_thread = None

    def register_hotkey(self, hotkey_combination: str, callback: Callable, suppress: bool = False) -> None:
        """
        Register a hotkey with a callback function.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'ctrl+shift+f12')
            callback: Function to call when the hotkey is pressed
            suppress: Whether to suppress the hotkey so it doesn't trigger in other applications (global_hotkeys suppresses by default)
        """
        # global_hotkeys suppresses by default, so we just need to store the hotkey and callback
        self.registered_hotkeys[hotkey_combination] = {
            'hotkey': hotkey_combination,
            'on_release_callback': callback, # Assuming we want to trigger on release
            'on_press_callback': None,
            'actuate_on_partial_release': False,
            'callback_params': None # No additional params needed for now
        }

    def start_listening(self) -> None:
        """Start listening for registered hotkeys."""
        if self.running:
            return

        self.running = True

        # Convert registered hotkeys to the format expected by global_hotkeys
        bindings = list(self.registered_hotkeys.values())

        # Register all of our keybindings
        register_hotkeys(bindings)

        # Start listening for keypresses in a separate thread
        self._listener_thread = threading.Thread(target=start_checking_hotkeys)
        self._listener_thread.daemon = True
        self._listener_thread.start()


    def stop_listening(self) -> None:
        """Stop listening for hotkeys."""
        if not self.running:
            return

        self.running = False
        stop_checking_hotkeys()
        if self._listener_thread and self._listener_thread.is_alive():
             # Give the listener a moment to stop gracefully
            self._listener_thread.join(timeout=1.0)
            self._listener_thread = None


class HotkeyHandler:
    """
    Handles the screenshot hotkey functionality using HotkeyManager.
    """

    def __init__(self, hotkey_combination: str, callback: Callable, suppress: bool = False):
        """
        Initialize the hotkey handler.

        Args:
            hotkey_combination: Hotkey combination string (e.g., 'ctrl+shift+f12')
            callback: Function to call when the hotkey is pressed
            suppress: Whether to suppress the hotkey so it doesn't trigger in other applications
        """
        self.hotkey_manager = HotkeyManager()
        self.hotkey_combination = hotkey_combination
        self.callback = callback
        self.suppress = suppress # Store suppress, though global_hotkeys handles it

    def start(self) -> None:
        """Start the hotkey handler."""
        # Pass suppress to the manager, although global_hotkeys handles it
        self.hotkey_manager.register_hotkey(self.hotkey_combination, self.callback, self.suppress)
        self.hotkey_manager.start_listening()

    def stop(self) -> None:
        """Stop the hotkey handler."""
        self.hotkey_manager.stop_listening()

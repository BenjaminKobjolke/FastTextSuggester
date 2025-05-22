"""
FastTestSuggestor - Screenshot OCR Tool

This tool captures screenshots when a hotkey is pressed,
processes the image with OCR, and saves the text to a file.
It also provides a suggestion window for quick text insertion.
"""
"""
FastTestSuggestor - Screenshot OCR Tool

This tool captures screenshots when a hotkey is pressed,
processes the image with OCR, and saves the text to a file.
It also provides a suggestion window for quick text insertion.
"""
import argparse
import sys
import configparser
import threading
import time
from typing import Optional
import pprint
from src.core.tool_state import ToolState
from src.core.screenshot_ocr_tool import ScreenshotOCRTool
import ctypes

# Import vk_key_names from keycodes.py
try:
    from keycodes import vk_key_names
except ImportError:
    vk_key_names = {}
    print("Warning: keycodes.py not found. Hotkeys will be stored as VK codes.")

MAPVK_VSC_TO_VK = 1

# Import keyboard for key logging and interactive key capture
try:
    import keyboard
except ImportError:
    keyboard = None
    print("Warning: keyboard library not available. Cannot use --log-keys or --register-hotkeys without keyboard.")

# Create a reverse mapping from VK Code to name
VK_TO_NAME_MAP = {v: k for k, v in vk_key_names.items()}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Screenshot OCR Tool")
    parser.add_argument(
        "--config",
        type=str,
        default="settings.ini",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-keys",
        action="store_true",
        help="Run in keycode checker mode to log pressed keys and their VK codes"
    )
    parser.add_argument(
        "--register-hotkeys",
        action="store_true",
        help="Interactively register new hotkey combinations"
    )
    return parser.parse_args()

def capture_hotkey_combination(prompt: str) -> Optional[str]:
    """
    Interactively captures a single hotkey combination from the user using the keyboard library.

    Args:
        prompt: The message to display to the user.

    Returns:
        A string representing the hotkey combination in global_hotkeys format (using VK Codes),
        or None if the user presses Esc.
    """
    if keyboard is None:
        print("Error: keyboard library not available for hotkey registration.")
        return None

    print(prompt)
    print("Press the desired key combination, then press Enter to finalize.")
    print("Press Esc to skip.")

    captured_scan_codes = set()
    combination_result = {"hotkey": None} # Use a dictionary to modify in nested function

    def on_key_event(event):
        if event.event_type == keyboard.KEY_DOWN:
            key_name = event.name
            scan_code = event.scan_code
            vk = vkey_from_sc(scan_code) # Get virtual key code
            
            if key_name == 'esc':
                combination_result["hotkey"] = None
                return False # Stop listener
                
            if key_name == 'enter':
                # Finalize combination using VK codes pressed before Enter
                combination_list = []
                for code in sorted(list(captured_scan_codes)):
                    # Look up string name in the mapping, fallback to hex VK code if not found
                    name = VK_TO_NAME_MAP.get(code, f"0x{code:02X}")
                    combination_list.append(name)
                    
                combination_result["hotkey"] = "+".join(combination_list)
                return False # Stop listener
                
            # Add other pressed key's VK code to the set
            captured_scan_codes.add(vk) # Store VK code instead of scan code
            print(f"Key pressed: {key_name} (VK Code: 0x{vk:02X})")
            return False # Suppress the key event

    # Start the listener and wait for Enter or Esc
    # keyboard.wait() can wait for a specific hotkey, but not easily for *any* key press
    # We'll use on_press and a blocking mechanism
    
    # Temporarily register Enter and Esc as hotkeys to stop the listener
    # This is a bit of a workaround with the keyboard library's API for this use case
    stop_event = threading.Event()

    def stop_listener_on_enter():
        stop_event.set()
        
    def stop_listener_on_esc():
        combination_result["hotkey"] = None
        stop_event.set()

    # Register temporary hotkeys for Enter and Esc
    keyboard.add_hotkey('enter', stop_listener_on_enter)
    keyboard.add_hotkey('esc', stop_listener_on_esc)

    # Listen for all key presses to build the combination
    keyboard.on_press(on_key_event)

    # Wait until Enter or Esc is pressed (handled by the temporary hotkeys)
    stop_event.wait()

    # Unhook the on_press listener and temporary hotkeys
    keyboard.unhook_all() # This might be too broad, unhooking other listeners too
    # A more targeted approach would be to store the hook and unhook it specifically
    # However, for simplicity in this interactive function, unhook_all might suffice
    # If issues arise, we'll need to refine this.

    return combination_result["hotkey"]


def vkey_from_sc(scan_code):
    return ctypes.windll.user32.MapVirtualKeyW(scan_code, MAPVK_VSC_TO_VK)

def run_keyboard_key_logger():
    """Runs a key logger using the keyboard library."""
    if keyboard is None:
        print("Error: keyboard library not available for key logging.")
        sys.exit(1)

    def on_key_event(event):
        if event.event_type == keyboard.KEY_DOWN:
            print(f"Key pressed: {event.name}")
            sc = event.scan_code
            vk = vkey_from_sc(sc)
            print(f"scan_code=0x{sc:02X}, vk_code=0x{vk:02X}")            

    print("Running in key logger mode. Press any key (Press Esc to exit).")
    keyboard.on_press(on_key_event)
    
    # Wait for Esc to be pressed to exit
    keyboard.wait('esc')


if __name__ == "__main__":
    args = parse_arguments()
    print(args)
    if args.log_keys:
        run_keyboard_key_logger()
    elif args.register_hotkeys:
        if keyboard is None: # Check for keyboard library here
            print("Cannot register hotkeys. keyboard library not found.")
            sys.exit(1)
            
        config = configparser.ConfigParser()
        config_path = args.config
        
        try:
            config.read(config_path)
            
            print("--- Register Hotkeys ---")
            
            # Capture Capture Hotkey
            capture_hotkey = capture_hotkey_combination("Press the key combination for Capture:")
            if capture_hotkey is not None:
                if 'Hotkey' not in config:
                    config['Hotkey'] = {}
                config['Hotkey']['combination'] = capture_hotkey
                print(f"Capture hotkey set to: {capture_hotkey}")
            else:
                print("Capture hotkey registration skipped.")
                
            # Capture Suggestion Only Hotkey
            suggestion_hotkey = capture_hotkey_combination("Press the key combination for Suggestion Only:")
            if suggestion_hotkey is not None:
                if 'Hotkey' not in config:
                    config['Hotkey'] = {}
                config['Hotkey']['suggestion_only'] = suggestion_hotkey
                print(f"Suggestion Only hotkey set to: {suggestion_hotkey}")
            else:
                print("Suggestion Only hotkey registration skipped.")
                
            # Write updated config back to file
            with open(config_path, 'w') as configfile:
                config.write(configfile)
                
            print(f"Settings updated in {config_path}")
            sys.exit(0) # Exit after successful registration
            
        except FileNotFoundError:
            print(f"Error: Configuration file not found at {config_path}")
            sys.exit(1)
        except Exception as e:
            print(f"Error during hotkey registration: {e}")
            sys.exit(1)
            
    else:
        # Create and start the Screenshot OCR Tool
        tool = ScreenshotOCRTool()
        tool.start()

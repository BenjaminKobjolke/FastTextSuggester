"""
Selection window for the Screenshot OCR Tool
"""
import tkinter as tk
import win32gui
import time


class SelectionWindow:
    """
    Minimalistic GUI for selecting OCR mode (whole screen or active window).
    """

    def __init__(self, logger=None):
        """
        Initialize the selection window.

        Args:
            logger: Logger instance for logging
        """
        self.logger = logger
        self.window = None
        self.root = None
        self.result = None
        self.last_active_window = None
        self.is_open = False
        
    def create_window(self):
        """Create the selection window."""
        if self.window:
            if self.logger:
                self.logger.warning("Selection window already created")
            return

        # Store the currently active window
        self.last_active_window = win32gui.GetForegroundWindow()
        
        # Create a root window if it doesn't exist
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        if self.logger:
            self.logger.info("Created root Tk window and hidden it")
        
        # Create the actual window as a Toplevel
        self.window = tk.Toplevel(self.root)
        self.window.title("OCR Selection")
        self.window.attributes('-topmost', True)  # Keep on top
        self.window.grab_set()  # Make window modal
        
        # Set window size
        window_width = 400  # Increased width
        window_height = 160  # Increased height
        
        # Get active window position and size
        try:
            left, top, right, bottom = win32gui.GetWindowRect(self.last_active_window)
            active_width = right - left
            active_height = bottom - top
            
            # Calculate position to center in the active window
            x = left + (active_width - window_width) // 2
            y = top + (active_height - window_height) // 2
        except Exception as e:
            # Fallback to center of screen if we can't get active window position
            if self.logger:
                self.logger.error(f"Error getting active window position: {e}")
            
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Configure window appearance
        self.window.configure(bg='#2b2b2b')  # Dark background
        
        # Create label
        label = tk.Label(
            self.window,
            text="Press 1 for whole screen\nPress 2 for active window",
            font=('Arial', 16),  # Increased font size
            bg='#1e1e1e',  # Darker background
            fg='#FFFFFF'  # White text
        )
        label.pack(pady=30)  # Increased padding
        
        # Configure window appearance
        self.window.configure(bg='#1e1e1e')  # Darker background
        
        # Bind key events
        self.window.bind('1', self._on_key_1)
        self.window.bind('2', self._on_key_2)
        self.window.bind('<Escape>', self._on_escape)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._on_escape)
        
        if self.logger:
            self.logger.info("Selection window created")
            
            
    def _on_key_1(self, event=None):
        """Handle key 1 press (whole screen)."""
        self.result = "whole_screen"
        self.window.destroy()
        
    def _on_key_2(self, event=None):
        """Handle key 2 press (active window)."""
        self.result = "active_window"
        self.window.destroy()
        
    def _on_escape(self, event=None):
        """Handle Escape key press (cancel)."""
        self.result = None
        if self.window:
            self.window.destroy()
            self.window = None
        
    def show(self):
        """
        Show the selection window and wait for user input.
        
        Returns:
            str: 'whole_screen', 'active_window', or None if canceled
        """
        if self.logger:
            self.logger.info("Showing selection window")
            
        self.create_window()
        
        # Set flag that window is open
        self.is_open = True
        
        # Make window modal and force focus
        self.window.grab_set()
        self.window.focus_force()
        
        # Start main loop
        self.window.wait_window(self.window)
        
        # Clean up
        self.is_open = False
        
        if self.logger:
            self.logger.info(f"Selection window closed with result: {self.result}")
            
        # Return the result
        return self.result
        
    def close(self):
        """Close the selection window if it's open."""
        if self.logger:
            self.logger.info("Closing selection window")
            
        if self.window:
            self._on_escape()
            return True
        return False

"""
Suggestion window for the Screenshot OCR Tool
"""
import tkinter as tk
import threading
import time
from typing import Callable, List, Optional

import win32gui
import win32con

from src.utils.logger import Logger

from .suggestion_manager import SuggestionManager


class SuggestionWindow:
    """
    Minimalistic GUI for text suggestions from OCR results.
    Provides an input field with auto-suggestions and text insertion.
    """

    def __init__(self, suggestion_manager: SuggestionManager, logger: Logger = None, on_escape_callback: Callable = None):
        """
        Initialize the suggestion window.

        Args:
            suggestion_manager: Manager for text suggestions
            logger: Logger instance for logging
            on_escape_callback: Callback function to call when window is closed by Escape key
        """
        self.suggestion_manager = suggestion_manager
        self.logger = logger
        self.window = None
        self.input_var = None
        self.input_field = None
        self.suggestion_listbox = None
        self.suggestions = []
        self.is_visible = False
        self.last_active_window = None
        self.hotkey_handler = None
        self.ocr_in_progress = False  # Flag to track OCR processing status
        self.on_escape_callback = on_escape_callback  # Callback for Escape key
        self.text_to_insert = None  # Text to insert after window is destroyed
        
    def set_ocr_in_progress(self, in_progress: bool = True):
        """
        Set the OCR processing status flag.
        This method only sets the flag without any UI interaction.
        
        Args:
            in_progress: Whether OCR is currently in progress
        """
        # Just set the flag - no Tkinter calls
        self.ocr_in_progress = in_progress
        
        if self.logger:
            self.logger.info(f"OCR in progress flag set to: {in_progress}")
    
    def update_ocr_status_ui(self):
        """
        Update the UI based on OCR status.
        This method should only be called from the main thread.
        """
        if not self.input_field or not self.window:
            return
            
        try:
            if self.ocr_in_progress:
                # Add red border when OCR is in progress
                self.input_field.configure(
                    highlightthickness=2,
                    highlightbackground='#FF0000',  # Red border
                    highlightcolor='#FF0000'  # Red border when focused
                )
                
                # Only show placeholder if there are no suggestions available
                # and the input field is empty
                has_words = self.suggestion_manager and hasattr(self.suggestion_manager, 'words') and self.suggestion_manager.words
                
                if self.is_visible and not self.input_var.get() and not self.suggestions and not has_words:
                    self.input_var.set("Processing OCR...")
                elif self.input_var.get() == "Processing OCR..." and (self.suggestions or has_words):
                    # Clear placeholder if we have words available
                    self.input_var.set("")
                    
                    # Load suggestions if we have words but no suggestions yet
                    if not self.suggestions and has_words:
                        self.suggestions = self.suggestion_manager.words[:10]
                        self._update_suggestions(self.suggestions)
            else:
                # Remove border when OCR is complete
                self.input_field.configure(
                    highlightthickness=0  # No border
                )
                
                # Clear the placeholder text if it's there
                if self.is_visible and self.input_var.get() == "Processing OCR...":
                    self.input_var.set("")
                
            if self.logger:
                #self.logger.info(f"OCR status UI updated, in progress: {self.ocr_in_progress}")
                pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating OCR status UI: {e}")

    def create_window(self):
        """Create the suggestion window."""
        if self.window:
            self.logger.warning("Suggestion window already created")
            return

        # Create a root window if it doesn't exist
        if not hasattr(self, 'root'):
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the root window
            if self.logger:
                self.logger.info("Created root Tk window and hidden it")
        
        # Create the actual window as a Toplevel
        self.window = tk.Toplevel(self.root)
        self.window.title("OCR Suggestions")
        self.window.overrideredirect(True)  # Remove window border
        self.window.attributes('-topmost', True)  # Keep on top
        self.window.resizable(False, False)
        if self.logger:
            self.logger.info("Created Toplevel window")
        
        # Set window size
        window_width = 500  # Increased width
        window_height = 50  # Increased height
        self.window.geometry(f"{window_width}x{window_height}")
        
        # Configure window appearance
        self.window.configure(bg='#1e1e1e')  # Darker background
        
        # Create input field
        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", self._on_input_change)
        
        self.input_field = tk.Entry(
            self.window,
            textvariable=self.input_var,
            font=('Arial', 16),  # Increased font size
            bg='#2d2d2d',  # Dark background
            fg='#FFFFFF',  # White text
            insertbackground='#FFFFFF',  # White cursor
            relief='flat',  # No border
            highlightthickness=0  # No highlight border
        )
        self.input_field.pack(fill=tk.X, expand=True, padx=8, pady=8)  # Increased padding
        
        # Create suggestion listbox
        self.suggestion_listbox = tk.Listbox(
            self.window,
            font=('Arial', 16),  # Increased font size
            bg='#2d2d2d',  # Dark background
            fg='#FFFFFF',  # White text
            selectbackground='#4a6ea9',  # Blue selection background
            selectforeground='#FFFFFF',  # White text when selected
            relief='flat',  # No border
            highlightthickness=0,  # No highlight border
            height=0
        )
        self.suggestion_listbox.pack(fill=tk.X, expand=True, padx=8)  # Increased padding
        
        # Bind events
        self.input_field.bind('<Return>', self._on_enter)
        self.input_field.bind('<Escape>', self._on_escape)
        self.input_field.bind('<Down>', self._on_down)
        self.input_field.bind('<Up>', self._on_up)
        self.suggestion_listbox.bind('<Return>', self._on_enter)
        self.suggestion_listbox.bind('<Double-Button-1>', self._on_enter)
        self.suggestion_listbox.bind('<Escape>', self._on_escape)
        
        # Hide window initially
        self.window.withdraw()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
        
        # Prevent focus loss from hiding the window
        self.window.bind('<FocusOut>', self._on_focus_out)
        self.logger.info("Suggestion window created")

    def show(self):
        """Show the suggestion window."""
        if not self.window:
            if self.logger:
                self.logger.info("Creating suggestion window")
            self.create_window()
            
        # Use after method to ensure this runs in the main thread
        self.window.after(0, self._show_window)
        
    def _show_window(self):
        """Internal method to show the window in the main thread."""
        try:
            # Store the currently active window
            self.last_active_window = win32gui.GetForegroundWindow()
            
            # Clear input field
            self.input_var.set('')
            
            # Load suggestions from the suggestion manager if available
            if self.suggestion_manager:
                # First check if we have any lines (highest priority)
                if hasattr(self.suggestion_manager, 'lines') and self.suggestion_manager.lines:
                    # Get lines as initial suggestions (limited to top 10)
                    self.suggestions = self.suggestion_manager.lines[:10]
                    self._update_suggestions(self.suggestions)
                # If no lines, fall back to words
                elif hasattr(self.suggestion_manager, 'words') and self.suggestion_manager.words:
                    # Get all words as initial suggestions (limited to top 10)
                    self.suggestions = self.suggestion_manager.words[:10]
                    self._update_suggestions(self.suggestions)
                else:
                    self.suggestions = []
                    self._update_suggestions([])
            else:
                self.suggestions = []
                self._update_suggestions([])
            
            # Get active window position and size
            try:
                left, top, right, bottom = win32gui.GetWindowRect(self.last_active_window)
                active_width = right - left
                active_height = bottom - top
                active_center_x = left + (active_width // 2)
                active_center_y = top + (active_height // 2)
                
                # Calculate window position (center on active window)
                window_width = 500  # Increased width
                window_height = 50  # Increased height
                x = max(0, active_center_x - (window_width // 2))
                y = max(0, active_center_y - (window_height // 2))
            except Exception as e:
                # Fallback to center of screen if we can't get active window position
                if self.logger:
                    self.logger.error(f"Error getting active window position: {e}")
                
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                window_width = 500  # Increased width
                window_height = 50  # Increased height
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
            
            # Position and configure window
            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Enhance window visibility
            self.window.attributes('-topmost', True)
            self.window.configure(bg='#1e1e1e')  # Darker background
            
            # Show window with more aggressive update commands
            self.window.deiconify()
            self.window.update_idletasks()  # Force update
            self.window.update()
            self.window.lift()
            self.window.attributes('-topmost', True)
            self.window.focus_force()
            self.input_field.focus_set()
            self.is_visible = True
            
            # Force another update
            self.window.update_idletasks()
            
            if self.logger:
                self.logger.info("Suggestion window shown")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error showing suggestion window: {e}")

    def hide(self, event=None, text_to_insert=None):
        """
        Hide the suggestion window.
        
        Args:
            event: The event that triggered the hide
            text_to_insert: Text to insert after window is destroyed
        """
        if not self.window:
            return
            
        # Set flag to indicate window should be hidden
        self.is_visible = False
        
        # Store text to insert
        if text_to_insert is not None:
            self.text_to_insert = text_to_insert
        
        # Call the escape callback if provided
        # Note: We don't call this in _hide_window because it might be called multiple times
        if self.on_escape_callback and event is not None:  # Only call if explicitly hidden (not from _on_escape)
            self.logger.info("Window hidden, calling escape callback")
            self.on_escape_callback()
        
        # Schedule the actual hiding to happen in the main thread
        if hasattr(self.window, 'after'):
            self.window.after(0, self._hide_window)
        else:
            # Fallback if window doesn't have after method
            self._hide_window()
            
    def _hide_window(self):
        """Internal method to hide the window in the main thread."""
        try:
            if self.window:
                # Store the last active window before destroying
                last_active = self.last_active_window
                
                # Store text to insert (if any)
                text_to_insert = self.text_to_insert
                
                # Destroy the window completely instead of just hiding it
                self.window.destroy()
                self.window = None
                
                # Don't try to restore focus - let the OS handle it
                
                if self.logger:
                    self.logger.info("Suggestion window destroyed")
                
                # Insert text after window is destroyed (if any)
                if text_to_insert:
                    if self.logger:
                        self.logger.info(f"Inserting text after window destroyed: {text_to_insert}")
                    self.suggestion_manager.insert_text(text_to_insert)
                    self.text_to_insert = None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error destroying suggestion window: {e}")

    def toggle(self):
        """Toggle the suggestion window visibility."""
        if self.is_visible:
            self.hide(None)  # Pass None to prevent hide from calling the callback again
        else:
            # Load data files first
            self.suggestion_manager.load_data_files()
            
            # Then try to load the latest OCR file
            ocr_loaded = self.suggestion_manager.load_latest_ocr_file()
            
            # Show the window regardless of OCR file availability
            # since we now have data files as a source of suggestions
            self.show()
            
            if self.logger:
                if ocr_loaded:
                    self.logger.info("OCR file loaded for toggle")
                else:
                    self.logger.info("No recent OCR file found for toggle, using data files only")

    def _on_input_change(self, *args):
        """Handle input field changes."""
        text = self.input_var.get()
        
        # Check for special commands
        if text == "/exit":
            self.logger.info("Exit command detected, closing application")
            self.exit_application()
            return
        elif text == "/reload":
            self.logger.info("Reload command detected, reloading data files")
            self._reload_data()
            return
            
        if text:
            # Get suggestions
            self.suggestions = self.suggestion_manager.get_suggestions(text)
            self._update_suggestions(self.suggestions)
        else:
            # Clear suggestions
            self.suggestions = []
            self._update_suggestions([])
    
    def _reload_data(self):
        """Reload data files and latest OCR file."""
        # Clear input field
        self.input_var.set("")
        
        # Reload data files
        data_loaded = self.suggestion_manager.load_data_files()
        
        # Reload latest OCR file
        ocr_loaded = self.suggestion_manager.load_latest_ocr_file()
        
        # Update suggestions
        if hasattr(self.suggestion_manager, 'lines') and self.suggestion_manager.lines:
            self.suggestions = self.suggestion_manager.lines[:10]
        elif hasattr(self.suggestion_manager, 'words') and self.suggestion_manager.words:
            self.suggestions = self.suggestion_manager.words[:10]
        else:
            self.suggestions = []
        
        # Update UI
        self._update_suggestions(self.suggestions)
        
        # Show feedback message
        self.input_var.set("Data reloaded successfully")
        
        # Schedule clearing the feedback message after a delay
        if self.window:
            self.window.after(2000, lambda: self.input_var.set(""))
            
    def exit_application(self):
        """Exit the application cleanly."""
        # Hide the window first
        self.hide(None)  # Pass None to prevent hide from calling the callback again
        
        # Schedule application exit after a short delay
        if hasattr(self, 'root') and self.root:
            self.root.after(100, self._perform_exit)
        else:
            self._perform_exit()
            
    def _perform_exit(self):
        """Perform the actual exit."""
        if self.logger:
            self.logger.info("Exiting application via suggestion window command")
        # Use os._exit to forcefully terminate the process
        import os
        os._exit(0)

    def _update_suggestions(self, suggestions: List[str]):
        """Update the suggestion listbox."""
        # Clear listbox
        self.suggestion_listbox.delete(0, tk.END)
        
        # Clear any "Processing OCR..." placeholder
        if self.input_var.get() == "Processing OCR...":
            self.input_var.set("")
        
        if not suggestions:
            # Hide listbox
            self.suggestion_listbox.configure(height=0)
            self.window.geometry(f"{self.window.winfo_width()}x50")  # Increased height
            return
            
        # Add suggestions to listbox
        for suggestion in suggestions:
            self.suggestion_listbox.insert(tk.END, suggestion)
            
        # Update listbox height
        list_height = min(5, len(suggestions))
        self.suggestion_listbox.configure(height=list_height)
        
        # Update window height
        window_height = 50 + (list_height * 30)  # 30 pixels per list item (increased)
        self.window.geometry(f"{self.window.winfo_width()}x{window_height}")
        
        # Select first item
        if suggestions:
            self.suggestion_listbox.selection_set(0)

    def _on_enter(self, event=None):
        """Handle Enter key press."""
        # Get selected suggestion
        selected_idx = self.suggestion_listbox.curselection()
        
        if selected_idx:
            # Use selected suggestion
            selected_text = self.suggestion_listbox.get(selected_idx[0])
        else:
            # Use input text
            selected_text = self.input_var.get()
            
        if selected_text:
            # Call the escape callback if provided
            if self.on_escape_callback:
                self.logger.info("Suggestion selected, calling escape callback")
                self.on_escape_callback()
                
            # Hide window and pass the text to insert after window is destroyed
            self.hide(None, selected_text)  # Pass None to prevent hide from calling the callback again
            
            # Don't try to restore focus - let the OS handle it
            # Text insertion is now handled in _hide_window after the window is destroyed

    def _on_escape(self, event=None):
        """Handle Escape key press."""
        # Call the escape callback if provided
        if self.on_escape_callback:
            self.logger.info("Calling escape callback")
            self.on_escape_callback()
        self.hide(None)  # Pass None to prevent hide from calling the callback again

    def _on_down(self, event=None):
        """Handle Down key press."""
        if not self.suggestions:
            return
            
        # Get current selection
        selected_idx = self.suggestion_listbox.curselection()
        
        if not selected_idx:
            # Select first item
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.focus_set()
        elif selected_idx[0] < len(self.suggestions) - 1:
            # Select next item
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(selected_idx[0] + 1)
            self.suggestion_listbox.see(selected_idx[0] + 1)
            self.suggestion_listbox.focus_set()

    def _on_up(self, event=None):
        """Handle Up key press."""
        if not self.suggestions:
            return
            
        # Get current selection
        selected_idx = self.suggestion_listbox.curselection()
        
        if selected_idx and selected_idx[0] > 0:
            # Select previous item
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(selected_idx[0] - 1)
            self.suggestion_listbox.see(selected_idx[0] - 1)
            self.suggestion_listbox.focus_set()
        else:
            # Return focus to input field
            self.input_field.focus_set()

    def _on_focus_out(self, event=None):
        """Handle window focus loss."""
        # Don't hide if focus is still within our window
        if event.widget.focus_get() is not None:
            return
            
        # Small delay to allow for focus changes within our application
        self.window.after(100, self._check_focus)

    def _check_focus(self):
        """Check if focus is still within our window."""
        if self.window.focus_get() is None:
            # Call the escape callback if provided
            if self.on_escape_callback:
                self.logger.info("Window lost focus, calling escape callback")
                self.on_escape_callback()
            self.hide(None)  # Pass None to prevent hide from calling the callback again

    def set_hotkey_handler(self, handler: Callable):
        """
        Set the hotkey handler for toggling the window.

        Args:
            handler: Callback function for hotkey press
        """
        self.hotkey_handler = handler

    def run(self):
        """Run the suggestion window main loop."""
        if not self.window:
            self.create_window()
        self.window.mainloop()

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

    def __init__(self, suggestion_manager: SuggestionManager, logger: Logger = None):
        """
        Initialize the suggestion window.

        Args:
            suggestion_manager: Manager for text suggestions
            logger: Logger instance for logging
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
        window_width = 400
        window_height = 40
        self.window.geometry(f"{window_width}x{window_height}")
        
        # Configure window appearance
        self.window.configure(bg='#2b2b2b')  # Dark background
        
        # Create input field
        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", self._on_input_change)
        
        self.input_field = tk.Entry(
            self.window,
            textvariable=self.input_var,
            font=('Arial', 14),  # Larger font
            bg='#FFFFFF',  # White background
            fg='#000000',  # Black text
            insertbackground='#000000',  # Black cursor
            relief='flat',  # No border
            highlightthickness=0  # No highlight border
        )
        self.input_field.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Create suggestion listbox
        self.suggestion_listbox = tk.Listbox(
            self.window,
            font=('Arial', 14),  # Larger font
            bg='#FFFFFF',  # White background
            fg='#000000',  # Black text
            selectbackground='#4a6ea9',  # Blue selection background
            selectforeground='#FFFFFF',  # White text when selected
            relief='flat',  # No border
            highlightthickness=0,  # No highlight border
            height=0
        )
        self.suggestion_listbox.pack(fill=tk.X, expand=True, padx=5)
        
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
            if self.suggestion_manager and hasattr(self.suggestion_manager, 'words') and self.suggestion_manager.words:
                # Get all words as initial suggestions (limited to top 10)
                self.suggestions = self.suggestion_manager.words[:10]
                self._update_suggestions(self.suggestions)
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
                window_width = 400
                window_height = 40
                x = max(0, active_center_x - (window_width // 2))
                y = max(0, active_center_y - (window_height // 2))
            except Exception as e:
                # Fallback to center of screen if we can't get active window position
                if self.logger:
                    self.logger.error(f"Error getting active window position: {e}")
                
                screen_width = self.window.winfo_screenwidth()
                screen_height = self.window.winfo_screenheight()
                window_width = 400
                window_height = 40
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
            
            # Position and configure window
            self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Enhance window visibility
            self.window.attributes('-topmost', True)
            self.window.configure(bg='#2b2b2b')  # Dark background
            
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

    def hide(self, event=None):
        """Hide the suggestion window."""
        if not self.window:
            return
            
        # Set flag to indicate window should be hidden
        self.is_visible = False
        
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
                self.window.withdraw()
                
                # Restore focus to the previous window
                if self.last_active_window:
                    try:
                        win32gui.SetForegroundWindow(self.last_active_window)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Error restoring focus: {e}")
                
                if self.logger:
                    self.logger.info("Suggestion window hidden")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error hiding suggestion window: {e}")

    def toggle(self):
        """Toggle the suggestion window visibility."""
        if self.is_visible:
            self.hide()
        else:
            # Load the latest OCR file
            if self.suggestion_manager.load_latest_ocr_file():
                self.show()
            else:
                if self.logger:
                    self.logger.warning("No OCR file found, not showing suggestion window")

    def _on_input_change(self, *args):
        """Handle input field changes."""
        text = self.input_var.get()
        
        # Check for special commands
        if text == "/exit":
            self.logger.info("Exit command detected, closing application")
            self.exit_application()
            return
            
        if text:
            # Get suggestions
            self.suggestions = self.suggestion_manager.get_suggestions(text)
            self._update_suggestions(self.suggestions)
        else:
            # Clear suggestions
            self.suggestions = []
            self._update_suggestions([])
            
    def exit_application(self):
        """Exit the application cleanly."""
        # Hide the window first
        self.hide()
        
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
            self.window.geometry(f"{self.window.winfo_width()}x40")
            return
            
        # Add suggestions to listbox
        for suggestion in suggestions:
            self.suggestion_listbox.insert(tk.END, suggestion)
            
        # Update listbox height
        list_height = min(5, len(suggestions))
        self.suggestion_listbox.configure(height=list_height)
        
        # Update window height
        window_height = 40 + (list_height * 24)  # 24 pixels per list item
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
            # Hide window
            self.hide()
            
            # Restore focus to the previous window
            if self.last_active_window:
                try:
                    win32gui.SetForegroundWindow(self.last_active_window)
                    time.sleep(0.1)  # Small delay to ensure window is active
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error restoring focus: {e}")
            
            # Insert text
            self.suggestion_manager.insert_text(selected_text)
            
            # Don't automatically show window again - let the user press the hotkey if needed

    def _on_escape(self, event=None):
        """Handle Escape key press."""
        self.hide()

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
            self.hide()

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

import os
import sys

# Set TCL/TK environment variables before tkinter is imported
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    base_path = sys._MEIPASS

    # Try different possible locations
    for tcl_ver in ['tcl8.6', 'tcl8', 'tcl']:
        tcl_path = os.path.join(base_path, tcl_ver)
        if os.path.exists(tcl_path):
            os.environ['TCL_LIBRARY'] = tcl_path
            break

    for tk_ver in ['tk8.6', 'tk8', 'tk']:
        tk_path = os.path.join(base_path, tk_ver)
        if os.path.exists(tk_path):
            os.environ['TK_LIBRARY'] = tk_path
            break

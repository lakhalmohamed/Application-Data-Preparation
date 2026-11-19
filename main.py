"""
AutoDataPrep - Main Application Entry Point
Intelligent Desktop Studio for Machine Learning Data Preparation.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Enable High DPI scaling on Windows if available
if sys.platform.startswith("win"):
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from ui.main_window import MainWindow


def main():
    """Starts the AutoDataPrep desktop application."""
    root = tk.Tk()
    
    # Configure minimal default geometry
    root.geometry("1280x820")
    
    # Set window icon if available or title
    root.title("AutoDataPrep — Studio Intelligent de Préparation des Données ML")
    
    try:
        app = MainWindow(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur Inattendue", f"Une erreur critique est survenue :\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

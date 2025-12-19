import tkinter as tk
from tkinter import ttk
from Vues.DataRecoveryApp import DataRecoveryApp

# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    
    # Style
    style = ttk.Style()
    style.theme_use('clam')
    
    app = DataRecoveryApp(root)
    root.mainloop()
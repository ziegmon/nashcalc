import tkinter as tk
from gui import NashCalculatorGUI
import traceback

if __name__ == "__main__":
    root = tk.Tk()
    app = NashCalculatorGUI(root)
    root.mainloop()
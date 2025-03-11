"""
Mass Spectrometry Data Processing Package
"""

from .data_processor import DataProcessor
from .voltage_plotter import VoltagePlotter
import tkinter as tk  # Import Tkinter globally

__version__ = "0.2.0"

def launch_difference_plotter():
    """Launches the GUI for the Difference Plotter."""
    from .gui import App  # Import inside function to prevent auto-launch

    root = tk.Tk()  # Create a fresh Tk instance
    app = App(root)

    # Ensure window fully closes before exiting event loop
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def launch_intensity_gui():
    """Launches the GUI for Intensity Over Time."""
    from .intensity_over_time import App as IntensityApp

    root = tk.Tk()  # Create a fresh Tk instance
    intensity_app = IntensityApp(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def launch_single_waveform_gui():
    """Launches the GUI for Single Waveform Analysis."""
    from .single_waveform import App as SingleWaveformApp

    root = tk.Tk()  # Create a fresh Tk instance
    single_waveform_app = SingleWaveformApp(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def on_close(root):
    """Properly destroys the Tkinter window to prevent reopening."""
    root.destroy()  # Fully destroy the window

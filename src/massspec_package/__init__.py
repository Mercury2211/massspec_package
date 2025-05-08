"""
Mass Spectrometry Data Processing Package
"""

from .data_processor import DataProcessor
from .voltage_plotter import VoltagePlotter
import tkinter as tk
import gc  # Import garbage collection module

__version__ = "0.2.0"

def launch_background_subtractor():
    """Launches the GUI for the Difference Plotter."""
    from .gui import App

    root = tk.Tk()
    app = App(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def launch_intensity_over_time():
    """Launches the GUI for Intensity Over Time."""
    from .intensity_over_time import App as IntensityApp

    root = tk.Tk()
    intensity_app = IntensityApp(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def launch_single_waveform_analysis():
    """Launches the GUI for Single Waveform Analysis."""
    from .single_waveform import App as SingleWaveformApp

    root = tk.Tk()
    single_waveform_app = SingleWaveformApp(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def launch_calibration():
    """Launches the GUI for Calibration."""
    from .calibration import App as CalibrationApp

    root = tk.Tk()
    calibration_app = CalibrationApp(root)

    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root))
    root.mainloop()

def on_close(root):
    """Ensures Tkinter is fully shut down and does not restart."""
    root.quit()      # Stop the main loop
    root.destroy()   # Destroy the window
    del root         # Remove root reference
    gc.collect()     # Force garbage collection

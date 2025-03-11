# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 11:07:59 2025

@author: iseli
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import re  # <-- We'll use regex for extracting digits from filenames
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

###############################################################################
# LOCAL DataProcessor
###############################################################################
class DataProcessor:
    """
    A local DataProcessor that includes get_files() so intensity_over_time.py 
    doesn't rely on data_processor.py.
    """
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def load_file(self, file_path):
        try:
            return np.fromfile(file_path, dtype=np.uint32)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return np.array([])

    def get_files(self):
        """
        Return a list of .data32 files in the folder_path,
        sorted by the numeric portion after 'Ch1_' if present.
        """
        if not self.folder_path:
            return []
        
        # All .data32 files
        raw_files = [f for f in os.listdir(self.folder_path) if f.endswith(".data32")]

        def numeric_key(fname):
            """
            Extract integer after 'Ch1_' in the filename.
            E.g. 'AP240 Ch1_10.data32' => 10
            If none found, return a large fallback or 0 so 
            they appear either at the start or end.
            """
            match = re.search(r"Ch1_(\d+)", fname)
            if match:
                return int(match.group(1))
            else:
                return 0  # or some fallback if you want them last

        # Sort using our numeric key
        sorted_files = sorted(raw_files, key=numeric_key)
        return sorted_files


###############################################################################
# VoltagePlotter for Intensity Over Time
###############################################################################
class VoltagePlotter:
    def __init__(self, measurement_processor):
        self.measurement_processor = measurement_processor
        self.x_min = 0
        self.x_max = None
        self.skip_interval = 1

    def plot_first_measurement(self):
        files = self.measurement_processor.get_files()
        if not files:
            messagebox.showwarning("Error", "No files available to plot.")
            return
        
        first_file = os.path.join(self.measurement_processor.folder_path, files[0])
        data = self.measurement_processor.load_file(first_file)
        
        if data.size == 0:
            messagebox.showerror("Error", f"Failed to load data from {files[0]}.")
            return
        
        plt.figure(figsize=(10, 5))
        plt.plot(np.arange(len(data)), data, linestyle='-')
        plt.xlabel("Sample Number")
        plt.ylabel("Value")
        plt.title(f"First Measurement: {files[0]}")
        plt.grid()
        plt.show()

    def plot_max_values(self):
        files = self.measurement_processor.get_files()
        if not files:
            messagebox.showwarning("Error", "No files available to process.")
            return
        
        max_values = []
        # If the user wants to skip files (e.g. skip_interval=2),
        # we select only every nth file
        selected_files = files[::self.skip_interval]
        
        file_numbers = list(range(1, len(selected_files) + 1))
        
        for file_name in selected_files:
            file_path = os.path.join(self.measurement_processor.folder_path, file_name)
            data = self.measurement_processor.load_file(file_path)
            
            if data.size == 0:
                messagebox.showerror("Error", f"Failed to load data from {file_name}.")
                max_values.append(None)
                continue
            
            x_upper = min(self.x_max, len(data)) if self.x_max else len(data)
            max_val = np.max(data[self.x_min:x_upper])
            max_values.append(max_val)
        
        # Plot
        plt.figure(figsize=(10, 5))
        plt.plot(file_numbers, max_values, marker='o', linestyle='-')
        plt.xlabel("File Number")
        plt.ylabel("Maximum Value")
        plt.title("Maximum Value in Selected X-Range per File")
        plt.grid()
        plt.show()

        return (selected_files, max_values)

    def set_x_range(self, x_min, x_max):
        self.x_min = x_min
        self.x_max = x_max

    def set_skip_interval(self, interval):
        self.skip_interval = max(1, interval)


###############################################################################
# App GUI for Intensity Over Time
###############################################################################
class App:
    def __init__(self, root):
        self.root = root
        self.measurement_folder = None

        # We'll store each file's max value here so we can save them:
        # keys = filenames, values = computed max values
        self.max_data = {}

        self.root.title("Intensity over Time Analysis")
        self.root.geometry("800x600")
        self.init_ui()

    def init_ui(self):
        ttk.Label(
            self.root,
            text="Intensity over Time Analysis",
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)
        
        folder_frame = ttk.Frame(self.root, padding=10)
        folder_frame.pack(pady=10, fill="x")
        
        ttk.Label(folder_frame, text="Select Measurement Folder:").grid(row=0, column=0, sticky="w")
        ttk.Button(folder_frame, text="Browse", command=self.select_measurement_folder).grid(row=0, column=1)
        self.measurement_label = ttk.Label(folder_frame, text="No folder selected", foreground="#808080")
        self.measurement_label.grid(row=1, column=0, columnspan=2, sticky="w")
        
        range_frame = ttk.Frame(self.root, padding=10)
        range_frame.pack()
        
        ttk.Label(range_frame, text="X-Range: Min:").grid(row=0, column=0)
        self.x_min_entry = ttk.Entry(range_frame, width=10)
        self.x_min_entry.grid(row=0, column=1)
        
        ttk.Label(range_frame, text="Max:").grid(row=0, column=2)
        self.x_max_entry = ttk.Entry(range_frame, width=10)
        self.x_max_entry.grid(row=0, column=3)
        
        ttk.Label(range_frame, text="Skip Files Interval:").grid(row=1, column=0)
        self.skip_entry = ttk.Entry(range_frame, width=10)
        self.skip_entry.grid(row=1, column=1)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack()
        
        ttk.Button(button_frame, text="Plot Max Values", command=self.plot_max_values).grid(row=0, column=0, padx=10)

        # Add "Save Data" button to export the computed max values
        ttk.Button(button_frame, text="Save Data", command=self.save_data).grid(row=0, column=1, padx=10)

        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(row=0, column=2, padx=10)
    
    def select_measurement_folder(self):
        """
        Let user pick a measurement folder containing .data32 files.
        We'll build our local DataProcessor & VoltagePlotter,
        and do a quick 'plot_first_measurement' as a preview.
        """
        self.measurement_folder = filedialog.askdirectory()
        self.measurement_label.config(
            text=os.path.basename(self.measurement_folder) if self.measurement_folder else "No folder selected"
        )

        if self.measurement_folder:
            # Use the LOCAL DataProcessor (see above)
            self.measurement_processor = DataProcessor(self.measurement_folder)
            self.voltage_plotter = VoltagePlotter(self.measurement_processor)
            # Quick preview of the first measurement
            self.voltage_plotter.plot_first_measurement()
    
    def plot_max_values(self):
        """
        Compute & plot the max values for each .data32 file 
        based on user-specified x-range & skip interval.
        """
        if not hasattr(self, 'measurement_processor'):
            messagebox.showwarning("No Folder", "Please select a measurement folder first.")
            return

        # Parse user inputs
        try:
            x_min = int(self.x_min_entry.get()) if self.x_min_entry.get() else 0
            x_max = int(self.x_max_entry.get()) if self.x_max_entry.get() else None
            skip_interval = int(self.skip_entry.get()) if self.skip_entry.get() else 1
        except ValueError:
            messagebox.showerror("Error", "Invalid input values for X-range or skip interval.")
            return
        
        self.voltage_plotter.set_x_range(x_min, x_max)
        self.voltage_plotter.set_skip_interval(skip_interval)

        # Plot & store results
        results = self.voltage_plotter.plot_max_values()
        if results is None:
            return

        file_names, max_values = results
        # Store them in self.max_data
        self.max_data.clear()
        for fname, val in zip(file_names, max_values):
            if val is not None:
                self.max_data[fname] = val
    
    def save_data(self):
        """
        Save the computed max_values to a CSV with columns:
        Filename, MaxValue

        Also sorted by the numeric portion after 'Ch1_' if present,
        so "AP240 Ch1_2.data32" < "AP240 Ch1_10.data32", etc.
        """
        if not self.max_data:
            messagebox.showwarning("No Data", "No max values to save. Please plot first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Intensity Data",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")]
        )

        if not file_path:
            return  # user canceled

        # We'll do a numeric sort based on digits after 'Ch1_' 
        def numeric_key(fname):
            match = re.search(r"Ch1_(\d+)", fname)
            if match:
                return int(match.group(1))
            else:
                return 0  # fallback

        # Sort filenames with numeric logic
        sorted_files = sorted(self.max_data.keys(), key=numeric_key)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Write header
                f.write("FileName,MaxValue\n")
                # Each row: file_name, max_val
                for fname in sorted_files:
                    max_val = self.max_data[fname]
                    f.write(f"{fname},{max_val}\n")

            messagebox.showinfo("Data Saved", f"Intensity data saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Data", str(e))

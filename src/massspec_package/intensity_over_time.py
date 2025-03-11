# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 11:07:59 2025

@author: iseli
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class DataProcessor:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def load_file(self, file_path):
        try:
            return np.fromfile(file_path, dtype=np.uint32)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return np.array([])

    def get_files(self):
        return [f for f in os.listdir(self.folder_path) if f.endswith(".data32")]

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
        selected_files = files[::self.skip_interval]  # Select files based on skip interval
        file_numbers = list(range(1, len(selected_files) + 1))
        
        for file_name in selected_files:
            file_path = os.path.join(self.measurement_processor.folder_path, file_name)
            data = self.measurement_processor.load_file(file_path)
            
            if data.size == 0:
                messagebox.showerror("Error", f"Failed to load data from {file_name}.")
                continue
            
            x_upper = min(self.x_max, len(data)) if self.x_max else len(data)
            max_values.append(np.max(data[self.x_min:x_upper]))
        
        plt.figure(figsize=(10, 5))
        plt.plot(file_numbers, max_values, marker='o', linestyle='-')
        plt.xlabel("File Number")
        plt.ylabel("Maximum Value")
        plt.title("Maximum Value in Selected X-Range per File")
        plt.grid()
        plt.show()
    
    def set_x_range(self, x_min, x_max):
        self.x_min = x_min
        self.x_max = x_max
    
    def set_skip_interval(self, interval):
        self.skip_interval = max(1, interval)  # Ensure at least every file is considered

class App:
    def __init__(self, root):
        self.root = root
        self.measurement_folder = None
        
        self.root.title("Intensity over Time Analysis")
        self.root.geometry("800x600")
        self.init_ui()

    def init_ui(self):
        ttk.Label(self.root, text="Intensity over Time Analysis", font=("Helvetica", 14, "bold")).pack(pady=10)
        
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
        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(row=0, column=1, padx=10)
    
    def select_measurement_folder(self):
        self.measurement_folder = filedialog.askdirectory()
        self.measurement_label.config(text=os.path.basename(self.measurement_folder) if self.measurement_folder else "No folder selected")
        
        if self.measurement_folder:
            self.measurement_processor = DataProcessor(self.measurement_folder)
            self.voltage_plotter = VoltagePlotter(self.measurement_processor)
            self.voltage_plotter.plot_first_measurement()
    
    def plot_max_values(self):
        try:
            x_min = int(self.x_min_entry.get()) if self.x_min_entry.get() else 0
            x_max = int(self.x_max_entry.get()) if self.x_max_entry.get() else None
            skip_interval = int(self.skip_entry.get()) if self.skip_entry.get() else 1
        except ValueError:
            messagebox.showerror("Error", "Invalid input values.")
            return
        
        self.voltage_plotter.set_x_range(x_min, x_max)
        self.voltage_plotter.set_skip_interval(skip_interval)
        self.voltage_plotter.plot_max_values()

root = tk.Tk()
app = App(root)
root.mainloop()

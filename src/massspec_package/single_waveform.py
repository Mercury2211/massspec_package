import numpy as np
import matplotlib.pyplot as plt
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading


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
        self.selected_files = []

    def plot_selected_waveforms(self):
        if not self.selected_files:
            return
        
        plt.figure(figsize=(14, 6))
        
        for file_name in self.selected_files:
            file_path = os.path.join(self.measurement_processor.folder_path, file_name)
            data = self.measurement_processor.load_file(file_path)
            
            if data.size == 0:
                messagebox.showerror("Error", f"Failed to load data from {file_name}.")
                continue
            
            plt.plot(np.arange(len(data)), data, label=file_name)
        
        plt.title("Selected Waveforms")
        plt.legend()
        plt.grid()
        plt.show()

    def set_selected_files(self, file_names):
        self.selected_files = file_names


class App:
    def __init__(self, root):
        self.root = root
        self.measurement_folder = None
        
        self.root.title("Single Waveform Analysis")
        self.root.geometry("800x600")
        self.init_ui()

    def init_ui(self):
        ttk.Label(self.root, text="Single Waveform Analysis", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        folder_frame = ttk.Frame(self.root, padding=10)
        folder_frame.pack(pady=10, fill="x")
        
        ttk.Label(folder_frame, text="Select Measurement Folder:").grid(row=0, column=0, sticky="w")
        ttk.Button(folder_frame, text="Browse", command=self.select_measurement_folder).grid(row=0, column=1)
        self.measurement_label = ttk.Label(folder_frame, text="No folder selected", foreground="#808080")
        self.measurement_label.grid(row=1, column=0, columnspan=2, sticky="w")
        
        self.file_selector = tk.Listbox(self.root, selectmode=tk.MULTIPLE, height=10, exportselection=False)
        self.file_selector.pack(pady=10, fill="both", expand=True)
        
        button_frame = ttk.Frame(self.root)
        button_frame.pack()
        
        ttk.Button(button_frame, text="Plot", command=self.plot_waveforms).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(row=0, column=1, padx=10)

    def select_measurement_folder(self):
        self.measurement_folder = filedialog.askdirectory()
        self.measurement_label.config(text=os.path.basename(self.measurement_folder) if self.measurement_folder else "No folder selected")
        
        if self.measurement_folder:
            self.measurement_processor = DataProcessor(self.measurement_folder)
            files = self.measurement_processor.get_files()
            self.file_selector.delete(0, tk.END)
            for file in files:
                self.file_selector.insert(tk.END, file)

    def plot_waveforms(self):
        selected_indices = self.file_selector.curselection()
        selected_files = [self.file_selector.get(i) for i in selected_indices]
        
        if not selected_files:
            messagebox.showwarning("Error", "No files selected.")
            return
        
        self.voltage_plotter = VoltagePlotter(self.measurement_processor)
        self.voltage_plotter.set_selected_files(selected_files)
        self.voltage_plotter.plot_selected_waveforms()


#root = tk.Tk()
#app = App(root)
#root.mainloop()

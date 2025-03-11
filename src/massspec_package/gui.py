import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from .data_processor import DataProcessor
from .voltage_plotter import VoltagePlotter

class App:
    def __init__(self, root):
        self.root = root
        self.measurement_folder = None
        self.background_folder = None
        self.data_processed = False
        self.total_files = 0
        self.processed_files = 0
        self.stop_event = threading.Event()  # Event to stop background threads

        # Configure the GUI window
        self.root.title("Voltage Data Processor")
        self.root.geometry("500x450")
        self.root.config(bg="#f0f0f5")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Styles
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Helvetica", 10))
        self.style.configure("TLabel", font=("Helvetica", 10), background="#f0f0f5")
        self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"), foreground="#4b0082")

        # Title label
        title_label = ttk.Label(root, text="Voltage Data Processor", style="Title.TLabel")
        title_label.pack(pady=10)

        # Folder selection frame
        folder_frame = ttk.Frame(root, padding="10")
        folder_frame.pack(pady=10, fill="x")

        # Measurement folder
        ttk.Label(folder_frame, text="Select Measurement Data Folder:").grid(row=0, column=0, sticky="w")
        ttk.Button(folder_frame, text="Browse", command=self.select_measurement_folder).grid(row=0, column=1, padx=5)
        self.measurement_folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="#808080")
        self.measurement_folder_label.grid(row=1, column=0, columnspan=2, sticky="w")

        # Background folder
        ttk.Label(folder_frame, text="Select Background Data Folder:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Button(folder_frame, text="Browse", command=self.select_background_folder).grid(row=2, column=1, padx=5)
        self.background_folder_label = ttk.Label(folder_frame, text="No folder selected", foreground="#808080")
        self.background_folder_label.grid(row=3, column=0, columnspan=2, sticky="w")

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=20)

        # Buttons frame
        button_frame = ttk.Frame(root)
        button_frame.pack(pady=10)

        process_button = ttk.Button(button_frame, text="Process and Plot", command=self.start_processing)
        process_button.grid(row=0, column=0, padx=10)

        self.plot_button = ttk.Button(button_frame, text="Plot Only", command=self.plot_only, state="disabled")
        self.plot_button.grid(row=0, column=1, padx=10)

        close_button = ttk.Button(button_frame, text="Close", command=self.on_closing)
        close_button.grid(row=0, column=2, padx=10)

    def select_measurement_folder(self):
        self.measurement_folder = filedialog.askdirectory(title="Select Measurement Folder")
        if self.measurement_folder:
            folder_name = os.path.basename(self.measurement_folder)
            self.measurement_folder_label.config(text=folder_name, foreground="#004080", font=("Helvetica", 10, "bold"))

    def select_background_folder(self):
        self.background_folder = filedialog.askdirectory(title="Select Background Folder")
        if self.background_folder:
            folder_name = os.path.basename(self.background_folder)
            self.background_folder_label.config(text=folder_name, foreground="#004080", font=("Helvetica", 10, "bold"))

    def count_total_files(self):
        measurement_files = len([f for f in os.listdir(self.measurement_folder) if f.endswith(".data32")])
        background_files = len([f for f in os.listdir(self.background_folder) if f.endswith(".data32")])
        self.total_files = measurement_files + background_files
        self.processed_files = 0

    def update_progress(self, current):
        self.processed_files += 1
        progress_value = (self.processed_files / self.total_files) * 100
        self.progress["value"] = progress_value
        self.root.update_idletasks()

    def start_processing(self):
        if not self.measurement_folder or not self.background_folder:
            messagebox.showwarning("Folders Not Selected", "Please select both folders before proceeding.")
            return

        self.count_total_files()
        self.progress["value"] = 0
        self.plot_button.config(state="disabled")
        self.data_processed = False
        self.stop_event.clear()

        threading.Thread(target=self.process_and_plot).start()

    def process_and_plot(self):
        try:
            measurement_processor = DataProcessor(self.measurement_folder, self.update_progress, self.stop_event)
            background_processor = DataProcessor(self.background_folder, self.update_progress, self.stop_event)

            self.voltage_plotter = VoltagePlotter(measurement_processor, background_processor)
            self.voltage_plotter.calculate_difference()

            self.data_processed = True
            self.root.after(0, lambda: self.plot_button.config(state="normal"))
            self.root.after(0, self.voltage_plotter.plot_difference)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def plot_only(self):
        if self.data_processed:
            self.voltage_plotter.plot_difference()
        else:
            messagebox.showinfo("No Data", "Data has not been processed yet. Please use 'Process and Plot' first.")

    def on_closing(self):
        self.stop_event.set()  # Signal the processing thread to stop
        self.root.destroy()  # Close the GUI window

import numpy as np
import matplotlib.pyplot as plt
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

###############################################################################
# LOCAL DataProcessor
###############################################################################
class DataProcessor:
    """
    A local DataProcessor that includes get_files() so single_waveform.py doesn't
    rely on data_processor.py.
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
        Return a list of .data32 files in the folder_path.
        """
        if not self.folder_path:
            return []
        return [
            f for f in os.listdir(self.folder_path)
            if f.endswith(".data32")
        ]


###############################################################################
# VoltagePlotter
###############################################################################
class VoltagePlotter:
    """
    Responsible for plotting selected waveforms from the measurement processor.
    """
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


###############################################################################
# App class (GUI)
###############################################################################
class App:
    """
    A GUI for selecting multiple waveforms, plotting them,
    and saving them in columns of a CSV file.
    """

    def __init__(self, root):
        self.root = root
        self.measurement_folder = None

        # waveforms stored here so we can save them
        # Key = filename, Value = NumPy array of data
        self.waveform_data = {}

        self.root.title("Single Waveform Analysis")
        self.root.geometry("800x600")
        self.init_ui()

    def init_ui(self):
        ttk.Label(
            self.root, 
            text="Single Waveform Analysis",
            font=("Helvetica", 14, "bold")
        ).pack(pady=10)

        folder_frame = ttk.Frame(self.root, padding=10)
        folder_frame.pack(pady=10, fill="x")

        ttk.Label(folder_frame, text="Select Measurement Folder:").grid(row=0, column=0, sticky="w")
        ttk.Button(folder_frame, text="Browse", command=self.select_measurement_folder).grid(row=0, column=1)
        self.measurement_label = ttk.Label(folder_frame, text="No folder selected", foreground="#808080")
        self.measurement_label.grid(row=1, column=0, columnspan=2, sticky="w")

        self.file_selector = tk.Listbox(
            self.root, 
            selectmode=tk.MULTIPLE, 
            height=10, 
            exportselection=False
        )
        self.file_selector.pack(pady=10, fill="both", expand=True)

        button_frame = ttk.Frame(self.root)
        button_frame.pack()

        # Plot button
        ttk.Button(button_frame, text="Plot", command=self.plot_waveforms).grid(row=0, column=0, padx=10)

        # Save Data button
        ttk.Button(button_frame, text="Save Data", command=self.save_data).grid(row=0, column=1, padx=10)

        # Close
        ttk.Button(button_frame, text="Close", command=self.root.destroy).grid(row=0, column=2, padx=10)

    def select_measurement_folder(self):
        """
        Let user pick a folder containing .data32 files
        and populate the listbox with those files.
        """
        self.measurement_folder = filedialog.askdirectory()
        self.measurement_label.config(
            text=os.path.basename(self.measurement_folder) if self.measurement_folder else "No folder selected"
        )

        if self.measurement_folder:
            # Build a local DataProcessor for the chosen folder
            self.measurement_processor = DataProcessor(self.measurement_folder)
            files = self.measurement_processor.get_files()
            self.file_selector.delete(0, tk.END)
            for file in files:
                self.file_selector.insert(tk.END, file)

    def plot_waveforms(self):
        """
        Load selected waveforms and plot them.
        """
        selected_indices = self.file_selector.curselection()
        selected_files = [self.file_selector.get(i) for i in selected_indices]

        # Debug: show what the user selected
        #print("DEBUG: Selected files in plot_waveforms:", selected_files)

        if not selected_files:
            messagebox.showwarning("Error", "No files selected.")
            return

        # Build a VoltagePlotter
        self.voltage_plotter = VoltagePlotter(self.measurement_processor)
        self.voltage_plotter.set_selected_files(selected_files)

        # Clear old waveforms
        self.waveform_data.clear()

        # Load and store waveforms
        for file_name in selected_files:
            file_path = os.path.join(self.measurement_folder, file_name)
            data = self.measurement_processor.load_file(file_path)
            if data.size > 0:
                self.waveform_data[file_name] = data

        # Debug: show what we stored
        print("DEBUG: waveforms stored keys:", list(self.waveform_data.keys()))

        # Plot them
        self.voltage_plotter.plot_selected_waveforms()

    def save_data(self):
        """
        Save waveforms in self.waveform_data to a single CSV file,
        each waveform in a separate column.
        """
        # Debug: what's inside waveforms before saving
        print("DEBUG: waveforms being saved:", list(self.waveform_data.keys()))

        if not self.waveform_data:
            messagebox.showwarning("No Data", "No waveforms to save. Please plot first.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Save Waveform Data",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt")]
        )

        if not file_path:
            return  # user canceled

        # Sort filenames so columns appear in a consistent order
        file_names = sorted(self.waveform_data.keys())
        # Retrieve waveforms in the same order
        waveforms = [self.waveform_data[f] for f in file_names]

        # Find the maximum length among all waveforms
        max_length = max(len(w) for w in waveforms)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Write a header row with file names
                f.write(",".join(file_names) + "\n")

                # For each row up to max_length
                for i in range(max_length):
                    row_values = []
                    for w in waveforms:
                        # If that waveform has a value at index i, use it; otherwise, empty
                        if i < len(w):
                            row_values.append(str(w[i]))
                        else:
                            row_values.append("")
                    f.write(",".join(row_values) + "\n")

            messagebox.showinfo("Data Saved", f"Waveform data saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Data", str(e))

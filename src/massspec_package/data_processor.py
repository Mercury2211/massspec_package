import os
import numpy as np

class DataProcessor:
    def __init__(self, folder_path, progress_callback=None, stop_event=None):
        self.folder_path = folder_path
        self.progress_callback = progress_callback
        self.stop_event = stop_event  # Event to signal the thread to stop

    def load_and_decode_file_to_decimal(self, file_path):
        decoded_values = []
        with open(file_path, 'rb') as file:
            while not self.stop_event.is_set():  # Check if stop event is triggered
                chunk = file.read(4)
                if not chunk:
                    break
                decoded_values.append(int.from_bytes(chunk, byteorder='little'))
        return decoded_values

    def calculate_summed_voltages(self):
        all_decimal_values = []
        files = [f for f in os.listdir(self.folder_path) if f.endswith(".data32")]

        for i, filename in enumerate(files):
            if self.stop_event.is_set():
                return []  # Exit if stop event is triggered
            file_path = os.path.join(self.folder_path, filename)
            decimal_values = self.load_and_decode_file_to_decimal(file_path)
            all_decimal_values.append(decimal_values)
            if self.progress_callback:
                self.progress_callback(i + 1)

        matrix = np.array(all_decimal_values, dtype=np.float64)
        voltage_step = 1  # Change if required
        summed_voltages = np.sum(matrix * voltage_step, axis=0)
        return summed_voltages

import numpy as np
import matplotlib.pyplot as plt
from .data_processor import DataProcessor

class VoltagePlotter:
    def __init__(self, measurement_processor, background_processor):
        self.measurement_processor = measurement_processor
        self.background_processor = background_processor
        self.difference = None

    def calculate_difference(self):
        summed_voltages_measurement = self.measurement_processor.calculate_summed_voltages()
        summed_voltages_background = self.background_processor.calculate_summed_voltages()
        self.difference = summed_voltages_measurement - summed_voltages_background

    def plot_difference(self):
        if self.difference is None:
            self.calculate_difference()

        x_array = np.arange(len(self.difference))
        figure = plt.figure(figsize=(14, 6))
        ax = figure.add_subplot(1, 1, 1)
        ax.plot(x_array, self.difference)
        ax.grid()
        plt.show()

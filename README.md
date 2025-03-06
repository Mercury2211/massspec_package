# MassSpec Package

## Overview

MassSpec Package is a Python package for processing and visualizing mass spectrometry data. It supports data from Acqiris ADC cards used in time-of-flight mass spectrometry (TOF-MS). The package provides functionality for decoding `.data32` files, computing summed voltages, and analyzing waveform intensities.

## Features
- Analyze recordings from Acqiris ADC cards for TOF-MS.
- Load and decode `.data32` files.
- Compute and visualize summed voltage differences.
- Plot intensity changes over time from recorded waveforms.
- Plot selected single waveforms from `.data32` files.
- Interactive GUI for selecting data folders and processing data.
- Supports progress tracking with a progress bar.
- Multi-threaded processing for efficiency.

## Package Functions
### **1️⃣ DataProcessor** (`data_processor.py`)
Handles file loading and decoding of `.data32` files. It processes the recorded data and computes summed voltages for further analysis.

### **2️⃣ VoltagePlotter** (`voltage_plotter.py`)
Plots the voltage differences between measurement and background data, providing a visual representation of the mass spectrometry output.

### **3️⃣ IntensityOverTime & SingleWaveform** (`intensity_over_time.py` and `single_waveform.py`)
- **IntensityOverTime**: Computes and visualizes intensity changes over time for recorded waveforms.
- **SingleWaveform**: Extracts and plots individual waveforms from `.data32` files for detailed analysis.

- Analyze recordings from Acqiris ADC cards for TOF-MS.
- Load and decode `.data32` files.
- Compute and visualize summed voltage differences.
- Plot intensity changes over time from recorded waveforms.
- Plot selected single waveforms from `.data32` files.
- Interactive GUI for selecting data folders and processing data.
- Supports progress tracking with a progress bar.
- Multi-threaded processing for efficiency.

## Installation

### Installing from GitHub

To install the package directly from GitHub, run:

```bash
pip install git+https://github.com/Mercury2211/massspec_package.git
```

### Installing from Source

If you have downloaded the source code, navigate to the package directory and install using:

```bash
pip install .
```

## Usage

### Running the GUI Application

You can launch the GUI using:

```bash
python -m massspec_package.gui
```

Or, if using the provided script:

```bash
python run_app.py
```

### Using the Package in a Script

```python
import massspec_package
from massspec_package.data_processor import DataProcessor
from massspec_package.voltage_plotter import VoltagePlotter
from massspec_package.intensity_over_time import IntensityOverTime
from massspec_package.single_waveform import SingleWaveform

print("MassSpec Package Version:", massspec_package.__version__)

# Example usage
processor = DataProcessor("C:/path/to/data")
intensity_analyzer = IntensityOverTime(processor)
single_waveform_viewer = SingleWaveform(processor)
```

## Repository Structure

```
massspec_package/
│── src/
│   ├── massspec_package/
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   ├── voltage_plotter.py
│   │   ├── intensity_over_time.py
│   │   ├── single_waveform.py
│   │   ├── gui.py
│── README.md
│── LICENSE
│── pyproject.toml
│── run_app.py
```

## Citation

If this package is used in academic work (including but not limited to Master's theses and PhD dissertations), please cite it as:

**Alex Iseli, *************************MassSpec Package*************************, 2025. Available at:**\
[https://github.com/Mercury2211/massspec\_package](https://github.com/Mercury2211/massspec_package)

## License

This package is for personal use and academic research only. Modification, redistribution, or commercial use is **not permitted** without explicit written permission from the author. See the `LICENSE` file for full details.

## Author

Developed by Alex Iseli.

---

For issues or feature requests, visit the [GitHub repository](https://github.com/Mercury2211/massspec_package).


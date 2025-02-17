# MassSpec Package

## Overview

MassSpec Package is a Python package designed for processing and visualizing mass spectrometry data. It can analyze recordings from an Acqiris ADC card for time-of-flight mass spectrometry (TOF-MS).
MassSpec Package is a Python package designed for processing and visualizing mass spectrometry data. It provides tools for reading and analyzing `.data32` files, computing voltage differences, and displaying results in a graphical user interface (GUI).

## Features

- Analyze recordings from an Acqiris ADC card for TOF mass spectrometry.
- Load and decode `.data32` files.
- Compute and visualize summed voltage differences.
- Sum up measurements from an output folder and subtract a second one (measurement - background).
- Interactive GUI for selecting data folders and processing data.
- Supports progress tracking with a progress bar.
- Multi-threaded processing for efficiency.
- Interactive GUI for selecting data folders and processing data.
- Supports progress tracking with a progress bar.

### Future Features

- Additional data analysis capabilities beyond summation and subtraction.
- Advanced signal processing options such as single wave from analysis

## Installation

You can install the package directly from GitHub:

```bash
pip install git+https://github.com/Mercury2211/massspec_package.git
```

## Usage

### Running the GUI Application

After installation, you can start the GUI with:

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

print("MassSpec Package Version:", massspec_package.__version__)

# Example usage
processor = DataProcessor("C:/path/to/data")
```

A GUI will appear which allows you to select two folders. One for the measurement and a second one for the background measurement.


## Repository Structure

```
massspec_package/
│── src/
│   ├── massspec_package/
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   ├── voltage_plotter.py
│   │   ├── gui.py
│── README.md
│── LICENSE
│── pyproject.toml
│── run_app.py
```

## Citation

If this package is used in academic work (including but not limited to Master's theses and PhD dissertations), please use the following citation:

**Alex Iseli, *********************************************************************MassSpec Package*********************************************************************, 2025. Available at:**\
[https://github.com/Mercury2211/massspec\_package](https://github.com/Mercury2211/massspec_package)

## License

This package is for **personal use only**. Modification, redistribution, or commercial use is **not permitted** without explicit written permission from the author. See the `LICENSE` file for full details.

## Author

Developed by Alex Iseli.

---

Feel free to report issues or suggest features in the GitHub repository.


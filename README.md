# MassSpec Package

## Overview
The **MassSpec Package** is designed for analyzing recordings from an **Acqiris ADC card** for **Time-of-Flight Mass Spectrometry (TOF-MS)**.  
It provides a GUI-based interface to process and visualize data.

---

## **Installation**
To install the package, use:
```sh
pip install git+https://github.com/Mercury2211/massspec_package.git
```
Ensure you have `numpy`, `matplotlib`, and `tkinter` installed.

---

## **Launching the GUI**
The package provides three different GUI applications for mass spectrometry analysis.  
Each GUI can be launched with **a single line of code**. Each GUI has the option to store the data
used for the plot either in a txt or csv file for further analysis.

### **1️⃣ Difference Plotter GUI**
Used for **Subtracting a Background Measurement from a Measurement**.
```python
import massspec_package
massspec_package.launch_difference_plotter()
```
✅ **Title:** "Background Subtraction"

---

### **2️⃣ Intensity Over Time GUI**
Used for **visualizing signal intensity over time**.
```python
import massspec_package
massspec_package.launch_intensity_gui()
```
✅ **Title:** "Intensity Over Time Analysis"

---

### **3️⃣ Single Waveform Analysis GUI**
Used for **plotting selected waveform files**.
```python
import massspec_package
massspec_package.launch_single_waveform_gui()
```
✅ **Title:** "Single Waveform Analysis"

---

## **Manual Usage**
For advanced users, you can manually interact with the classes:

```python
from massspec_package.data_processor import DataProcessor
processor = DataProcessor("C:/path/to/data")
voltages = processor.calculate_summed_voltages()
print(voltages)
```

```python
from massspec_package.voltage_plotter import VoltagePlotter
plotter = VoltagePlotter(measurement_processor, background_processor)
plotter.plot_difference()
```

---

## **License**
This package is provided under a **custom license** for **personal and academic use**.  
If used in academic work (e.g., Master Thesis, Research Papers), **citation is required**.  
For any **commercial use**, a **formal request is required**.

---

## **Contact**
For issues or contributions, please submit a GitHub issue or contact:  
📧 **iseli.alex.5@gmail.com**  
👤 **GitHub:** [Mercury2211](https://github.com/Mercury2211)


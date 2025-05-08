# MassSpec Package

**MassSpec Package** is a Python toolkit for analyzing recordings from an **Acqiris ADC card** for **Time-of-Flight Mass Spectrometry (TOF-MS)**. It provides both GUI applications and programmatic interfaces to process, calibrate, and visualize mass spectrometry data.

---

## 🎉 What's New in v1.0.0

* Added **Calibration GUI** for X‑ and Y‑axis calibration of TOF spectra.
* Refactored GUI launch functions with clearer names.
* Improved data loading and processing in `DataProcessor`.
* Updated `VoltagePlotter` to separate calculation and plotting methods.

---

## 🚀 Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/Mercury2211/massspec_package.git
```

Ensure you have the following dependencies:

* `numpy`
* `matplotlib`
* `scipy`
* `tkinter` (usually included with Python)
* `Pillow` (`PIL`)

---

## 🖥️ Launching GUIs

Each GUI can be launched via a single function call. All GUIs allow exporting processed data (TXT or CSV).

```python
import massspec_package
```

### 1️⃣ Background Subtractor (Difference Plotter)

Subtract a background measurement from a signal measurement:

```python
massspec_package.launch_background_subtractor()
```

* **Window Title:** "Background Subtractor"
* Select a **Measurement Folder** and a **Background Folder**, then click **Process and Plot**.

---

### 2️⃣ Intensity Over Time Analysis

Plot the maximum signal intensity of a selected mass peak across a series of measurements:

```python
massspec_package.launch_intensity_over_time()
```

* **Window Title:** "Intensity over Time Analysis"
* Select a **Measurement Folder**, set **X Min**, **X Max**, and **Skip Interval**, then click **Proceed**.

---

### 3️⃣ Single Waveform Analysis

Visualize individual waveform files from a measurement:

```python
massspec_package.launch_single_waveform_analysis()
```

* **Window Title:** "Single Waveform Analysis"
* Select a **Measurement Folder**, choose one or more `.data32` files, then click **Proceed**.

---

### 4️⃣ Calibration GUI

Perform X‑axis calibration (time-to-mass conversion) and optional Y‑axis calibration (pressure or normalization):

```python
massspec_package.launch_calibration()
```

* **Window Title:** "Calibration"
* **Setup Tab:** Choose measurement and background folders and Y‑axis mode.
* **Raw Plot Tab:** Preview background-subtracted signal.
* **X‑Calibration Tab:** Select two time points (T₁, T₂) and their known masses (m₁, m₂) to compute calibration curve.
* **Y‑Calibration Tab:** Fit peak intensities to partial pressures or normalize to 100.
* **Final Tab:** View calibrated spectrum, toggle log scale, export data.

---

## 🔧 Manual Usage

For scripting or advanced workflows, use the core classes:

```python
from massspec_package.data_processor import DataProcessor
from massspec_package.voltage_plotter import VoltagePlotter

# Sum voltages in a folder of .data32 files
processor = DataProcessor("/path/to/data")
summed = processor.calculate_summed_voltages()

# Calculate difference between two folders
mea = DataProcessor("/path/to/measurement")
bkg = DataProcessor("/path/to/background")
vp = VoltagePlotter(mea, bkg)
vp.calculate_difference()
# Plot programmatically
vp.plot_difference()
```

---

## 📄 License

This package is provided under a **custom license** for **personal and academic use**.  
If used in academic work (e.g., Master Thesis, Research Papers), **citation is required**.  
For any **commercial use**, a **formal request is required**.

---

## 📚 Citation

If you use MassSpec Package in academic work, cite as:

> **Iseli, Alex (2025). *MassSpec Package* (Version 0.2.0) \[Computer software].**
> Retrieved from [https://github.com/Mercury2211/massspec\_package](https://github.com/Mercury2211/massspec_package)

*(Adapt to your citation style: APA, IEEE, etc.)*

---

## 🤝 Contact & Contributions

* GitHub Issues: [https://github.com/Mercury2211/massspec\_package/issues](https://github.com/Mercury2211/massspec_package/issues)
* Email: [iseli.alex.5@gmail.com](mailto:iseli.alex.5@gmail.com)
* GitHub: [Mercury2211](https://github.com/Mercury2211)

Pull requests and feedback are welcome!

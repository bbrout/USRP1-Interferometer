# USRP1-Interferometer

Software and data pipeline for a 21 cm hydrogen line interferometer using a USRP-1. Automates observation scheduling, LST-based data capture, spectral analysis, and visualization of galactic rotation profiles.

## 📡 Overview

The pipeline reads an observation queue (`InterferometerWorkbook.csv`), waits for the appropriate Local Sidereal Time, captures raw binary data from the USRP, processes it into power and frequency data, and produces plots of the resulting signal.

## 🔁 Pipeline Flow

1. **Schedule Setup**  
   - Define target objects in `InterferometerWorkbook.csv` (RA, DEC, width, velocity, date).
2. **Start Observation**  
   - Run `Start_Observation.py` to:
     - Parse each object.
     - Calculate central frequency from velocity.
     - Wait until LST is right.
     - Record raw data to `RX_AB.dat` and save `freq.dat`.
3. **Data Archival**  
   - Automatically moves results into per-object directories (e.g., `M58/`).
4. **Post-Processing**  
   - Run `process_data` to generate:
     - `power.dat`: time series RMS
     - `fft.dat`: 256-bin FFT centered around the 21 cm line
5. **Plotting**  
   - Use `plot_power.py` and `plot_fft.py` to visualize the results.

## 🧾 File Descriptions

- `InterferometerWorkbook.csv`: Main observation queue.
- `get_LST.py`: Computes Local Sidereal Time using site info in `location.dat`.
- `Start_Observation.py`: Master script for automated observing.
- `process_data.c`: C program for processing raw radio data.
- `plot_power.py`: Plots RMS over time.
- `plot_fft.py`: Plots frequency spectrum.
- `doc/`: Diagrams, antenna photos, feedhorn design, etc.
- `usrp1_fpga_4rx.rbf`: Firmware for 4-receiver USRP mode.

## 🧪 Requirements

- Python 3.x
- GNU Radio (or appropriate USRP tools)
- Matplotlib for plotting
- C compiler (e.g., gcc for `process_data.c`)

## ⚙️ Sample Rate Notes

- Default sample rate: `2e6` (±211 kHz BW)
- To extend to ±300 kHz, increase to `3e6` in both `Start_Observation.py` and `process_data`.

## 📍 Example Observation

```
$ python Start_Observation.py
... waiting for LST ...
... observing M58 ...
... observation complete, data saved to M58/
$ cd M58
$ ../process_data
$ python ../plot_fft.py
```

## 📦 Archive

Finalized data and diagrams can be archived on [Zenodo](https://zenodo.org/), with versioned releases of this repository.

## 🧙 Author

Bruce Rout  
Green NABR Research Ltd.  
Astrophysics, radio astronomy, and the war against unfocused software logic.

## 📝 License

This project is licensed under the [MIT License](LICENSE). You are free to use, modify, and distribute this software with attribution.

# T-MEDNet Desktop

Desktop application for visualising and analysing Mediterranean Sea temperature data collected by the T-MEDNet monitoring network.

---

## Features

- **Time-series plots** — overlays all depth sensors for a site on a single chart
- **Hovmöller / Stratification diagram** — depth × time heatmap showing thermal stratification
- **Marine Heat Wave detection** — highlights anomalous temperature events
- **Data exports** — Excel reports, GeoJSON, netCDF, and plain TXT
- **PDF / TXT quality reports**
- **Light and dark themes** — ocean-dark by default, switchable at runtime
- **HOBOware automation** — batch-export `.hobo` files and generate all plots without manual interaction

---

## Requirements

| Component | Minimum version |
|-----------|----------------|
| Python    | 3.9            |
| OS        | Windows 10 / macOS 11 / Ubuntu 20.04 |
| RAM       | 4 GB           |

Windows-only dependencies (`pyautogui`, `pywin32`, `psutil`) are only needed for the HOBOware automation scripts. The main GUI app runs on all platforms.

---

## Installation

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python main.py
```

---

## Directory structure

```
tmednet-app/
├── main.py                  ← entry point (also accepts CLI flags)
├── requirements.txt
├── build_app.py             ← builds a standalone .exe with PyInstaller
├── tmednet.spec             ← PyInstaller spec
│
├── app/                     ← PyQt6 UI layer
│   ├── main_window.py       ← main window, menus, keyboard shortcuts
│   ├── theme.py             ← ocean-dark / ocean-light stylesheets
│   ├── adapters.py          ← bridges PyQt6 widgets to the core backend
│   └── widgets/
│       ├── file_panel.py    ← left sidebar (file list + buttons)
│       ├── plot_widget.py   ← matplotlib canvas embedded in Qt
│       ├── console_widget.py
│       └── dialogs.py       ← About, Browser, HistoricalMerge, Progress
│
├── core/                    ← platform-independent backend
│   ├── data_manager.py      ← loads .txt files, parses dates, stores DataFrames
│   ├── gui_plots.py         ← time-series, Hovmöller, zoom, MHW plots
│   ├── excel_writer.py      ← statistical Excel report
│   ├── file_writer.py       ← TXT / GeoJSON / netCDF output
│   ├── surface_temperature.py
│   ├── marineHeatWaves.py
│   └── ...
│
├── data/
│   └── metadata.json        ← station registry (coordinates, site codes, names)
│
├── automate_tmednet.py      ← automates one site: load files → plot → save PNGs
└── run_all_sites.py         ← batch pipeline for multiple sites (configure paths)
```

---

## Usage — manual GUI

| Action | How |
|--------|-----|
| Open files | `Ctrl+O` or **File → Open** |
| Plot a file | Click its name in the left panel |
| Save current plot | `Ctrl+S` or **File → Save Plot…** |
| Hovmöller diagram | `Ctrl+H` or **File → Plot Hovmöller** |
| Toggle light/dark | **View → Toggle Theme** |
| Excel report | **Tools → Excel Report** |
| Generate PDF report | **Report** button |

---

## Data file format

The app reads **tab-separated `.txt`** files exported by HOBOware.  
Expected columns (after a one-line header):

```
#    Date        Time        Temp (°C)   ...
1    12/08/25    12:00:00    14.960      ...
```

The filename encodes station metadata and is used at load time:

```
{site_code}_{start_YYYYMMDD-HH}_{end_YYYYMMDD-HH}_{depth_m}.txt

Example:  5_20251208-12_20260606-10_05.txt
          └─ site 5, from 2025-12-08 12:00 to 2026-06-06 10:00, depth 5 m
```

Supported date formats are auto-detected per file:

| Format | Example | Source |
|--------|---------|--------|
| `MM/DD/YY` | `12/08/25` | HOBOware (default export) |
| `DD/MM/YY` | `08/12/25` | Legacy T-MEDNet |
| `DD/MM/YYYY` | `08/12/2025` | T-MEDNet 4-digit year |

---

## CLI flags

```bash
# Open with light theme
python main.py --light

# Load files directly on startup (skips the Open dialog)
python main.py --light --auto-load path/to/file1.txt path/to/file2.txt
```

---

## HOBOware batch automation (Windows)

These scripts automate the full pipeline: HOBOware export → tmednet graphs → PNG saved to Desktop.

### Single site

```bash
python automate_tmednet.py <export_dir> <site_label> <site_code>
```

| Argument | Description |
|----------|-------------|
| `export_dir` | Folder containing the `.txt` files exported by HOBOware |
| `site_label` | Label used in the output filename (e.g. `capraia`) |
| `site_code` | Numeric site code from `data/metadata.json` (e.g. `252`) |

**Output** (saved to Desktop):
```
capraia_252_timeseries_20250925_20260410.png
capraia_252_hovmoller_20250925_20260410.png
```

### Multiple sites

Edit the `SITES` list at the top of `run_all_sites.py` to point to your `.hobo` source folders and set the correct site codes, then run:

```bash
python run_all_sites.py
```

The script skips the HOBOware export step automatically if `.txt` files are already present in the export folder.

**Dependencies for automation scripts** (Windows only):

```bash
pip install pyautogui pywin32 psutil pyperclip
```

---

## Building a standalone executable

```bash
pip install pyinstaller
python build_app.py
```

The `dist/tmednet/` folder is self-contained — copy it anywhere and launch `tmednet.exe`.

---

## Site registry

Station coordinates and names are stored in `data/metadata.json`.  
Each entry uses the numeric site code as key:

```json
"5": { "name": "Cap de Creus S (El Gat)", "lat": 42.32, "long": 3.31 }
```

---

## License

Creative Commons Attribution 4.0 — T-MEDNet Research

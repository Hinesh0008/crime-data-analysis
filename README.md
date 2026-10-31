# Crime Data Analysis System

A beginner-friendly Streamlit mini project for exploring fictional crime records with Python, Pandas, NumPy, Matplotlib, and Seaborn.

> **Sample data notice:** `crime_data.csv` contains 180 synthetic, fictional records created only for this educational project. The dashboard does not predict crime or identify suspects.

## Features

- Summary cards for record count, city count, most common category, and years represented.
- Crime category, city, year, and monthly trend charts, including bar, pie, and line charts.
- Sidebar filters for city, crime type, year, month, and date range.
- A table of matching records and a CSV download of the filtered report.
- CSV upload with required-column validation, missing-value handling, invalid-date removal, and duplicate Crime_ID removal.
- Data cleaning summary and clear CSV upload error messages.

## Project files

- `app.py` — Streamlit application and data cleaning/analysis logic.
- `crime_data.csv` — fictional sample dataset.
- `requirements.txt` — Python package dependencies.

## Run in Visual Studio Code

1. Install Python 3.9 or later and open this project folder in Visual Studio Code.
2. Open the VS Code terminal (`Terminal` → `New Terminal`).
3. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```cmd
   py -m venv .venv
   .venv\Scripts\activate.bat
   ```

4. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the dashboard:

   ```powershell
   python -m streamlit run app.py
   ```

6. Open the local URL printed in the terminal (usually `http://localhost:8501`).

## Uploading your own CSV

Use the sidebar upload control. Your CSV must have these columns (capitalization is not important):

```text
Crime_ID, City, Crime_Type, Date, Area, Time_Period, Record_Status
```

Rows missing an ID, city, crime type, or valid date are removed. Repeated Crime_ID values keep their first row. Missing Area, Time_Period, and Record_Status values are filled with `Unknown`. The Data Management page summarizes the cleaning that was performed. Clear the uploaded file in the sidebar to return to the bundled sample.

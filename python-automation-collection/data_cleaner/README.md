# Data Cleaner Module

A powerful utility to instantly clean, standardize, and format messy datasets from CSV or Excel files.

## Features
- **Remove Duplicates**: Quickly drop identical rows.
- **Remove Null Rows**: Eliminate rows where all data is missing.
- **Whitespace Trimming**: Strip accidental spaces from the beginning or end of text.
- **Normalize Phone Numbers**: Automatically detects phone columns and strips non-numeric characters (leaving a standard numeric string or + sign).
- **Split Full Names**: Detects `Name` or `Full Name` columns and splits them into `First Name` and `Last Name`.
- **Convert Case**: Standardize all text to Title, Lower, or Upper case.

## Quick Start

### 1. Configuration
Open `config.yaml` to set default rules.

### 2. Streamlit Web Interface
Run the UI to upload your file, toggle rules visually, and download the cleaned version:

```bash
cd python-automation-collection/data_cleaner
streamlit run streamlit_app.py
```

### 3. Command Line Interface (CLI)
Run the script on a messy file directly from your terminal:

```bash
cd python-automation-collection/data_cleaner
python clean.py messy_data.csv --output my_clean_data.xlsx
```

Logs detailing the modifications made are saved to `data_cleaner.log`.

# Excel to Database Module

This module automates the process of reading an Excel file, cleaning the data, and inserting it into a database (SQLite or PostgreSQL).

## Features
- **Upload Excel**: Read `.xlsx` files easily.
- **Data Validation & Cleaning**: Remove completely null rows, drop duplicates, and strip out unnamed columns.
- **Database Insertion**: Automatically create tables and insert data securely using SQLAlchemy.
- **Reporting**: Displays success and error reports via logging and the Streamlit interface.

## Quick Start

### 1. Configuration
Open `config.yaml` to set your default database URL, Excel processing rules, and logging level.
By default, it uses a local SQLite database (`sqlite:///database.sqlite`).

### 2. Streamlit Web Interface
Run the Streamlit application for an easy-to-use graphical interface:

```bash
cd python-automation-collection/excel_to_db
streamlit run streamlit_app.py
```

### 3. Command Line Interface (CLI)
Run the script directly from your terminal:

```bash
cd python-automation-collection/excel_to_db
python cli_version.py sample.xlsx --table my_data
```

You can view the processing logs in the generated `excel_to_db.log` file.

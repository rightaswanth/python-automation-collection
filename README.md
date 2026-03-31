# Python Automation Collection

A production-ready collection of Python automation tools designed for freelance clients and business operations. Each module provides a Command Line Interface (CLI) and a Streamlit Web Interface (UI), adhering to clean architecture, modularity, and scalability principles.

## Features Overview

This repository includes the following robust modules:

1. **Excel to Database**: Automatically read Excel files, clean missing/duplicate data, and securely ingest the data into an SQLite or PostgreSQL database.
2. **Web Scraper**: Extract data from websites with support for pagination, custom CSS selectors, anti-block headers, and export to CSV/Excel.
3. **Email Automation**: Send personalized, bulk emails via SMTP using customizable templates and Excel-based contact lists, complete with rate limiting and attachment support.
4. **Data Cleaner**: Standardize datasets by trimming whitespace, normalizing phone numbers, splitting names, removing duplicates, and enforcing consistent casing.
5. **Invoice Generator**: Automatically generate professional PDF invoices from Excel order data and an HTML template, supporting bulk processing and ZIP downloads.

## Prerequisites

- **Python 3.10+**
- (Optional, for Invoice Generator) **wkhtmltopdf**: Ensure this tool is installed on your system if you are generating PDF invoices.
  - Windows: Download from the official site.
  - macOS: `brew install wkhtmltopdf`
  - Linux: `sudo apt-get install wkhtmltopdf`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd python-automation-collection
   ```

2. **Set up a virtual environment (Recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Each module is designed to run independently. You can interact with them either via the CLI scripts or via the Streamlit web apps.

### Running Streamlit UIs
To run any module's UI, navigate into the module folder and use `streamlit run`.

Example for the **Excel to Database** module:
```bash
cd excel_to_db
streamlit run streamlit_app.py
```

### Running CLI Scripts
To run the underlying automation logic directly from the terminal, execute the module's main Python file.

Example for the **Data Cleaner** module:
```bash
cd data_cleaner
python clean.py --help
```

*For detailed instructions on each tool, please see the `README.md` inside each module's respective folder.*

## Architecture & Code Quality

- **Clean Code:** Separation of concerns between core logic (e.g., `clean.py`) and presentation (`streamlit_app.py`).
- **Configuration-Driven:** Uses `config.yaml` in each module for easily modifying defaults without changing code.
- **Robustness:** Built-in logging (`module.log`) and comprehensive exception handling.
- **Typing:** Fully type-hinted core logic.
- **Professional UIs:** Streamlit interfaces feature minimal spacing, progress spinners, success/error alerts, and immediate file downloads.

# Invoice Generator Module

Automatically generate professional, bulk PDF invoices from Excel or CSV order data. Perfect for freelancers or small businesses dealing with regular client billing.

## Features
- **Bulk Processing**: Upload a list of orders and generate hundreds of invoices in seconds.
- **Customization**: A clean HTML/Jinja2 template that you can easily modify to match your brand.
- **Dynamic Data**: Automatically calculates taxes, subtotals, and totals based on your input.
- **ZIP Export**: The Streamlit interface lets you download all generated PDFs in a single ZIP file.

## Prerequisites

**wkhtmltopdf is required** to convert HTML to PDF.
- **Windows**: Download from the official site and add it to your PATH.
- **macOS**: `brew install wkhtmltopdf`
- **Linux (Ubuntu/Debian)**: `sudo apt-get install wkhtmltopdf`

## Quick Start

### 1. Configuration
Open `config.yaml` to set your default company information (Name, Address, Logo URL) and default invoice settings (Tax rate, Currency symbol).

### 2. Streamlit Web Interface
Run the UI to upload orders and download a ZIP file of invoices:

```bash
cd python-automation-collection/invoice_generator
streamlit run streamlit_app.py
```

### 3. Command Line Interface (CLI)
Run the script to generate invoices directly into a folder:

```bash
cd python-automation-collection/invoice_generator
python generate.py orders.xlsx --output-dir my_invoices
```

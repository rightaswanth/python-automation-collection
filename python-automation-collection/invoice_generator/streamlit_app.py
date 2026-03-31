"""
Streamlit Web App for Invoice Generator Module

Upload order data, configure company details and tax rates,
generate PDF invoices using an HTML template, and download them as a ZIP archive.
"""

import streamlit as st
import pandas as pd
import yaml
import logging
import os
import zipfile
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
import pdfkit
from datetime import datetime, timedelta
import uuid

st.set_page_config(page_title="Invoice Generator", page_icon="🧾", layout="wide")

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("invoice_generator_ui")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def load_config() -> dict:
    try:
        with open("config.yaml", 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"Failed to load config file: {e}")
        return {}

def create_zip(pdf_files: dict) -> bytes:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, pdf_bytes in pdf_files.items():
            zf.writestr(filename, pdf_bytes)
    return zip_buffer.getvalue()

def generate_pdfs(df: pd.DataFrame, config: dict, company_details: dict, invoice_details: dict, logger: logging.Logger):
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('template.html')

    try:
        pdf_config = pdfkit.configuration()
    except OSError:
        st.error("wkhtmltopdf is not installed. PDF generation cannot proceed. Please install it to use this module.")
        return None

    pdf_files = {}
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(df)

    for i, row in df.iterrows():
        try:
            client_name = row.get('Client Name', 'Valued Customer')
            client_email = row.get('Client Email', '')
            client_address = row.get('Client Address', '')

            description = str(row.get('Item Description', 'Service Rendered'))
            price = float(row.get('Item Price', 0.0))

            subtotal = price
            tax_rate = invoice_details['tax_rate']
            tax = subtotal * tax_rate
            total_amt = subtotal + tax

            invoice_id = str(row.get('Invoice ID', f"{invoice_details['prefix']}{uuid.uuid4().hex[:6].upper()}"))

            html_content = template.render(
                logo_url=company_details['logo_url'],
                company_name=company_details['name'],
                company_address=company_details['address'],
                company_email=company_details['email'],
                client_name=client_name,
                client_email=client_email,
                client_address=client_address,
                invoice_id=invoice_id,
                date=datetime.now().strftime("%Y-%m-%d"),
                due_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                items=[{"description": description, "price": price}],
                subtotal=subtotal,
                tax_rate=tax_rate,
                tax=tax,
                total=total_amt,
                currency=invoice_details['currency']
            )

            # Generate PDF in memory
            pdf_bytes = pdfkit.from_string(html_content, False, configuration=pdf_config, options={'enable-local-file-access': ''})
            pdf_files[f"{invoice_id}.pdf"] = pdf_bytes
            logger.info(f"Generated invoice: {invoice_id}.pdf")

        except Exception as e:
            logger.error(f"Error generating invoice for row {i}: {e}")
            st.warning(f"Skipped row {i} due to error: {e}")

        progress_bar.progress((i + 1) / total)
        status_text.text(f"Generated {i + 1} / {total} invoices...")

    return pdf_files

def main():
    st.title("🧾 Invoice Generator")
    st.markdown("Upload order data (Excel/CSV) to automatically generate professional PDF invoices and download them as a ZIP archive.")

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'invoice_generator.log'))

    # Sidebar
    st.sidebar.header("🏢 Company Details")
    default_company = config.get('company', {})

    company_name = st.sidebar.text_input("Company Name", value=default_company.get('name', ''))
    company_address = st.sidebar.text_area("Address", value=default_company.get('address', ''))
    company_email = st.sidebar.text_input("Email", value=default_company.get('email', ''))
    logo_url = st.sidebar.text_input("Logo URL", value=default_company.get('logo_url', ''))

    st.sidebar.header("🧾 Invoice Settings")
    default_invoice = config.get('invoice', {})
    prefix = st.sidebar.text_input("Invoice Prefix", value=default_invoice.get('prefix', 'INV-'))
    currency = st.sidebar.text_input("Currency Symbol", value=default_invoice.get('currency', '$'))
    tax_rate = st.sidebar.number_input("Tax Rate (%)", value=default_invoice.get('tax_rate', 0.05) * 100, step=0.5) / 100.0

    # Main Area
    uploaded_file = st.file_uploader("Upload Orders Excel/CSV (Columns needed: 'Client Name', 'Item Description', 'Item Price')", type=["xlsx", "csv"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("### Data Preview")
            st.dataframe(df.head())

            required_cols = ['Client Name', 'Item Description', 'Item Price']
            missing = [col for col in required_cols if col not in df.columns]

            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}")
            else:
                if st.button("🚀 Generate PDF Invoices"):
                    with st.spinner("Generating invoices..."):
                        company_details = {
                            "name": company_name,
                            "address": company_address,
                            "email": company_email,
                            "logo_url": logo_url
                        }
                        invoice_details = {
                            "prefix": prefix,
                            "currency": currency,
                            "tax_rate": tax_rate
                        }

                        pdf_files = generate_pdfs(df, config, company_details, invoice_details, logger)

                        if pdf_files:
                            st.success(f"🎉 Successfully generated {len(pdf_files)} invoices!")

                            zip_data = create_zip(pdf_files)
                            st.download_button(
                                label="📥 Download All Invoices (ZIP)",
                                data=zip_data,
                                file_name="invoices.zip",
                                mime="application/zip"
                            )
        except Exception as e:
            st.error(f"Error reading or processing file: {e}")

if __name__ == "__main__":
    main()

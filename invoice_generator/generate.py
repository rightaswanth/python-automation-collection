"""
Invoice Generator CLI

Reads order data from an Excel file, applies formatting via a Jinja2 HTML template,
and generates PDF invoices using pdfkit.
"""

import argparse
import logging
import pandas as pd
import yaml
import os
import pdfkit
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta
import uuid
import zipfile
from typing import Dict, Any, Optional, List

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("invoice_generator")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

class InvoiceGenerator:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.company = self.config.get('company', {})
        self.inv_config = self.config.get('invoice', {})

        # Jinja setup
        template_dir = os.path.dirname(os.path.abspath(__file__))
        self.env = Environment(loader=FileSystemLoader(template_dir))

        # Verify wkhtmltopdf is installed/available
        try:
            # Check config for path, else assume it's in system PATH
            path_wkhtmltopdf = self.config.get('wkhtmltopdf_path', None)
            if path_wkhtmltopdf and os.path.exists(path_wkhtmltopdf):
                 self.pdf_config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
            else:
                 self.pdf_config = pdfkit.configuration()
        except OSError as e:
            self.logger.error("wkhtmltopdf is not installed or not found in PATH.")
            self.pdf_config = None

    def load_orders(self, filepath: str) -> Optional[pd.DataFrame]:
        try:
            if filepath.endswith('.csv'):
                return pd.read_csv(filepath)
            else:
                return pd.read_excel(filepath)
        except Exception as e:
            self.logger.error(f"Error reading orders file: {e}")
            return None

    def generate_invoice_html(self, row: pd.Series) -> str:
        template = self.env.get_template('template.html')

        # Safely get values, handling NAs
        client_name = row.get('Client Name', 'Valued Customer')
        client_email = row.get('Client Email', '')
        client_address = row.get('Client Address', '')

        # Item parsing - simplistic logic assuming simple columns:
        # For complex orders, we would parse a JSON string or group by Order ID.
        # Here we assume columns: Item Description, Item Price
        items = [{"description": str(row.get('Item Description', 'Service Rendered')), "price": float(row.get('Item Price', 0.0))}]

        subtotal = sum(item['price'] for item in items)
        tax_rate = float(self.inv_config.get('tax_rate', 0.0))
        tax = subtotal * tax_rate
        total = subtotal + tax

        invoice_id = str(row.get('Invoice ID', f"{self.inv_config.get('prefix', 'INV-')}{uuid.uuid4().hex[:6].upper()}"))
        date_str = datetime.now().strftime("%Y-%m-%d")
        due_date_str = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        html_content = template.render(
            logo_url=self.company.get('logo_url', ''),
            company_name=self.company.get('name', ''),
            company_address=self.company.get('address', ''),
            company_email=self.company.get('email', ''),
            client_name=client_name,
            client_email=client_email,
            client_address=client_address,
            invoice_id=invoice_id,
            date=date_str,
            due_date=due_date_str,
            items=items,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax=tax,
            total=total,
            currency=self.inv_config.get('currency', '$')
        )
        return html_content, invoice_id

    def generate_pdfs(self, df: pd.DataFrame, output_dir: str = "output"):
        if self.pdf_config is None:
            self.logger.error("Cannot generate PDFs without wkhtmltopdf.")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        generated_files = []
        for index, row in df.iterrows():
            try:
                html, inv_id = self.generate_invoice_html(row)
                output_path = os.path.join(output_dir, f"{inv_id}.pdf")

                pdfkit.from_string(html, output_path, configuration=self.pdf_config, options={'enable-local-file-access': ''})
                self.logger.info(f"Generated invoice: {output_path}")
                generated_files.append(output_path)
            except Exception as e:
                self.logger.error(f"Failed to generate invoice for row {index}: {e}")

        self.logger.info(f"Successfully generated {len(generated_files)} invoices.")

def main():
    parser = argparse.ArgumentParser(description="Invoice Generator CLI.")
    parser.add_argument("orders", type=str, help="Excel file containing order data.")
    parser.add_argument("--output-dir", type=str, default="invoices", help="Directory to save generated PDFs.")

    args = parser.parse_args()

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'invoice_generator.log'))

    generator = InvoiceGenerator(config, logger)
    df = generator.load_orders(args.orders)

    if df is not None:
        generator.generate_pdfs(df, args.output_dir)

if __name__ == "__main__":
    main()

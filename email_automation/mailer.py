"""
Email Automation CLI

Reads contacts from an Excel file, personalizes an email template,
and sends bulk emails via an SMTP server (default Gmail) with rate limiting
and optional attachments.
"""

import argparse
import logging
import pandas as pd
import yaml
import smtplib
from email.message import EmailMessage
import time
import os
from typing import Dict, Any, Optional

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("email_automation")
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

class BulkMailer:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger, smtp_user: str, smtp_pass: str):
        self.config = config
        self.logger = logger
        self.smtp_host = config.get('smtp', {}).get('host', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp', {}).get('port', 587)
        self.use_tls = config.get('smtp', {}).get('use_tls', True)
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.rate_limit = config.get('email', {}).get('rate_limit_seconds', 2)
        self.subject_prefix = config.get('email', {}).get('subject_prefix', '')

    def get_smtp_connection(self) -> Optional[smtplib.SMTP]:
        try:
            self.logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            self.logger.info("SMTP Connection successful.")
            return server
        except Exception as e:
            self.logger.error(f"SMTP Connection failed: {e}")
            return None

    def create_message(self, recipient_email: str, recipient_name: str, subject: str, template: str, attachment_path: Optional[str] = None) -> EmailMessage:
        msg = EmailMessage()

        # Personalize
        body = template.replace("{{Name}}", str(recipient_name))

        msg.set_content(body)

        full_subject = f"{self.subject_prefix} {subject}".strip()
        msg['Subject'] = full_subject
        msg['From'] = self.smtp_user
        msg['To'] = recipient_email

        # Add attachment
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(attachment_path)
                    # Simple assumption for demo: generic octet-stream for attachments
                    msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            except Exception as e:
                self.logger.warning(f"Failed to attach {attachment_path}: {e}")

        return msg

    def send_bulk(self, contacts_df: pd.DataFrame, subject: str, template: str, attachment_path: Optional[str] = None):
        server = self.get_smtp_connection()
        if not server:
            self.logger.error("Cannot proceed without SMTP connection.")
            return

        success_count = 0
        fail_count = 0

        # Check if required columns exist
        if 'Email' not in contacts_df.columns or 'Name' not in contacts_df.columns:
             self.logger.error("Contacts must have 'Email' and 'Name' columns.")
             server.quit()
             return

        for index, row in contacts_df.iterrows():
            email = row['Email']
            name = row['Name']

            if pd.isna(email) or not str(email).strip():
                self.logger.warning(f"Skipping row {index}: Missing email address.")
                fail_count += 1
                continue

            msg = self.create_message(email, name, subject, template, attachment_path)

            try:
                server.send_message(msg)
                self.logger.info(f"Sent email to {email}")
                success_count += 1
                time.sleep(self.rate_limit) # Rate limit
            except Exception as e:
                self.logger.error(f"Failed to send to {email}: {e}")
                fail_count += 1

        server.quit()
        self.logger.info(f"Bulk send complete. Success: {success_count}, Failed: {fail_count}")

def main():
    parser = argparse.ArgumentParser(description="Bulk Email Automation CLI.")
    parser.add_argument("contacts", type=str, help="Excel file containing 'Name' and 'Email' columns.")
    parser.add_argument("--subject", type=str, required=True, help="Email subject.")
    parser.add_argument("--template", type=str, required=True, help="Path to text file with email template (use {{Name}} for personalization).")
    parser.add_argument("--attachment", type=str, default=None, help="Path to an optional attachment file.")

    # In a real CLI, avoid passing passwords via args, use env vars. For simplicity:
    parser.add_argument("--user", type=str, required=True, help="SMTP username (e.g. your Gmail).")
    parser.add_argument("--password", type=str, required=True, help="SMTP App Password.")

    args = parser.parse_args()

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'email_automation.log'))

    try:
        contacts_df = pd.read_excel(args.contacts)
    except Exception as e:
        logger.error(f"Could not read contacts file: {e}")
        return

    try:
        with open(args.template, 'r') as f:
            template_text = f.read()
    except Exception as e:
        logger.error(f"Could not read template file: {e}")
        return

    mailer = BulkMailer(config, logger, args.user, args.password)
    mailer.send_bulk(contacts_df, args.subject, template_text, args.attachment)

if __name__ == "__main__":
    main()

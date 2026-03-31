"""
Streamlit Web App for Email Automation Module

Upload contacts, personalize an email template, configure SMTP credentials,
preview the email, and send in bulk with progress tracking and rate limiting.
"""

import streamlit as st
import pandas as pd
import yaml
import logging
import smtplib
from email.message import EmailMessage
import time
from io import BytesIO

st.set_page_config(page_title="Email Automation", page_icon="📧", layout="wide")

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("email_automation_ui")
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

def test_smtp_connection(host: str, port: int, user: str, password: str, use_tls: bool) -> bool:
    try:
        server = smtplib.SMTP(host, port)
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.quit()
        return True
    except Exception as e:
        st.error(f"SMTP Connection Failed: {e}")
        return False

def send_bulk_emails(df: pd.DataFrame, subject: str, template: str, host: str, port: int, user: str, password: str, use_tls: bool, rate_limit: int, attachment: BytesIO = None, attachment_name: str = None, logger: logging.Logger = None):
    try:
        server = smtplib.SMTP(host, port)
        if use_tls:
            server.starttls()
        server.login(user, password)
    except Exception as e:
        st.error(f"Could not connect to SMTP server: {e}")
        return 0, len(df)

    success = 0
    failed = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(df)

    for i, row in df.iterrows():
        email = row.get('Email', '')
        name = row.get('Name', '')

        if pd.isna(email) or not str(email).strip():
            failed += 1
            continue

        msg = EmailMessage()
        body = template.replace("{{Name}}", str(name))
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = user
        msg['To'] = email

        if attachment and attachment_name:
            attachment.seek(0)
            msg.add_attachment(attachment.read(), maintype='application', subtype='octet-stream', filename=attachment_name)

        try:
            server.send_message(msg)
            success += 1
            if logger: logger.info(f"Sent email to {email}")
        except Exception as e:
            failed += 1
            if logger: logger.error(f"Failed to send to {email}: {e}")

        progress_bar.progress((i + 1) / total)
        status_text.text(f"Processed {i + 1} / {total} emails...")
        time.sleep(rate_limit)

    server.quit()
    return success, failed

def main():
    st.title("📧 Email Automation")
    st.markdown("Send personalized, bulk emails via SMTP. Upload a contact list, write a template, and preview your emails before sending.")

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'email_automation.log'))

    # Sidebar
    st.sidebar.header("⚙️ SMTP Configuration")
    smtp_host = st.sidebar.text_input("SMTP Host", value=config.get('smtp', {}).get('host', 'smtp.gmail.com'))
    smtp_port = st.sidebar.number_input("SMTP Port", value=config.get('smtp', {}).get('port', 587))
    use_tls = st.sidebar.checkbox("Use TLS", value=config.get('smtp', {}).get('use_tls', True))
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Credentials** *(Use App Passwords for Gmail)*")
    smtp_user = st.sidebar.text_input("Email Address")
    smtp_pass = st.sidebar.text_input("Password", type="password")

    rate_limit = config.get('email', {}).get('rate_limit_seconds', 2)

    # Main Area
    st.write("### 1. Upload Contacts")
    contacts_file = st.file_uploader("Upload Excel file (Must contain 'Name' and 'Email' columns)", type=["xlsx"])

    df = pd.DataFrame()
    if contacts_file:
        try:
            df = pd.read_excel(contacts_file)
            st.dataframe(df.head())
            if 'Name' not in df.columns or 'Email' not in df.columns:
                st.error("The uploaded file MUST contain 'Name' and 'Email' columns.")
                df = pd.DataFrame() # Clear invalid DF
        except Exception as e:
            st.error(f"Error reading file: {e}")

    st.write("### 2. Email Content")
    subject = st.text_input("Subject", value="Your Weekly Update")
    template = st.text_area("Email Body (Use {{Name}} to insert recipient's name)",
                            value="Hi {{Name}},\n\nThis is a friendly reminder.\n\nBest,\nYour Team",
                            height=200)

    st.write("### 3. Attachments (Optional)")
    attachment_file = st.file_uploader("Select a file to attach")

    # Preview
    if not df.empty and template:
        st.write("### 4. Preview")
        preview_name = df.iloc[0]['Name'] if not pd.isna(df.iloc[0]['Name']) else "Recipient"
        preview_email = df.iloc[0]['Email'] if not pd.isna(df.iloc[0]['Email']) else "recipient@example.com"

        st.info(f"**To:** {preview_email}\n\n**Subject:** {subject}\n\n**Body:**\n\n{template.replace('{{Name}}', str(preview_name))}")

    # Process Button
    st.write("### 5. Send Emails")
    if st.button("🚀 Start Sending"):
        if not smtp_user or not smtp_pass:
            st.error("Please provide SMTP credentials in the sidebar.")
        elif df.empty:
            st.error("Please upload a valid contacts file.")
        elif not subject or not template:
            st.error("Please provide a subject and email body.")
        else:
            with st.spinner("Connecting to SMTP server..."):
                if test_smtp_connection(smtp_host, smtp_port, smtp_user, smtp_pass, use_tls):
                    st.success("Connection successful. Beginning bulk send...")

                    attachment_bytes = BytesIO(attachment_file.getvalue()) if attachment_file else None
                    attachment_name = attachment_file.name if attachment_file else None

                    success, failed = send_bulk_emails(
                        df, subject, template, smtp_host, smtp_port, smtp_user, smtp_pass, use_tls, rate_limit, attachment_bytes, attachment_name, logger
                    )

                    if success > 0:
                        st.success(f"🎉 Successfully sent {success} emails! (Failed: {failed})")
                        logger.info(f"UI Send complete: {success} sent, {failed} failed.")
                    else:
                        st.error(f"Failed to send emails. (Failed: {failed})")

if __name__ == "__main__":
    main()

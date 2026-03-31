# Email Automation Module

A bulk email sender that personalizes messages from an Excel file and sends them securely via an SMTP server (default Gmail). Includes rate limiting, attachment support, and a preview feature.

## Features
- **Excel Contacts**: Simply provide an Excel file with `Name` and `Email` columns.
- **Personalization**: Use `{{Name}}` in your template to inject the recipient's name dynamically.
- **Attachments**: Attach any file type.
- **Rate Limiting**: Configurable delay between emails to prevent spam flags.
- **SMTP Support**: Defaults to Gmail but configurable for any SMTP server via the Streamlit UI or `config.yaml`.

## Quick Start

### 1. Configuration
Open `config.yaml` to adjust your SMTP server settings, rate limiting, and log levels.

**Security Note:** If using Gmail, you must use an **App Password** (enabled via Google Account Settings -> Security -> 2-Step Verification), not your standard account password.

### 2. Streamlit Web Interface
Run the app to upload files, preview emails, and send them visually:

```bash
cd python-automation-collection/email_automation
streamlit run streamlit_app.py
```

### 3. Command Line Interface (CLI)
Run the script directly from your terminal:

```bash
cd python-automation-collection/email_automation
python mailer.py contacts.xlsx --subject "Important Update" --template template.txt --user "your.email@gmail.com" --password "your-app-password"
```

Logs will be saved to `email_automation.log`.

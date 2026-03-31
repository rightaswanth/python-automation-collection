"""
Streamlit Web App for Data Cleaner Module

Upload messy data (CSV/Excel) and apply a suite of data cleaning rules
via the sidebar. Visualize the changes in a preview and download the cleaned data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yaml
import logging
import re
from io import BytesIO

st.set_page_config(page_title="Data Cleaner", page_icon="🧹", layout="wide")

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("data_cleaner_ui")
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

def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cleaned Data')
    return output.getvalue()

def clean_data(df: pd.DataFrame, rules: dict, logger: logging.Logger) -> pd.DataFrame:
    df_clean = df.copy()
    initial_len = len(df_clean)

    if rules.get('remove_null_rows', True):
        df_clean.dropna(how='all', inplace=True)
        logger.info(f"Removed {initial_len - len(df_clean)} null rows.")

    if rules.get('trim_whitespace', True):
        # Apply string trimming specifically to string/object columns
        str_cols = df_clean.select_dtypes(include=['object']).columns
        for col in str_cols:
             df_clean[col] = df_clean[col].astype(str).str.strip()
        logger.info("Trimmed whitespace.")

    case_rule = rules.get('convert_case', 'title').lower()
    if case_rule in ['lower', 'upper', 'title']:
        str_cols = df_clean.select_dtypes(include=['object']).columns
        for col in str_cols:
            if case_rule == 'lower':
                df_clean[col] = df_clean[col].str.lower()
            elif case_rule == 'upper':
                df_clean[col] = df_clean[col].str.upper()
            elif case_rule == 'title':
                df_clean[col] = df_clean[col].str.title()
        logger.info(f"Converted text to {case_rule} case.")

    if rules.get('normalize_phone', True):
        phone_cols = [col for col in df_clean.columns if 'phone' in col.lower() or 'mobile' in col.lower()]
        for col in phone_cols:
            df_clean[col] = df_clean[col].apply(lambda x: re.sub(r'[^\d+]', '', str(x)) if pd.notnull(x) else x)
            logger.info(f"Normalized phone column: {col}")

    if rules.get('split_full_name', True):
        name_cols = [col for col in df_clean.columns if col.lower() in ['name', 'full name', 'fullname']]
        for col in name_cols:
            try:
                split_df = df_clean[col].str.split(' ', n=1, expand=True)
                if len(split_df.columns) == 2:
                    df_clean['First Name'] = split_df[0]
                    df_clean['Last Name'] = split_df[1]
                    df_clean.drop(columns=[col], inplace=True)
                elif len(split_df.columns) == 1:
                    df_clean['First Name'] = split_df[0]
                    df_clean['Last Name'] = ""
                    df_clean.drop(columns=[col], inplace=True)
                logger.info(f"Split full name column: {col}")
            except Exception as e:
                logger.warning(f"Could not split name column: {e}")

    if rules.get('remove_duplicates', True):
        pre_dedup_len = len(df_clean)
        df_clean.drop_duplicates(inplace=True)
        logger.info(f"Removed {pre_dedup_len - len(df_clean)} duplicates.")

    return df_clean

def main():
    st.title("🧹 Data Cleaner")
    st.markdown("Upload a messy dataset and standardize it automatically using configurable rules.")

    config = load_config()
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'data_cleaner.log'))

    # Sidebar
    st.sidebar.header("⚙️ Cleaning Rules")
    default_rules = config.get('cleaning_rules', {})

    rules = {
        'remove_null_rows': st.sidebar.checkbox("Remove Empty Rows", value=default_rules.get('remove_null_rows', True)),
        'trim_whitespace': st.sidebar.checkbox("Trim Whitespace", value=default_rules.get('trim_whitespace', True)),
        'remove_duplicates': st.sidebar.checkbox("Remove Duplicates", value=default_rules.get('remove_duplicates', True)),
        'normalize_phone': st.sidebar.checkbox("Normalize Phone Numbers", help="Strips non-numeric characters from columns containing 'phone' or 'mobile'.", value=default_rules.get('normalize_phone', True)),
        'split_full_name': st.sidebar.checkbox("Split Full Names", help="Splits 'Name' or 'Full Name' columns into First and Last.", value=default_rules.get('split_full_name', True)),
        'convert_case': st.sidebar.selectbox("Convert Text Case", options=["none", "title", "lower", "upper"], index=["none", "title", "lower", "upper"].index(default_rules.get('convert_case', 'title')))
    }

    # Main Area
    uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.write("### Original Data Preview")
            st.dataframe(df.head())
            st.info(f"Original Row Count: {len(df)}")

            if st.button("🚀 Clean Data"):
                with st.spinner("Applying cleaning rules..."):
                    cleaned_df = clean_data(df, rules, logger)

                    st.success("Data successfully cleaned!")
                    st.write("### Cleaned Data Preview")
                    st.dataframe(cleaned_df.head())
                    st.info(f"Final Row Count: {len(cleaned_df)}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download Cleaned CSV",
                            data=convert_df_to_csv(cleaned_df),
                            file_name="cleaned_data.csv",
                            mime="text/csv"
                        )
                    with col2:
                        st.download_button(
                            label="📥 Download Cleaned Excel",
                            data=convert_df_to_excel(cleaned_df),
                            file_name="cleaned_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

        except Exception as e:
            st.error(f"Error reading or processing file: {e}")
            logger.error(f"UI Error: {e}")

if __name__ == "__main__":
    main()

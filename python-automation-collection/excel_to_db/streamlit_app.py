"""
Streamlit Web App for Excel to Database Module

This script provides a user-friendly web interface for uploading Excel files,
processing them based on configuration settings, and inserting the data into a database.
"""

import streamlit as st
import pandas as pd
import yaml
from io import BytesIO
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
import os

# Set up page config
st.set_page_config(page_title="Excel to DB Pipeline", page_icon="🗄️", layout="wide")

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("excel_to_db_ui")
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

def process_dataframe(df: pd.DataFrame, clean_nulls: bool, remove_duplicates: bool) -> pd.DataFrame:
    if clean_nulls:
        df.dropna(how='all', inplace=True)
    if remove_duplicates:
        df.drop_duplicates(inplace=True)

    unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
    if unnamed_cols:
        df.drop(columns=unnamed_cols, inplace=True)

    return df

def insert_to_db(df: pd.DataFrame, db_url: str, table_name: str) -> bool:
    try:
        engine = create_engine(db_url)
        with engine.begin() as connection:
            df.to_sql(name=table_name, con=connection, if_exists='replace', index=False)
        return True
    except SQLAlchemyError as e:
        st.error(f"Database error: {e}")
        return False
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return False

def to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Processed Data')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title("🗄️ Excel to Database Pipeline")
    st.markdown("Upload an Excel file to clean, validate, and insert its contents into a database.")

    # Sidebar Configuration
    st.sidebar.header("⚙️ Configuration")
    config = load_config()

    db_url = st.sidebar.text_input("Database URL", value=config.get('db', {}).get('url', 'sqlite:///database.sqlite'))
    table_name = st.sidebar.text_input("Target Table Name", value="excel_data")

    st.sidebar.subheader("Processing Rules")
    clean_nulls = st.sidebar.checkbox("Clean Null Values", value=config.get('excel', {}).get('clean_nulls', True))
    remove_duplicates = st.sidebar.checkbox("Remove Duplicates", value=config.get('excel', {}).get('remove_duplicates', True))

    log_level = config.get('logging', {}).get('level', 'INFO')
    log_file = config.get('logging', {}).get('file', 'excel_to_db.log')
    logger = setup_logger(log_level, log_file)

    # Main Area
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("### Preview of Uploaded Data")
            st.dataframe(df.head())

            if st.button("🚀 Process & Insert"):
                with st.spinner("Processing data..."):
                    processed_df = process_dataframe(df.copy(), clean_nulls, remove_duplicates)

                    st.write("### Preview of Processed Data")
                    st.dataframe(processed_df.head())
                    st.info(f"Rows before: {len(df)} | Rows after: {len(processed_df)}")

                    if insert_to_db(processed_df, db_url, table_name):
                        st.success(f"Data successfully inserted into table `{table_name}`!")
                        logger.info("UI: Data successfully processed and inserted.")

                        # Download Processed File
                        st.download_button(
                            label="📥 Download Processed File",
                            data=to_excel(processed_df),
                            file_name="processed_data.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        st.error("Failed to insert data into the database.")
                        logger.error("UI: Database insertion failed.")

        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
            logger.error(f"UI: Error reading Excel file - {e}")

if __name__ == "__main__":
    main()

"""
Excel to Database CLI

This script reads an Excel file, validates its columns, cleans null values,
removes duplicates, and inserts the data into an SQLite or PostgreSQL database.
"""

import argparse
import logging
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import yaml
from typing import Optional, List, Dict, Any

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    """Sets up the module logger."""
    logger = logging.getLogger("excel_to_db")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logger.level)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logger.level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def process_excel(filepath: str, config: Dict[str, Any], logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Reads and processes the Excel file according to configuration settings.
    """
    try:
        logger.info(f"Reading Excel file: {filepath}")
        df = pd.read_excel(filepath, sheet_name=config.get('excel', {}).get('sheet_name', 0))

        if df.empty:
            logger.warning("The Excel file is empty.")
            return None

        initial_rows = len(df)

        # Clean Nulls
        if config.get('excel', {}).get('clean_nulls', True):
            df.dropna(how='all', inplace=True) # Drop rows where all elements are missing.
            logger.info("Cleaned rows with all null values.")

        # Remove Duplicates
        if config.get('excel', {}).get('remove_duplicates', True):
            df.drop_duplicates(inplace=True)
            logger.info("Removed duplicate rows.")

        # Validate columns (basic example: ensure no unnamed columns)
        unnamed_cols = [col for col in df.columns if str(col).startswith('Unnamed:')]
        if unnamed_cols:
            df.drop(columns=unnamed_cols, inplace=True)
            logger.info(f"Dropped unnamed columns: {unnamed_cols}")

        final_rows = len(df)
        logger.info(f"Processing complete. Kept {final_rows} out of {initial_rows} rows.")
        return df

    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        return None

def insert_to_db(df: pd.DataFrame, db_url: str, table_name: str, logger: logging.Logger) -> bool:
    """
    Inserts a Pandas DataFrame into the specified database.
    """
    try:
        logger.info(f"Connecting to database: {db_url}")
        engine = create_engine(db_url)

        with engine.begin() as connection:
            logger.info(f"Inserting data into table '{table_name}'...")
            df.to_sql(name=table_name, con=connection, if_exists='replace', index=False)

        logger.info("Data inserted successfully.")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during database insertion: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Process an Excel file and insert it into a database.")
    parser.add_argument("filepath", type=str, help="Path to the Excel file.")
    parser.add_argument("--table", type=str, default="excel_data", help="Target database table name (default: excel_data).")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to the config.yaml file.")

    args = parser.parse_args()

    config = load_config(args.config)
    log_level = config.get('logging', {}).get('level', 'INFO')
    log_file = config.get('logging', {}).get('file', 'excel_to_db.log')

    logger = setup_logger(log_level, log_file)
    logger.info("Starting Excel to DB process...")

    df = process_excel(args.filepath, config, logger)

    if df is not None:
        db_url = config.get('db', {}).get('url', 'sqlite:///database.sqlite')
        success = insert_to_db(df, db_url, args.table, logger)
        if success:
            logger.info("Process completed successfully.")
        else:
            logger.error("Process failed during database insertion.")
    else:
        logger.error("Process failed during Excel reading/processing.")

if __name__ == "__main__":
    main()

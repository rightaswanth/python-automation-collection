"""
Data Cleaner CLI

Reads an Excel or CSV file and applies a suite of data cleaning rules
(trim whitespace, normalize phones, remove nulls, remove duplicates, etc.).
Exports the cleaned dataset to a new file.
"""

import argparse
import logging
import pandas as pd
import numpy as np
import yaml
import re
from typing import Dict, Any, Optional

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def setup_logger(log_level: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger("data_cleaner")
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

class DataCleaner:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.rules = self.config.get('cleaning_rules', {})

    def load_data(self, filepath: str) -> Optional[pd.DataFrame]:
        try:
            self.logger.info(f"Loading data from {filepath}")
            if filepath.endswith('.csv'):
                return pd.read_csv(filepath)
            elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                return pd.read_excel(filepath)
            else:
                self.logger.error("Unsupported file format. Please provide a CSV or Excel file.")
                return None
        except Exception as e:
            self.logger.error(f"Error reading file: {e}")
            return None

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        self.logger.info(f"Starting data cleaning. Initial rows: {len(df)}")

        # 1. Remove Null Rows
        if self.rules.get('remove_null_rows', True):
            original_len = len(df)
            df = df.dropna(how='all')
            self.logger.info(f"Removed {original_len - len(df)} rows containing all nulls.")

        # 2. Trim Whitespace
        if self.rules.get('trim_whitespace', True):
            df = df.map(lambda x: str(x).strip() if isinstance(x, str) else x)
            self.logger.info("Trimmed leading/trailing whitespace from all string columns.")

        # 3. Convert Case
        case_rule = self.rules.get('convert_case', 'title').lower()
        if case_rule in ['lower', 'upper', 'title']:
            for col in df.select_dtypes(include=['object']):
                if case_rule == 'lower':
                    df[col] = df[col].str.lower()
                elif case_rule == 'upper':
                    df[col] = df[col].str.upper()
                elif case_rule == 'title':
                    df[col] = df[col].str.title()
            self.logger.info(f"Converted all string columns to {case_rule} case.")

        # 4. Normalize Phone Numbers
        if self.rules.get('normalize_phone', True):
            # Look for common phone column names (case-insensitive)
            phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'mobile' in col.lower()]
            for col in phone_cols:
                # Strip non-numeric characters (basic international/national cleaning)
                # Keep '+' if it's the first character
                df[col] = df[col].apply(lambda x: re.sub(r'[^\d+]', '', str(x)) if pd.notnull(x) else x)
                # E.g., "(123) 456-7890" -> "1234567890"
                self.logger.info(f"Normalized phone numbers in column '{col}'.")

        # 5. Split Full Name
        if self.rules.get('split_full_name', True):
            name_cols = [col for col in df.columns if col.lower() in ['name', 'full name', 'fullname']]
            for col in name_cols:
                # Basic split by first space
                try:
                    split_df = df[col].str.split(' ', n=1, expand=True)
                    if len(split_df.columns) == 2:
                        df['First Name'] = split_df[0]
                        df['Last Name'] = split_df[1]
                        df.drop(columns=[col], inplace=True)
                        self.logger.info(f"Split column '{col}' into 'First Name' and 'Last Name'.")
                    elif len(split_df.columns) == 1:
                        df['First Name'] = split_df[0]
                        df['Last Name'] = ""
                        df.drop(columns=[col], inplace=True)
                        self.logger.info(f"Split column '{col}' into 'First Name' (no Last Name found).")
                except Exception as e:
                    self.logger.warning(f"Could not split full name column '{col}': {e}")

        # 6. Remove Duplicates
        if self.rules.get('remove_duplicates', True):
            original_len = len(df)
            df = df.drop_duplicates()
            self.logger.info(f"Removed {original_len - len(df)} duplicate rows.")

        self.logger.info(f"Data cleaning complete. Final rows: {len(df)}")
        return df

    def save_data(self, df: pd.DataFrame, filepath: str):
        try:
            if filepath.endswith('.csv'):
                df.to_csv(filepath, index=False)
            elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                df.to_excel(filepath, index=False)
            self.logger.info(f"Saved cleaned data to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Data Cleaner CLI.")
    parser.add_argument("input", type=str, help="Input file path (.csv or .xlsx).")
    parser.add_argument("--output", type=str, default="cleaned_data.xlsx", help="Output file path.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file path.")

    args = parser.parse_args()

    config = load_config(args.config)
    logger = setup_logger(config.get('logging', {}).get('level', 'INFO'), config.get('logging', {}).get('file', 'data_cleaner.log'))

    cleaner = DataCleaner(config, logger)
    df = cleaner.load_data(args.input)

    if df is not None:
        cleaned_df = cleaner.clean(df)
        cleaner.save_data(cleaned_df, args.output)

if __name__ == "__main__":
    main()

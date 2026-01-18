import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Tuple

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
CLEANED_DIR = os.path.join(os.path.dirname(__file__), 'cleaned')
PREVIEW_DIR = os.path.join(os.path.dirname(__file__), 'preview')

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

def load_data(file_path: str) -> Tuple[pd.DataFrame, str]:
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
        return df, 'csv'
    elif ext in ['.xls', '.xlsx']:
        df = pd.read_excel(file_path)
        return df, 'excel'
    elif ext == '.dta':
        try:
            import pyreadstat
            df, meta = pyreadstat.read_dta(file_path)
        except ImportError:
            df = pd.read_stata(file_path)
        return df, 'stata'
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=lambda x: str(x).strip().lower().replace(' ', '_'))
    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    # Drop columns with >50% missing
    thresh = int(0.5 * len(df))
    df = df.dropna(axis=1, thresh=thresh)
    # Forward fill, then backward fill
    df = df.ffill().bfill()
    return df

def drop_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, df.nunique(dropna=False) > 1]

def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def convert_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    return df.convert_dtypes()

def remove_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    # Remove extreme outliers using IQR for numeric columns
    for col in df.select_dtypes(include=[np.number]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        mask = (df[col] >= Q1 - 3 * IQR) & (df[col] <= Q3 + 3 * IQR)
        df = df[mask]
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_column_names(df)
    df = handle_missing_values(df)
    df = drop_constant_columns(df)
    df = drop_duplicates(df)
    df = convert_dtypes(df)
    df = remove_outliers_iqr(df)
    return df

def generate_column_summary(df: pd.DataFrame) -> dict:
    summary = {}
    for col in df.columns:
        col_data = df[col]
        summary[col] = {
            'data_type': str(col_data.dtype),
            'missing_pct': float(col_data.isnull().mean()) * 100,
            'unique_values': int(col_data.nunique(dropna=True)),
            'sample_values': col_data.dropna().unique()[:5].tolist()
        }
    return summary

def save_cleaned_data(df: pd.DataFrame, original_filename: str) -> str:
    base = os.path.splitext(os.path.basename(original_filename))[0]
    cleaned_path = os.path.join(CLEANED_DIR, f'{base}_cleaned.csv')
    df.to_csv(cleaned_path, index=False)
    return cleaned_path

def save_preview(df: pd.DataFrame, original_filename: str) -> str:
    base = os.path.splitext(os.path.basename(original_filename))[0]
    preview_path = os.path.join(PREVIEW_DIR, f'{base}_preview.csv')
    df.head(10).to_csv(preview_path, index=False)
    return preview_path

def save_column_summary(summary: dict, original_filename: str) -> str:
    base = os.path.splitext(os.path.basename(original_filename))[0]
    summary_path = os.path.join(CLEANED_DIR, f'{base}_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    return summary_path

def main(file_path: str):
    print(f"\n Cleaning: {file_path}")
    df, filetype = load_data(file_path)
    print(f"Loaded {filetype.upper()} file with shape: {df.shape}")
    cleaned = clean_data(df)
    print(f"Cleaned data shape: {cleaned.shape}")
    summary = generate_column_summary(cleaned)
    cleaned_path = save_cleaned_data(cleaned, file_path)
    preview_path = save_preview(cleaned, file_path)
    summary_path = save_column_summary(summary, file_path)
    print(f"\n Cleaned file saved to: {cleaned_path}")
    print(f" Preview (first 10 rows) saved to: {preview_path}")
    print(f" Column summary saved to: {summary_path}")
    print("\nColumn Summary:")
    print(json.dumps(summary, indent=2))
    print("\nPreview of cleaned data:")
    print(cleaned.head(10).to_string(index=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleaner.py uploads/yourfile.csv")
        sys.exit(1)
    main(sys.argv[1]) 
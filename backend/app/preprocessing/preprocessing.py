"""
Preprocess the cleaned job postings dataset.

This script:
1. Loads the cleaned dataset.
2. Cleans and normalizes text.
3. Creates a combined text field for job matching.
4. Saves the processed dataset.
"""

from pathlib import Path
import re

import pandas as pd

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[3]

CLEANED_DATA_DIRECTORY = (
    BASE_DIR
    / "data"
    / "cleaned"
)

PROCESSED_DATA_DIRECTORY = (
    BASE_DIR
    / "data"
    / "processed"
)

PROCESSED_DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

INPUT_FILE = (
    CLEANED_DATA_DIRECTORY
    / "jobs_clean.csv"
)

OUTPUT_FILE = (
    PROCESSED_DATA_DIRECTORY
    / "jobs_processed.csv"
)

# ==========================================
# LOAD DATASET
# ==========================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Clean dataset not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("=" * 50)
print("PREPROCESSING DATASET")
print("=" * 50)
print(f"Input Shape : {df.shape}")

# ==========================================
# TEXT CLEANING
# ==========================================

def clean_text(text: str) -> str:

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(
        r"<.*?>",
        " ",
        text,
    )

    text = re.sub(
        r"http\\S+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9 ]",
        " ",
        text,
    )

    text = re.sub(
        r"\\s+",
        " ",
        text,
    )

    return text.strip()

# ==========================================
# CLEAN TEXT COLUMNS
# ==========================================

text_columns = [
    "Job Title",
    "Job Description",
    "Company Name",
    "Companydescription",
    "Industry",
    "Categories",
    "Job Type",
]

for column in text_columns:

    if column in df.columns:

        df[column] = (
            df[column]
            .fillna("")
            .apply(clean_text)
        )

# ==========================================
# CREATE COMBINED TEXT
# ==========================================

combined_columns = [
    "Job Title",
    "Job Description",
    "Companydescription",
    "Industry",
    "Categories",
]

available_columns = [
    column
    for column in combined_columns
    if column in df.columns
]

df["combined_text"] = (
    df[available_columns]
    .astype(str)
    .agg(
        " ".join,
        axis=1,
    )
)

# ==========================================
# SAVE DATASET
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

# ==========================================
# SUMMARY
# ==========================================

print("\nPreprocessing Completed Successfully!")
print("-" * 50)
print(f"Final Shape : {df.shape}")
print(f"Output File : {OUTPUT_FILE}")
print("=" * 50)
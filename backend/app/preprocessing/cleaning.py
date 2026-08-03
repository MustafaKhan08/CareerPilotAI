"""
Clean the raw job postings dataset before importing it into the database.
"""

from pathlib import Path

import pandas as pd

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[3]

RAW_DATA_DIRECTORY = (
    BASE_DIR
    / "data"
    / "raw"
)

CLEANED_DATA_DIRECTORY = (
    BASE_DIR
    / "data"
    / "cleaned"
)

CLEANED_DATA_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

INPUT_FILE = (
    RAW_DATA_DIRECTORY
    / "job_postings_dataset.csv"
)

OUTPUT_FILE = (
    CLEANED_DATA_DIRECTORY
    / "jobs_clean.csv"
)

# ==========================================
# CHECK IF DATASET EXISTS
# ==========================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found:\n{INPUT_FILE}"
    )

# ==========================================
# LOAD DATASET
# ==========================================

df = pd.read_csv(INPUT_FILE)

print("=" * 50)
print("DATASET LOADED SUCCESSFULLY")
print("=" * 50)
print(f"Original Shape : {df.shape}")

# ==========================================
# HANDLE MISSING VALUES
# ==========================================

text_columns = [
    "Job Title",
    "Job Description",
    "Job Type",
    "Categories",
    "Location",
    "City",
    "State",
    "Country",
    "Industry",
    "Company Name",
    "Companydescription",
    "Apply Url",
]

for column in text_columns:

    if column in df.columns:

        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

salary_columns = [
    "Salary From",
    "Salary To",
]

for column in salary_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

# ==========================================
# REMOVE UNWANTED COLUMNS
# ==========================================

columns_to_drop = [
    "Uniq Id",
    "Address",
    "Employer Email",
    "Employer Website",
    "Employer Phone",
    "Employer Logo",
    "Employer Location",
    "Employer City",
    "Employer State",
    "Employer Country",
    "Employer Zip Code",
    "Zip Code",
]

existing_columns = [
    column
    for column in columns_to_drop
    if column in df.columns
]

if existing_columns:

    df.drop(
        columns=existing_columns,
        inplace=True,
    )

    print(
        f"\nRemoved Columns : {len(existing_columns)}"
    )

else:

    print("\nNo columns removed.")

# ==========================================
# REMOVE DUPLICATES
# ==========================================

duplicates_removed = df.duplicated().sum()

df.drop_duplicates(
    inplace=True,
)

df.reset_index(
    drop=True,
    inplace=True,
)

# ==========================================
# SAVE CLEAN DATASET
# ==========================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

# ==========================================
# SUMMARY
# ==========================================

print("\nCleaning Completed Successfully!")
print("-" * 50)
print(f"Final Shape        : {df.shape}")
print(f"Duplicates Removed : {duplicates_removed}")
print(f"Output File        : {OUTPUT_FILE}")
print("=" * 50)
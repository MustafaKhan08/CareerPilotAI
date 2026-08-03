"""
Import processed jobs from a CSV file into the database.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.jobs.model import Job


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PROCESSED_DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "jobs_processed.csv"
)


# =====================================================
# HELPERS
# =====================================================

def clean_value(value):
    """
    Convert pandas NaN values to None.
    """

    if pd.isna(value):
        return None

    return value


def clean_string(value):
    """
    Return a stripped string or None.
    """

    value = clean_value(value)

    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def clean_float(value):
    """
    Convert values to float safely.
    """

    value = clean_value(value)

    if value is None:
        return None

    try:
        return float(value)

    except Exception:
        return None


def clean_int(value):
    """
    Convert values to int safely.
    """

    value = clean_value(value)

    if value is None:
        return None

    try:
        return int(value)

    except Exception:
        return None


def clean_datetime(value):
    """
    Convert timestamps safely.
    """

    value = clean_value(value)

    if value is None:
        return None

    try:
        return pd.to_datetime(value)

    except Exception:
        return None


# =====================================================
# IMPORT JOBS
# =====================================================

def import_jobs(
    db: Session,
) -> tuple[int, int]:
    """
    Import all processed jobs into PostgreSQL.

    Returns
    -------
    (imported, skipped)
    """

    if not PROCESSED_DATA_FILE.exists():

        raise FileNotFoundError(
            f"Processed dataset not found:\n{PROCESSED_DATA_FILE}"
        )

    df = pd.read_csv(
        PROCESSED_DATA_FILE,
    )

    imported = 0
    skipped = 0

    jobs = []

    for _, row in df.iterrows():

        title = clean_string(
            row.get("Job Title")
        )

        description = clean_string(
            row.get("Job Description")
        )

        combined_text = clean_string(
            row.get("combined_text")
        )

        if (
            title is None
            or description is None
            or combined_text is None
        ):

            skipped += 1
            continue

        job = Job(

            job_title=title,

            job_description=description,

            combined_text=combined_text,

            job_type=clean_string(
                row.get("Job Type")
            ),

            categories=clean_string(
                row.get("Categories")
            ),

            location=clean_string(
                row.get("Location")
            ),

            city=clean_string(
                row.get("City")
            ),

            state=clean_string(
                row.get("State")
            ),

            country=clean_string(
                row.get("Country")
            ),

            salary_from=clean_float(
                row.get("Salary From")
            ),

            salary_to=clean_float(
                row.get("Salary To")
            ),

            salary_period=clean_string(
                row.get("Salary Period")
            ),

            apply_url=clean_string(
                row.get("Apply Url")
            ),

            apply_email=clean_string(
                row.get("Apply Email")
            ),

            employees=clean_int(
                row.get("Employees")
            ),

            industry=clean_string(
                row.get("Industry")
            ),

            company_name=clean_string(
                row.get("Company Name")
            ),

            company_description=clean_string(
                row.get("Companydescription")
            ),

            crawl_timestamp=clean_datetime(
                row.get("Crawl Timestamp")
            ),
        )

        jobs.append(job)

    print(f"\nPrepared {len(jobs)} jobs for import...")

    try:
        db.bulk_save_objects(jobs)
        db.commit()

    except Exception:
        db.rollback()
        raise

    imported = len(jobs)

    return (
        imported,
        skipped,
    )
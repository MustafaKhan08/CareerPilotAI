"""
Import jobs_processed.csv into PostgreSQL.

Run from the backend folder:

    python ..\scripts\import_jobs.py
"""

import sys
from pathlib import Path

import pandas as pd

# =====================================================
# PROJECT PATHS
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

# =====================================================
# IMPORTS
# =====================================================

from app.db.database import SessionLocal
from app.jobs.model import Job

# =====================================================
# CONFIG
# =====================================================

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jobs_processed.csv"
)

BATCH_SIZE = 1000

# =====================================================
# HELPERS
# =====================================================


def clean(value):
    if pd.isna(value):
        return None
    return value


def parse_timestamp(value):
    if pd.isna(value):
        return None

    try:
        return pd.to_datetime(
            value,
            utc=True,
        ).to_pydatetime()
    except Exception:
        return None


# =====================================================
# IMPORT
# =====================================================


def main():

    print("=" * 60)
    print("Loading CSV...")
    print("=" * 60)

    df = pd.read_csv(CSV_PATH)

    print(f"Rows found: {len(df)}")
    print()

    db = SessionLocal()

    try:

        total = len(df)

        for start in range(
            0,
            total,
            BATCH_SIZE,
        ):

            end = min(
                start + BATCH_SIZE,
                total,
            )

            batch = df.iloc[start:end]

            objects = []

            for _, row in batch.iterrows():

                objects.append(
                    Job(
                        id=int(row["id"]),
                        job_title=clean(row["Job Title"]),
                        job_description=clean(
                            row["Job Description"]
                        ),
                        combined_text=clean(
                            row["combined_text"]
                        ),
                        job_type=clean(
                            row["Job Type"]
                        ),
                        categories=clean(
                            row["Categories"]
                        ),
                        location=clean(
                            row["Location"]
                        ),
                        city=clean(
                            row["City"]
                        ),
                        state=clean(
                            row["State"]
                        ),
                        country=clean(
                            row["Country"]
                        ),
                        salary_from=clean(
                            row["Salary From"]
                        ),
                        salary_to=clean(
                            row["Salary To"]
                        ),
                        salary_period=clean(
                            row["Salary Period"]
                        ),
                        apply_url=clean(
                            row["Apply Url"]
                        ),
                        apply_email=clean(
                            row["Apply Email"]
                        ),
                        employees=clean(
                            row["Employees"]
                        ),
                        industry=clean(
                            row["Industry"]
                        ),
                        company_name=clean(
                            row["Company Name"]
                        ),
                        company_description=clean(
                            row["Companydescription"]
                        ),
                        crawl_timestamp=parse_timestamp(
                            row["Crawl Timestamp"]
                        ),
                    )
                )

            db.bulk_save_objects(objects)
            db.commit()

            print(
                f"Imported {end:,}/{total:,}"
            )

        print()
        print("=" * 60)
        print("IMPORT COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:

        db.rollback()
        print(e)
        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
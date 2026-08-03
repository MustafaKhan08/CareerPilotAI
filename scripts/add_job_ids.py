"""
Add sequential IDs to jobs_processed.csv.

This is a one-time migration script.

Workflow
--------
1. Create a backup of the original CSV.
2. Insert an 'id' column as the first column.
3. Save the updated CSV.
"""

from pathlib import Path
import shutil

import pandas as pd


# ==========================================================
# File Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jobs_processed.csv"
)

BACKUP_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jobs_processed_backup.csv"
)


# ==========================================================
# Main
# ==========================================================

def main() -> None:

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found:\n{CSV_PATH}"
        )

    # Create backup only once
    if not BACKUP_PATH.exists():
        shutil.copy2(
            CSV_PATH,
            BACKUP_PATH,
        )
        print(f"Backup created:\n{BACKUP_PATH}")

    df = pd.read_csv(CSV_PATH)

    if "id" in df.columns:
        print("The CSV already contains an 'id' column.")
        return

    df.insert(
        0,
        "id",
        range(1, len(df) + 1),
    )

    df.to_csv(
        CSV_PATH,
        index=False,
    )

    print(f"Added IDs to {len(df)} rows.")
    print(f"Updated CSV:\n{CSV_PATH}")


if __name__ == "__main__":
    main()
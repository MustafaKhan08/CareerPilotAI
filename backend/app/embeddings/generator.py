"""
Embedding Index Generator
=========================

Generates semantic embeddings for every job in the processed
dataset using the NVIDIA Embedding API.

Responsibilities
----------------
- Read processed jobs dataset
- Generate embeddings in batches
- Resume after interruption
- Save embeddings
- Save job IDs
- Save metadata
- Track progress
- Log failures

This script is intended to be run whenever the jobs dataset
changes.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from app.embeddings.client import EmbeddingClient
from app.embeddings.config import (
    CHECKPOINT_PATH,
    EMBEDDING_BATCH_SIZE,
    FAILED_BATCHES_LOG,
)
from app.embeddings.storage import EmbeddingStorage

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates embedding indexes from jobs_processed.csv.
    """

    REQUIRED_COLUMNS = (
        "combined_text",
    )

    JOB_ID_CANDIDATES = (
        "id",
        "job_id",
        "Job ID",
        "JobID",
        "AppID",
    )


    def __init__(
        self,
        csv_path: str | Path,
    ) -> None:
        """
        Initialize the generator.

        Parameters
        ----------
        csv_path:
            Path to jobs_processed.csv
        """

        self.csv_path = Path(csv_path)

        self.client = EmbeddingClient()

        self.df: pd.DataFrame | None = None

        self.job_id_column: str | None = None

        self.job_ids: list[int] = []

        self.embeddings: list[np.ndarray] = []

        self.checkpoint = self._load_checkpoint()


    async def run(self) -> None:
        """
        Main entry point.

        Workflow

        1. Load CSV
        2. Validate dataset
        3. Generate embeddings
        4. Save embeddings
        5. Save metadata
        """

        logger.info(
            "Starting embedding generation..."
        )

        try:
            self._load_dataset()

            await self._generate()

            self._save_everything()

            logger.info(
                "Embedding generation completed successfully."
            )

        finally:
            await self.client.close()


    def _load_dataset(self) -> None:
        """
        Load jobs_processed.csv.
        """

        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.csv_path}"
            )

        self.df = pd.read_csv(self.csv_path)

        logger.info(
            "Loaded dataset with %d rows.",
            len(self.df),
        )


        self._validate_dataset()


    def _validate_dataset(self) -> None:
        """
        Validate required dataset columns.
        """

        if self.df is None:
            raise RuntimeError(
                "Dataset has not been loaded."
            )

        for column in self.REQUIRED_COLUMNS:
            if column not in self.df.columns:
                raise ValueError(
                    f"Missing required column: {column}"
                )

        job_id_column = None

        for candidate in self.JOB_ID_CANDIDATES:
            if candidate in self.df.columns:
                job_id_column = candidate
                break

        if job_id_column is None:
            raise ValueError(
                "Unable to locate job ID column."
            )

        self.job_id_column = job_id_column

        logger.info(
            "Using '%s' as job ID column.",
            job_id_column,
        )


    def _load_checkpoint(self) -> dict[str, Any]:
        """
        Load checkpoint if it exists.
        """

        if not CHECKPOINT_PATH.exists():
            return {
                "next_batch": 0,
            }

        with open(
            CHECKPOINT_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            checkpoint = json.load(file)

        logger.info(
            "Resuming from batch %d.",
            checkpoint["next_batch"],
        )

        return checkpoint


    async def _generate(self) -> None:
        """
        Generate embeddings for every job.

        Supports checkpoint recovery and batch processing.
        """

        if self.df is None:
            raise RuntimeError(
                "Dataset has not been loaded."
            )

        start_batch = self.checkpoint.get(
            "next_batch",
            0,
        )

        total_rows = len(self.df)

        logger.info(
            "Generating embeddings for %d jobs.",
            total_rows,
        )

        progress = tqdm(
            range(
                start_batch,
                total_rows,
                EMBEDDING_BATCH_SIZE,
            ),
            desc="Embedding Jobs",
            unit="batch",
        )

        for batch_start in progress:
            batch_end = min(
                batch_start + EMBEDDING_BATCH_SIZE,
                total_rows,
            )

            batch = self.df.iloc[
                batch_start:batch_end
            ]

            try:
                await self._process_batch(
                    batch=batch,
                    batch_start=batch_start,
                    batch_end=batch_end,
                )

                self._save_checkpoint(
                    batch_end,
                )

            except Exception as exc:

                logger.exception(
                    "Batch %d-%d failed.",
                    batch_start,
                    batch_end,
                )

                self._log_failed_batch(
                    batch_start=batch_start,
                    batch_end=batch_end,
                    error=str(exc),
                )


    async def _process_batch(
        self,
        batch: pd.DataFrame,
        batch_start: int,
        batch_end: int,
    ) -> None:
        """
        Generate embeddings for one batch.
        """

        texts = (
            batch["combined_text"]
            .fillna("")
            .astype(str)
            .tolist()
        )

        ids = (
            batch[self.job_id_column]
            .tolist()
        )

        vectors = await self.client.embed_passages(
            texts
        )

        self.embeddings.extend(vectors)

        self.job_ids.extend(ids)

        logger.info(
            "Processed batch %d-%d (%d jobs).",
            batch_start,
            batch_end,
            len(ids),
        )


    def _save_checkpoint(
        self,
        next_batch: int,
    ) -> None:
        """
        Save current progress.
        """

        checkpoint = {
            "next_batch": next_batch,
        }

        with open(
            CHECKPOINT_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                checkpoint,
                file,
                indent=4,
            )


    def _log_failed_batch(
        self,
        batch_start: int,
        batch_end: int,
        error: str,
    ) -> None:
        """
        Permanently log failed batches.
        """

        with open(
            FAILED_BATCHES_LOG,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                (
                    f"{batch_start},"
                    f"{batch_end},"
                    f"{error}\n"
                )
            )


    def _save_everything(self) -> None:
        """
        Save the completed embedding index.

        This includes:

        - Embedding vectors
        - Job ID mapping
        - Metadata
        - Validation
        """

        logger.info(
            "Saving embedding index..."
        )

        embeddings = np.asarray(
            self.embeddings,
            dtype=np.float32,
        )

        job_ids = np.asarray(
            self.job_ids,
            dtype=np.int64,
        )

        if len(embeddings) != len(job_ids):
            raise RuntimeError(
                "Embedding count does not match job ID count."
            )

        EmbeddingStorage.save_embeddings(
            embeddings,
        )

        EmbeddingStorage.save_job_ids(
            job_ids,
        )

        metadata = self._build_metadata(
            embeddings,
        )

        EmbeddingStorage.save_metadata(
            metadata,
        )

        EmbeddingStorage.validate_index()

        self._cleanup_checkpoint()

        logger.info(
            "Embedding index saved successfully."
        )


    def _build_metadata(
        self,
        embeddings: np.ndarray,
    ) -> dict[str, Any]:
        """
        Build metadata describing the generated index.
        """

        model_name = getattr(
            self.client,
            "active_model",
            None,
        )

        if model_name is None:
            model_name = "unknown"

        return {
            "model": model_name,
            "embedding_dimension": int(
                embeddings.shape[1]
            ),
            "job_count": int(
                embeddings.shape[0]
            ),
            "created_at": datetime.now(
                UTC
            ).isoformat(),
            "generator_version": "1.0",
            "csv_sha256": self._calculate_csv_hash(),
        }


    def _calculate_csv_hash(self) -> str:
        """
        Calculate a SHA256 hash of the source CSV.

        Used to detect when the dataset changes.
        """

        sha256 = hashlib.sha256()

        with open(
            self.csv_path,
            "rb",
        ) as file:

            while True:

                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()


    def _cleanup_checkpoint(self) -> None:
        """
        Remove the checkpoint after successful generation.
        """

        if CHECKPOINT_PATH.exists():

            CHECKPOINT_PATH.unlink()

            logger.info(
                "Checkpoint removed."
            )


async def generate_embeddings(
    csv_path: str | Path,
) -> None:
    """
    Convenience entry point for embedding generation.
    """

    generator = EmbeddingGenerator(csv_path)

    await generator.run()


if __name__ == "__main__":

    DEFAULT_DATASET = (
        Path(__file__)
        .resolve()
        .parents[3]
        / "data"
        / "processed"
        / "jobs_processed.csv"
    )

    asyncio.run(
        generate_embeddings(
            DEFAULT_DATASET,
        )
    )
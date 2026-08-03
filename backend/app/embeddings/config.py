"""
Embedding subsystem configuration.

This module centralizes every configuration value used by the
semantic search pipeline.

No business logic should exist here.
"""

from pathlib import Path

from app.core.config import settings


# ==========================================================
# Base Directory
# ==========================================================

# Backend directory
BACKEND_DIR = Path(__file__).resolve().parents[2]


# ==========================================================
# NVIDIA API
# ==========================================================

NVIDIA_EMBEDDING_API_URL = settings.nvidia_embedding_api_url

PRIMARY_EMBEDDING_MODEL = settings.embedding_primary_model

FALLBACK_EMBEDDING_MODEL = settings.embedding_fallback_model

EXPECTED_EMBEDDING_DIMENSION = 2048


# ==========================================================
# Runtime Configuration
# ==========================================================

EMBEDDING_BATCH_SIZE = settings.embedding_batch_size

EMBEDDING_TIMEOUT = settings.embedding_timeout

EMBEDDING_MAX_RETRIES = settings.embedding_max_retries

EMBEDDING_BACKOFF_SECONDS = (
    settings.embedding_backoff_base_seconds
)

DEFAULT_TOP_K = settings.embedding_similarity_top_k


# ==========================================================
# Storage
# ==========================================================

EMBEDDINGS_DIRECTORY = (
    BACKEND_DIR
    / settings.embedding_storage_directory
)

EMBEDDINGS_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


# ==========================================================
# Primary Embedding Index
# ==========================================================

PRIMARY_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIRECTORY
    / "job_embeddings_nemotron3.npy"
)

PRIMARY_METADATA_PATH = (
    EMBEDDINGS_DIRECTORY
    / "metadata_primary.json"
)

# ==========================================================
# Fallback Embedding Index
# ==========================================================

FALLBACK_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIRECTORY
    / "job_embeddings_llama.npy"
)

FALLBACK_METADATA_PATH = (
    EMBEDDINGS_DIRECTORY
    / "metadata_fallback.json"
)


# ==========================================================
# Shared Files
# ==========================================================

JOB_IDS_PATH = (
    EMBEDDINGS_DIRECTORY
    / "job_ids.npy"
)

CHECKPOINT_PATH = (
    EMBEDDINGS_DIRECTORY
    / "checkpoint.json"
)

FAILED_BATCHES_LOG = (
    EMBEDDINGS_DIRECTORY
    / "failed_batches.log"
)
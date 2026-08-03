"""
Business logic for the Job module.

Provides CRUD operations and semantic job search.
"""

from __future__ import annotations

import logging

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.embeddings.client import EmbeddingClient
from app.embeddings.similarity import similarity_engine
from app.jobs.model import Job
from app.jobs.schema import JobCreate

logger = logging.getLogger(__name__)

# =====================================================
# Shared Semantic Search Components
# =====================================================

embedding_client = EmbeddingClient()
# =====================================================
# CREATE
# =====================================================

def create_job(
    db: Session,
    job_data: JobCreate,
) -> Job:
    """
    Create and persist a new job.
    """

    job = Job(
        **job_data.model_dump(
            exclude_none=True,
        )
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


# =====================================================
# READ
# =====================================================

def get_job_by_id(
    db: Session,
    job_id: int,
) -> Job | None:
    """
    Return a job by its ID.
    """

    return (
        db.query(Job)
        .filter(
            Job.id == job_id,
        )
        .first()
    )


def get_all_jobs(
    db: Session,
) -> list[Job]:
    """
    Return all jobs ordered by newest first.
    """

    return (
        db.query(Job)
        .order_by(
            Job.created_at.desc(),
        )
        .all()
    )


# =====================================================
# SEARCH
# =====================================================

# =====================================================
# SEARCH
# =====================================================

async def search_jobs(
    db: Session,
    query: str,
    *,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """
    Perform semantic job search using the embedding index.
    """

    logger.info(
        "Performing semantic search for '%s'.",
        query,
    )

    query_embedding = await embedding_client.embed_query(
        query
    )

    matches = similarity_engine.search(
        query_embedding=query_embedding,
        top_k=100,
        page=page,
        limit=limit,
    )

    if not matches:
        return {
            "total": 0,
            "jobs": [],
        }

    job_ids = [
        match["job_id"]
        for match in matches
    ]

    similarity_scores = {
        match["job_id"]: match["similarity_score"]
        for match in matches
    }

    ordering = case(
        {job_id: index for index, job_id in enumerate(job_ids)},
        value=Job.id,
    )

    jobs = (
        db.query(Job)
        .filter(
            Job.id.in_(job_ids),
        )
        .order_by(ordering)
        .all()
    )

    results = []

    for job in jobs:

        results.append(
            {
                "id": job.id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "location": job.location,
                "job_type": job.job_type,
                "salary_from": job.salary_from,
                "salary_to": job.salary_to,
                "industry": job.industry,
                "apply_url": job.apply_url,
                "similarity_score": similarity_scores.get(
                    job.id,
                    0.0,
                ),
            }
        )

    logger.info(
        "Semantic search returned %d jobs.",
        len(results),
    )

    return {
        "total": len(results),
        "jobs": results,
    }

# =====================================================
# DELETE
# =====================================================

def delete_job(
    db: Session,
    job_id: int,
) -> bool:
    """
    Delete a job.
    """

    job = get_job_by_id(
        db=db,
        job_id=job_id,
    )

    if job is None:
        return False

    db.delete(job)
    db.commit()

    return True


# =====================================================
# CSV IMPORT (Placeholder)
# =====================================================

def import_jobs_from_csv(
    db: Session,
) -> None:
    """
    Placeholder.

    In the next sprint this function will:

    - Load jobs_processed.csv
    - Convert every row into a Job model
    - Bulk insert all jobs
    - Skip duplicates
    """

    raise NotImplementedError(
        "CSV importer will be implemented in the next sprint."
    )
"""
HTTP endpoints for the Job module.
"""

from app.jobs.importer import import_jobs
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.db.database import get_db
from app.jobs.schema import (
    JobCreate,
    JobResponse,
    JobSearchResponse,
    JobSummaryResponse,
)
from app.jobs.service import (
    create_job,
    delete_job,
    get_all_jobs,
    get_job_by_id,
    search_jobs,
)
from app.users.model import User

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


# =====================================================
# GET ALL JOBS
# =====================================================

@router.get(
    "",
    response_model=list[JobResponse],
    status_code=status.HTTP_200_OK,
)
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> list[JobResponse]:
    """
    Return all available jobs.
    """

    jobs = get_all_jobs(
        db=db,
    )

    return [
        JobResponse.model_validate(job)
        for job in jobs
    ]


# =====================================================
# SEARCH JOBS
# =====================================================

@router.get(
    "/search",
    response_model=JobSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_job_listings(
    query: Annotated[
        str,
        Query(
            min_length=1,
            description="Semantic search query",
        ),
    ],
    *,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    page: Annotated[
        int,
        Query(
            ge=1,
            description="Page number",
        ),
    ] = 1,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=50,
            description="Results per page",
        ),
    ] = 20,
) -> JobSearchResponse:
    """
    Perform semantic job search.
    """

    jobs = await search_jobs(
        db=db,
        query=query,
        page=page,
        limit=limit,
    )

    return JobSearchResponse(
        query=query,
        total=jobs["total"],
        page=page,
        limit=limit,
        jobs=[
            JobSummaryResponse.model_validate(job)
            for job in jobs["jobs"]
        ],
    )


# =====================================================
# GET JOB
# =====================================================

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
def get_job(
    job_id: int,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> JobResponse:
    """
    Return a job by its ID.
    """

    job = get_job_by_id(
        db=db,
        job_id=job_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return JobResponse.model_validate(
        job,
    )


# =====================================================
# CREATE JOB
# =====================================================

@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_job_listing(
    job_data: JobCreate,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> JobResponse:
    """
    Create a new job.
    """

    job = create_job(
        db=db,
        job_data=job_data,
    )

    return JobResponse.model_validate(
        job,
    )


# =====================================================
# DELETE JOB
# =====================================================

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_job(
    job_id: int,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> Response:
    """
    Delete a job.
    """

    deleted = delete_job(
        db=db,
        job_id=job_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

# =====================================================
# IMPORT JOBS
# =====================================================

@router.post(
    "/import",
    status_code=status.HTTP_200_OK,
)
def import_jobs_endpoint(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> dict[str, int | str]:
    """
    Import all processed jobs into the database.
    """

    imported, skipped = import_jobs(
        db=db,
    )

    return {
        "message": "Job import completed successfully.",
        "imported": imported,
        "skipped": skipped,
    }
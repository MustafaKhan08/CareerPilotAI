"""
Business logic for persisted resume analyses.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.analyses.model import (
    AnalysisStatus,
    ResumeAnalysis,
)
from app.analyses.schema import (
    ResumeAnalysisCreate,
    ResumeAnalysisResponse,
    ResumeAnalysisSummary,
)

logger = logging.getLogger(__name__)


# ==========================================================
# CREATE
# ==========================================================


def create_analysis(
    db: Session,
    analysis: ResumeAnalysisCreate,
) -> ResumeAnalysis:
    """
    Persist a newly generated AI analysis.
    """

    logger.info(
        "Creating resume analysis for resume_id=%s",
        analysis.resume_id,
    )

    try:
        db_analysis = ResumeAnalysis(
            **analysis.model_dump(),
        )

        db.add(db_analysis)

        db.commit()

        db.refresh(db_analysis)

        logger.info(
            "Analysis %s stored successfully.",
            db_analysis.id,
        )

        return db_analysis

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to create analysis for resume_id=%s",
            analysis.resume_id,
        )

        raise


# ==========================================================
# READ
# ==========================================================


def get_analysis_by_id(
    db: Session,
    analysis_id: int,
) -> Optional[ResumeAnalysis]:
    """
    Return analysis by primary key.
    """

    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.id == analysis_id,
        )
        .first()
    )


def get_latest_analysis(
    db: Session,
    resume_id: int,
) -> Optional[ResumeAnalysis]:
    """
    Return latest cached analysis.
    """

    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.is_latest.is_(True),
        )
        .first()
    )


def get_analysis_history(
    db: Session,
    resume_id: int,
) -> list[ResumeAnalysis]:
    """
    Return every stored analysis for a resume.

    Latest version first.
    """

    return (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
        )
        .order_by(
            ResumeAnalysis.version.desc(),
        )
        .all()
    )


# ==========================================================
# VERSION HELPERS
# ==========================================================


def get_next_version(
    db: Session,
    resume_id: int,
) -> int:
    """
    Compute the next version number.
    """

    latest = get_latest_analysis(
        db=db,
        resume_id=resume_id,
    )

    if latest is None:
        return 1

    return latest.version + 1


def clear_latest_flag(
    db: Session,
    resume_id: int,
) -> None:
    """
    Marks every existing analysis as non-latest.
    """

    (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
            ResumeAnalysis.is_latest.is_(True),
        )
        .update(
            {
                ResumeAnalysis.is_latest: False,
            },
            synchronize_session=False,
        )
    )


# ==========================================================
# SAVE AI ANALYSIS
# ==========================================================


def save_ai_analysis(
    db: Session,
    *,
    resume_id: int,
    ai_response: ResumeAnalysisResponse,
    provider: str,
    model_name: str,
    model_version: str | None = None,
    prompt_version: str = "v1",
    processing_time_ms: float | None = None,
) -> ResumeAnalysis:
    """
    Persist an AI-generated resume analysis.

    Workflow
    --------
    1. Determine next version number.
    2. Clear previous latest flag.
    3. Store new analysis.
    4. Return persisted entity.
    """

    logger.info(
        "Saving AI analysis for resume_id=%s",
        resume_id,
    )

    try:
        version = get_next_version(
            db=db,
            resume_id=resume_id,
        )

        clear_latest_flag(
            db=db,
            resume_id=resume_id,
        )

        analysis = ResumeAnalysis(
            resume_id=resume_id,
            version=version,
            is_latest=True,
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            prompt_version=prompt_version,
            analysis_status=AnalysisStatus.COMPLETED,
            processing_time_ms=processing_time_ms,
            ats_score=ai_response.ats_score,
            career_domain=ai_response.career_domain,
            experience_level=ai_response.experience_level,
            summary=ai_response.summary,
            skills=ai_response.skills,
            missing_skills=ai_response.missing_skills,
            strengths=ai_response.strengths,
            weaknesses=ai_response.weaknesses,
            suggestions=ai_response.suggestions,
        )

        db.add(analysis)

        db.commit()

        db.refresh(analysis)

        logger.info(
            "Analysis version %s saved successfully for resume_id=%s",
            analysis.version,
            resume_id,
        )

        return analysis

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to save analysis for resume_id=%s",
            resume_id,
        )

        raise

# ==========================================================
# UPDATE
# ==========================================================


def update_analysis_status(
    db: Session,
    analysis: ResumeAnalysis,
    status: AnalysisStatus,
) -> ResumeAnalysis:
    """
    Update the processing status of an existing analysis.
    """

    try:
        analysis.analysis_status = status

        db.commit()

        db.refresh(analysis)

        logger.info(
            "Updated analysis_id=%s status to %s",
            analysis.id,
            status.value,
        )

        return analysis

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to update analysis status for analysis_id=%s",
            analysis.id,
        )

        raise

# ==========================================================
# CACHE
# ==========================================================


def cached_analysis_exists(
    db: Session,
    resume_id: int,
) -> bool:
    """
    Returns True if a cached latest analysis exists.
    """

    return (
        get_latest_analysis(
            db=db,
            resume_id=resume_id,
        )
        is not None
    )


def get_cached_analysis(
    db: Session,
    resume_id: int,
) -> ResumeAnalysis | None:
    """
    Returns the cached latest analysis.
    """

    return get_latest_analysis(
        db=db,
        resume_id=resume_id,
    )


# ==========================================================
# HISTORY
# ==========================================================


def get_analysis_summaries(
    db: Session,
    resume_id: int,
) -> list[ResumeAnalysisSummary]:
    """
    Returns lightweight analysis history for UI pages.
    """

    analyses = get_analysis_history(
        db=db,
        resume_id=resume_id,
    )

    return [
        ResumeAnalysisSummary.model_validate(
            analysis,
        )
        for analysis in analyses
    ]
# ==========================================================
# REGENERATION
# ==========================================================


def regenerate_analysis(
    db: Session,
    *,
    resume_id: int,
    ai_response: ResumeAnalysisResponse,
    provider: str,
    model_name: str,
    model_version: str | None = None,
    prompt_version: str = "v1",
    processing_time_ms: float | None = None,
) -> ResumeAnalysis:
    """
    Force creation of a brand-new analysis version.
    """

    logger.info(
        "Regenerating analysis for resume_id=%s",
        resume_id,
    )

    return save_ai_analysis(
        db=db,
        resume_id=resume_id,
        ai_response=ai_response,
        provider=provider,
        model_name=model_name,
        model_version=model_version,
        prompt_version=prompt_version,
        processing_time_ms=processing_time_ms,
    )

# ==========================================================
# LATEST VERSION HELPERS
# ==========================================================


def promote_latest_analysis(
    db: Session,
    resume_id: int,
) -> None:
    """
    Promote the highest remaining version to latest.

    Called after deleting the current latest analysis.
    """

    newest = (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
        )
        .order_by(
            ResumeAnalysis.version.desc(),
        )
        .first()
    )

    if newest is None:
        return

    newest.is_latest = True


# ==========================================================
# DELETE
# ==========================================================


def delete_resume_analyses(
    db: Session,
    resume_id: int,
) -> int:
    """
    Delete every analysis belonging to a resume.

    Returns
    -------
    int
        Number of deleted analyses.
    """

    analyses = get_analysis_history(
        db=db,
        resume_id=resume_id,
    )

    count = len(analyses)

    try:
        (
            db.query(ResumeAnalysis)
            .filter(
                ResumeAnalysis.resume_id == resume_id,
            )
            .delete(
                synchronize_session=False,
            )
        )

        db.commit()

        logger.info(
            "Deleted %s analyses for resume_id=%s",
            count,
            resume_id,
        )

        return count

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to delete analyses for resume_id=%s",
            resume_id,
        )

        raise


def delete_analysis(
    db: Session,
    analysis_id: int,
) -> bool:
    """
    Delete a single analysis.

    If the deleted analysis was the latest version,
    automatically promote the highest remaining version.
    """

    analysis = get_analysis_by_id(
        db=db,
        analysis_id=analysis_id,
    )

    if analysis is None:
        return False

    resume_id = analysis.resume_id
    was_latest = analysis.is_latest

    try:
        db.delete(analysis)

        db.flush()

        if was_latest:
            promote_latest_analysis(
                db=db,
                resume_id=resume_id,
            )

        db.commit()

        logger.info(
            "Deleted analysis %s",
            analysis_id,
        )

        return True

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to delete analysis_id=%s",
            analysis_id,
        )

        raise


# ==========================================================
# CACHE HELPERS
# ==========================================================


def should_use_cache(
    regenerate: bool,
    cached_exists: bool,
) -> bool:
    """
    Determine whether an existing cached analysis should be returned.

    Returns True only when:
    - a cached analysis exists, and
    - the caller did not request regeneration.
    """

    return cached_exists and not regenerate

# ==========================================================
# VERSION HELPERS
# ==========================================================


def latest_version_number(
    db: Session,
    resume_id: int,
) -> int:
    """
    Return latest stored version number.
    """

    latest = get_latest_analysis(
        db=db,
        resume_id=resume_id,
    )

    if latest is None:
        return 0

    return latest.version


# ==========================================================
# EXISTENCE HELPERS
# ==========================================================


def analysis_exists(
    db: Session,
    resume_id: int,
) -> bool:
    """
    Returns True when at least one analysis exists.
    """

    return (
        db.query(ResumeAnalysis.id)
        .filter(
            ResumeAnalysis.resume_id == resume_id,
        )
        .first()
        is not None
    )


# ==========================================================
# RESPONSE HELPERS
# ==========================================================

def to_response(
    analysis: ResumeAnalysis,
) -> ResumeAnalysisResponse:
    """
    Convert a SQLAlchemy ResumeAnalysis model into a
    ResumeAnalysisResponse schema.
    """

    return ResumeAnalysisResponse.model_validate(
        analysis,
    )


def latest_analysis_response(
    db: Session,
    resume_id: int,
) -> ResumeAnalysisResponse | None:
    """
    Return the latest analysis as a response schema.
    """

    analysis = get_latest_analysis(
        db=db,
        resume_id=resume_id,
    )

    if analysis is None:
        return None

    return to_response(
        analysis,
    )


# ==========================================================
# AI CONTEXT
# ==========================================================


def format_resume_context(
    analysis: ResumeAnalysisResponse | None,
) -> str | None:
    """
    Convert the latest resume analysis into a compact
    prompt context for the AI Career Mentor.

    Returns None when no analysis is available.
    """

    if analysis is None:
        return None

    sections: list[str] = [
        "Latest Resume Analysis",
        "",
        f"ATS Score: {analysis.ats_score}/100",
        f"Career Domain: {analysis.career_domain}",
        f"Experience Level: {analysis.experience_level}",
        "",
        "Professional Summary:",
        analysis.summary,
    ]

    if analysis.skills:
        sections.extend(
            [
                "",
                "Skills:",
                *[
                    f"- {skill}"
                    for skill in analysis.skills
                ],
            ]
        )

    if analysis.missing_skills:
        sections.extend(
            [
                "",
                "Missing Skills:",
                *[
                    f"- {skill}"
                    for skill in analysis.missing_skills
                ],
            ]
        )

    if analysis.strengths:
        sections.extend(
            [
                "",
                "Strengths:",
                *[
                    f"- {item}"
                    for item in analysis.strengths
                ],
            ]
        )

    if analysis.weaknesses:
        sections.extend(
            [
                "",
                "Weaknesses:",
                *[
                    f"- {item}"
                    for item in analysis.weaknesses
                ],
            ]
        )

    if analysis.suggestions:
        sections.extend(
            [
                "",
                "Recommendations:",
                *[
                    f"- {item}"
                    for item in analysis.suggestions
                ],
            ]
        )

    return "\n".join(sections)
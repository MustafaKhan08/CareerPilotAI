"""
PDF rendering for the Interview Preparation module.

All PDF layout logic lives exclusively in this module.

No business logic.
No database access.
No AI calls.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.platypus.flowables import KeepTogether


# ==========================================================
# Colour Palette
# ==========================================================

_BRAND_DARK = colors.HexColor("#0F172A")      # slate-900
_BRAND_ACCENT = colors.HexColor("#6366F1")    # indigo-500
_BRAND_LIGHT = colors.HexColor("#F8FAFC")     # slate-50
_TEXT_BODY = colors.HexColor("#1E293B")       # slate-800
_TEXT_MUTED = colors.HexColor("#64748B")      # slate-500
_DIVIDER = colors.HexColor("#E2E8F0")         # slate-200
_HIGHLIGHT_BG = colors.HexColor("#EEF2FF")    # indigo-50


# ==========================================================
# Style Definitions
# ==========================================================

_BASE = getSampleStyleSheet()


def _build_styles() -> dict[str, ParagraphStyle]:
    """
    Construct all paragraph styles used in the PDF.
    Returns a name→style mapping.
    """

    return {
        "brand": ParagraphStyle(
            "brand",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=_BRAND_ACCENT,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=13,
            textColor=_TEXT_MUTED,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "cover_label": ParagraphStyle(
            "cover_label",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=_TEXT_MUTED,
            alignment=TA_LEFT,
            spaceAfter=1,
        ),
        "cover_value": ParagraphStyle(
            "cover_value",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=11,
            textColor=_TEXT_BODY,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "score_value": ParagraphStyle(
            "score_value",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=_BRAND_ACCENT,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "section_heading": ParagraphStyle(
            "section_heading",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=_BRAND_DARK,
            alignment=TA_LEFT,
            spaceBefore=14,
            spaceAfter=4,
        ),
        "body_text": ParagraphStyle(
            "body_text",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=_TEXT_BODY,
            alignment=TA_LEFT,
            leading=15,
            spaceAfter=4,
        ),
        "bullet_item": ParagraphStyle(
            "bullet_item",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=_TEXT_BODY,
            alignment=TA_LEFT,
            leading=15,
            leftIndent=14,
            spaceAfter=2,
        ),
        "question_label": ParagraphStyle(
            "question_label",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=_BRAND_DARK,
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "question_text": ParagraphStyle(
            "question_text",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=_TEXT_BODY,
            alignment=TA_LEFT,
            leading=15,
            spaceAfter=6,
        ),
        "answer_label": ParagraphStyle(
            "answer_label",
            parent=_BASE["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=_TEXT_MUTED,
            alignment=TA_LEFT,
            spaceAfter=3,
        ),
        "answer_text": ParagraphStyle(
            "answer_text",
            parent=_BASE["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=_TEXT_BODY,
            alignment=TA_LEFT,
            leading=15,
            spaceAfter=4,
        ),
    }


# ==========================================================
# Private Helpers
# ==========================================================

def _divider() -> HRFlowable:
    """Return a full-width horizontal rule."""
    return HRFlowable(
        width="100%",
        thickness=0.5,
        color=_DIVIDER,
        spaceAfter=8,
        spaceBefore=8,
    )


def _accent_divider() -> HRFlowable:
    """Return a short accent-coloured rule used under headings."""
    return HRFlowable(
        width="30%",
        thickness=1.5,
        color=_BRAND_ACCENT,
        spaceAfter=6,
        spaceBefore=0,
    )


def _escape(text: str) -> str:
    """
    Escape characters that ReportLab's Paragraph renderer
    treats as markup so that raw user/AI text is safe to embed.
    """
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _format_date(dt: datetime | None) -> str:
    """Return a human-readable date string, or 'N/A' if None."""
    if dt is None:
        return "N/A"
    return dt.strftime("%d %B %Y")


def _bullet_paragraphs(
    items: list[str],
    style: ParagraphStyle,
) -> list[Paragraph]:
    """Convert a list of strings into bullet-prefixed Paragraphs."""
    return [
        Paragraph(f"• {_escape(item)}", style)
        for item in items
        if item
    ]


# ==========================================================
# Page 1 — Cover
# ==========================================================


def _build_cover_page(
    *,
    styles: dict[str, ParagraphStyle],
    title: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
    overall_score: float | None,
    career_readiness: str,
    completed_at: datetime | None,
) -> list[Any]:
    """
    Build the cover page flowables.

    Contains: brand name, report subtitle, and all
    session metadata fields listed in the spec.
    """

    story: list[Any] = []

    # --- Brand header ---
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("CareerPilotAI", styles["brand"]))
    story.append(
        Paragraph("Interview Assessment Report", styles["cover_subtitle"])
    )
    story.append(_divider())
    story.append(Spacer(1, 8 * mm))

    # --- Metadata rows ---
    def _row(label: str, value: str, score: bool = False) -> list[Any]:
        value_style = styles["score_value"] if score else styles["cover_value"]
        return [
            Paragraph(label.upper(), styles["cover_label"]),
            Paragraph(_escape(value), value_style),
        ]

    score_str = (
        f"{overall_score:.1f} / 10.0"
        if overall_score is not None
        else "N/A"
    )

    for para in _row("Interview Title", title):
        story.append(para)
    for para in _row("Target Role", target_role):
        story.append(para)
    for para in _row("Interview Type", interview_type.replace("_", " ").title()):
        story.append(para)
    for para in _row("Difficulty", difficulty.title()):
        story.append(para)
    for para in _row("Overall Score", score_str, score=True):
        story.append(para)
    for para in _row("Career Readiness", career_readiness):
        story.append(para)
    for para in _row("Completion Date", _format_date(completed_at)):
        story.append(para)

    story.append(PageBreak())
    return story


# ==========================================================
# Page 2 — Report Summary
# ==========================================================


def _build_report_page(
    *,
    styles: dict[str, ParagraphStyle],
    summary: str,
    strengths: list[str],
    weaknesses: list[str],
    recommendations: str,
    next_steps: list[str],
) -> list[Any]:
    """
    Build the report summary page flowables.

    Contains: Summary, Strengths, Weaknesses,
    Recommendations, and Next Steps.
    """

    story: list[Any] = []

    def _section(heading: str, content: list[Any]) -> list[Any]:
        return [
            Paragraph(heading, styles["section_heading"]),
            _accent_divider(),
            *content,
            Spacer(1, 4 * mm),
        ]

    # Summary
    story.extend(
        _section(
            "Summary",
            [Paragraph(_escape(summary), styles["body_text"])],
        )
    )

    # Strengths
    story.extend(
        _section(
            "Strengths",
            _bullet_paragraphs(strengths, styles["bullet_item"])
            or [Paragraph("None noted.", styles["body_text"])],
        )
    )

    # Weaknesses
    story.extend(
        _section(
            "Weaknesses",
            _bullet_paragraphs(weaknesses, styles["bullet_item"])
            or [Paragraph("None noted.", styles["body_text"])],
        )
    )

    # Recommendations
    story.extend(
        _section(
            "Recommendations",
            [Paragraph(_escape(recommendations), styles["body_text"])],
        )
    )

    # Next Steps
    story.extend(
        _section(
            "Next Steps",
            _bullet_paragraphs(next_steps, styles["bullet_item"])
            or [Paragraph("None noted.", styles["body_text"])],
        )
    )

    story.append(PageBreak())
    return story


# ==========================================================
# Remaining Pages — Q&A Transcript
# ==========================================================


def _build_qa_pages(
    *,
    styles: dict[str, ParagraphStyle],
    questions: list[dict[str, str | None]],
) -> list[Any]:
    """
    Build the Q&A transcript flowables.

    Each entry in `questions` must have:
        - order:  int   (1-based question number)
        - text:   str   (the question text)
        - answer: str | None

    A light divider separates each question block.
    Each block is wrapped in KeepTogether where possible
    to avoid orphaned question labels at page bottoms.
    """

    story: list[Any] = []

    for idx, q in enumerate(questions):
        block: list[Any] = []

        # Question label + text
        block.append(
            Paragraph(
                f"Question {q['order']}",
                styles["question_label"],
            )
        )
        block.append(
            Paragraph(
                _escape(q["text"] or ""),
                styles["question_text"],
            )
        )

        # Candidate answer label + text
        answer_text = q.get("answer") or "[No answer recorded]"
        block.append(
            Paragraph("Candidate Answer", styles["answer_label"])
        )
        block.append(
            Paragraph(
                _escape(answer_text),
                styles["answer_text"],
            )
        )

        # Separator between questions (not after the last one)
        if idx < len(questions) - 1:
            block.append(_divider())

        story.append(KeepTogether(block))

    return story


# ==========================================================
# Public API
# ==========================================================


def generate_report_pdf(
    *,
    title: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
    overall_score: float | None,
    career_readiness: str,
    completed_at: datetime | None,
    summary: str,
    strengths: list[str],
    weaknesses: list[str],
    recommendations: str,
    next_steps: list[str],
    questions: list[dict[str, str | None]],
) -> bytes:
    """
    Render the interview assessment report PDF in memory
    and return the raw bytes.

    Args:
        title:            Interview session title.
        target_role:      Target job role.
        interview_type:   Type of interview (hr, technical, etc.).
        difficulty:       Difficulty level.
        overall_score:    Float 0–10, or None if not available.
        career_readiness: Holistic readiness summary string.
        completed_at:     Session completion timestamp.
        summary:          AI-generated overall summary paragraph.
        strengths:        List of strength strings.
        weaknesses:       List of weakness strings.
        recommendations:  AI-generated recommendations paragraph.
        next_steps:       List of next-step action strings.
        questions:        Ordered list of dicts, each with keys:
                            - order (int)
                            - text  (str)
                            - answer (str | None)

    Returns:
        PDF file contents as bytes.
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"CareerPilotAI — {title}",
        author="CareerPilotAI",
        subject="Interview Assessment Report",
    )

    styles = _build_styles()
    story: list[Any] = []

    # Page 1 — Cover
    story.extend(
        _build_cover_page(
            styles=styles,
            title=title,
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            overall_score=overall_score,
            career_readiness=career_readiness,
            completed_at=completed_at,
        )
    )

    # Page 2 — Report summary
    story.extend(
        _build_report_page(
            styles=styles,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            next_steps=next_steps,
        )
    )

    # Remaining pages — Q&A transcript
    story.extend(
        _build_qa_pages(
            styles=styles,
            questions=questions,
        )
    )

    doc.build(story)
    return buffer.getvalue()

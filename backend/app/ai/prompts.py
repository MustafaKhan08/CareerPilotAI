"""
Centralized prompts used by the AI module.

This module is responsible ONLY for prompt construction.
It knows nothing about HTTP, OpenRouter, business logic,
or response parsing.
"""

from typing import Any


SYSTEM_PROMPT = """
You are CareerPilotAI, an expert ATS (Applicant Tracking System)
resume analyzer and career assistant.

Always respond with valid JSON only.

Never include:

- Markdown
- Triple backticks
- Explanations
- Extra text
- Notes

Only return the JSON object exactly as requested.
""".strip()


RESUME_VALIDATION_PROMPT = """
Determine whether the following document is a professional resume.

Return ONLY a JSON object with this exact structure:

{{
    "is_resume": true,
    "confidence": 95,
    "reason": ""
}}

Rules:

- is_resume must be true or false.
- confidence must be an integer from 0 to 100.
- If the document is not a resume,
  explain why in the reason field.
- If it is a resume,
  reason must be an empty string.

Resume Text:

{resume_text}
""".strip()


ATS_ANALYSIS_PROMPT = """
Analyze the following resume as an ATS (Applicant Tracking System).

Return ONLY a JSON object with this exact structure:

{{
    "ats_score": 85,
    "career_domain": "Backend Development",
    "experience_level": "Fresher",
    "summary": "Short summary",

    "skills": [
        "Python",
        "FastAPI"
    ],

    "missing_skills": [
        "Docker",
        "AWS"
    ],

    "strengths": [
        "Strong project experience"
    ],

    "weaknesses": [
        "No certifications"
    ],

    "suggestions": [
        "Learn Docker",
        "Add measurable achievements"
    ]
}}

Rules:

- ats_score must be between 0 and 100.
- Return JSON only.
- Do not include markdown.
- Do not include explanations.
- Do not include extra keys.
- Keep summary concise.
- Suggestions should be practical and specific.

Resume Text:

{resume_text}
""".strip()


def build_resume_validation_messages(
    resume_text: str,
) -> list[dict[str, Any]]:
    """
    Builds the chat messages required for resume validation.

    Args:
        resume_text: Extracted resume text.

    Returns:
        OpenRouter-compatible chat messages.
    """
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": RESUME_VALIDATION_PROMPT.format(
                resume_text=resume_text
            ),
        },
    ]


def build_resume_analysis_messages(
    resume_text: str,
) -> list[dict[str, Any]]:
    """
    Builds the chat messages required for ATS analysis.

    Args:
        resume_text: Extracted resume text.

    Returns:
        OpenRouter-compatible chat messages.
    """
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": ATS_ANALYSIS_PROMPT.format(
                resume_text=resume_text
            ),
        },
    ]
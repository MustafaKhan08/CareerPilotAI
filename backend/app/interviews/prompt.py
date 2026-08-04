"""
Prompt builders for the Interview Preparation module.

This module is responsible only for constructing prompts
for the AI interview system.

No business logic should exist here.
"""

from __future__ import annotations


INTERVIEW_SYSTEM_PROMPT = """
You are an expert technical interviewer.

Your job is to generate professional interview questions.

Rules:

- Generate ONLY ONE interview question.
- Personalize the question using the candidate's resume analysis.
- Match the requested interview type.
- Match the requested difficulty.
- Do NOT ask multiple questions.
- Do NOT explain the question.
- Do NOT include markdown.
- Do NOT include code fences.
- Return ONLY valid JSON.

The JSON format MUST be:

{
    "question": "...",
    "category": "...",
    "difficulty": "...",
    "expected_focus": [
        "...",
        "..."
    ]
}
""".strip()


def build_question_prompt(
    *,
    resume_context: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
) -> list[dict[str, str]]:
    """
    Build the prompt used to generate
    the first interview question.
    """

    user_prompt = f"""
Target Role:
{target_role}

Interview Type:
{interview_type}

Difficulty:
{difficulty}

Candidate Resume Analysis:

{resume_context}

Generate the first interview question.
""".strip()

    return [
        {
            "role": "system",
            "content": INTERVIEW_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
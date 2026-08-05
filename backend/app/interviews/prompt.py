"""
Prompt builders for the Interview Preparation module.

This module is responsible only for constructing prompts
for the AI interview system.

No business logic should exist here.
"""

from __future__ import annotations


# ==========================================================
# QUESTION GENERATION
# ==========================================================


INTERVIEW_SYSTEM_PROMPT = """
You are an expert technical interviewer with extensive industry experience.

Your task is to generate exactly ONE professional interview question.

Rules:

- Generate ONLY ONE interview question.
- Personalize the question using the candidate's resume analysis.
- Match the requested interview type.
- Match the requested difficulty.
- The question must be relevant to the target role.
- Focus on the candidate's actual experience and skills.
- Do NOT ask the candidate to repeat information already present in the resume.
- Do NOT generate generic "Tell me about yourself" style questions unless the interview type explicitly requires it.
- Do NOT ask multiple questions.
- Do NOT explain the question.
- Do NOT include markdown.
- Do NOT include code fences.
- Return ONLY valid JSON.

If previous interview questions are provided, generate a NEW question that is not semantically similar to any previous question.

Return exactly this JSON:

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
    previous_questions: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Build the prompt used to generate
    the next interview question.
    """

    prev_q_text = ""
    if previous_questions:
        prev_qs = "\n".join(f"- {q}" for q in previous_questions)
        prev_q_text = f"\nPrevious Questions Asked:\n{prev_qs}\n"

    user_prompt = f"""
Target Role:
{target_role}

Interview Type:
{interview_type}

Difficulty:
{difficulty}

Candidate Resume Analysis:

{resume_context}
{prev_q_text}
Generate the next interview question.
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


# ==========================================================
# ANSWER EVALUATION
# ==========================================================


EVALUATION_SYSTEM_PROMPT = """
You are an expert technical interviewer evaluating a candidate's answer.

Your evaluation must be objective, fair, and based ONLY on the answer provided.

Rules:

- Evaluate ONLY the submitted answer.
- Use the candidate's resume context to personalize the evaluation.
- Evaluate according to the candidate's experience level.
- Do NOT expect senior-level knowledge from junior candidates.
- Do NOT hallucinate information that is not present in the answer.
- If important concepts are missing, explicitly state they were not mentioned.
- Do NOT ask follow-up questions.
- Do NOT include markdown.
- Do NOT include code fences.
- Return ONLY valid JSON.

Scoring Guide:

10 = Exceptional interview answer
9 = Excellent
8 = Strong
7 = Good
6 = Acceptable
5 = Average
4 = Weak
3 = Poor
2 = Very Poor
1 = Minimal understanding
0 = Incorrect or empty answer

Return exactly this JSON:

{
    "score": <float between 0.0 and 10.0>,
    "strengths": ["...", "..."],
    "weaknesses": ["..."],
    "communication": "...",
    "confidence": "...",
    "technical_accuracy": "...",
    "ideal_answer": "...",
    "improvements": ["...", "..."]
}

Requirements:

- "score" must be a numeric value.
- "strengths", "weaknesses", and "improvements" must be arrays of strings.
- Every field is required.
""".strip()


def build_evaluation_prompt(
    *,
    resume_context: str,
    question: str,
    candidate_answer: str,
) -> list[dict[str, str]]:
    """
    Build the prompt used to evaluate a candidate's answer.
    """

    user_prompt = f"""
Candidate Resume Context:

{resume_context}

Interview Question:
{question}

Candidate Answer:
{candidate_answer}

Evaluate the candidate's answer objectively.

Return ONLY valid JSON.
""".strip()

    return [
        {
            "role": "system",
            "content": EVALUATION_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


# ==========================================================
# FINAL REPORT GENERATION
# ==========================================================


REPORT_SYSTEM_PROMPT = """
You are a senior technical interviewer writing a final performance report
for a candidate who has just completed a full interview.

Your report must be thorough, fair, and actionable.

Rules:

- Base your report ONLY on the questions, answers, and evaluations provided.
- Do NOT invent information that is not present in the transcript.
- Use the candidate's resume context to personalise the report.
- Highlight genuine patterns across all answers, not just individual responses.
- Be constructive — weaknesses must come with actionable recommendations.
- Do NOT simply average the individual question scores.
- Assess the candidate's overall interview performance holistically.
- Do NOT include markdown.
- Do NOT include code fences.
- Return ONLY valid JSON.

Scoring Guide for overall_score:

9.0–10.0 = Exceptional candidate, strongly recommend
7.0–8.9  = Strong candidate, recommend with minor reservations
5.0–6.9  = Average candidate, recommend with conditions
3.0–4.9  = Below-average, significant gaps identified
0.0–2.9  = Not recommended at this time

Return exactly this JSON:

{
    "overall_score": <float between 0.0 and 10.0>,
    "summary": "...",
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "recommendations": "...",
    "career_readiness": "...",
    "next_steps": ["...", "..."]
}

Requirements:

- "overall_score" must be a numeric value between 0.0 and 10.0.
- "strengths", "weaknesses", and "next_steps" must be arrays of strings.
- "summary", "recommendations", and "career_readiness" must be non-empty strings.
- Every field is required.
""".strip()


def build_report_prompt(
    *,
    resume_context: str,
    target_role: str,
    interview_type: str,
    difficulty: str,
    transcript: str,
) -> list[dict[str, str]]:
    """
    Build the prompt used to generate the final interview report.

    Args:
        resume_context:
            Formatted resume analysis text.
        target_role:
            The role the candidate was interviewed for.
        interview_type:
            The type of interview (technical, hr, behavioral, etc.).
        difficulty:
            The difficulty level of the interview.
        transcript:
            A structured, human-readable string containing all
            questions, candidate answers, and per-question evaluations
            formatted by the service layer.

    Returns:
        OpenAI-compatible chat messages list.
    """

    user_prompt = f"""
Candidate Resume Context:

{resume_context}

Interview Details:

Target Role: {target_role}
Interview Type: {interview_type}
Difficulty: {difficulty}

Full Interview Transcript:

{transcript}

Generate the final interview report.

Return ONLY valid JSON.
""".strip()

    return [
        {
            "role": "system",
            "content": REPORT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
"""Prompt construction utilities for the AI Career Mentor."""

from app.chat.prompts import CAREER_MENTOR_SYSTEM_PROMPT


def build_prompt(
    user_message: str,
    history: list[dict[str, str]],
    resume_context: str | None = None,
) -> list[dict[str, str]]:
    """
    Build OpenAI-compatible messages for the AI Career Mentor.

    Args:
        user_message:
            The current user message.

        history:
            Previously stored conversation messages.

        resume_context:
            Optional resume context.

    Returns:
        Ordered OpenAI-compatible chat messages.

    Raises:
        ValueError:
            If the input is invalid.
    """

    _validate_input(
        user_message=user_message,
        history=history,
    )

    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": CAREER_MENTOR_SYSTEM_PROMPT,
        }
    ]

    if resume_context and resume_context.strip():
        messages.append(
            _build_resume_context_message(
                resume_context=resume_context,
            )
        )

    messages.extend(history.copy())

    messages.append(
        {
            "role": "user",
            "content": user_message.strip(),
        }
    )

    return messages


def _build_resume_context_message(
    resume_context: str,
) -> dict[str, str]:
    """
    Build the system message containing
    the user's resume context.
    """

    return {
        "role": "system",
        "content": (
            "Resume Context:\n"
            f"{resume_context.strip()}"
        ),
    }


def _validate_input(
    user_message: str,
    history: list[dict[str, str]],
) -> None:
    """
    Validate prompt builder inputs.
    """

    if (
        not isinstance(user_message, str)
        or not user_message.strip()
    ):
        raise ValueError(
            "User message must be a non-empty string."
        )

    if not isinstance(history, list):
        raise ValueError(
            "History must be a list."
        )
"""Utility functions for the AI Career Mentor."""

from __future__ import annotations

from app.chat.model import ChatMessage


def format_chat_history(
    messages: list[ChatMessage],
) -> list[dict[str, str]]:
    """
    Convert stored chat messages into the format
    expected by the LLM.

    Example:

    [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hi!"
        }
    ]
    """

    return [
        {
            "role": message.role.value,
            "content": message.message,
        }
        for message in messages
    ]


def build_resume_context(
    resume_analysis: str | None,
) -> str:
    """
    Convert the latest resume analysis into a
    prompt section for the LLM.

    If no analysis exists,
    return an empty string.
    """

    if not resume_analysis:
        return ""

    return (
        "Resume Analysis:\n"
        f"{resume_analysis.strip()}\n"
    )


def truncate_chat_history(
    messages: list[dict[str, str]],
    max_messages: int = 20,
) -> list[dict[str, str]]:
    """
    Limit the amount of conversation history
    sent to the LLM.

    Only the most recent messages are retained.
    """

    if len(messages) <= max_messages:
        return messages

    return messages[-max_messages:]


def clean_ai_response(
    response: str,
) -> str:
    """
    Normalize the LLM response before returning
    it to the frontend.
    """

    return response.strip()
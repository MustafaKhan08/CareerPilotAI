"""Service layer for the AI Career Mentor."""

import logging

from sqlalchemy.orm import Session

from app.chat.ai_client import (
    ChatClientError,
    generate_chat_response,
)
from app.chat.memory import (
    clear_chat_history as clear_chat_history_memory,
)
from app.chat.memory import (
    load_chat_history,
    load_prompt_history,
    save_assistant_message,
    save_user_message,
)
from app.chat.prompt_builder import build_prompt
from app.analyses.service import (
    format_resume_context,
    latest_analysis_response,
)
from app.resumes.service import get_latest_resume

from app.chat.schema import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)
from app.users.model import User

logger = logging.getLogger(__name__)


FALLBACK_RESPONSE = (
    "I'm sorry, but I'm currently unable to "
    "generate a response. Please try again "
    "in a few moments."
)

async def send_message(
    db: Session,
    current_user: User,
    chat_request: ChatRequest,
) -> ChatResponse:
    """
    Process a user message through the AI Career Mentor.

    Workflow:

    1. Save the user's message.
    2. Load previous conversation history.
    3. Load the latest resume analysis (if available).
    4. Build the OpenRouter prompt.
    5. Generate an AI response.
    6. Save the AI response.
    7. Return the response.
    """

    logger.info(
        "Received AI Career Mentor request from user %s.",
        current_user.id,
    )

    save_user_message(
        db=db,
        current_user=current_user,
        message=chat_request.message,
    )

    history = load_prompt_history(
        db=db,
        current_user=current_user,
    )

    resume = get_latest_resume(
        db=db,
        user_id=current_user.id,
    )

    logger.info(
        "Latest resume: %s",
        resume.id if resume else None,
    )

    resume_context = None

    if resume is not None:
        analysis = latest_analysis_response(
            db=db,
            resume_id=resume.id,
        )

        print("\n" + "=" * 80)
        print("LATEST RESUME")
        print(resume)
        print("=" * 80 + "\n")

        resume_context = format_resume_context(
            analysis,
        )

        logger.info(
            "Resume context:\n%s",
            resume_context,
        )

    prompt = build_prompt(
        user_message=chat_request.message,
        history=history,
        resume_context=resume_context,
    )

    logger.info(
        "Prompt successfully built."
    )

    try:
        assistant_message = await generate_chat_response(
            messages=prompt,
        )

        logger.info(
            "Received response from OpenRouter."
        )

    except ChatClientError as exc:
        logger.exception(
            "OpenRouter request failed: %s",
            exc,
        )

        assistant_message = FALLBACK_RESPONSE

    save_assistant_message(
        db=db,
        current_user=current_user,
        message=assistant_message,
    )

    logger.info(
        "Assistant response saved."
    )

    return ChatResponse(
        role="assistant",
        message=assistant_message,
    )

def get_chat_history(
    db: Session,
    current_user: User,
) -> ChatHistoryResponse:
    """
    Return the authenticated user's
    complete chat history.
    """

    logger.info(
        "Loading chat history for user %s.",
        current_user.id,
    )

    messages = load_chat_history(
        db=db,
        current_user=current_user,
    )

    logger.info(
        "Loaded %d chat messages.",
        len(messages),
    )

    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse.model_validate(message)
            for message in messages
        ]
    )


def clear_chat_history(
    db: Session,
    current_user: User,
) -> dict[str, str]:
    """
    Delete every stored message for
    the authenticated user.
    """

    logger.info(
        "Clearing chat history for user %s.",
        current_user.id,
    )

    clear_chat_history_memory(
        db=db,
        current_user=current_user,
    )

    logger.info(
        "Chat history cleared."
    )

    return {
        "message": "Chat history cleared successfully."
    }
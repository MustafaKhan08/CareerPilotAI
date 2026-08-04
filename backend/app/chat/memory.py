"""Memory management utilities for the AI Career Mentor."""

from sqlalchemy.orm import Session

from app.chat.model import ChatMessage
from app.chat.model import ChatRole
from app.users.model import User


def save_user_message(
    db: Session,
    current_user: User,
    message: str,
) -> ChatMessage:
    """
    Persist a user's message.

    Returns the newly created ChatMessage.
    """

    chat_message = ChatMessage(
        user_id=current_user.id,
        role=ChatRole.USER,
        message=message,
    )

    db.add(chat_message)

    try:
        db.commit()
        db.refresh(chat_message)

    except Exception:
        db.rollback()
        raise

    return chat_message


def save_assistant_message(
    db: Session,
    current_user: User,
    message: str,
) -> ChatMessage:
    """
    Persist an assistant response.

    Returns the newly created ChatMessage.
    """

    chat_message = ChatMessage(
        user_id=current_user.id,
        role=ChatRole.ASSISTANT,
        message=message,
    )

    db.add(chat_message)

    try:
        db.commit()
        db.refresh(chat_message)

    except Exception:
        db.rollback()
        raise

    return chat_message


def load_chat_history(
    db: Session,
    current_user: User,
) -> list[ChatMessage]:
    """
    Return every stored message for the authenticated user.

    Messages are always returned in chronological order.
    """

    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.user_id == current_user.id,
        )
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.id.asc(),
        )
        .all()
    )


def clear_chat_history(
    db: Session,
    current_user: User,
) -> None:
    """
    Delete every stored message belonging
    to the authenticated user.
    """

    try:
        (
            db.query(ChatMessage)
            .filter(
                ChatMessage.user_id == current_user.id,
            )
            .delete(
                synchronize_session=False,
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise


def load_prompt_history(
    db: Session,
    current_user: User,
) -> list[dict[str, str]]:
    """
    Load the authenticated user's chat history
    in OpenAI-compatible message format.

    Returns:
        [
            {
                "role": "user",
                "content": "..."
            },
            {
                "role": "assistant",
                "content": "..."
            },
        ]
    """

    messages = load_chat_history(
        db=db,
        current_user=current_user,
    )

    return [
        {
            "role": message.role.value,
            "content": message.message,
        }
        for message in messages
    ]
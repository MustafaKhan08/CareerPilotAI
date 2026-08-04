"""HTTP endpoints for the AI Career Mentor."""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.chat.schema import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
)
from app.chat.service import (
    clear_chat_history,
    get_chat_history,
    send_message,
)
from app.db.database import get_db
from app.users.model import User

router = APIRouter(
    prefix="/chat",
    tags=["AI Career Mentor"],
)


@router.post(
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def send_chat_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a message to the AI Career Mentor.
    """

    return await send_message(
        db=db,
        current_user=current_user,
        chat_request=chat_request,
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def read_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    """
    Return the authenticated user's
    persistent chat history.
    """

    return get_chat_history(
        db=db,
        current_user=current_user,
    )


@router.delete(
    "/history",
    status_code=status.HTTP_200_OK,
)
def remove_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Delete every stored message
    for the authenticated user.
    """

    return clear_chat_history(
        db=db,
        current_user=current_user,
    )
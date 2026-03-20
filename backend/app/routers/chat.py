import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ChatMessage, Player, Report
from app.schemas import ChatRequest, ChatResponse
from app.services.openai_chat import chat_with_coach

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat with the AI chess coach about your analysis."""
    username = request.username.lower().strip()

    # Load player
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    # Load most recent report
    result = await db.execute(
        select(Report)
        .where(Report.player_id == player.id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()

    if not report or not report.report_data:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No analysis report found for '{username}'. "
                "Please run an analysis first."
            ),
        )

    # Load chat history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.player_id == player.id)
        .order_by(ChatMessage.created_at.asc())
    )
    history_objs = result.scalars().all()
    chat_history = [
        {"role": m.role, "content": m.content}
        for m in history_objs[-settings.CHAT_HISTORY_LIMIT:]
    ]

    # Store user message
    user_msg = ChatMessage(
        player_id=player.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Get AI response
    response_text = await chat_with_coach(
        username=username,
        message=request.message,
        report_data=report.report_data,
        chat_history=chat_history,
    )

    # Store assistant message
    assistant_msg = ChatMessage(
        player_id=player.id,
        role="assistant",
        content=response_text,
    )
    db.add(assistant_msg)

    return ChatResponse(response=response_text)


@router.delete("/chat/{username}")
async def clear_chat(username: str, db: AsyncSession = Depends(get_db)):
    """Clear chat history for a player."""
    username = username.lower().strip()

    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    await db.execute(
        delete(ChatMessage).where(ChatMessage.player_id == player.id)
    )

    return {"status": "cleared", "username": username}

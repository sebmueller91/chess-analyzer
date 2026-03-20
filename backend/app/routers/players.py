import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Player
from app.routers.analysis import _run_analysis
from app.schemas import AnalyzeResponse, PlayerResponse, PlayersListResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["players"])


@router.get("/players", response_model=PlayersListResponse)
async def list_players(db: AsyncSession = Depends(get_db)):
    """List all analyzed players."""
    result = await db.execute(select(Player).order_by(Player.created_at.desc()))
    players = result.scalars().all()

    return PlayersListResponse(
        players=[
            PlayerResponse(
                username=p.username,
                last_analyzed_at=p.last_analyzed_at,
                games_analyzed=p.games_analyzed or 0,
                time_control=p.time_control,
                status=p.status or "idle",
                error_message=p.error_message,
            )
            for p in players
        ]
    )


@router.delete("/players/{username}")
async def delete_player(username: str, db: AsyncSession = Depends(get_db)):
    """Delete a player and all associated data."""
    username = username.lower().strip()
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    await db.delete(player)
    return {"status": "deleted", "username": username}


@router.post("/players/{username}/reanalyze", response_model=AnalyzeResponse)
async def reanalyze_player(
    username: str,
    background_tasks: BackgroundTasks,
    time_control: str = "all",
    game_count: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Delete existing data and trigger fresh analysis."""
    username = username.lower().strip()
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    if player.status == "analyzing":
        raise HTTPException(
            status_code=409,
            detail=f"Analysis already in progress for {username}",
        )

    # Delete associated data (cascade will handle games, analysis, reports, chat)
    # Recreate the player record
    await db.delete(player)
    await db.flush()

    new_player = Player(username=username)
    db.add(new_player)
    await db.flush()

    new_player.status = "analyzing"

    background_tasks.add_task(_run_analysis, username, time_control, game_count)

    return AnalyzeResponse(status="analyzing", username=username)

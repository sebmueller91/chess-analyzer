import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Player, Report
from app.schemas import ReportResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["reports"])


@router.get("/reports/{username}", response_model=ReportResponse)
async def get_report(username: str, db: AsyncSession = Depends(get_db)):
    """Return the full analysis report for a player."""
    username = username.lower().strip()

    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    if player.status != "complete":
        raise HTTPException(
            status_code=404,
            detail=f"No completed analysis for '{username}'. Status: {player.status}",
        )

    # Get the most recent report
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
            detail=f"Report not found for '{username}'",
        )

    report_data = report.report_data
    report_data["coaching_summary"] = report.coaching_summary

    return ReportResponse(**report_data)

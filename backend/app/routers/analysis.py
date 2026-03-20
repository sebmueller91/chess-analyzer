import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_db
from app.models import AnalysisResult, Game, Player, Report
from app.schemas import AnalyzeRequest, AnalyzeResponse, StatusResponse
from app.services.chess_com import PlayerNotFoundError, fetch_player_games
from app.services.openai_summary import generate_coaching_summary
from app.services.pgn_parser import parse_game
from app.services.stockfish import StockfishAnalyzer
from app.services.weakness import generate_report

logger = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])

# Module-level progress tracking (single-process)
analysis_progress: dict[str, dict[str, int]] = {}


async def _run_analysis(
    username: str,
    time_control: str,
    game_count: int,
) -> None:
    """Background task: full analysis pipeline."""
    analysis_progress[username] = {"games_fetched": 0, "games_analyzed": 0}

    async with async_session() as db:
        try:
            # Set player status
            result = await db.execute(
                select(Player).where(Player.username == username)
            )
            player = result.scalar_one_or_none()
            if not player:
                logger.error("Player %s not found in DB for analysis", username)
                return

            player.status = "analyzing"
            player.error_message = None
            await db.commit()

            # 1. Fetch games from Chess.com
            logger.info("Fetching games for %s", username)
            raw_games = await fetch_player_games(username, time_control, game_count)
            analysis_progress[username]["games_fetched"] = len(raw_games)

            if not raw_games:
                player.status = "complete"
                player.games_analyzed = 0
                player.last_analyzed_at = datetime.now(timezone.utc)
                await db.commit()
                return

            # 2. Parse and store games
            logger.info("Parsing %d games for %s", len(raw_games), username)
            stored_games: list[Game] = []
            parsed_game_data: list[dict[str, Any]] = []

            for raw in raw_games:
                parsed = parse_game(raw, username)
                parsed_game_data.append(parsed)

                # Check for duplicate
                existing = await db.execute(
                    select(Game).where(Game.chess_com_id == parsed["chess_com_id"])
                )
                if existing.scalar_one_or_none():
                    continue

                game_obj = Game(player_id=player.id, **parsed)
                db.add(game_obj)
                stored_games.append(game_obj)

            await db.commit()

            # Reload games from DB to get IDs
            result = await db.execute(
                select(Game).where(Game.player_id == player.id)
            )
            all_player_games = result.scalars().all()

            # 3. Run Stockfish analysis
            logger.info("Running Stockfish analysis on %d games", len(all_player_games))
            analysis_results_data: list[dict[str, Any]] = []

            try:
                with StockfishAnalyzer() as analyzer:
                    for i, game_obj in enumerate(all_player_games):
                        # Skip if already analyzed
                        existing_ar = await db.execute(
                            select(AnalysisResult).where(
                                AnalysisResult.game_id == game_obj.id
                            )
                        )
                        if existing_ar.scalar_one_or_none():
                            analysis_progress[username]["games_analyzed"] = i + 1
                            continue

                        try:
                            ar_data = analyzer.analyze_game(
                                game_obj.pgn, game_obj.player_color
                            )
                        except Exception as e:
                            logger.warning(
                                "Stockfish failed for game %s: %s",
                                game_obj.chess_com_id,
                                e,
                            )
                            ar_data = {
                                "mistakes": [],
                                "opening_accuracy": 0.0,
                                "middlegame_accuracy": 0.0,
                                "endgame_accuracy": 0.0,
                                "total_blunders": 0,
                                "total_mistakes": 0,
                                "total_inaccuracies": 0,
                            }

                        ar_obj = AnalysisResult(game_id=game_obj.id, **ar_data)
                        db.add(ar_obj)
                        analysis_results_data.append(ar_data)
                        analysis_progress[username]["games_analyzed"] = i + 1

                        # Commit periodically
                        if (i + 1) % 5 == 0:
                            await db.commit()

                await db.commit()
            except FileNotFoundError:
                logger.error(
                    "Stockfish not found. Skipping engine analysis. "
                    "Install stockfish or set STOCKFISH_PATH."
                )
                # Continue without engine analysis — create empty results
                for game_obj in all_player_games:
                    existing_ar = await db.execute(
                        select(AnalysisResult).where(
                            AnalysisResult.game_id == game_obj.id
                        )
                    )
                    if not existing_ar.scalar_one_or_none():
                        ar_obj = AnalysisResult(
                            game_id=game_obj.id,
                            mistakes=[],
                            opening_accuracy=0.0,
                            middlegame_accuracy=0.0,
                            endgame_accuracy=0.0,
                            total_blunders=0,
                            total_mistakes=0,
                            total_inaccuracies=0,
                        )
                        db.add(ar_obj)
                await db.commit()

            # Reload all analysis results
            game_dicts: list[dict[str, Any]] = []
            ar_dicts: list[dict[str, Any]] = []

            for game_obj in all_player_games:
                game_dicts.append({
                    "result": game_obj.result,
                    "player_color": game_obj.player_color,
                    "opening_name": game_obj.opening_name,
                    "eco_code": game_obj.eco_code,
                    "opponent": game_obj.opponent,
                    "date_played": game_obj.date_played,
                })
                ar_result = await db.execute(
                    select(AnalysisResult).where(
                        AnalysisResult.game_id == game_obj.id
                    )
                )
                ar = ar_result.scalar_one_or_none()
                if ar:
                    ar_dicts.append({
                        "mistakes": ar.mistakes or [],
                        "opening_accuracy": ar.opening_accuracy or 0.0,
                        "middlegame_accuracy": ar.middlegame_accuracy or 0.0,
                        "endgame_accuracy": ar.endgame_accuracy or 0.0,
                        "total_blunders": ar.total_blunders or 0,
                        "total_mistakes": ar.total_mistakes or 0,
                        "total_inaccuracies": ar.total_inaccuracies or 0,
                    })

            # 4. Generate weakness report
            logger.info("Generating report for %s", username)
            report_data = generate_report(username, game_dicts, ar_dicts)

            # 5. Generate coaching summary
            logger.info("Generating coaching summary for %s", username)
            coaching_summary = await generate_coaching_summary(report_data, username)

            # 6. Store report
            report_obj = Report(
                player_id=player.id,
                report_data=report_data,
                coaching_summary=coaching_summary,
            )
            db.add(report_obj)

            # 7. Update player
            player.status = "complete"
            player.games_analyzed = len(all_player_games)
            player.time_control = time_control
            player.last_analyzed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info("Analysis complete for %s", username)

        except PlayerNotFoundError as e:
            logger.error("Player not found: %s", e)
            result = await db.execute(
                select(Player).where(Player.username == username)
            )
            player = result.scalar_one_or_none()
            if player:
                player.status = "error"
                player.error_message = str(e)
                await db.commit()

        except Exception as e:
            logger.exception("Analysis failed for %s: %s", username, e)
            try:
                result = await db.execute(
                    select(Player).where(Player.username == username)
                )
                player = result.scalar_one_or_none()
                if player:
                    player.status = "error"
                    player.error_message = f"Analysis failed: {str(e)[:200]}"
                    await db.commit()
            except Exception:
                logger.exception("Failed to update error status for %s", username)

        finally:
            analysis_progress.pop(username, None)


@router.post("/analyze", response_model=AnalyzeResponse)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start game analysis for a Chess.com player."""
    username = request.username.lower().strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    # Create or get player
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if player and player.status == "analyzing":
        raise HTTPException(
            status_code=409,
            detail=f"Analysis already in progress for {username}",
        )

    if not player:
        player = Player(username=username)
        db.add(player)
        await db.flush()

    player.status = "analyzing"
    player.error_message = None

    background_tasks.add_task(
        _run_analysis,
        username,
        request.time_control,
        request.game_count,
    )

    return AnalyzeResponse(status="analyzing", username=username)


@router.get("/status/{username}", response_model=StatusResponse)
async def get_status(username: str, db: AsyncSession = Depends(get_db)):
    """Get the analysis status for a player."""
    username = username.lower().strip()
    result = await db.execute(select(Player).where(Player.username == username))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{username}' not found")

    progress = analysis_progress.get(username, {
        "games_fetched": player.games_analyzed,
        "games_analyzed": player.games_analyzed,
    })

    return StatusResponse(
        username=player.username,
        status=player.status or "idle",
        progress=progress,
    )

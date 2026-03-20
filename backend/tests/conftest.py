import os
import tempfile
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Base

# Use an in-memory SQLite for tests
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "test_chess_analyzer.db")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_client():
    """Create a test client with mocked database."""
    from app.database import get_db
    from app.main import app

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.fixture
def sample_chess_com_game() -> dict[str, Any]:
    """A sample Chess.com API game object."""
    return {
        "url": "https://www.chess.com/game/live/12345",
        "pgn": (
            '[Event "Live Chess"]\n'
            '[Site "Chess.com"]\n'
            '[Date "2024.01.15"]\n'
            '[White "testplayer"]\n'
            '[Black "opponent1"]\n'
            '[Result "1-0"]\n'
            '[ECO "C50"]\n'
            '[ECOUrl "https://www.chess.com/openings/Italian-Game"]\n'
            '[TimeControl "600"]\n'
            "\n"
            "1. e4 e5 2. Nf3 Nc6 3. Bc4 Nf6 4. d3 Be7 5. O-O O-O "
            "6. Re1 d6 7. c3 Bg4 8. h3 Bh5 9. Nbd2 Nd7 10. Nf1 Nc5 1-0\n"
        ),
        "time_control": "600",
        "time_class": "rapid",
        "rated": True,
        "white": {"username": "testplayer", "rating": 1500, "result": "win"},
        "black": {"username": "opponent1", "rating": 1400, "result": "checkmated"},
        "end_time": 1705315200,
    }


@pytest.fixture
def sample_chess_com_game_black() -> dict[str, Any]:
    """A sample game where testplayer plays black."""
    return {
        "url": "https://www.chess.com/game/live/67890",
        "pgn": (
            '[Event "Live Chess"]\n'
            '[Site "Chess.com"]\n'
            '[Date "2024.01.16"]\n'
            '[White "opponent2"]\n'
            '[Black "testplayer"]\n'
            '[Result "0-1"]\n'
            '[ECO "B20"]\n'
            '[ECOUrl "https://www.chess.com/openings/Sicilian-Defense"]\n'
            '[TimeControl "180"]\n'
            "\n"
            "1. e4 c5 2. d3 Nc6 3. Nf3 d6 4. Be2 Nf6 5. O-O g6 0-1\n"
        ),
        "time_control": "180",
        "time_class": "blitz",
        "rated": True,
        "white": {"username": "opponent2", "rating": 1450, "result": "resigned"},
        "black": {"username": "testplayer", "rating": 1520, "result": "win"},
        "end_time": 1705401600,
    }


@pytest.fixture
def sample_analysis_result() -> dict[str, Any]:
    """A sample analysis result."""
    return {
        "mistakes": [
            {
                "move_number": 7,
                "phase": "opening",
                "eval_before": 0.3,
                "eval_after": -0.5,
                "eval_drop": 0.8,
                "best_move": "d4",
                "played_move": "c3",
                "fen": "r1bqkb1r/pppppppp/2n2n2/8/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
                "classification": "inaccuracy",
            },
            {
                "move_number": 15,
                "phase": "middlegame",
                "eval_before": 0.5,
                "eval_after": -1.2,
                "eval_drop": 1.7,
                "best_move": "Nf3",
                "played_move": "Bg5",
                "fen": "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
                "classification": "mistake",
            },
            {
                "move_number": 22,
                "phase": "middlegame",
                "eval_before": -0.3,
                "eval_after": -3.5,
                "eval_drop": 3.2,
                "best_move": "Rxe1",
                "played_move": "Qd2",
                "fen": "2rq1rk1/pp3ppp/2np4/2b1p3/4P3/2NP4/PPP2PPP/R1BQR1K1 w - - 0 15",
                "classification": "blunder",
            },
        ],
        "opening_accuracy": 85.0,
        "middlegame_accuracy": 65.0,
        "endgame_accuracy": 90.0,
        "total_blunders": 1,
        "total_mistakes": 1,
        "total_inaccuracies": 1,
    }


@pytest.fixture
def sample_game_data() -> dict[str, Any]:
    """A sample parsed game data dict."""
    return {
        "chess_com_id": "12345",
        "pgn": "1. e4 e5 2. Nf3 Nc6 1-0",
        "time_control": "600",
        "player_color": "white",
        "result": "win",
        "opponent": "opponent1",
        "date_played": datetime(2024, 1, 15, tzinfo=timezone.utc),
        "opening_name": "Italian Game",
        "eco_code": "C50",
    }

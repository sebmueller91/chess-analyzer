import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.chess_com import (
    fetch_player_games,
    PlayerNotFoundError,
    ChessComError,
)
from app.services.pgn_parser import parse_game, _extract_pgn_header


class TestPgnParser:
    """Tests for PGN parsing functions."""

    def test_parse_game_white(self, sample_chess_com_game):
        result = parse_game(sample_chess_com_game, "testplayer")
        assert result["chess_com_id"] == "12345"
        assert result["player_color"] == "white"
        assert result["result"] == "win"
        assert result["opponent"] == "opponent1"
        assert result["time_control"] == "600"
        assert result["eco_code"] == "C50"
        assert "Italian Game" in (result["opening_name"] or "")

    def test_parse_game_black(self, sample_chess_com_game_black):
        result = parse_game(sample_chess_com_game_black, "testplayer")
        assert result["chess_com_id"] == "67890"
        assert result["player_color"] == "black"
        assert result["result"] == "win"
        assert result["opponent"] == "opponent2"

    def test_parse_game_case_insensitive(self, sample_chess_com_game):
        result = parse_game(sample_chess_com_game, "TestPlayer")
        assert result["player_color"] == "white"

    def test_parse_game_draw(self):
        game = {
            "url": "https://www.chess.com/game/live/99999",
            "pgn": '[Event "Live Chess"]\n[White "player1"]\n[Black "player2"]\n[Result "1/2-1/2"]\n\n1. e4 e5 1/2-1/2\n',
            "time_control": "300",
            "time_class": "blitz",
            "white": {"username": "player1", "rating": 1500, "result": "stalemate"},
            "black": {"username": "player2", "rating": 1500, "result": "stalemate"},
            "end_time": 1705315200,
        }
        result = parse_game(game, "player1")
        assert result["result"] == "draw"
        assert result["player_color"] == "white"

    def test_parse_game_loss(self):
        game = {
            "url": "https://www.chess.com/game/live/11111",
            "pgn": '[Event "Live Chess"]\n[White "player1"]\n[Black "player2"]\n[Result "0-1"]\n\n1. e4 e5 0-1\n',
            "time_control": "600",
            "time_class": "rapid",
            "white": {"username": "player1", "rating": 1500, "result": "checkmated"},
            "black": {"username": "player2", "rating": 1500, "result": "win"},
            "end_time": 1705315200,
        }
        result = parse_game(game, "player1")
        assert result["result"] == "loss"

    def test_extract_pgn_header(self):
        pgn = '[Event "Live Chess"]\n[White "testplayer"]\n[ECO "C50"]\n'
        assert _extract_pgn_header(pgn, "ECO") == "C50"
        assert _extract_pgn_header(pgn, "White") == "testplayer"
        assert _extract_pgn_header(pgn, "Missing") is None


class TestChessComFetch:
    """Tests for Chess.com API client."""

    @pytest.mark.asyncio
    async def test_fetch_player_not_found(self):
        """Test 404 handling for unknown player."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {}

        with patch("app.services.chess_com.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(PlayerNotFoundError):
                await fetch_player_games("nonexistent_player_xyz")

    @pytest.mark.asyncio
    async def test_fetch_empty_archives(self):
        """Test handling empty archives."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"archives": []}

        with patch("app.services.chess_com.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            games = await fetch_player_games("testplayer")
            assert games == []

    @pytest.mark.asyncio
    async def test_fetch_with_time_filter(self):
        """Test time control filtering."""
        archives_response = MagicMock()
        archives_response.status_code = 200
        archives_response.json.return_value = {
            "archives": ["https://api.chess.com/pub/player/test/games/2024/01"]
        }

        games_response = MagicMock()
        games_response.status_code = 200
        games_response.json.return_value = {
            "games": [
                {
                    "url": "https://www.chess.com/game/live/1",
                    "pgn": "1. e4 e5 1-0",
                    "time_class": "rapid",
                    "time_control": "600",
                    "white": {"username": "test"},
                    "black": {"username": "opp"},
                },
                {
                    "url": "https://www.chess.com/game/live/2",
                    "pgn": "1. d4 d5 1-0",
                    "time_class": "blitz",
                    "time_control": "180",
                    "white": {"username": "test"},
                    "black": {"username": "opp2"},
                },
            ]
        }

        with patch("app.services.chess_com.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [archives_response, games_response]
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            games = await fetch_player_games("test", time_control="rapid", game_count=50)
            assert len(games) == 1
            assert games[0]["time_class"] == "rapid"

import pytest

from app.services.stockfish import _classify_mistake, _get_phase, ENDGAME_PIECE_THRESHOLD

import chess


class TestClassifyMistake:
    """Tests for eval drop classification."""

    def test_blunder(self):
        assert _classify_mistake(200) == "blunder"
        assert _classify_mistake(500) == "blunder"

    def test_mistake(self):
        assert _classify_mistake(100) == "mistake"
        assert _classify_mistake(150) == "mistake"
        assert _classify_mistake(199) == "mistake"

    def test_inaccuracy(self):
        assert _classify_mistake(50) == "inaccuracy"
        assert _classify_mistake(75) == "inaccuracy"
        assert _classify_mistake(99) == "inaccuracy"

    def test_no_mistake(self):
        assert _classify_mistake(0) is None
        assert _classify_mistake(10) is None
        assert _classify_mistake(49) is None


class TestPhaseDetection:
    """Tests for game phase detection."""

    def test_opening_phase(self):
        board = chess.Board()
        assert _get_phase(1, board) == "opening"
        assert _get_phase(5, board) == "opening"
        assert _get_phase(10, board) == "opening"

    def test_middlegame_phase(self):
        board = chess.Board()
        assert _get_phase(11, board) == "middlegame"
        assert _get_phase(20, board) == "middlegame"
        assert _get_phase(25, board) == "middlegame"

    def test_endgame_by_move_number(self):
        board = chess.Board()
        assert _get_phase(26, board) == "endgame"
        assert _get_phase(40, board) == "endgame"

    def test_endgame_by_piece_count(self):
        # Create a board with few pieces (endgame)
        board = chess.Board("8/8/4k3/8/8/4K3/4P3/8 w - - 0 1")  # K+P vs K
        total_pieces = len(board.piece_map())
        assert total_pieces <= ENDGAME_PIECE_THRESHOLD
        # Even at move 5, this should be endgame due to piece count
        assert _get_phase(5, board) == "endgame"

    def test_middlegame_with_many_pieces(self):
        # Standard position with many pieces
        board = chess.Board()
        assert len(board.piece_map()) > ENDGAME_PIECE_THRESHOLD
        assert _get_phase(15, board) == "middlegame"

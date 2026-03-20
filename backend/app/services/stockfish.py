import io
import logging
from typing import Any, Optional

import chess
import chess.engine
import chess.pgn

from app.config import settings

logger = logging.getLogger(__name__)

INACCURACY_THRESHOLD = 50   # centipawns
MISTAKE_THRESHOLD = 100
BLUNDER_THRESHOLD = 200

ENDGAME_PIECE_THRESHOLD = 10  # total pieces on board


def _classify_mistake(eval_drop_cp: int) -> Optional[str]:
    """Classify a mistake by centipawn eval drop."""
    if eval_drop_cp >= BLUNDER_THRESHOLD:
        return "blunder"
    elif eval_drop_cp >= MISTAKE_THRESHOLD:
        return "mistake"
    elif eval_drop_cp >= INACCURACY_THRESHOLD:
        return "inaccuracy"
    return None


def _get_phase(move_number: int, board: chess.Board) -> str:
    """Determine game phase based on move number and piece count."""
    total_pieces = len(board.piece_map())
    if total_pieces <= ENDGAME_PIECE_THRESHOLD:
        return "endgame"
    if move_number > 25:
        return "endgame"
    if move_number > 10:
        return "middlegame"
    return "opening"


def _score_to_cp(score: chess.engine.PovScore, color: chess.Color) -> float:
    """Convert a PovScore to centipawns from the given color's perspective."""
    pov = score.pov(color)
    if pov.is_mate():
        mate_in = pov.mate()
        if mate_in is not None:
            return 10000 if mate_in > 0 else -10000
        return 0
    cp = pov.score()
    return cp if cp is not None else 0


class StockfishAnalyzer:
    """Analyze chess games using Stockfish engine."""

    def __init__(
        self,
        stockfish_path: Optional[str] = None,
        depth: Optional[int] = None,
    ):
        self.stockfish_path = stockfish_path or settings.STOCKFISH_PATH
        self.depth = depth or settings.ANALYSIS_DEPTH
        self._engine: Optional[chess.engine.SimpleEngine] = None

    def _ensure_engine(self) -> chess.engine.SimpleEngine:
        if self._engine is None:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
        return self._engine

    def analyze_game(self, pgn_str: str, player_color: str) -> dict[str, Any]:
        """Analyze a single game and return mistakes and accuracy stats."""
        game = chess.pgn.read_game(io.StringIO(pgn_str))
        if game is None:
            logger.warning("Failed to parse PGN")
            return self._empty_result()

        color = chess.WHITE if player_color == "white" else chess.BLACK
        engine = self._ensure_engine()

        board = game.board()
        mistakes: list[dict[str, Any]] = []
        phase_evals: dict[str, list[float]] = {
            "opening": [],
            "middlegame": [],
            "endgame": [],
        }

        prev_eval_cp: Optional[float] = None
        # Get initial position eval
        try:
            info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
            prev_eval_cp = _score_to_cp(info["score"], color)
        except Exception as e:
            logger.warning("Engine analysis failed for initial position: %s", e)
            prev_eval_cp = 0

        move_number = 0
        for node in game.mainline():
            move = node.move
            is_player_move = board.turn == color
            move_number_display = board.fullmove_number

            # Apply the move
            san_move = board.san(move)
            board.push(move)

            if not is_player_move:
                # Evaluate after opponent's move to update prev_eval
                try:
                    info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
                    prev_eval_cp = _score_to_cp(info["score"], color)
                except Exception:
                    pass
                continue

            move_number += 1
            phase = _get_phase(move_number_display, board)

            # Evaluate position after player's move
            try:
                info = engine.analyse(board, chess.engine.Limit(depth=self.depth))
                current_eval_cp = _score_to_cp(info["score"], color)
            except Exception as e:
                logger.warning("Engine analysis failed at move %d: %s", move_number, e)
                continue

            if prev_eval_cp is not None:
                eval_drop_cp = prev_eval_cp - current_eval_cp
                eval_drop_cp = max(0, eval_drop_cp)  # only count drops

                phase_evals[phase].append(eval_drop_cp)

                classification = _classify_mistake(eval_drop_cp)
                if classification:
                    # Get the best move from the position before this move
                    board_before = board.copy()
                    board_before.pop()
                    try:
                        best_info = engine.analyse(
                            board_before, chess.engine.Limit(depth=self.depth)
                        )
                        best_move_obj = best_info.get("pv", [None])[0]
                        best_move_san = (
                            board_before.san(best_move_obj) if best_move_obj else "?"
                        )
                    except Exception:
                        best_move_san = "?"

                    mistakes.append(
                        {
                            "move_number": move_number_display,
                            "phase": phase,
                            "eval_before": round(prev_eval_cp / 100, 2),
                            "eval_after": round(current_eval_cp / 100, 2),
                            "eval_drop": round(eval_drop_cp / 100, 2),
                            "best_move": best_move_san,
                            "played_move": san_move,
                            "fen": board_before.fen(),
                            "classification": classification,
                        }
                    )

            prev_eval_cp = current_eval_cp

        # Calculate accuracy per phase
        def phase_accuracy(drops: list[float]) -> float:
            if not drops:
                return 100.0
            avg_drop = sum(drops) / len(drops)
            return max(0.0, min(100.0, 100.0 - avg_drop / 100 * 10))

        opening_acc = phase_accuracy(phase_evals["opening"])
        middlegame_acc = phase_accuracy(phase_evals["middlegame"])
        endgame_acc = phase_accuracy(phase_evals["endgame"])

        total_blunders = sum(1 for m in mistakes if m["classification"] == "blunder")
        total_mistakes = sum(1 for m in mistakes if m["classification"] == "mistake")
        total_inaccuracies = sum(
            1 for m in mistakes if m["classification"] == "inaccuracy"
        )

        return {
            "mistakes": mistakes,
            "opening_accuracy": round(opening_acc, 1),
            "middlegame_accuracy": round(middlegame_acc, 1),
            "endgame_accuracy": round(endgame_acc, 1),
            "total_blunders": total_blunders,
            "total_mistakes": total_mistakes,
            "total_inaccuracies": total_inaccuracies,
        }

    def _empty_result(self) -> dict[str, Any]:
        return {
            "mistakes": [],
            "opening_accuracy": 100.0,
            "middlegame_accuracy": 100.0,
            "endgame_accuracy": 100.0,
            "total_blunders": 0,
            "total_mistakes": 0,
            "total_inaccuracies": 0,
        }

    def close(self) -> None:
        """Shut down the Stockfish engine."""
        if self._engine is not None:
            try:
                self._engine.quit()
            except Exception:
                pass
            self._engine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

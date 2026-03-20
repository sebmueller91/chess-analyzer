import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _extract_pgn_header(pgn: str, header: str) -> Optional[str]:
    """Extract a header value from a PGN string."""
    pattern = rf'\[{header}\s+"([^"]*)"\]'
    match = re.search(pattern, pgn)
    return match.group(1) if match else None


def _chess_com_id_from_url(url: str) -> str:
    """Extract a unique game ID from a Chess.com game URL."""
    # URLs look like https://www.chess.com/game/live/12345
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else url


def _determine_result(game_data: dict, player_color: str) -> str:
    """Determine win/loss/draw from the player's perspective."""
    color_data = game_data.get(player_color, {})
    result_str = color_data.get("result", "")

    if result_str == "win":
        return "win"
    elif result_str in (
        "checkmated",
        "timeout",
        "resigned",
        "abandoned",
        "kingofthehill",
        "threecheck",
    ):
        return "loss"
    else:
        # stalemate, insufficient, 50move, repetition, agreed, timevsinsufficient
        return "draw"


def parse_game(game_data: dict, username: str) -> dict[str, Any]:
    """Parse a Chess.com game into a structured record."""
    username_lower = username.lower()
    pgn = game_data.get("pgn", "")
    url = game_data.get("url", "")

    # Determine player color
    white_user = game_data.get("white", {}).get("username", "").lower()
    black_user = game_data.get("black", {}).get("username", "").lower()

    if white_user == username_lower:
        player_color = "white"
        opponent = game_data.get("black", {}).get("username", black_user)
    else:
        player_color = "black"
        opponent = game_data.get("white", {}).get("username", white_user)

    result = _determine_result(game_data, player_color)

    # Extract PGN headers
    opening_name = _extract_pgn_header(pgn, "ECOUrl")
    if opening_name:
        # ECOUrl is like "https://www.chess.com/openings/Sicilian-Defense..."
        opening_name = opening_name.rstrip("/").split("/")[-1].replace("-", " ")
    if not opening_name:
        opening_name = _extract_pgn_header(pgn, "Opening")

    eco_code = _extract_pgn_header(pgn, "ECO")

    # Parse date
    end_time = game_data.get("end_time")
    if end_time:
        date_played = datetime.fromtimestamp(end_time, tz=timezone.utc)
    else:
        date_str = _extract_pgn_header(pgn, "Date")
        if date_str:
            try:
                date_played = datetime.strptime(date_str, "%Y.%m.%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                date_played = datetime.now(timezone.utc)
        else:
            date_played = datetime.now(timezone.utc)

    time_control = game_data.get("time_control", "")
    chess_com_id = _chess_com_id_from_url(url)

    return {
        "chess_com_id": chess_com_id,
        "pgn": pgn,
        "time_control": time_control,
        "player_color": player_color,
        "result": result,
        "opponent": opponent,
        "date_played": date_played,
        "opening_name": opening_name,
        "eco_code": eco_code,
    }

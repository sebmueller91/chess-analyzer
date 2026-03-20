import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CHESS_COM_BASE = "https://api.chess.com/pub"
USER_AGENT = "ChessAnalyzer/1.0"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0


class ChessComError(Exception):
    """Raised for Chess.com API errors."""
    pass


class PlayerNotFoundError(ChessComError):
    """Raised when a player is not found on Chess.com."""
    pass


async def _request_with_retry(client: httpx.AsyncClient, url: str) -> dict | list:
    """Make a GET request with exponential backoff on rate limits."""
    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        resp = await client.get(url)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            raise PlayerNotFoundError(f"Resource not found: {url}")
        if resp.status_code == 429:
            logger.warning("Rate limited by Chess.com, retrying in %.1fs", backoff)
            await asyncio.sleep(backoff)
            backoff *= 2
            continue
        resp.raise_for_status()
    raise ChessComError(f"Failed to fetch {url} after {MAX_RETRIES} retries")


async def fetch_player_games(
    username: str,
    time_control: str = "all",
    game_count: int = 50,
) -> list[dict[str, Any]]:
    """Fetch recent games for a player from Chess.com public API."""
    username_lower = username.lower()

    async with httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
    ) as client:
        # Get archive URLs
        archives_url = f"{CHESS_COM_BASE}/player/{username_lower}/games/archives"
        try:
            archives_data = await _request_with_retry(client, archives_url)
        except PlayerNotFoundError:
            raise PlayerNotFoundError(
                f"Player '{username}' not found on Chess.com. Check the username."
            )

        archive_urls = archives_data.get("archives", [])
        if not archive_urls:
            logger.info("No game archives found for %s", username)
            return []

        # Reverse to process most recent months first
        archive_urls = list(reversed(archive_urls))

        collected_games: list[dict[str, Any]] = []

        for archive_url in archive_urls:
            if len(collected_games) >= game_count:
                break

            try:
                archive_data = await _request_with_retry(client, archive_url)
            except ChessComError as e:
                logger.warning("Failed to fetch archive %s: %s", archive_url, e)
                continue

            games = archive_data.get("games", [])
            # Reverse games within archive (most recent first)
            games = list(reversed(games))

            for game in games:
                if len(collected_games) >= game_count:
                    break

                # Filter by time control if specified
                if time_control != "all":
                    game_time_class = game.get("time_class", "")
                    if game_time_class != time_control:
                        continue

                # Only include games with PGN data
                if "pgn" not in game:
                    continue

                collected_games.append(game)

        logger.info(
            "Fetched %d games for %s (requested %d, filter=%s)",
            len(collected_games),
            username,
            game_count,
            time_control,
        )
        return collected_games

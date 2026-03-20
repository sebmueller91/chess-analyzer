import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import require_openai_key, settings

logger = logging.getLogger(__name__)


def _build_system_prompt(username: str, report_data: dict[str, Any]) -> str:
    """Build a system prompt with structured context from the report."""
    summary = report_data.get("summary", {})
    weaknesses = report_data.get("top_weaknesses", [])
    openings = report_data.get("openings", [])
    phase_dist = report_data.get("phase_distribution", {})
    examples = report_data.get("mistake_examples", [])

    weakness_text = ""
    for i, w in enumerate(weaknesses[:3], 1):
        weakness_text += f"  {i}. {w.get('name')}: {w.get('description')}\n"

    opening_text = ""
    for o in openings[:5]:
        opening_text += (
            f"  - {o.get('name')}: {o.get('games_played')} games, "
            f"{o.get('win_rate', 0)}% win rate, {o.get('avg_accuracy', 0)}% accuracy\n"
        )

    examples_text = ""
    for e in examples[:3]:
        examples_text += (
            f"  - Move {e.get('move_number')} vs {e.get('game_opponent')} "
            f"({e.get('phase')}): played {e.get('played_move')}, "
            f"best was {e.get('best_move')} "
            f"(eval {e.get('eval_before')} -> {e.get('eval_after')})\n"
        )

    return f"""You are an expert chess coach for {username}. Use ONLY the analysis data provided below to answer questions. If the data doesn't contain the answer, say so honestly. Never invent claims or statistics not in the data. Be specific, reference actual games and positions when possible.

PLAYER DATA:
- Games analyzed: {summary.get('total_games', 0)}
- Record: {summary.get('wins', 0)}W / {summary.get('losses', 0)}L / {summary.get('draws', 0)}D ({summary.get('win_rate', 0)}% win rate)
- Average accuracy: {summary.get('avg_accuracy', 0)}%

PHASE ACCURACY:
- Opening: {phase_dist.get('opening', {}).get('avg_accuracy', 'N/A')}%
- Middlegame: {phase_dist.get('middlegame', {}).get('avg_accuracy', 'N/A')}%
- Endgame: {phase_dist.get('endgame', {}).get('avg_accuracy', 'N/A')}%

TOP WEAKNESSES:
{weakness_text if weakness_text else '  None identified'}

OPENING PERFORMANCE:
{opening_text if opening_text else '  No data'}

EXAMPLE MISTAKES:
{examples_text if examples_text else '  No examples'}"""


async def chat_with_coach(
    username: str,
    message: str,
    report_data: dict[str, Any],
    chat_history: list[dict[str, str]],
) -> str:
    """Send a message to the AI chess coach and get a response."""
    try:
        api_key = require_openai_key()
    except RuntimeError as e:
        logger.warning("OpenAI unavailable: %s", e)
        return (
            "I'm sorry, the AI coaching feature is currently unavailable. "
            "Please check that the OPENAI_API_KEY is configured."
        )

    system_prompt = _build_system_prompt(username, report_data)

    messages = [{"role": "system", "content": system_prompt}]

    # Add recent chat history
    history_limit = settings.CHAT_HISTORY_LIMIT
    for entry in chat_history[-history_limit:]:
        messages.append({
            "role": entry.get("role", "user"),
            "content": entry.get("content", ""),
        })

    messages.append({"role": "user", "content": message})

    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content or "I couldn't generate a response."
    except Exception as e:
        logger.error("OpenAI chat error: %s", e)
        return (
            "I'm sorry, I encountered an error processing your question. "
            "Please try again in a moment."
        )

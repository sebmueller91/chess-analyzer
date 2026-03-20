import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import require_openai_key, settings

logger = logging.getLogger(__name__)


def _build_system_prompt(username: str, report_data: dict[str, Any]) -> str:
    """Build a system prompt with rich, specific context from the report."""
    summary = report_data.get("summary", {})
    weaknesses = report_data.get("top_weaknesses", [])
    openings = report_data.get("openings", [])
    phase_dist = report_data.get("phase_distribution", {})
    examples = report_data.get("mistake_examples", [])

    # Weakness text with motif detail
    weakness_text = ""
    for i, w in enumerate(weaknesses[:5], 1):
        motif = w.get("motif", "")
        freq = w.get("frequency", 0)
        severity = w.get("severity", "")
        weakness_text += f"  {i}. [{severity}] {w.get('name')} (motif: {motif}, {freq}x)\n"
        weakness_text += f"     {w.get('description')}\n"
        for ex in w.get("examples", [])[:2]:
            played = ex.get("played", "?")
            best = ex.get("best", "?")
            move = ex.get("move", "?")
            opp = ex.get("opponent", "?")
            drop = ex.get("eval_drop", 0)
            drop_str = f"{round(drop/100,1)}" if drop else "?"
            weakness_text += f"     Example: move {move} vs {opp} — played {played}, best {best} (-{drop_str}p)\n"

    # Opening text: include struggling openings prominently
    opening_text = ""
    struggling = [o for o in openings if o.get("games_played", 0) >= 2 and o.get("win_rate", 100) < 40]
    good = [o for o in openings if o.get("games_played", 0) >= 2 and o.get("win_rate", 0) >= 55]
    for o in sorted(struggling, key=lambda x: x.get("win_rate", 0))[:4]:
        opening_text += (
            f"  ⚠ {o.get('name')}: {o.get('win_rate', 0)}% win rate in {o.get('games_played', 0)} games "
            f"({o.get('avg_accuracy', 0)}% accuracy) — STRUGGLING\n"
        )
    for o in sorted(good, key=lambda x: x.get("win_rate", 0), reverse=True)[:3]:
        opening_text += (
            f"  ✓ {o.get('name')}: {o.get('win_rate', 0)}% win rate in {o.get('games_played', 0)} games "
            f"({o.get('avg_accuracy', 0)}% accuracy) — OK\n"
        )
    if not opening_text:
        for o in openings[:5]:
            opening_text += (
                f"  - {o.get('name')}: {o.get('games_played')} games, "
                f"{o.get('win_rate', 0)}% win rate, {o.get('avg_accuracy', 0)}% accuracy\n"
            )

    # Concrete mistake examples with motif labels
    examples_text = ""
    for e in examples[:6]:
        motif = e.get("motif_label") or e.get("motif", "")
        move = e.get("move_number", "?")
        opp = e.get("game_opponent", "?")
        played = e.get("played_move", "?")
        best = e.get("best_move", "?")
        phase = e.get("phase", "")
        cls_ = e.get("classification", "")
        eb = e.get("eval_before", 0)
        ea = e.get("eval_after", 0)
        drop = round(abs((eb or 0) - (ea or 0)) / 100, 1)
        opening = e.get("opening_name", "")
        examples_text += (
            f"  - Move {move} vs {opp} [{phase}, {cls_}]"
            + (f" in {opening}" if opening else "")
            + f": played {played}, best was {best} (eval {eb}→{ea}, -{drop}p)"
            + (f" | {motif}" if motif and "oversight" not in motif else "")
            + "\n"
        )

    return f"""You are an expert chess coach for {username}. Use ONLY the analysis data provided. Never invent statistics. Be highly specific: when discussing weaknesses, name the exact tactical patterns (knight fork, hanging piece, back-rank, etc.) and reference specific games. If asked about a weakness, describe the exact examples from the data. If data doesn't cover something, say so honestly.

PLAYER STATS ({summary.get('total_games', 0)} games):
- Record: {summary.get('wins', 0)}W / {summary.get('losses', 0)}L / {summary.get('draws', 0)}D ({summary.get('win_rate', 0)}% win rate)
- Average accuracy: {summary.get('avg_accuracy', 0)}%

PHASE ACCURACY:
- Opening: {phase_dist.get('opening', {}).get('avg_accuracy', 'N/A')}% | Middlegame: {phase_dist.get('middlegame', {}).get('avg_accuracy', 'N/A')}% | Endgame: {phase_dist.get('endgame', {}).get('avg_accuracy', 'N/A')}%
- Opening blunders: {phase_dist.get('opening', {}).get('blunders', 0)} | Middlegame blunders: {phase_dist.get('middlegame', {}).get('blunders', 0)} | Endgame blunders: {phase_dist.get('endgame', {}).get('blunders', 0)}

DETECTED WEAKNESSES (specific tactical patterns):
{weakness_text if weakness_text else '  None identified'}

OPENING PERFORMANCE:
{opening_text if opening_text else '  No data'}

CONCRETE MISTAKE EXAMPLES (most significant):
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

import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import require_openai_key, settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert chess coach reviewing a student's game analysis. "
    "Write a personalized coaching summary based on the data provided. "
    "Be highly specific: reference actual tactical patterns detected, exact counts, "
    "and concrete game examples. Do NOT give generic advice like 'do puzzles'. "
    "Instead say 'practice KNIGHT FORK puzzles because you missed 3 knight forks'. "
    "Reference specific openings where the player struggles. Be encouraging but honest."
)


async def generate_coaching_summary(report_data: dict[str, Any], username: str) -> str:
    """Generate a 200-300 word coaching summary from structured report data."""
    try:
        api_key = require_openai_key()
    except RuntimeError as e:
        logger.warning("OpenAI unavailable: %s", e)
        return _fallback_summary(report_data, username)

    summary = report_data.get("summary", {})
    weaknesses = report_data.get("top_weaknesses", [])
    phase_dist = report_data.get("phase_distribution", {})
    color_comp = report_data.get("color_comparison", {})
    recommendations = report_data.get("training_recommendations", [])
    openings = report_data.get("openings", [])
    examples = report_data.get("mistake_examples", [])

    user_prompt = f"""Player: {username}

Games analyzed: {summary.get('total_games', 0)}
Record: {summary.get('wins', 0)}W / {summary.get('losses', 0)}L / {summary.get('draws', 0)}D
Win rate: {summary.get('win_rate', 0)}%
Average accuracy: {summary.get('avg_accuracy', 0)}%

SPECIFIC WEAKNESSES DETECTED (with examples from actual games):
{_format_weaknesses_detailed(weaknesses)}

PHASE ACCURACY:
- Opening (moves 1-10): {phase_dist.get('opening', {}).get('avg_accuracy', 'N/A')}%
- Middlegame: {phase_dist.get('middlegame', {}).get('avg_accuracy', 'N/A')}%
- Endgame: {phase_dist.get('endgame', {}).get('avg_accuracy', 'N/A')}%

COLOR PERFORMANCE:
- White: {color_comp.get('white', {}).get('win_rate', 0)}% win rate, {color_comp.get('white', {}).get('avg_accuracy', 0)}% accuracy
- Black: {color_comp.get('black', {}).get('win_rate', 0)}% win rate, {color_comp.get('black', {}).get('avg_accuracy', 0)}% accuracy

STRUGGLING OPENINGS (win rate < 40% with 2+ games):
{_format_struggling_openings(openings)}

CONCRETE MISTAKE EXAMPLES:
{_format_mistake_examples_detailed(examples)}

TRAINING RECOMMENDATIONS:
{_format_recommendations(recommendations)}

Write a 200-300 word personalized coaching summary. Be SPECIFIC: mention actual tactical patterns by name (e.g. 'knight forks', 'hanging pieces'), reference struggling openings by name, and cite concrete counts from the data. Give actionable next steps tied to the specific weaknesses found."""

    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content or _fallback_summary(
            report_data, username
        )
    except Exception as e:
        logger.error("OpenAI API error generating coaching summary: %s", e)
        return _fallback_summary(report_data, username)


def _format_weaknesses(weaknesses: list[dict]) -> str:
    if not weaknesses:
        return "No significant weaknesses detected."
    lines = []
    for i, w in enumerate(weaknesses, 1):
        lines.append(f"{i}. {w.get('name', '?')}: {w.get('description', '')}")
    return "\n".join(lines)


def _format_weaknesses_detailed(weaknesses: list[dict]) -> str:
    if not weaknesses:
        return "No significant weaknesses detected."
    lines = []
    for i, w in enumerate(weaknesses, 1):
        motif = w.get("motif", "")
        name = w.get("name", "?")
        desc = w.get("description", "")
        freq = w.get("frequency", 0)
        severity = w.get("severity", "")
        lines.append(f"{i}. [{severity.upper()}] {name} (occurred {freq}x, motif: {motif})")
        lines.append(f"   {desc}")
        examples = w.get("examples", [])
        for ex in examples[:2]:
            played = ex.get("played", "?")
            best = ex.get("best", "?")
            move = ex.get("move", "?")
            opp = ex.get("opponent", "?")
            drop = ex.get("eval_drop", 0)
            drop_str = f"{round(drop/100,1)} pawns" if drop else "?"
            lines.append(f"   → Move {move} vs {opp}: played {played}, best was {best} (-{drop_str})")
    return "\n".join(lines)


def _format_struggling_openings(openings: list[dict]) -> str:
    struggling = [
        o for o in openings
        if o.get("games_played", 0) >= 2 and o.get("win_rate", 100) < 40
    ]
    if not struggling:
        return "None identified (or insufficient games per opening)."
    lines = []
    for o in sorted(struggling, key=lambda x: x.get("win_rate", 0))[:4]:
        lines.append(
            f"- {o.get('name', '?')}: {o.get('win_rate', 0)}% win rate "
            f"in {o.get('games_played', 0)} games, {o.get('avg_accuracy', 0)}% accuracy"
        )
    return "\n".join(lines)


def _format_mistake_examples_detailed(examples: list[dict]) -> str:
    if not examples:
        return "No examples available."
    lines = []
    for e in examples[:5]:
        motif = e.get("motif_label") or e.get("motif", "")
        move = e.get("move_number", "?")
        opp = e.get("game_opponent", "?")
        played = e.get("played_move", "?")
        best = e.get("best_move", "?")
        phase = e.get("phase", "")
        classification = e.get("classification", "")
        eb = e.get("eval_before", 0)
        ea = e.get("eval_after", 0)
        drop = round(abs((eb or 0) - (ea or 0)) / 100, 1)
        lines.append(
            f"- Move {move} vs {opp} [{phase}, {classification}]: "
            f"played {played}, best was {best} "
            f"(eval {eb} → {ea}, -{drop} pawns)"
            + (f" | Pattern: {motif}" if motif and motif != "tactical_oversight" else "")
        )
    return "\n".join(lines)


def _format_recommendations(recommendations: list[dict]) -> str:
    if not recommendations:
        return "No specific recommendations."
    lines = []
    for r in recommendations:
        lines.append(f"- [{r.get('priority', 'medium')}] {r.get('title', '?')}: {r.get('description', '')}")
    return "\n".join(lines)


def _fallback_summary(report_data: dict, username: str) -> str:
    """Generate a basic summary when OpenAI is unavailable."""
    summary = report_data.get("summary", {})
    weaknesses = report_data.get("top_weaknesses", [])

    text = (
        f"Analysis for {username}: {summary.get('total_games', 0)} games analyzed. "
        f"Record: {summary.get('wins', 0)}W/{summary.get('losses', 0)}L/{summary.get('draws', 0)}D "
        f"({summary.get('win_rate', 0)}% win rate). "
        f"Average accuracy: {summary.get('avg_accuracy', 0)}%. "
    )

    if weaknesses:
        text += "Key areas to improve: "
        text += ", ".join(w.get("name", "?") for w in weaknesses[:3])
        text += ". "

    text += (
        "Review your games regularly and focus on the training recommendations "
        "in your report to see improvement."
    )

    return text

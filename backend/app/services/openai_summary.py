import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import require_openai_key, settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert chess coach reviewing a student's game analysis. "
    "Write a personalized coaching summary based on the data provided. "
    "Be specific, reference actual numbers, and provide actionable advice. "
    "Be encouraging but honest."
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

    user_prompt = f"""Player: {username}

Games analyzed: {summary.get('total_games', 0)}
Record: {summary.get('wins', 0)}W / {summary.get('losses', 0)}L / {summary.get('draws', 0)}D
Win rate: {summary.get('win_rate', 0)}%
Average accuracy: {summary.get('avg_accuracy', 0)}%

Top weaknesses:
{_format_weaknesses(weaknesses)}

Phase accuracy:
- Opening: {phase_dist.get('opening', {}).get('avg_accuracy', 'N/A')}%
- Middlegame: {phase_dist.get('middlegame', {}).get('avg_accuracy', 'N/A')}%
- Endgame: {phase_dist.get('endgame', {}).get('avg_accuracy', 'N/A')}%

Color performance:
- White: {color_comp.get('white', {}).get('win_rate', 0)}% win rate, {color_comp.get('white', {}).get('avg_accuracy', 0)}% accuracy
- Black: {color_comp.get('black', {}).get('win_rate', 0)}% win rate, {color_comp.get('black', {}).get('avg_accuracy', 0)}% accuracy

Training recommendations:
{_format_recommendations(recommendations)}

Write a 200-300 word personalized coaching summary for this player. Reference specific numbers from the data."""

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

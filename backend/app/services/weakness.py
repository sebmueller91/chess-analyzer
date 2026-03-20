import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)


def generate_report(
    player_username: str,
    games: list[dict[str, Any]],
    analysis_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate a comprehensive weakness/performance report from analyzed games."""
    if not games or not analysis_results:
        return _empty_report(player_username)

    # --- 1. Summary stats ---
    total_games = len(games)
    wins = sum(1 for g in games if g.get("result") == "win")
    losses = sum(1 for g in games if g.get("result") == "loss")
    draws = sum(1 for g in games if g.get("result") == "draw")
    win_rate = round(wins / total_games * 100, 1) if total_games else 0.0

    all_accuracies = []
    for ar in analysis_results:
        accs = [
            ar.get("opening_accuracy", 0),
            ar.get("middlegame_accuracy", 0),
            ar.get("endgame_accuracy", 0),
        ]
        valid = [a for a in accs if a > 0]
        if valid:
            all_accuracies.append(sum(valid) / len(valid))

    avg_accuracy = round(sum(all_accuracies) / len(all_accuracies), 1) if all_accuracies else 0.0

    summary = {
        "total_games": total_games,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": win_rate,
        "avg_accuracy": avg_accuracy,
    }

    # Collect all mistakes across games with game context
    all_mistakes: list[dict[str, Any]] = []
    for game, ar in zip(games, analysis_results):
        for m in ar.get("mistakes", []):
            enriched = {
                **m,
                "game_opponent": game.get("opponent", "?"),
                "game_date": str(game.get("date_played", "")),
                "opening_name": game.get("opening_name", ""),
                "player_color": game.get("player_color", ""),
                "result": game.get("result", ""),
            }
            all_mistakes.append(enriched)

    # --- 2. Top weaknesses ---
    top_weaknesses = _identify_weaknesses(all_mistakes, analysis_results)

    # --- 3. Opening performance ---
    openings = _opening_performance(games, analysis_results)

    # --- 4. Phase distribution ---
    phase_distribution = _phase_distribution(all_mistakes, analysis_results)

    # --- 5. Color comparison ---
    color_comparison = _color_comparison(games, analysis_results)

    # --- 6. Mistake examples ---
    mistake_examples = _select_mistake_examples(all_mistakes)

    # --- 7. Training recommendations ---
    training_recommendations = _generate_recommendations(
        top_weaknesses, phase_distribution, color_comparison, summary
    )

    return {
        "username": player_username,
        "summary": summary,
        "top_weaknesses": top_weaknesses,
        "openings": openings,
        "phase_distribution": phase_distribution,
        "color_comparison": color_comparison,
        "mistake_examples": mistake_examples,
        "training_recommendations": training_recommendations,
    }


def _identify_weaknesses(
    all_mistakes: list[dict], analysis_results: list[dict]
) -> list[dict[str, Any]]:
    """Identify top 3-5 weaknesses from mistake patterns."""
    phase_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    phase_examples: dict[str, list[dict]] = defaultdict(list)

    for m in all_mistakes:
        phase = m.get("phase", "middlegame")
        classification = m.get("classification", "inaccuracy")
        phase_counts[phase][classification] += 1
        phase_examples[phase].append(m)

    weaknesses: list[dict[str, Any]] = []

    # Middlegame tactical issues
    mg = phase_counts.get("middlegame", {})
    mg_total = sum(mg.values())
    if mg_total >= 2:
        mg_blunders = mg.get("blunder", 0) + mg.get("mistake", 0)
        severity = "high" if mg_blunders > mg_total * 0.3 else "medium"
        examples = sorted(
            phase_examples.get("middlegame", []),
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:3]
        weaknesses.append({
            "name": "Tactical oversights in middlegame",
            "description": (
                f"You made {mg_total} errors in the middlegame phase across analyzed games, "
                f"including {mg.get('blunder', 0)} blunders and {mg.get('mistake', 0)} mistakes."
            ),
            "frequency": mg_total,
            "severity": severity,
            "phase": "middlegame",
            "examples": [
                {"opponent": e.get("game_opponent"), "move": e.get("move_number")}
                for e in examples
            ],
        })

    # Endgame technique
    eg = phase_counts.get("endgame", {})
    eg_total = sum(eg.values())
    if eg_total >= 2:
        severity = "high" if eg.get("blunder", 0) >= 2 else "medium"
        examples = sorted(
            phase_examples.get("endgame", []),
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:3]
        weaknesses.append({
            "name": "Endgame technique",
            "description": (
                f"You made {eg_total} errors in endgames, "
                f"including {eg.get('blunder', 0)} blunders. Endgame precision is critical."
            ),
            "frequency": eg_total,
            "severity": severity,
            "phase": "endgame",
            "examples": [
                {"opponent": e.get("game_opponent"), "move": e.get("move_number")}
                for e in examples
            ],
        })

    # Opening preparation
    op = phase_counts.get("opening", {})
    op_total = sum(op.values())
    if op_total >= 2:
        severity = "medium" if op_total >= 5 else "low"
        examples = sorted(
            phase_examples.get("opening", []),
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:3]
        weaknesses.append({
            "name": "Opening preparation",
            "description": (
                f"You made {op_total} errors in the opening phase. "
                f"Better preparation could avoid early disadvantages."
            ),
            "frequency": op_total,
            "severity": severity,
            "phase": "opening",
            "examples": [
                {"opponent": e.get("game_opponent"), "move": e.get("move_number")}
                for e in examples
            ],
        })

    # Piece activity — blunders across all phases suggest piece coordination issues
    total_blunders = sum(
        1 for m in all_mistakes if m.get("classification") == "blunder"
    )
    if total_blunders >= 3:
        big_blunders = sorted(
            [m for m in all_mistakes if m.get("classification") == "blunder"],
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:3]
        weaknesses.append({
            "name": "Piece activity",
            "description": (
                f"You had {total_blunders} blunders across all phases, suggesting issues "
                f"with keeping pieces active and coordinated."
            ),
            "frequency": total_blunders,
            "severity": "high",
            "phase": "all",
            "examples": [
                {"opponent": e.get("game_opponent"), "move": e.get("move_number")}
                for e in big_blunders
            ],
        })

    # Late-game mistakes (time pressure proxy — mistakes after move 30)
    late_mistakes = [m for m in all_mistakes if m.get("move_number", 0) > 30]
    if len(late_mistakes) >= 3:
        severity = "high" if len(late_mistakes) >= 5 else "medium"
        examples = sorted(
            late_mistakes,
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:3]
        weaknesses.append({
            "name": "Time pressure",
            "description": (
                f"You made {len(late_mistakes)} errors after move 30, which may indicate "
                f"time management issues in longer games."
            ),
            "frequency": len(late_mistakes),
            "severity": severity,
            "phase": "endgame",
            "examples": [
                {"opponent": e.get("game_opponent"), "move": e.get("move_number")}
                for e in examples
            ],
        })

    # Sort by frequency descending and take top 5
    weaknesses.sort(key=lambda w: w["frequency"], reverse=True)
    return weaknesses[:5]


def _opening_performance(
    games: list[dict], analysis_results: list[dict]
) -> list[dict[str, Any]]:
    """Group games by opening and calculate performance."""
    opening_data: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "name": "",
            "eco": None,
            "games_played": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "accuracies": [],
        }
    )

    for game, ar in zip(games, analysis_results):
        name = game.get("opening_name") or "Unknown"
        eco = game.get("eco_code")
        entry = opening_data[name]
        entry["name"] = name
        if eco:
            entry["eco"] = eco
        entry["games_played"] += 1

        result = game.get("result", "")
        if result == "win":
            entry["wins"] += 1
        elif result == "loss":
            entry["losses"] += 1
        else:
            entry["draws"] += 1

        accs = [
            ar.get("opening_accuracy", 0),
            ar.get("middlegame_accuracy", 0),
            ar.get("endgame_accuracy", 0),
        ]
        valid = [a for a in accs if a > 0]
        if valid:
            entry["accuracies"].append(sum(valid) / len(valid))

    openings: list[dict[str, Any]] = []
    for entry in opening_data.values():
        if entry["games_played"] < 2:
            continue
        avg_acc = (
            round(sum(entry["accuracies"]) / len(entry["accuracies"]), 1)
            if entry["accuracies"]
            else 0.0
        )
        gp = entry["games_played"]
        openings.append({
            "name": entry["name"],
            "eco": entry["eco"],
            "games_played": gp,
            "wins": entry["wins"],
            "losses": entry["losses"],
            "draws": entry["draws"],
            "win_rate": round(entry["wins"] / gp * 100, 1) if gp else 0.0,
            "avg_accuracy": avg_acc,
        })

    openings.sort(key=lambda o: o["games_played"], reverse=True)
    return openings


def _phase_distribution(
    all_mistakes: list[dict], analysis_results: list[dict]
) -> dict[str, dict[str, Any]]:
    """Calculate mistake distribution by game phase."""
    phases = {
        "opening": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "accuracies": []},
        "middlegame": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "accuracies": []},
        "endgame": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "accuracies": []},
    }

    for m in all_mistakes:
        phase = m.get("phase", "middlegame")
        classification = m.get("classification", "inaccuracy")
        if phase in phases:
            if classification == "blunder":
                phases[phase]["blunders"] += 1
            elif classification == "mistake":
                phases[phase]["mistakes"] += 1
            elif classification == "inaccuracy":
                phases[phase]["inaccuracies"] += 1

    for ar in analysis_results:
        phases["opening"]["accuracies"].append(ar.get("opening_accuracy", 100.0))
        phases["middlegame"]["accuracies"].append(ar.get("middlegame_accuracy", 100.0))
        phases["endgame"]["accuracies"].append(ar.get("endgame_accuracy", 100.0))

    result = {}
    for phase, data in phases.items():
        accs = data["accuracies"]
        avg_acc = round(sum(accs) / len(accs), 1) if accs else 0.0
        result[phase] = {
            "mistakes": data["mistakes"],
            "inaccuracies": data["inaccuracies"],
            "blunders": data["blunders"],
            "avg_accuracy": avg_acc,
        }

    return result


def _color_comparison(
    games: list[dict], analysis_results: list[dict]
) -> dict[str, dict[str, Any]]:
    """Compare performance as white vs black."""
    colors: dict[str, dict[str, Any]] = {
        "white": {
            "games": 0, "wins": 0, "losses": 0, "draws": 0,
            "accuracies": [], "mistake_counts": [],
        },
        "black": {
            "games": 0, "wins": 0, "losses": 0, "draws": 0,
            "accuracies": [], "mistake_counts": [],
        },
    }

    for game, ar in zip(games, analysis_results):
        color = game.get("player_color", "white")
        if color not in colors:
            continue

        colors[color]["games"] += 1
        result = game.get("result", "")
        if result == "win":
            colors[color]["wins"] += 1
        elif result == "loss":
            colors[color]["losses"] += 1
        else:
            colors[color]["draws"] += 1

        accs = [
            ar.get("opening_accuracy", 0),
            ar.get("middlegame_accuracy", 0),
            ar.get("endgame_accuracy", 0),
        ]
        valid = [a for a in accs if a > 0]
        if valid:
            colors[color]["accuracies"].append(sum(valid) / len(valid))

        total_errs = (
            ar.get("total_blunders", 0)
            + ar.get("total_mistakes", 0)
            + ar.get("total_inaccuracies", 0)
        )
        colors[color]["mistake_counts"].append(total_errs)

    result = {}
    for color, data in colors.items():
        gp = data["games"]
        accs = data["accuracies"]
        mc = data["mistake_counts"]
        result[color] = {
            "games": gp,
            "wins": data["wins"],
            "losses": data["losses"],
            "draws": data["draws"],
            "win_rate": round(data["wins"] / gp * 100, 1) if gp else 0.0,
            "avg_accuracy": round(sum(accs) / len(accs), 1) if accs else 0.0,
            "avg_mistakes": round(sum(mc) / len(mc), 1) if mc else 0.0,
        }

    return result


def _select_mistake_examples(all_mistakes: list[dict]) -> list[dict[str, Any]]:
    """Select 5-8 most instructive mistake examples."""
    # Sort by eval_drop descending for most dramatic
    sorted_mistakes = sorted(
        all_mistakes, key=lambda m: m.get("eval_drop", 0), reverse=True
    )

    # Pick diverse phases
    selected: list[dict[str, Any]] = []
    phases_seen: dict[str, int] = defaultdict(int)

    for m in sorted_mistakes:
        if len(selected) >= 8:
            break
        phase = m.get("phase", "middlegame")
        # Don't pick more than 3 from same phase for diversity
        if phases_seen[phase] >= 3:
            continue
        phases_seen[phase] += 1

        selected.append({
            "game_opponent": m.get("game_opponent", "?"),
            "game_date": m.get("game_date"),
            "move_number": m.get("move_number", 0),
            "phase": phase,
            "played_move": m.get("played_move", "?"),
            "best_move": m.get("best_move", "?"),
            "eval_before": m.get("eval_before", 0),
            "eval_after": m.get("eval_after", 0),
            "fen": m.get("fen", ""),
            "classification": m.get("classification", "inaccuracy"),
            "opening_name": m.get("opening_name"),
            "player_color": m.get("player_color", ""),
            "result": m.get("result", ""),
        })

    return selected


def _generate_recommendations(
    weaknesses: list[dict],
    phase_distribution: dict[str, dict],
    color_comparison: dict[str, dict],
    summary: dict,
) -> list[dict[str, Any]]:
    """Generate training recommendations based on identified weaknesses."""
    recommendations: list[dict[str, Any]] = []

    for w in weaknesses[:3]:
        name = w["name"]
        if "middlegame" in name.lower() or "tactical" in name.lower():
            recommendations.append({
                "title": "Practice tactical puzzles",
                "description": (
                    f"You had {w['frequency']} tactical errors in the middlegame. "
                    "Solve 10-15 tactical puzzles daily on Chess.com or Lichess, "
                    "focusing on patterns like pins, forks, and discovered attacks."
                ),
                "priority": "high" if w["severity"] == "high" else "medium",
                "related_weakness": name,
            })
        elif "endgame" in name.lower():
            recommendations.append({
                "title": "Study endgame fundamentals",
                "description": (
                    f"You made {w['frequency']} endgame errors. Focus on basic rook endgames, "
                    "king activity, and pawn promotion technique. "
                    "Silman's Complete Endgame Course is an excellent resource."
                ),
                "priority": "high" if w["severity"] == "high" else "medium",
                "related_weakness": name,
            })
        elif "opening" in name.lower():
            recommendations.append({
                "title": "Build an opening repertoire",
                "description": (
                    f"You had {w['frequency']} opening errors. Choose 1-2 openings for each color "
                    "and study the key ideas and typical plans rather than memorizing long lines."
                ),
                "priority": "medium",
                "related_weakness": name,
            })
        elif "piece" in name.lower():
            recommendations.append({
                "title": "Improve piece coordination",
                "description": (
                    f"You had {w['frequency']} blunders suggesting piece activity issues. "
                    "Before each move, check all opponent threats and ensure your pieces "
                    "are actively placed. A simple blunder check can save many games."
                ),
                "priority": "high",
                "related_weakness": name,
            })
        elif "time" in name.lower():
            recommendations.append({
                "title": "Improve time management",
                "description": (
                    f"You made {w['frequency']} errors in later moves, likely due to time pressure. "
                    "Practice with increment time controls and develop a habit of "
                    "checking the clock after every 5 moves."
                ),
                "priority": "medium",
                "related_weakness": name,
            })

    # Add a general recommendation if we have fewer than 3
    if len(recommendations) < 3:
        if summary.get("avg_accuracy", 100) < 75:
            recommendations.append({
                "title": "Analyze your games regularly",
                "description": (
                    f"Your average accuracy is {summary.get('avg_accuracy', 0)}%. "
                    "Review each game after playing, identify where you went wrong, "
                    "and try to understand the correct ideas."
                ),
                "priority": "high",
                "related_weakness": "General improvement",
            })

    # Color-specific recommendation
    white_data = color_comparison.get("white", {})
    black_data = color_comparison.get("black", {})
    w_wr = white_data.get("win_rate", 50)
    b_wr = black_data.get("win_rate", 50)
    if abs(w_wr - b_wr) > 15 and len(recommendations) < 5:
        weaker = "black" if b_wr < w_wr else "white"
        recommendations.append({
            "title": f"Improve your {weaker} repertoire",
            "description": (
                f"Your win rate as {weaker} ({min(w_wr, b_wr):.1f}%) is significantly "
                f"lower than as {'white' if weaker == 'black' else 'black'} "
                f"({max(w_wr, b_wr):.1f}%). Focus on building confidence "
                f"with your {weaker} openings."
            ),
            "priority": "medium",
            "related_weakness": f"{weaker.capitalize()} performance",
        })

    return recommendations[:5]


def _empty_report(username: str) -> dict[str, Any]:
    return {
        "username": username,
        "summary": {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_rate": 0.0,
            "avg_accuracy": 0.0,
        },
        "top_weaknesses": [],
        "openings": [],
        "phase_distribution": {
            "opening": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "avg_accuracy": 0.0},
            "middlegame": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "avg_accuracy": 0.0},
            "endgame": {"mistakes": 0, "inaccuracies": 0, "blunders": 0, "avg_accuracy": 0.0},
        },
        "color_comparison": {
            "white": {
                "games": 0, "wins": 0, "losses": 0, "draws": 0,
                "win_rate": 0.0, "avg_accuracy": 0.0, "avg_mistakes": 0.0,
            },
            "black": {
                "games": 0, "wins": 0, "losses": 0, "draws": 0,
                "win_rate": 0.0, "avg_accuracy": 0.0, "avg_mistakes": 0.0,
            },
        },
        "mistake_examples": [],
        "training_recommendations": [],
    }

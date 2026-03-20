import logging
from collections import defaultdict
from typing import Any

import chess

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tactical motif detection
# ---------------------------------------------------------------------------

_PIECE_NAMES = {
    chess.PAWN: "pawn",
    chess.KNIGHT: "knight",
    chess.BISHOP: "bishop",
    chess.ROOK: "rook",
    chess.QUEEN: "queen",
    chess.KING: "king",
}

_VALUABLE = {chess.QUEEN, chess.ROOK, chess.KNIGHT, chess.BISHOP}


def _detect_tactical_motif(fen: str, best_move_san: str, player_color: str) -> str:
    """Return the primary tactical motif the best move would have exploited.

    Returns a short slug like 'knight_fork', 'hanging_piece', 'back_rank_mate',
    'check_forcing', 'discovered_attack', 'pin', or 'tactical_oversight'.
    """
    if not fen or not best_move_san or best_move_san in ("?", ""):
        return "tactical_oversight"
    try:
        board = chess.Board(fen)
        color = chess.WHITE if player_color == "white" else chess.BLACK
        best_move = board.parse_san(best_move_san)

        # --- Hanging piece capture (opponent left a piece undefended) ---
        if board.is_capture(best_move):
            victim = board.piece_at(best_move.to_square)
            if victim:
                defenders = board.attackers(not color, best_move.to_square)
                if not defenders:
                    return "hanging_piece"

        board_after = board.copy()
        board_after.push(best_move)

        # --- Checkmate ---
        if board_after.is_checkmate():
            return "missed_checkmate"

        moved_piece = board.piece_at(best_move.from_square)
        landing_sq = best_move.to_square

        # --- Fork: piece attacks 2+ valuable targets after the move ---
        if moved_piece and moved_piece.piece_type != chess.PAWN:
            attacks = board_after.attacks(landing_sq)
            attacked_valuable = [
                sq for sq in attacks
                if (p := board_after.piece_at(sq))
                and p.color != color
                and p.piece_type in _VALUABLE | {chess.KING}
            ]
            if len(attacked_valuable) >= 2:
                piece_name = _PIECE_NAMES.get(moved_piece.piece_type, "piece")
                return f"{piece_name}_fork"

        # Pawn fork: pawn attacks 2+ pieces diagonally
        if moved_piece and moved_piece.piece_type == chess.PAWN:
            attacks = board_after.attacks(landing_sq)
            attacked_valuable = [
                sq for sq in attacks
                if (p := board_after.piece_at(sq))
                and p.color != color
                and p.piece_type in _VALUABLE | {chess.KING}
            ]
            if len(attacked_valuable) >= 2:
                return "pawn_fork"

        # --- Check-forcing move (forcing move that was missed) ---
        if board_after.is_check():
            return "check_forcing"

        # --- Back-rank mate threat ---
        opp_king_sq = board_after.king(not color)
        if opp_king_sq is not None:
            back_rank = 7 if color == chess.WHITE else 0
            if chess.square_rank(opp_king_sq) == back_rank:
                for heavy_type in (chess.ROOK, chess.QUEEN):
                    for sq in board_after.pieces(heavy_type, color):
                        if chess.square_rank(sq) == back_rank:
                            return "back_rank_mate"

        # --- Discovered attack: moving piece reveals an attacker behind it ---
        from_sq = best_move.from_square
        attackers_before = set(board.attackers(color, from_sq))
        attackers_after_sq = set()
        for sq in chess.SQUARES:
            p = board_after.piece_at(sq)
            if p and p.color == color and sq != landing_sq:
                if len(board_after.attacks(sq) & board_after.pieces(chess.QUEEN, not color)) > 0:
                    continue
                if board_after.is_attacked_by(color, sq):
                    continue
        # Simpler discovered check/attack heuristic: a piece on the landing rank/file
        # now attacks a valuable piece it couldn't before because the moved piece was blocking
        if moved_piece:
            for sq in board.pieces(chess.ROOK, color) | board.pieces(chess.BISHOP, color) | board.pieces(chess.QUEEN, color):
                if sq == from_sq:
                    continue
                targets_before = {
                    s for s in board.attacks(sq)
                    if (p := board.piece_at(s)) and p.color != color and p.piece_type in _VALUABLE | {chess.KING}
                }
                targets_after = {
                    s for s in board_after.attacks(sq)
                    if (p := board_after.piece_at(s)) and p.color != color and p.piece_type in _VALUABLE | {chess.KING}
                }
                if targets_after - targets_before:
                    return "discovered_attack"

        # --- Pin: after the move a valuable opponent piece is pinned to the king ---
        opp_king = board_after.king(not color)
        if opp_king is not None:
            for sq in chess.SQUARES:
                p = board_after.piece_at(sq)
                if p and p.color == color and p.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                    if board_after.is_pinned(not color, sq):
                        pinned = board_after.piece_at(sq)
                        if pinned and pinned.piece_type in _VALUABLE:
                            return "pin"

    except Exception:
        pass
    return "tactical_oversight"


_MOTIF_DISPLAY: dict[str, str] = {
    "knight_fork": "Missed knight fork",
    "bishop_fork": "Missed bishop fork",
    "rook_fork": "Missed rook fork",
    "queen_fork": "Missed queen fork",
    "pawn_fork": "Missed pawn fork",
    "hanging_piece": "Left piece hanging / missed free material",
    "missed_checkmate": "Missed checkmate",
    "back_rank_mate": "Back-rank vulnerability",
    "check_forcing": "Missed forcing check",
    "discovered_attack": "Missed discovered attack",
    "pin": "Missed pin",
    "tactical_oversight": "Tactical oversight",
}

_MOTIF_ADVICE: dict[str, str] = {
    "knight_fork": (
        "Practice knight fork puzzles on Lichess.org/training (search 'fork' theme). "
        "Before each move, visualize where your knight could jump to attack two pieces simultaneously."
    ),
    "bishop_fork": (
        "Practice bishop fork puzzles. Train yourself to spot long diagonal attacks that threaten "
        "two pieces at once."
    ),
    "rook_fork": (
        "Practice rook skewer and fork patterns. Rook forks often arise when pieces are on the same rank or file."
    ),
    "queen_fork": (
        "Practice queen fork and double-attack puzzles. "
        "After each opponent move, check if your queen can attack two undefended targets."
    ),
    "pawn_fork": (
        "Practice pawn fork puzzles. Pawn advances that attack two pieces diagonally are common "
        "and easy to miss — scan for them before playing a pawn push."
    ),
    "hanging_piece": (
        "Before every move, do a quick 'hang-check': look at all opponent pieces and ask "
        "'is this piece defended?' Capturing undefended pieces is always the first priority. "
        "Practice 'hanging piece' puzzles on Lichess."
    ),
    "missed_checkmate": (
        "Practice mate-in-1, mate-in-2, and mate-in-3 puzzles daily. "
        "Always check for checkmate before playing any other move."
    ),
    "back_rank_mate": (
        "Practice back-rank mate puzzles on Lichess. "
        "In your own games, always ensure your king has a luft (escape square) by moving a pawn. "
        "Check for back-rank weaknesses before making rook moves."
    ),
    "check_forcing": (
        "Practice forcing-sequence puzzles — checks, captures, threats. "
        "Develop a habit of always asking 'what checks, captures, or threats are available?' before each move."
    ),
    "discovered_attack": (
        "Practice discovered attack and discovered check puzzles on Lichess. "
        "Look for pieces that are 'hiding behind' another piece along a rank, file, or diagonal."
    ),
    "pin": (
        "Practice pin and skewer puzzles. Look for opportunities to place bishops, rooks, "
        "or queens on diagonals/files that pin opponent pieces to their king or queen."
    ),
    "tactical_oversight": (
        "Solve tactical puzzles daily covering all themes: forks, pins, back-rank, discovered attacks. "
        "Use Lichess.org/training for free themed puzzles."
    ),
}


def _format_motif_example(m: dict) -> str:
    """Build a short human-readable example string from a mistake dict."""
    move = m.get("move_number", "?")
    opp = m.get("game_opponent", "?")
    played = m.get("played_move", "?")
    best = m.get("best_move", "?")
    drop = m.get("eval_drop", 0)
    phase = m.get("phase", "")
    date = str(m.get("game_date", ""))[:10]
    color = m.get("player_color", "")
    result = m.get("result", "")
    drop_pawns = round(drop / 100, 1) if drop else "?"
    parts = [f"move {move} vs {opp}"]
    if date and date != "None":
        parts.append(f"({date})")
    if color:
        parts.append(f"as {color}")
    if phase:
        parts.append(f"[{phase}]")
    parts.append(f"— played {played}, best was {best} ({drop_pawns} pawn loss)")
    if result:
        parts.append(f"[{result}]")
    return " ".join(parts)


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
    """Identify top 5 weaknesses, grouped by specific tactical motif and pattern."""
    # --- Step 1: Detect motif for each blunder/mistake (skip inaccuracies for motif grouping) ---
    motif_mistakes: dict[str, list[dict]] = defaultdict(list)
    phase_mistakes: dict[str, list[dict]] = defaultdict(list)

    for m in all_mistakes:
        phase = m.get("phase", "middlegame")
        classification = m.get("classification", "inaccuracy")
        phase_mistakes[phase].append(m)

        # Only run motif detection on blunders and mistakes (significant errors)
        if classification in ("blunder", "mistake"):
            motif = _detect_tactical_motif(
                m.get("fen", ""),
                m.get("best_move", ""),
                m.get("player_color", "white"),
            )
            m["_motif"] = motif
            motif_mistakes[motif].append(m)
        else:
            m["_motif"] = "inaccuracy"

    weaknesses: list[dict[str, Any]] = []

    # --- Step 2: Motif-based weaknesses (most specific) ---
    # Sort motifs by frequency, excluding the generic fallback first
    motif_counts = {k: len(v) for k, v in motif_mistakes.items()}
    sorted_motifs = sorted(motif_counts.items(), key=lambda x: x[1], reverse=True)

    for motif, count in sorted_motifs:
        if count < 2:
            continue
        examples = sorted(
            motif_mistakes[motif],
            key=lambda x: x.get("eval_drop", 0),
            reverse=True,
        )[:4]

        display_name = _MOTIF_DISPLAY.get(motif, "Tactical oversight")
        blunder_count = sum(1 for e in motif_mistakes[motif] if e.get("classification") == "blunder")
        mistake_count = sum(1 for e in motif_mistakes[motif] if e.get("classification") == "mistake")
        severity = "high" if blunder_count >= 2 else ("medium" if count >= 3 else "low")

        # Build specific description referencing actual games
        example_refs = [_format_motif_example(e) for e in examples[:3]]
        example_text = "; ".join(example_refs)

        if motif == "hanging_piece":
            description = (
                f"You missed free material {count} time{'s' if count > 1 else ''} "
                f"({blunder_count} blunder{'s' if blunder_count != 1 else ''}, "
                f"{mistake_count} mistake{'s' if mistake_count != 1 else ''}). "
                f"Examples: {example_text}."
            )
        elif motif == "missed_checkmate":
            description = (
                f"You missed checkmate {count} time{'s' if count > 1 else ''} — "
                f"always scan for mate before other moves. "
                f"Examples: {example_text}."
            )
        elif motif == "back_rank_mate":
            description = (
                f"You missed {count} back-rank threats. "
                f"Ensure your king always has an escape square (luft). "
                f"Examples: {example_text}."
            )
        elif "_fork" in motif:
            piece = motif.replace("_fork", "")
            description = (
                f"You missed {piece} fork{'s' if count > 1 else ''} {count} time{'s' if count > 1 else ''}. "
                f"After every {piece} move, ask: 'Can I attack two pieces at once?' "
                f"Examples: {example_text}."
            )
        elif motif == "discovered_attack":
            description = (
                f"You missed {count} discovered attack opportunity{'ies' if count > 1 else 'y'}. "
                f"Look for pieces hiding behind others along ranks, files, and diagonals. "
                f"Examples: {example_text}."
            )
        elif motif == "pin":
            description = (
                f"You missed {count} pin opportunity{'ies' if count > 1 else 'y'}. "
                f"Scan for bishop/rook/queen moves that restrict opponent's most valuable piece. "
                f"Examples: {example_text}."
            )
        elif motif == "check_forcing":
            description = (
                f"You missed {count} forcing check{'s' if count > 1 else ''} that would have "
                f"won material or improved your position. "
                f"Always ask 'What checks are available?' before each move. "
                f"Examples: {example_text}."
            )
        else:
            description = (
                f"You had {count} tactical oversights across analyzed games "
                f"({blunder_count} blunders, {mistake_count} mistakes). "
                f"Examples: {example_text}."
            )

        weaknesses.append({
            "name": display_name,
            "motif": motif,
            "description": description,
            "frequency": count,
            "severity": severity,
            "phase": "all",
            "examples": [
                {
                    "opponent": e.get("game_opponent"),
                    "move": e.get("move_number"),
                    "played": e.get("played_move"),
                    "best": e.get("best_move"),
                    "eval_drop": e.get("eval_drop"),
                    "phase": e.get("phase"),
                }
                for e in examples[:3]
            ],
        })

    # --- Step 3: Phase-based weaknesses (as additional context if motif list < 3) ---
    # Opening-specific: flag specific openings with high error rates
    opening_mistakes = phase_mistakes.get("opening", [])
    if len(opening_mistakes) >= 2 and len(weaknesses) < 5:
        op_blunders = sum(1 for m in opening_mistakes if m.get("classification") in ("blunder", "mistake"))
        severity = "high" if op_blunders >= 3 else "medium"
        examples = sorted(opening_mistakes, key=lambda x: x.get("eval_drop", 0), reverse=True)[:3]
        # Group by opening name
        op_names: dict[str, int] = defaultdict(int)
        for m in opening_mistakes:
            op_name = m.get("opening_name") or "unknown opening"
            op_names[op_name] += 1
        top_op = sorted(op_names.items(), key=lambda x: x[1], reverse=True)[:2]
        op_name_str = " and ".join(f"{n} ({c}x)" for n, c in top_op)
        example_refs = [_format_motif_example(e) for e in examples[:2]]

        weaknesses.append({
            "name": "Opening preparation gaps",
            "motif": "opening_errors",
            "description": (
                f"You made {len(opening_mistakes)} errors in the opening phase "
                f"(moves 1-10), most frequently in: {op_name_str}. "
                f"Examples: {'; '.join(example_refs)}."
            ),
            "frequency": len(opening_mistakes),
            "severity": severity,
            "phase": "opening",
            "examples": [
                {
                    "opponent": e.get("game_opponent"),
                    "move": e.get("move_number"),
                    "played": e.get("played_move"),
                    "best": e.get("best_move"),
                    "eval_drop": e.get("eval_drop"),
                    "phase": "opening",
                }
                for e in examples[:3]
            ],
        })

    # Endgame technique
    endgame_mistakes = phase_mistakes.get("endgame", [])
    if len(endgame_mistakes) >= 2 and len(weaknesses) < 5:
        eg_blunders = sum(1 for m in endgame_mistakes if m.get("classification") == "blunder")
        severity = "high" if eg_blunders >= 2 else "medium"
        examples = sorted(endgame_mistakes, key=lambda x: x.get("eval_drop", 0), reverse=True)[:3]
        example_refs = [_format_motif_example(e) for e in examples[:2]]

        weaknesses.append({
            "name": "Endgame technique",
            "motif": "endgame_errors",
            "description": (
                f"You made {len(endgame_mistakes)} errors in endgame positions "
                f"({eg_blunders} blunders). "
                f"Examples: {'; '.join(example_refs)}."
            ),
            "frequency": len(endgame_mistakes),
            "severity": severity,
            "phase": "endgame",
            "examples": [
                {
                    "opponent": e.get("game_opponent"),
                    "move": e.get("move_number"),
                    "played": e.get("played_move"),
                    "best": e.get("best_move"),
                    "eval_drop": e.get("eval_drop"),
                    "phase": "endgame",
                }
                for e in examples[:3]
            ],
        })

    # Sort by frequency descending and return top 5
    weaknesses.sort(key=lambda w: (w["frequency"], w["severity"] == "high"), reverse=True)
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
    """Select 5-8 most instructive mistake examples, annotated with detected motif."""
    # Sort by eval_drop descending for most dramatic
    sorted_mistakes = sorted(
        all_mistakes, key=lambda m: m.get("eval_drop", 0), reverse=True
    )

    # Pick diverse phases and motifs
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

        motif = m.get("_motif") or _detect_tactical_motif(
            m.get("fen", ""),
            m.get("best_move", ""),
            m.get("player_color", "white"),
        )

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
            "motif": motif,
            "motif_label": _MOTIF_DISPLAY.get(motif, "Tactical oversight"),
        })

    return selected


def _generate_recommendations(
    weaknesses: list[dict],
    phase_distribution: dict[str, dict],
    color_comparison: dict[str, dict],
    summary: dict,
) -> list[dict[str, Any]]:
    """Generate specific training recommendations based on detected tactical motifs."""
    recommendations: list[dict[str, Any]] = []
    seen_titles: set[str] = set()

    for w in weaknesses[:4]:
        motif = w.get("motif", "")
        name = w.get("name", "")
        freq = w.get("frequency", 0)
        severity = w.get("severity", "medium")
        priority = "high" if severity == "high" else "medium"

        if motif in _MOTIF_ADVICE:
            advice = _MOTIF_ADVICE[motif]
            display = _MOTIF_DISPLAY.get(motif, name)

            if motif == "hanging_piece":
                title = "Train hanging-piece awareness"
                description = (
                    f"You missed free material {freq} times in analyzed games. "
                    f"{advice}"
                )
            elif motif == "missed_checkmate":
                title = "Daily mate-finding practice"
                description = (
                    f"You missed checkmate {freq} time{'s' if freq > 1 else ''} — "
                    f"this is critical. {advice}"
                )
            elif motif == "back_rank_mate":
                title = "Eliminate back-rank vulnerabilities"
                description = (
                    f"You missed {freq} back-rank opportunities and may have been "
                    f"vulnerable to them yourself. {advice}"
                )
            elif "_fork" in motif:
                piece = motif.replace("_fork", "")
                title = f"Practice {piece} fork puzzles"
                description = (
                    f"You missed {piece} forks {freq} time{'s' if freq > 1 else ''}. "
                    f"{advice}"
                )
            elif motif == "discovered_attack":
                title = "Train discovered attack patterns"
                description = (
                    f"You missed {freq} discovered attack{'s' if freq > 1 else ''}. "
                    f"{advice}"
                )
            elif motif == "pin":
                title = "Practice pin and skewer puzzles"
                description = (
                    f"You missed {freq} pin opportunity{'ies' if freq > 1 else 'y'}. "
                    f"{advice}"
                )
            elif motif == "check_forcing":
                title = "Train forcing sequences (checks & captures)"
                description = (
                    f"You missed {freq} forcing check{'s' if freq > 1 else ''} that "
                    f"would have changed the outcome. {advice}"
                )
            elif motif == "opening_errors":
                title = "Fix your opening preparation"
                description = (
                    f"You made {freq} errors in the first 10 moves. "
                    "Study the key ideas of your chosen openings rather than memorizing long lines. "
                    "Focus especially on piece development, king safety, and central control."
                )
                priority = "medium"
            elif motif == "endgame_errors":
                title = "Study endgame fundamentals"
                description = (
                    f"You made {freq} endgame errors. "
                    "Focus on king activity, pawn promotion technique, and basic rook endgames. "
                    "Lichess.org/practice has free endgame training."
                )
            else:
                title = "Daily tactical training"
                description = (
                    f"You had {freq} tactical oversights. {advice}"
                )

            if title not in seen_titles:
                seen_titles.add(title)
                recommendations.append({
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "related_weakness": name,
                })

    # Color-specific recommendation
    white_data = color_comparison.get("white", {})
    black_data = color_comparison.get("black", {})
    w_wr = white_data.get("win_rate", 50)
    b_wr = black_data.get("win_rate", 50)
    if abs(w_wr - b_wr) > 15 and len(recommendations) < 5:
        weaker = "black" if b_wr < w_wr else "white"
        title = f"Strengthen your {weaker} repertoire"
        if title not in seen_titles:
            seen_titles.add(title)
            recommendations.append({
                "title": title,
                "description": (
                    f"Your win rate as {weaker} is {min(w_wr, b_wr):.1f}% vs "
                    f"{max(w_wr, b_wr):.1f}% as {'white' if weaker == 'black' else 'black'}. "
                    f"This gap ({abs(w_wr - b_wr):.1f}%) suggests a specific problem with your "
                    f"{weaker} openings. Review the worst-performing openings in your stats and "
                    "consider replacing or studying them deeply."
                ),
                "priority": "medium",
                "related_weakness": f"{weaker.capitalize()} performance",
            })

    # Fallback general recommendation
    if len(recommendations) < 2:
        recommendations.append({
            "title": "Analyze your games regularly",
            "description": (
                f"Your average accuracy is {summary.get('avg_accuracy', 0)}%. "
                "Review each game after playing, identify the key turning point, "
                "and try to understand the best continuation."
            ),
            "priority": "high" if summary.get("avg_accuracy", 100) < 70 else "medium",
            "related_weakness": "General improvement",
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

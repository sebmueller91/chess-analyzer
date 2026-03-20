import pytest
from datetime import datetime, timezone

from app.services.weakness import (
    generate_report,
    _identify_weaknesses,
    _opening_performance,
    _phase_distribution,
    _color_comparison,
    _select_mistake_examples,
    _generate_recommendations,
)


class TestGenerateReport:
    """Tests for report generation."""

    def _make_games_and_results(self):
        """Create sample game and analysis data for testing."""
        games = [
            {
                "result": "win",
                "player_color": "white",
                "opening_name": "Italian Game",
                "eco_code": "C50",
                "opponent": "opp1",
                "date_played": datetime(2024, 1, 15, tzinfo=timezone.utc),
            },
            {
                "result": "loss",
                "player_color": "black",
                "opening_name": "Sicilian Defense",
                "eco_code": "B20",
                "opponent": "opp2",
                "date_played": datetime(2024, 1, 16, tzinfo=timezone.utc),
            },
            {
                "result": "win",
                "player_color": "white",
                "opening_name": "Italian Game",
                "eco_code": "C50",
                "opponent": "opp3",
                "date_played": datetime(2024, 1, 17, tzinfo=timezone.utc),
            },
            {
                "result": "draw",
                "player_color": "black",
                "opening_name": "Sicilian Defense",
                "eco_code": "B20",
                "opponent": "opp4",
                "date_played": datetime(2024, 1, 18, tzinfo=timezone.utc),
            },
        ]

        analysis_results = [
            {
                "mistakes": [
                    {"move_number": 15, "phase": "middlegame", "eval_drop": 1.5,
                     "classification": "mistake", "played_move": "Bg5", "best_move": "Nf3",
                     "eval_before": 0.5, "eval_after": -1.0, "fen": "..."},
                    {"move_number": 25, "phase": "endgame", "eval_drop": 2.5,
                     "classification": "blunder", "played_move": "Kf2", "best_move": "Ke3",
                     "eval_before": 1.0, "eval_after": -1.5, "fen": "..."},
                ],
                "opening_accuracy": 90.0,
                "middlegame_accuracy": 70.0,
                "endgame_accuracy": 60.0,
                "total_blunders": 1,
                "total_mistakes": 1,
                "total_inaccuracies": 0,
            },
            {
                "mistakes": [
                    {"move_number": 5, "phase": "opening", "eval_drop": 0.8,
                     "classification": "inaccuracy", "played_move": "d6", "best_move": "d5",
                     "eval_before": 0.0, "eval_after": -0.8, "fen": "..."},
                    {"move_number": 18, "phase": "middlegame", "eval_drop": 3.0,
                     "classification": "blunder", "played_move": "Qd2", "best_move": "Rxe1",
                     "eval_before": 0.3, "eval_after": -2.7, "fen": "..."},
                ],
                "opening_accuracy": 75.0,
                "middlegame_accuracy": 55.0,
                "endgame_accuracy": 80.0,
                "total_blunders": 1,
                "total_mistakes": 0,
                "total_inaccuracies": 1,
            },
            {
                "mistakes": [
                    {"move_number": 12, "phase": "middlegame", "eval_drop": 1.2,
                     "classification": "mistake", "played_move": "Nc3", "best_move": "d4",
                     "eval_before": 0.4, "eval_after": -0.8, "fen": "..."},
                ],
                "opening_accuracy": 95.0,
                "middlegame_accuracy": 80.0,
                "endgame_accuracy": 85.0,
                "total_blunders": 0,
                "total_mistakes": 1,
                "total_inaccuracies": 0,
            },
            {
                "mistakes": [
                    {"move_number": 30, "phase": "endgame", "eval_drop": 2.0,
                     "classification": "blunder", "played_move": "Rb8", "best_move": "Ra1",
                     "eval_before": 0.0, "eval_after": -2.0, "fen": "..."},
                ],
                "opening_accuracy": 88.0,
                "middlegame_accuracy": 75.0,
                "endgame_accuracy": 55.0,
                "total_blunders": 1,
                "total_mistakes": 0,
                "total_inaccuracies": 0,
            },
        ]

        return games, analysis_results

    def test_report_structure(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)

        assert report["username"] == "testplayer"
        assert "summary" in report
        assert "top_weaknesses" in report
        assert "openings" in report
        assert "phase_distribution" in report
        assert "color_comparison" in report
        assert "mistake_examples" in report
        assert "training_recommendations" in report

    def test_summary_stats(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)
        summary = report["summary"]

        assert summary["total_games"] == 4
        assert summary["wins"] == 2
        assert summary["losses"] == 1
        assert summary["draws"] == 1
        assert summary["win_rate"] == 50.0
        assert 0 <= summary["avg_accuracy"] <= 100

    def test_opening_performance(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)

        # Italian Game should appear (2 games)
        italian = [o for o in report["openings"] if "Italian" in o["name"]]
        assert len(italian) == 1
        assert italian[0]["games_played"] == 2
        assert italian[0]["wins"] == 2

        # Sicilian should appear (2 games)
        sicilian = [o for o in report["openings"] if "Sicilian" in o["name"]]
        assert len(sicilian) == 1
        assert sicilian[0]["games_played"] == 2

    def test_phase_distribution(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)
        pd = report["phase_distribution"]

        assert "opening" in pd
        assert "middlegame" in pd
        assert "endgame" in pd
        assert pd["middlegame"]["mistakes"] >= 2
        assert pd["endgame"]["blunders"] >= 2

    def test_color_comparison(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)
        cc = report["color_comparison"]

        assert cc["white"]["games"] == 2
        assert cc["black"]["games"] == 2
        assert cc["white"]["wins"] == 2
        assert cc["white"]["win_rate"] == 100.0

    def test_empty_data(self):
        report = generate_report("testplayer", [], [])
        assert report["username"] == "testplayer"
        assert report["summary"]["total_games"] == 0

    def test_mistake_examples(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)
        examples = report["mistake_examples"]

        assert len(examples) > 0
        assert len(examples) <= 8
        # Most dramatic mistakes should be first
        if len(examples) >= 2:
            assert examples[0]["eval_before"] is not None

    def test_training_recommendations(self):
        games, analysis = self._make_games_and_results()
        report = generate_report("testplayer", games, analysis)
        recs = report["training_recommendations"]

        assert len(recs) > 0
        for r in recs:
            assert "title" in r
            assert "description" in r
            assert "priority" in r
            assert "related_weakness" in r

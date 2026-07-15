"""Tests for rule-based insights (explainability, confidence, scenarios)."""

from __future__ import annotations

from app.services.analytics import build_comparison, build_profile
from app.services.insights import (
    annotate_similar_players,
    build_confidence,
    build_explainability,
    build_recommendation,
    build_strengths_and_risks,
    value_alternatives,
)
from tests.conftest import make_player


class TestConfidence:
    def test_low_minutes_adds_reason(self) -> None:
        player = make_player(1, "Low", minutes_played=200, matches_played=5)
        peers = [
            player,
            make_player(2, "A", minutes_played=2000),
            make_player(3, "B", minutes_played=1800),
        ]
        assessment = build_confidence(player, peers, len(peers))
        assert assessment.level == "low"
        assert any("minutes" in r.lower() for r in assessment.reasons)
        assert any("matches" in r.lower() for r in assessment.reasons)


class TestExplainability:
    def test_star_striker_gets_performance_insights(self) -> None:
        star = make_player(
            1,
            "Star",
            goals=30,
            goals_per90=1.2,
            assists_per90=0.3,
            market_value_eur=80_000_000,
            age=22,
            minutes_played=2500,
        )
        peers = [
            star,
            make_player(2, "A", goals=5, goals_per90=0.2),
            make_player(3, "B", goals=3, goals_per90=0.1),
        ]
        profile = build_profile(star, peers)
        assert len(profile.explainability) >= 2
        assert any("goal" in i.lower() for i in profile.explainability)


class TestStrengthsAndRisks:
    def test_profile_includes_summary_lists(self) -> None:
        star = make_player(1, "Star", goals=25, goals_per90=1.0)
        peers = [star, make_player(2, "A", goals=2, goals_per90=0.1)]
        profile = build_profile(star, peers)
        assert len(profile.strengths) >= 1
        assert isinstance(profile.risks, list)


class TestValueAlternatives:
    def test_flags_cheaper_similar_players(self) -> None:
        target = make_player(1, "Target", market_value_eur=50_000_000, goals=20, goals_per90=0.8)
        cheap = make_player(2, "Cheap", market_value_eur=5_000_000, goals=18, goals_per90=0.75)
        pricey = make_player(3, "Pricey", market_value_eur=80_000_000, goals=19, goals_per90=0.78)
        profile = build_profile(target, [target, cheap, pricey])
        cheaper = [p for p in profile.similar_players if p.lower_market_value]
        assert len(cheaper) >= 1
        assert profile.value_alternatives[0].lower_market_value is True


class TestRecommendation:
    def test_elite_young_player_strong_signing(self) -> None:
        star = make_player(
            1,
            "Star",
            goals=25,
            goals_per90=1.0,
            assists_per90=0.4,
            age=22,
            minutes_played=2500,
            matches_played=28,
        )
        peers = [
            star,
            *[make_player(i, f"P{i}", goals=3, goals_per90=0.1) for i in range(2, 55)],
        ]
        profile = build_profile(star, peers)
        assert profile.recommendation is not None
        assert profile.recommendation.verdict in ("strong_signing", "good_signing")
        assert len(profile.recommendation.reasons) >= 1


class TestTrends:
    def test_hot_form_trends_up(self) -> None:
        hot = make_player(
            1,
            "Hot",
            goals_per90=0.4,
            last5_goals_per90=1.0,
            last5_goals=5,
            last5_matches=5,
            assists_per90=0.1,
            last5_assists_per90=0.1,
        )
        peers = [hot, make_player(2, "Other", goals_per90=0.3)]
        profile = build_profile(hot, peers)
        finishing = next((t for t in profile.trends if t.label == "Finishing"), None)
        assert finishing is not None
        assert finishing.direction == "up"

    def test_comparison_includes_scenarios(self) -> None:
        young = make_player(1, "Young", age=21, goals=15, goals_per90=0.7, minutes_played=2200)
        veteran = make_player(2, "Vet", age=33, goals=12, goals_per90=0.5, minutes_played=2100)
        peers = [young, veteran, make_player(3, "Other", goals=5)]
        comparison = build_comparison(young, peers, veteran, peers)
        assert comparison.scenario_one is not None
        assert comparison.scenario_two is not None
        assert comparison.scenario_one.upside in ("higher", "lower", "similar")

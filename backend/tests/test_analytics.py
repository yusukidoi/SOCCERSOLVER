"""Tests for the analytics business logic (percentiles and comparisons)."""

from __future__ import annotations

from app.services.analytics import (
    build_comparison,
    build_profile,
    metrics_for_comparison,
    metrics_for_position,
    peer_confidence,
    percentile_rank,
)
from tests.conftest import make_player


class TestPercentileRank:
    def test_empty_population_returns_zero(self) -> None:
        assert percentile_rank(5.0, []) == 0

    def test_best_value_is_top_percentile(self) -> None:
        assert percentile_rank(10.0, [1.0, 2.0, 3.0, 10.0]) == 100

    def test_worst_value_is_low_percentile(self) -> None:
        assert percentile_rank(1.0, [1.0, 2.0, 3.0, 4.0]) == 25

    def test_middle_value(self) -> None:
        assert percentile_rank(3.0, [1.0, 2.0, 3.0, 4.0, 5.0]) == 60

    def test_lower_is_better_inverts_polarity(self) -> None:
        assert percentile_rank(1.0, [1.0, 2.0, 3.0, 4.0], higher_is_better=False) == 100


class TestPeerConfidence:
    def test_high_when_many_peers(self) -> None:
        assert peer_confidence(118) == "high"

    def test_medium_for_moderate_sample(self) -> None:
        assert peer_confidence(30) == "medium"

    def test_low_for_small_sample(self) -> None:
        assert peer_confidence(10) == "low"


class TestPositionMetrics:
    def test_attack_prioritises_goals(self) -> None:
        keys = [m.key for m in metrics_for_position("Attack")]
        assert keys[0] == "goals_per90"

    def test_midfield_prioritises_assists(self) -> None:
        keys = [m.key for m in metrics_for_position("Midfield")]
        assert keys[0] == "assists_per90"

    def test_defender_uses_discipline_metrics(self) -> None:
        keys = [m.key for m in metrics_for_position("Defender")]
        assert "yellow_cards" in keys
        yellow = next(m for m in metrics_for_position("Defender") if m.key == "yellow_cards")
        assert yellow.higher_is_better is False

    def test_cross_position_uses_shared_metrics(self) -> None:
        attack = make_player(1, "A", position="Attack")
        mid = make_player(2, "B", position="Midfield")
        keys = [m.key for m in metrics_for_comparison(attack, mid)]
        assert keys[0] == "minutes_played"


class TestBuildProfile:
    def test_standout_player_ranks_at_the_top(self) -> None:
        star = make_player(1, "Star", goals=30, goals_per90=1.2, market_value_eur=200_000_000)
        peers = [
            star,
            make_player(2, "A", goals=5, goals_per90=0.2, market_value_eur=10_000_000),
            make_player(3, "B", goals=3, goals_per90=0.1, market_value_eur=5_000_000),
        ]
        profile = build_profile(star, peers)

        assert profile.peer_group_size == 3
        assert profile.peer_confidence == "low"
        assert profile.peer_group_label == "Attacks in the Premier League"
        assert profile.market_value_percentile == 100

        goals_metric = next(m for m in profile.metrics if m.key == "goals")
        assert goals_metric.percentile == 100
        assert goals_metric.value == 30.0
        assert goals_metric.peer_average == round((30 + 5 + 3) / 3, 2)


class TestBuildComparison:
    def test_winner_is_decided_per_metric(self) -> None:
        one = make_player(1, "One", goals=20, assists=2)
        two = make_player(2, "Two", goals=10, assists=9)
        comparison = build_comparison(one, [one, two], two, [one, two])

        goals = next(m for m in comparison.metrics if m.key == "goals")
        assists = next(m for m in comparison.metrics if m.key == "assists")
        assert goals.winner == "one"
        assert goals.delta == 10.0
        assert assists.winner == "two"

    def test_equal_values_are_a_tie(self) -> None:
        one = make_player(1, "One", goals=10)
        two = make_player(2, "Two", goals=10)
        comparison = build_comparison(one, [one, two], two, [one, two])
        goals = next(m for m in comparison.metrics if m.key == "goals")
        assert goals.winner == "tie"
        assert goals.delta == 0.0

    def test_cross_position_sets_note(self) -> None:
        one = make_player(1, "Striker", position="Attack")
        two = make_player(2, "Mid", position="Midfield")
        comparison = build_comparison(one, [one, two], two, [one, two])
        assert comparison.comparison_note is not None

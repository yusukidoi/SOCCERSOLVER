"""Tests for the analytics business logic (percentiles and comparisons)."""

from __future__ import annotations

from app.services.analytics import (
    build_comparison,
    build_profile,
    percentile_rank,
)
from tests.conftest import make_player


class TestPercentileRank:
    def test_empty_population_returns_zero(self) -> None:
        assert percentile_rank(5.0, []) == 0

    def test_best_value_is_top_percentile(self) -> None:
        assert percentile_rank(10.0, [1.0, 2.0, 3.0, 10.0]) == 100

    def test_worst_value_is_low_percentile(self) -> None:
        # Only the value itself is at-or-below -> 1/4 = 25.
        assert percentile_rank(1.0, [1.0, 2.0, 3.0, 4.0]) == 25

    def test_middle_value(self) -> None:
        # 3 of 5 values are <= 3.0 -> 60th percentile.
        assert percentile_rank(3.0, [1.0, 2.0, 3.0, 4.0, 5.0]) == 60

    def test_lower_is_better_inverts_polarity(self) -> None:
        # With lower-is-better, the smallest value should rank highest.
        assert percentile_rank(1.0, [1.0, 2.0, 3.0, 4.0], higher_is_better=False) == 100


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
        assert assists.winner == "two"

    def test_equal_values_are_a_tie(self) -> None:
        one = make_player(1, "One", goals=10)
        two = make_player(2, "Two", goals=10)
        comparison = build_comparison(one, [one, two], two, [one, two])
        goals = next(m for m in comparison.metrics if m.key == "goals")
        assert goals.winner == "tie"

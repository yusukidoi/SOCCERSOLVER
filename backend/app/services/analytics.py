"""Business logic: percentiles, peer averages, profiles and comparisons.

These are pure functions. The peer group is passed in (fetched by the API layer
from the repository), which keeps this module free of I/O and easy to unit-test.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.analytics import (
    ComparisonMetric,
    MetricContext,
    PlayerComparison,
    PlayerProfile,
    Winner,
)
from app.models.player import Player


@dataclass(frozen=True)
class MetricDefinition:
    """Describes a metric we contextualise: where to read it and its polarity."""

    key: str
    label: str
    higher_is_better: bool = True


# The metrics shown on the profile radar and the comparison view. All are
# "higher is better" for this offensive-oriented dataset; the polarity flag
# keeps the door open for metrics like cards where lower is better.
METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition("goals_per90", "Goals /90"),
    MetricDefinition("assists_per90", "Assists /90"),
    MetricDefinition("goal_contributions_per90", "G+A /90"),
    MetricDefinition("goals", "Goals"),
    MetricDefinition("assists", "Assists"),
    MetricDefinition("minutes_played", "Minutes"),
)


def _metric_value(player: Player, key: str) -> float:
    return float(getattr(player, key))


def percentile_rank(value: float, population: list[float], higher_is_better: bool = True) -> int:
    """Percentile of ``value`` within ``population`` (0-100, rounded).

    Uses the fraction of peers the player is at least as good as. With
    ``higher_is_better=False`` the polarity is inverted (lower value ranks higher).
    """
    if not population:
        return 0
    if higher_is_better:
        at_or_below = sum(1 for v in population if v <= value)
    else:
        at_or_below = sum(1 for v in population if v >= value)
    return round(at_or_below / len(population) * 100)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_profile(player: Player, peers: list[Player]) -> PlayerProfile:
    """Contextualise a player's metrics against their league + position peers."""
    metrics: list[MetricContext] = []
    for definition in METRICS:
        value = _metric_value(player, definition.key)
        population = [_metric_value(peer, definition.key) for peer in peers]
        metrics.append(
            MetricContext(
                key=definition.key,
                label=definition.label,
                value=round(value, 2),
                peer_average=round(mean(population), 2),
                percentile=percentile_rank(value, population, definition.higher_is_better),
                higher_is_better=definition.higher_is_better,
            )
        )

    market_values = [float(peer.market_value_eur) for peer in peers]
    return PlayerProfile(
        player=player,
        peer_group_label=f"{player.position}s in the {player.league}",
        peer_group_size=len(peers),
        market_value_percentile=percentile_rank(float(player.market_value_eur), market_values),
        metrics=metrics,
    )


def _decide_winner(
    one_value: float, two_value: float, higher_is_better: bool
) -> Winner:
    if one_value == two_value:
        return "tie"
    one_leads = one_value > two_value
    if not higher_is_better:
        one_leads = not one_leads
    return "one" if one_leads else "two"


def build_comparison(
    one: Player,
    one_peers: list[Player],
    two: Player,
    two_peers: list[Player],
) -> PlayerComparison:
    """Compare two players metric by metric, each ranked within their own peers."""
    metrics: list[ComparisonMetric] = []
    for definition in METRICS:
        one_value = _metric_value(one, definition.key)
        two_value = _metric_value(two, definition.key)
        metrics.append(
            ComparisonMetric(
                key=definition.key,
                label=definition.label,
                higher_is_better=definition.higher_is_better,
                one_value=round(one_value, 2),
                two_value=round(two_value, 2),
                one_percentile=percentile_rank(
                    one_value,
                    [_metric_value(p, definition.key) for p in one_peers],
                    definition.higher_is_better,
                ),
                two_percentile=percentile_rank(
                    two_value,
                    [_metric_value(p, definition.key) for p in two_peers],
                    definition.higher_is_better,
                ),
                winner=_decide_winner(one_value, two_value, definition.higher_is_better),
            )
        )

    return PlayerComparison(
        one=one,
        two=two,
        one_market_value_percentile=percentile_rank(
            float(one.market_value_eur), [float(p.market_value_eur) for p in one_peers]
        ),
        two_market_value_percentile=percentile_rank(
            float(two.market_value_eur), [float(p.market_value_eur) for p in two_peers]
        ),
        metrics=metrics,
    )

"""Business logic: percentiles, peer averages, profiles and comparisons.

These are pure functions. The peer group is passed in (fetched by the API layer
from the repository), which keeps this module free of I/O and easy to unit-test.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.analytics import (
    ComparisonMetric,
    ConfidenceLevel,
    MetricContext,
    PlayerComparison,
    PlayerProfile,
    SimilarPlayer,
    Winner,
)
from app.models.player import Player
from app.services.insights import (
    annotate_similar_players,
    build_confidence,
    build_explainability,
    build_player_scenario,
    build_recommendation,
    build_strengths_and_risks,
    build_team_fit,
    build_trends,
    value_alternatives,
)

# Minimum peer counts for confidence labelling (percentiles get noisy below this).
CONFIDENCE_HIGH_MIN = 50
CONFIDENCE_MEDIUM_MIN = 20
SIMILAR_PLAYERS_LIMIT = 5


@dataclass(frozen=True)
class MetricDefinition:
    """Describes a metric we contextualise: where to read it and its polarity."""

    key: str
    label: str
    higher_is_better: bool = True


# Position-aware metric sets — each role surfaces what matters most with the
# data we have today. Defenders/GKs lean on minutes and discipline where
# attacking stats are less meaningful.
POSITION_METRICS: dict[str, tuple[MetricDefinition, ...]] = {
    "Attack": (
        MetricDefinition("goals_per90", "Goals /90"),
        MetricDefinition("assists_per90", "Assists /90"),
        MetricDefinition("goal_contributions_per90", "G+A /90"),
        MetricDefinition("goals", "Goals"),
        MetricDefinition("assists", "Assists"),
        MetricDefinition("minutes_played", "Minutes"),
    ),
    "Midfield": (
        MetricDefinition("assists_per90", "Assists /90"),
        MetricDefinition("goal_contributions_per90", "G+A /90"),
        MetricDefinition("assists", "Assists"),
        MetricDefinition("goals_per90", "Goals /90"),
        MetricDefinition("goals", "Goals"),
        MetricDefinition("minutes_played", "Minutes"),
    ),
    "Defender": (
        MetricDefinition("minutes_played", "Minutes"),
        MetricDefinition("yellow_cards", "Yellow cards", higher_is_better=False),
        MetricDefinition("red_cards", "Red cards", higher_is_better=False),
        MetricDefinition("goal_contributions_per90", "G+A /90"),
        MetricDefinition("assists_per90", "Assists /90"),
        MetricDefinition("goals_per90", "Goals /90"),
    ),
    "Goalkeeper": (
        MetricDefinition("minutes_played", "Minutes"),
        MetricDefinition("yellow_cards", "Yellow cards", higher_is_better=False),
        MetricDefinition("red_cards", "Red cards", higher_is_better=False),
        MetricDefinition("assists", "Assists"),
        MetricDefinition("goal_contributions_per90", "G+A /90"),
        MetricDefinition("goals", "Goals"),
    ),
}

# Fallback when position is unknown or for cross-position head-to-head.
DEFAULT_METRICS: tuple[MetricDefinition, ...] = POSITION_METRICS["Midfield"]

SHARED_COMPARISON_METRICS: tuple[MetricDefinition, ...] = (
    MetricDefinition("minutes_played", "Minutes"),
    MetricDefinition("goal_contributions_per90", "G+A /90"),
    MetricDefinition("goals_per90", "Goals /90"),
    MetricDefinition("assists_per90", "Assists /90"),
    MetricDefinition("goals", "Goals"),
    MetricDefinition("assists", "Assists"),
)


def metrics_for_position(position: str) -> tuple[MetricDefinition, ...]:
    """Return the metric set tailored to a broad position."""
    return POSITION_METRICS.get(position, DEFAULT_METRICS)


def metrics_for_comparison(one: Player, two: Player) -> tuple[MetricDefinition, ...]:
    """Same role → position-specific metrics; different roles → shared output set."""
    if one.position == two.position:
        return metrics_for_position(one.position)
    return SHARED_COMPARISON_METRICS


def peer_confidence(peer_group_size: int) -> ConfidenceLevel:
    """Label how trustworthy percentiles are given the peer sample size."""
    if peer_group_size >= CONFIDENCE_HIGH_MIN:
        return "high"
    if peer_group_size >= CONFIDENCE_MEDIUM_MIN:
        return "medium"
    return "low"


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


def _build_metric_contexts(
    player: Player, peers: list[Player], definitions: tuple[MetricDefinition, ...]
) -> list[MetricContext]:
    metrics: list[MetricContext] = []
    for definition in definitions:
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
    return metrics


def _feature_vector(
    target: Player,
    peers: list[Player],
    definitions: tuple[MetricDefinition, ...],
) -> list[float]:
    """Min-max normalise position metrics across the peer group into a 0-1 vector."""
    vector: list[float] = []
    for definition in definitions:
        values = [_metric_value(peer, definition.key) for peer in peers]
        value = _metric_value(target, definition.key)
        low, high = min(values), max(values)
        if high == low:
            normalised = 1.0
        else:
            normalised = (value - low) / (high - low)
        if not definition.higher_is_better:
            normalised = 1.0 - normalised
        vector.append(normalised)
    return vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0.0 or norm_right == 0.0:
        return 0.0
    return dot / (norm_left * norm_right)


def find_similar_players(
    player: Player,
    peers: list[Player],
    limit: int = SIMILAR_PLAYERS_LIMIT,
) -> list[SimilarPlayer]:
    """Rank peers by cosine similarity on position-specific performance metrics."""
    definitions = metrics_for_position(player.position)
    target_vector = _feature_vector(player, peers, definitions)
    scored: list[SimilarPlayer] = []

    for peer in peers:
        if peer.player_id == player.player_id:
            continue
        score = cosine_similarity(target_vector, _feature_vector(peer, peers, definitions))
        scored.append(
            SimilarPlayer(
                player=peer.summary(),
                similarity=round(score * 100),
            )
        )

    scored.sort(key=lambda item: item.similarity, reverse=True)
    return scored[:limit]


def build_profile(player: Player, peers: list[Player]) -> PlayerProfile:
    """Contextualise a player's metrics against their league + position peers."""
    definitions = metrics_for_position(player.position)
    market_values = [float(peer.market_value_eur) for peer in peers]
    peer_group_label = f"{player.position}s in the {player.league}"
    metrics = _build_metric_contexts(player, peers, definitions)
    market_value_percentile = percentile_rank(float(player.market_value_eur), market_values)
    confidence = build_confidence(player, peers, len(peers))
    strengths, risks = build_strengths_and_risks(player, metrics, confidence)
    similar = annotate_similar_players(
        player, find_similar_players(player, peers)
    )

    return PlayerProfile(
        player=player,
        peer_group_label=peer_group_label,
        peer_group_size=len(peers),
        peer_confidence=confidence.level,
        confidence=confidence,
        market_value_percentile=market_value_percentile,
        metrics=metrics,
        explainability=build_explainability(
            player, metrics, market_value_percentile, peer_group_label
        ),
        strengths=strengths,
        risks=risks,
        trends=build_trends(player, metrics),
        team_fit=build_team_fit(player, metrics),
        recommendation=build_recommendation(
            player, metrics, market_value_percentile, confidence, strengths, risks
        ),
        similar_players=similar,
        value_alternatives=value_alternatives(similar),
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
    definitions = metrics_for_comparison(one, two)
    cross_position = one.position != two.position
    metrics: list[ComparisonMetric] = []

    for definition in definitions:
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
                delta=round(abs(one_value - two_value), 2),
            )
        )

    one_mv_pct = percentile_rank(
        float(one.market_value_eur), [float(p.market_value_eur) for p in one_peers]
    )
    two_mv_pct = percentile_rank(
        float(two.market_value_eur), [float(p.market_value_eur) for p in two_peers]
    )
    one_defs = metrics_for_position(one.position)
    two_defs = metrics_for_position(two.position)
    one_metrics = _build_metric_contexts(one, one_peers, one_defs)
    two_metrics = _build_metric_contexts(two, two_peers, two_defs)
    one_conf = build_confidence(one, one_peers, len(one_peers))
    two_conf = build_confidence(two, two_peers, len(two_peers))

    return PlayerComparison(
        one=one,
        two=two,
        one_market_value_percentile=one_mv_pct,
        two_market_value_percentile=two_mv_pct,
        one_peer_group_size=len(one_peers),
        two_peer_group_size=len(two_peers),
        peer_confidence_one=one_conf.level,
        peer_confidence_two=two_conf.level,
        comparison_note=(
            "Cross-position comparison uses shared output metrics."
            if cross_position
            else None
        ),
        scenario_one=build_player_scenario(one, one_metrics, one_mv_pct, one_conf),
        scenario_two=build_player_scenario(two, two_metrics, two_mv_pct, two_conf),
        metrics=metrics,
    )

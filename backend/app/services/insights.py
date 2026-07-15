"""Rule-based insights: explainability, confidence, strengths/risks, trends, team fit.

Derived from season aggregates and peer percentiles — no match-level or tracking data.
Keeps logic pure and testable; the API layer supplies peers.
"""

from __future__ import annotations

from typing import Literal

from app.models.analytics import (
    ConfidenceAssessment,
    ConfidenceLevel,
    MetricContext,
    PlayerScenario,
    Recommendation,
    SimilarPlayer,
    TeamFitRating,
    TrendItem,
)
from app.models.player import Player

CONFIDENCE_HIGH_MIN = 50
CONFIDENCE_MEDIUM_MIN = 20

FitRating = Literal["excellent", "high", "medium", "low"]
TrendDirection = Literal["up", "down", "stable"]
RecommendationVerdict = Literal["strong_signing", "good_signing", "monitor", "caution"]

MINUTES_LOW_RATIO = 0.5
MATCHES_LOW_THRESHOLD = 8
STRENGTH_PERCENTILE_MIN = 70
RISK_PERCENTILE_MAX = 35
INSIGHT_PERCENTILE_MIN = 75


def _peer_confidence(peer_group_size: int) -> ConfidenceLevel:
    if peer_group_size >= CONFIDENCE_HIGH_MIN:
        return "high"
    if peer_group_size >= CONFIDENCE_MEDIUM_MIN:
        return "medium"
    return "low"


def _effective_percentile(metric: MetricContext) -> int:
    """Percentile where higher always means stronger for this player."""
    if metric.higher_is_better:
        return metric.percentile
    return 100 - metric.percentile


def _pct_above_peer(metric: MetricContext) -> int | None:
    if metric.peer_average == 0:
        return None
    delta = (metric.value - metric.peer_average) / metric.peer_average * 100
    return round(delta)


def _strength_label(metric: MetricContext) -> str:
    above = _pct_above_peer(metric)
    if above is not None and abs(above) >= 10:
        direction = "above" if above > 0 else "below"
        return f"{metric.label} ({above:+d}% vs peers)"
    return metric.label


def build_confidence(player: Player, peers: list[Player], peer_group_size: int) -> ConfidenceAssessment:
    """Confidence level plus human-readable data-quality reasons."""
    level = _peer_confidence(peer_group_size)
    reasons: list[str] = []

    if peer_group_size < CONFIDENCE_MEDIUM_MIN:
        reasons.append(f"Only {peer_group_size} peers in comparison group")
    elif peer_group_size < CONFIDENCE_HIGH_MIN:
        reasons.append(f"Moderate peer sample ({peer_group_size} players)")

    if player.matches_played < MATCHES_LOW_THRESHOLD:
        reasons.append(f"Only {player.matches_played} matches in season sample")

    if player.last5_matches < 5:
        reasons.append(f"Last-5 form based on {player.last5_matches} recent appearances")

    peer_minutes = [float(p.minutes_played) for p in peers]
    avg_minutes = sum(peer_minutes) / len(peer_minutes) if peer_minutes else 0.0
    if avg_minutes > 0 and player.minutes_played < avg_minutes * MINUTES_LOW_RATIO:
        reasons.append(
            f"Limited minutes ({player.minutes_played:,} vs peer avg {round(avg_minutes):,})"
        )

    if player.progressive_passes_per90 == 0 and player.position in ("Midfield", "Defender"):
        reasons.append("Missing advanced stats (progressive passes / defensive actions)")

    if player.progressive_passes_per90 == 0 and player.defensive_actions_per90 == 0:
        reasons.append("No tracking data — using output and appearance logs only")
    else:
        reasons.append("Advanced stats available for subset of metrics")

    if not reasons:
        reasons.append("Large peer group with full-season minutes")

    return ConfidenceAssessment(level=level, reasons=reasons)


def build_explainability(
    player: Player,
    metrics: list[MetricContext],
    market_value_percentile: int,
    peer_group_label: str,
) -> list[str]:
    """Why this player ranks well — top percentile drivers in plain language."""
    insights: list[str] = []

    ranked = sorted(metrics, key=_effective_percentile, reverse=True)
    for metric in ranked[:3]:
        eff = _effective_percentile(metric)
        if eff < INSIGHT_PERCENTILE_MIN:
            continue
        above = _pct_above_peer(metric)
        if above is not None and above >= 10:
            insights.append(f"Strong {metric.label.lower()} ({above:+d}% vs {peer_group_label})")
        else:
            insights.append(
                f"Elite {metric.label.lower()} — {eff}th percentile vs {peer_group_label}"
            )

    if market_value_percentile >= INSIGHT_PERCENTILE_MIN:
        insights.append(
            f"High market value — {market_value_percentile}th percentile in peer group"
        )

    if player.age is not None:
        if player.age <= 23:
            insights.append("Age profile fits long-term investment (under 24)")
        elif player.age <= 27:
            insights.append("Prime age window with peak-performance potential")

    if player.minutes_played >= 2000:
        insights.append("Consistent availability — 2,000+ minutes this season")

    if player.last5_goal_contributions >= 3 and player.last5_matches >= 3:
        insights.append(
            f"Hot recent form — {player.last5_goal_contributions} G+A in last {player.last5_matches} matches"
        )

    if player.progressive_passes_per90 > 0:
        prog_metric = next((m for m in metrics if m.key == "progressive_passes_per90"), None)
        if prog_metric and _effective_percentile(prog_metric) >= INSIGHT_PERCENTILE_MIN:
            insights.append("Strong progressive passing vs midfield peers")

    if player.defensive_actions_per90 > 0:
        def_metric = next((m for m in metrics if m.key == "defensive_actions_per90"), None)
        if def_metric and _effective_percentile(def_metric) >= INSIGHT_PERCENTILE_MIN:
            insights.append("High defensive contribution vs peers")

    return insights[:6]


def build_strengths_and_risks(
    player: Player,
    metrics: list[MetricContext],
    confidence: ConfidenceAssessment,
) -> tuple[list[str], list[str]]:
    """Top strengths and risks for a quick sporting-director summary."""
    ranked = sorted(metrics, key=_effective_percentile, reverse=True)

    strengths = [
        _strength_label(m)
        for m in ranked
        if _effective_percentile(m) >= STRENGTH_PERCENTILE_MIN
    ][:3]

    risks = [
        _strength_label(m)
        for m in sorted(metrics, key=_effective_percentile)
        if _effective_percentile(m) <= RISK_PERCENTILE_MAX
    ][:3]

    for reason in confidence.reasons:
        if "matches" in reason.lower() or "minutes" in reason.lower():
            risks.append(reason)
        if "tracking" in reason.lower() or "aggregates" in reason.lower():
            if reason not in risks:
                risks.append(reason)

    if player.age is not None and player.age >= 32:
        risks.append("Advanced age — shorter resale horizon")

    return strengths[:3], risks[:4]


def _form_direction(season_rate: float, last5_rate: float, min_delta: float = 0.15) -> TrendDirection | None:
    if season_rate <= 0 and last5_rate <= 0:
        return None
    baseline = season_rate if season_rate > 0 else last5_rate
    if last5_rate >= baseline * (1 + min_delta):
        return "up"
    if last5_rate <= baseline * (1 - min_delta):
        return "down"
    return "stable"


def build_trends(player: Player, metrics: list[MetricContext]) -> list[TrendItem]:
    """Last-5-match form vs season rate, plus market-value positioning."""
    trends: list[TrendItem] = []

    def add(label: str, direction: TrendDirection, detail: str) -> None:
        trends.append(TrendItem(label=label, direction=direction, detail=detail))

    if player.last5_matches > 0:
        finishing = _form_direction(player.goals_per90, player.last5_goals_per90)
        if finishing:
            detail = (
                f"{player.last5_goals} goals in last {player.last5_matches} "
                f"({player.last5_goals_per90:.2f}/90 vs {player.goals_per90:.2f}/90 season)"
            )
            add("Finishing", finishing, detail)

        creation = _form_direction(player.assists_per90, player.last5_assists_per90)
        if creation:
            detail = (
                f"{player.last5_assists} assists in last {player.last5_matches} "
                f"({player.last5_assists_per90:.2f}/90 vs {player.assists_per90:.2f}/90 season)"
            )
            add("Chance creation", creation, detail)

        contrib = _form_direction(
            player.goal_contributions_per90, player.last5_goal_contributions_per90
        )
        if contrib and contrib != finishing and contrib != creation:
            add(
                "Goal contributions",
                contrib,
                f"{player.last5_goal_contributions} G+A in last {player.last5_matches} matches",
            )

    if player.highest_market_value_eur > 0:
        peak = player.market_value_pct_of_peak
        if peak >= 95:
            add("Market value", "stable", "At or near career-high valuation")
        elif peak <= 70 and player.age is not None and player.age <= 27:
            add(
                "Market value",
                "up",
                f"Trading at {peak}% of peak — room to recover if form holds",
            )
        elif peak <= 60:
            add("Market value", "down", f"Currently {peak}% of recorded peak value")

    by_key = {m.key: m for m in metrics}
    minutes = by_key.get("minutes_played")
    if minutes and player.last5_minutes > 0:
        last5_share = player.last5_minutes / player.minutes_played if player.minutes_played else 0
        expected_share = min(player.last5_matches, 5) / max(player.matches_played, 1)
        if last5_share >= expected_share * 1.2:
            add("Playing time", "up", "Recent minutes share above season average")
        elif last5_share <= expected_share * 0.7:
            add("Playing time", "down", "Fewer minutes in recent matches")

    return trends[:6]


def _fit_rating(score: float) -> FitRating:
    if score >= 0.75:
        return "excellent"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def build_team_fit(player: Player, metrics: list[MetricContext]) -> list[TeamFitRating]:
    """Playing-style fit scores from available output and availability metrics."""
    by_key = {m.key: m for m in metrics}
    eff = {k: _effective_percentile(v) / 100 for k, v in by_key.items()}

    minutes = eff.get("minutes_played", 0.5)
    g90 = eff.get("goals_per90", 0.0)
    a90 = eff.get("assists_per90", 0.0)
    ga90 = eff.get("goal_contributions_per90", 0.0)
    discipline = eff.get("yellow_cards", 0.5)

    if player.position == "Attack":
        possession = 0.45 * a90 + 0.35 * ga90 + 0.2 * g90
        counter = 0.5 * g90 + 0.3 * minutes + 0.2 * (1 - discipline)
        press = 0.5 * minutes + 0.3 * g90 + 0.2 * ga90
    elif player.position == "Midfield":
        possession = 0.5 * a90 + 0.3 * ga90 + 0.2 * minutes
        counter = 0.4 * g90 + 0.35 * minutes + 0.25 * ga90
        press = 0.45 * minutes + 0.35 * discipline + 0.2 * ga90
    elif player.position == "Defender":
        possession = 0.4 * a90 + 0.35 * minutes + 0.25 * discipline
        counter = 0.45 * minutes + 0.35 * discipline + 0.2 * ga90
        press = 0.5 * minutes + 0.3 * discipline + 0.2 * ga90
    else:
        possession = 0.5 * minutes + 0.5 * discipline
        counter = 0.5 * minutes + 0.5 * discipline
        press = 0.6 * minutes + 0.4 * discipline

    return [
        TeamFitRating(style="Possession", rating=_fit_rating(possession)),
        TeamFitRating(style="Counter attack", rating=_fit_rating(counter)),
        TeamFitRating(style="High press", rating=_fit_rating(press)),
    ]


def build_recommendation(
    player: Player,
    metrics: list[MetricContext],
    market_value_percentile: int,
    confidence: ConfidenceAssessment,
    strengths: list[str],
    risks: list[str],
) -> Recommendation:
    """Signing verdict with reasons — built for trust, not a single score."""
    avg_perf = sum(_effective_percentile(m) for m in metrics) / len(metrics) if metrics else 50
    reasons: list[str] = []
    verdict: RecommendationVerdict = "monitor"

    if player.age is not None and player.age <= 26:
        reasons.append("Young with development runway")
    if avg_perf >= 65:
        reasons.append("Above-average output vs position peers")
    if market_value_percentile <= 50 and avg_perf >= 55:
        reasons.append("Affordable relative to peer valuations")
    if strengths:
        reasons.append(f"Standout: {strengths[0].split('(')[0].strip().lower()}")

    risk_count = len([r for r in risks if "sample" in r.lower() or "minutes" in r.lower()])
    if confidence.level == "low" or risk_count >= 2:
        verdict = "caution"
        if confidence.level == "low":
            reasons.append("Low data confidence — validate before committing")
    elif avg_perf >= 75 and confidence.level != "low" and len(strengths) >= 2:
        verdict = "strong_signing"
        reasons.append("Multiple elite metrics with reliable peer context")
    elif avg_perf >= 55 and len(risks) <= 2:
        verdict = "good_signing"
    else:
        verdict = "monitor"
        reasons.append("Promising but needs more evidence")

    if player.age is not None and player.age >= 32 and verdict == "strong_signing":
        verdict = "good_signing"

    return Recommendation(verdict=verdict, reasons=reasons[:5])


def annotate_similar_players(
    target: Player, similar: list[SimilarPlayer]
) -> list[SimilarPlayer]:
    """Flag similar profiles with lower market value — recruitment alternatives."""
    annotated: list[SimilarPlayer] = []
    for item in similar:
        lower = item.player.market_value_eur < target.market_value_eur
        savings = target.market_value_eur - item.player.market_value_eur if lower else None
        annotated.append(
            item.model_copy(
                update={
                    "lower_market_value": lower,
                    "value_savings_eur": savings,
                }
            )
        )
    return annotated


def value_alternatives(similar: list[SimilarPlayer]) -> list[SimilarPlayer]:
    """Similar players who cost less — sorted by similarity then savings."""
    cheaper = [p for p in similar if p.lower_market_value]
    return sorted(
        cheaper,
        key=lambda p: (p.similarity, p.value_savings_eur or 0),
        reverse=True,
    )


def build_player_scenario(
    player: Player,
    metrics: list[MetricContext],
    market_value_percentile: int,
    confidence: ConfidenceAssessment,
) -> PlayerScenario:
    """Upside / risk / consistency framing for investment decisions."""
    eff = [_effective_percentile(m) for m in metrics]
    avg = sum(eff) / len(eff) if eff else 50
    spread = max(eff) - min(eff) if eff else 0

    upside: Literal["higher", "lower", "similar"] = "similar"
    if player.age is not None and player.age <= 24 and avg >= 55:
        upside = "higher"
    elif player.age is not None and player.age >= 30:
        upside = "lower"

    risk: Literal["higher", "lower", "similar"] = "similar"
    risk_signals = sum(
        1
        for r in confidence.reasons
        if any(w in r.lower() for w in ("only", "limited", "aggregates"))
    )
    if confidence.level == "low" or risk_signals >= 2:
        risk = "higher"
    elif confidence.level == "high" and player.minutes_played >= 1500:
        risk = "lower"

    consistency: Literal["higher", "lower", "similar"] = "similar"
    if spread <= 25 and avg >= 45:
        consistency = "higher"
    elif spread >= 45:
        consistency = "lower"

    parts: list[str] = []
    if upside == "higher":
        parts.append("younger profile with growth potential")
    elif upside == "lower":
        parts.append("limited upside given age")
    if risk == "higher":
        parts.append("noisier data or smaller sample")
    elif risk == "lower":
        parts.append("stable season minutes")
    if consistency == "higher":
        parts.append("steady across metrics")
    elif consistency == "lower":
        parts.append("peaks in some areas, weak in others")
    if market_value_percentile >= 80:
        parts.append("premium valuation")

    summary = "; ".join(parts).capitalize() + "." if parts else "Balanced profile across dimensions."

    return PlayerScenario(
        upside=upside,
        risk=risk,
        consistency=consistency,
        summary=summary,
    )

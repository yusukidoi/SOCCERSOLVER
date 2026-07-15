"""Response models for analytics: contextualised profiles and comparisons."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.player import Player, PlayerSummary

Winner = Literal["one", "two", "tie"]
ConfidenceLevel = Literal["high", "medium", "low"]
TrendDirection = Literal["up", "down", "stable"]
FitRating = Literal["excellent", "high", "medium", "low"]
RecommendationVerdict = Literal["strong_signing", "good_signing", "monitor", "caution"]
ScenarioLevel = Literal["higher", "lower", "similar"]


class MetricContext(BaseModel):
    """One performance metric placed in context against a peer group."""

    key: str
    label: str
    value: float
    peer_average: float
    percentile: int
    higher_is_better: bool


class SimilarPlayer(BaseModel):
    """A peer with a comparable performance profile."""

    player: PlayerSummary
    similarity: int = Field(ge=0, le=100, description="Cosine similarity vs target, 0-100")
    lower_market_value: bool = Field(
        default=False,
        description="True when this peer costs less than the target player",
    )
    value_savings_eur: int | None = Field(
        default=None,
        description="How much cheaper than the target, when lower_market_value is true",
    )


class ConfidenceAssessment(BaseModel):
    """How much to trust the profile, with explicit data-quality reasons."""

    level: ConfidenceLevel
    reasons: list[str]


class TrendItem(BaseModel):
    """Season indicator — direction inferred from efficiency vs volume gaps."""

    label: str
    direction: TrendDirection
    detail: str | None = None


class TeamFitRating(BaseModel):
    """How well the player suits a playing style (heuristic from output metrics)."""

    style: str
    rating: FitRating


class Recommendation(BaseModel):
    """Signing verdict with reasons — explainable, not just a score."""

    verdict: RecommendationVerdict
    reasons: list[str]


class PlayerScenario(BaseModel):
    """Investment framing: upside, risk, and consistency."""

    upside: ScenarioLevel
    risk: ScenarioLevel
    consistency: ScenarioLevel
    summary: str


class PlayerProfile(BaseModel):
    """A player plus their metrics contextualised within league + position."""

    player: Player
    peer_group_label: str
    peer_group_size: int
    peer_confidence: ConfidenceLevel = Field(
        description="How reliable percentiles are given peer-group sample size"
    )
    confidence: ConfidenceAssessment = Field(
        description="Confidence level with data-quality reasons"
    )
    market_value_percentile: int
    metrics: list[MetricContext]
    explainability: list[str] = Field(
        default_factory=list,
        description="Why this player ranks well — top drivers in plain language",
    )
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    trends: list[TrendItem] = Field(default_factory=list)
    team_fit: list[TeamFitRating] = Field(default_factory=list)
    recommendation: Recommendation | None = None
    similar_players: list[SimilarPlayer] = Field(
        default_factory=list,
        description="Peers with the closest performance profile",
    )
    value_alternatives: list[SimilarPlayer] = Field(
        default_factory=list,
        description="Similar profiles with lower market value — recruitment targets",
    )


class ComparisonMetric(BaseModel):
    """A single metric compared head-to-head between two players."""

    key: str
    label: str
    higher_is_better: bool
    one_value: float
    two_value: float
    one_percentile: int
    two_percentile: int
    winner: Winner
    delta: float = Field(description="Absolute gap between the two values")


class PlayerComparison(BaseModel):
    """Two players side by side with a clear reading of the differences."""

    one: Player
    two: Player
    one_market_value_percentile: int
    two_market_value_percentile: int
    one_peer_group_size: int
    two_peer_group_size: int
    peer_confidence_one: ConfidenceLevel
    peer_confidence_two: ConfidenceLevel
    comparison_note: str | None = Field(
        default=None,
        description="Shown when a cross-position comparison uses shared metrics",
    )
    scenario_one: PlayerScenario | None = None
    scenario_two: PlayerScenario | None = None
    metrics: list[ComparisonMetric]

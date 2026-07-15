"""Response models for analytics: contextualised profiles and comparisons."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.models.player import Player

Winner = Literal["one", "two", "tie"]
ConfidenceLevel = Literal["high", "medium", "low"]


class MetricContext(BaseModel):
    """One performance metric placed in context against a peer group."""

    key: str
    label: str
    value: float
    peer_average: float
    percentile: int
    higher_is_better: bool


class PlayerProfile(BaseModel):
    """A player plus their metrics contextualised within league + position."""

    player: Player
    peer_group_label: str
    peer_group_size: int
    peer_confidence: ConfidenceLevel = Field(
        description="How reliable percentiles are given peer-group sample size"
    )
    market_value_percentile: int
    metrics: list[MetricContext]


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
    metrics: list[ComparisonMetric]

"""Response models for analytics: contextualised profiles and comparisons."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.models.player import Player

Winner = Literal["one", "two", "tie"]


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


class PlayerComparison(BaseModel):
    """Two players side by side with a clear reading of the differences."""

    one: Player
    two: Player
    one_market_value_percentile: int
    two_market_value_percentile: int
    metrics: list[ComparisonMetric]

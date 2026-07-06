"""Pydantic domain models for players."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PlayerBase(BaseModel):
    """Identity and market context shared across responses."""

    player_id: int = Field(..., description="Stable Transfermarkt player id")
    name: str
    position: str = Field(..., description="Broad position: Goalkeeper/Defender/Midfield/Attack")
    sub_position: str = Field(..., description="Detailed position, e.g. Left Winger")
    age: int | None = None
    club: str
    league: str
    market_value_eur: int = Field(..., ge=0, description="Market value in euros")


class PlayerSummary(PlayerBase):
    """Lightweight representation used in search results and pickers."""


class Player(PlayerBase):
    """Full player record including one season of performance metrics."""

    minutes_played: int = Field(..., ge=0)
    matches_played: int = Field(..., ge=0)
    goals: int = Field(..., ge=0)
    assists: int = Field(..., ge=0)
    goal_contributions: int = Field(..., ge=0)
    yellow_cards: int = Field(..., ge=0)
    red_cards: int = Field(..., ge=0)
    goals_per90: float = Field(..., ge=0)
    assists_per90: float = Field(..., ge=0)
    goal_contributions_per90: float = Field(..., ge=0)

    def summary(self) -> PlayerSummary:
        """Project this record onto the lightweight summary model."""
        return PlayerSummary.model_validate(self.model_dump())

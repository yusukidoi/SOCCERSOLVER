"""Shared test helpers."""

from __future__ import annotations

from app.models.player import Player

_DEFAULTS: dict[str, object] = {
    "sub_position": "Centre-Forward",
    "age": 25,
    "club": "Test FC",
    "league": "Premier League",
    "market_value_eur": 1_000_000,
    "minutes_played": 900,
    "matches_played": 10,
    "goals": 0,
    "assists": 0,
    "goal_contributions": 0,
    "yellow_cards": 0,
    "red_cards": 0,
    "goals_per90": 0.0,
    "assists_per90": 0.0,
    "goal_contributions_per90": 0.0,
}


def make_player(player_id: int, name: str, position: str = "Attack", **overrides: object) -> Player:
    """Build a Player with sensible defaults, overriding only what a test cares about."""
    data: dict[str, object] = {
        "player_id": player_id,
        "name": name,
        "position": position,
        **_DEFAULTS,
        **overrides,
    }
    return Player.model_validate(data)

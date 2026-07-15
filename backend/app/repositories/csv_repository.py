"""CSV-backed implementation of :class:`PlayerRepository`.

The dataset is small and read-only, so it is loaded into memory once at
construction and indexed for fast lookup by id and by (league, position).
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from app.models.player import Player
from app.repositories.base import PlayerRepository

# CSV columns that must be parsed as integers / floats.
_INT_FIELDS = frozenset(
    {
        "player_id",
        "market_value_eur",
        "highest_market_value_eur",
        "market_value_pct_of_peak",
        "minutes_played",
        "matches_played",
        "goals",
        "assists",
        "goal_contributions",
        "yellow_cards",
        "red_cards",
        "last5_matches",
        "last5_minutes",
        "last5_goals",
        "last5_assists",
        "last5_goal_contributions",
    }
)
_FLOAT_FIELDS = frozenset(
    {
        "goals_per90",
        "assists_per90",
        "goal_contributions_per90",
        "avg_minutes_per_match",
        "last5_goals_per90",
        "last5_assists_per90",
        "last5_goal_contributions_per90",
        "progressive_passes_per90",
        "defensive_actions_per90",
    }
)


class CsvPlayerRepository(PlayerRepository):
    """Load players from a CSV file and serve them from memory."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path
        self._players: list[Player] = []
        self._by_id: dict[int, Player] = {}
        self._by_league_position: dict[tuple[str, str], list[Player]] = defaultdict(list)
        self._load()

    def _load(self) -> None:
        if not self._csv_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self._csv_path}")
        with self._csv_path.open("r", encoding="utf-8", newline="") as handle:
            for raw in csv.DictReader(handle):
                player = self._parse_row(raw)
                self._players.append(player)
                self._by_id[player.player_id] = player
                key = (player.league, player.position)
                self._by_league_position[key].append(player)

    @staticmethod
    def _parse_row(raw: dict[str, str]) -> Player:
        parsed: dict[str, object] = {}
        for key, value in raw.items():
            if key in _INT_FIELDS:
                parsed[key] = int(value) if value else 0
            elif key in _FLOAT_FIELDS:
                parsed[key] = float(value) if value else 0.0
            elif key == "age":
                parsed[key] = int(value) if value else None
            else:
                parsed[key] = value
        return Player.model_validate(parsed)

    def all(self) -> list[Player]:
        return list(self._players)

    def get(self, player_id: int) -> Player | None:
        return self._by_id.get(player_id)

    def search(self, query: str, limit: int = 20) -> list[Player]:
        needle = query.strip().casefold()
        if not needle:
            return []
        matches = [p for p in self._players if needle in p.name.casefold()]
        # Rank exact prefix matches first, then by market value as a proxy for relevance.
        matches.sort(
            key=lambda p: (not p.name.casefold().startswith(needle), -p.market_value_eur)
        )
        return matches[:limit]

    def filter_by_league_position(self, league: str, position: str) -> list[Player]:
        return list(self._by_league_position.get((league, position), []))

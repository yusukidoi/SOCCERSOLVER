"""Repository interface for player data access.

Endpoints and services depend on this abstraction, never on a concrete data
source. Swapping the CSV for a real database means adding one implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.player import Player


class PlayerRepository(ABC):
    """Read-only access to the player dataset."""

    @abstractmethod
    def all(self) -> list[Player]:
        """Return every player."""

    @abstractmethod
    def get(self, player_id: int) -> Player | None:
        """Return a single player by id, or None if not found."""

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> list[Player]:
        """Return players whose name matches the query, best matches first."""

    @abstractmethod
    def filter_by_league_position(self, league: str, position: str) -> list[Player]:
        """Return players sharing a league and (broad) position — the peer group."""

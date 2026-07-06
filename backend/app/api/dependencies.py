"""Shared FastAPI dependencies.

The repository is built once (dataset loaded into memory) and reused across
requests. Routes depend on the abstract ``PlayerRepository`` type, not the CSV.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.repositories.base import PlayerRepository
from app.repositories.csv_repository import CsvPlayerRepository


@lru_cache
def get_player_repository() -> PlayerRepository:
    """Return the shared, in-memory player repository."""
    return CsvPlayerRepository(get_settings().resolved_csv_path)

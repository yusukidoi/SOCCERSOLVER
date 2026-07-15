"""Tests for the CSV repository's loading, search and filtering."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.repositories.csv_repository import CsvPlayerRepository

_COLUMNS = [
    "player_id", "name", "position", "sub_position", "age", "club", "league",
    "market_value_eur", "highest_market_value_eur", "market_value_pct_of_peak",
    "minutes_played", "matches_played", "avg_minutes_per_match",
    "goals", "assists", "goal_contributions", "yellow_cards", "red_cards",
    "goals_per90", "assists_per90", "goal_contributions_per90",
    "last5_matches", "last5_minutes", "last5_goals", "last5_assists",
    "last5_goal_contributions", "last5_goals_per90", "last5_assists_per90",
    "last5_goal_contributions_per90", "progressive_passes_per90", "defensive_actions_per90",
]

_ROWS = [
    [1, "Bruno Fernandes", "Midfield", "AM", 30, "MUFC", "Premier League", 70000000, 80000000, 88, 3000, 34, 88.2, 8, 10, 18, 5, 0, 0.24, 0.30, 0.54, 5, 450, 2, 3, 5, 0.4, 0.6, 1.0, 0.0, 0.0],
    [2, "Bruno Guimaraes", "Midfield", "CM", 27, "NUFC", "Premier League", 80000000, 85000000, 94, 2800, 32, 87.5, 4, 6, 10, 6, 0, 0.13, 0.19, 0.32, 5, 400, 1, 1, 2, 0.23, 0.23, 0.45, 0.0, 0.0],
    [3, "Rodri", "Midfield", "DM", 28, "MCFC", "Premier League", 110000000, 120000000, 92, 1500, 17, 88.2, 3, 2, 5, 3, 1, 0.18, 0.12, 0.30, 5, 430, 1, 0, 1, 0.21, 0.0, 0.21, 0.0, 0.0],
    [4, "Lautaro Martinez", "Attack", "CF", 28, "Inter", "Serie A", 90000000, 95000000, 95, 2600, 33, 78.8, 18, 4, 22, 4, 0, 0.62, 0.14, 0.76, 5, 390, 3, 1, 4, 0.69, 0.23, 0.92, 0.0, 0.0],
]


@pytest.fixture
def repository(tmp_path: Path) -> CsvPlayerRepository:
    csv_path = tmp_path / "players.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(_COLUMNS)
        writer.writerows(_ROWS)
    return CsvPlayerRepository(csv_path)


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        CsvPlayerRepository(tmp_path / "does_not_exist.csv")


def test_all_and_get(repository: CsvPlayerRepository) -> None:
    assert len(repository.all()) == 4
    assert repository.get(3).name == "Rodri"
    assert repository.get(999) is None


def test_search_is_case_insensitive_and_partial(repository: CsvPlayerRepository) -> None:
    names = [p.name for p in repository.search("BRUNO")]
    # Both match "bruno"; tie on prefix, so higher market value (Guimaraes, 80M) ranks first.
    assert names == ["Bruno Guimaraes", "Bruno Fernandes"]


def test_search_ranks_prefix_matches_first(repository: CsvPlayerRepository) -> None:
    # "martinez" only appears mid-name for one player; prefix "lautaro" should surface it.
    assert repository.search("lautaro")[0].name == "Lautaro Martinez"


def test_search_respects_limit(repository: CsvPlayerRepository) -> None:
    assert len(repository.search("bruno", limit=1)) == 1


def test_search_empty_query_returns_nothing(repository: CsvPlayerRepository) -> None:
    assert repository.search("   ") == []


def test_filter_by_league_position(repository: CsvPlayerRepository) -> None:
    pl_mids = repository.filter_by_league_position("Premier League", "Midfield")
    assert {p.name for p in pl_mids} == {"Bruno Fernandes", "Bruno Guimaraes", "Rodri"}
    assert repository.filter_by_league_position("Serie A", "Midfield") == []

"""Tests for the CSV repository's loading, search and filtering."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from app.repositories.csv_repository import CsvPlayerRepository

_COLUMNS = [
    "player_id", "name", "position", "sub_position", "age", "club", "league",
    "market_value_eur", "minutes_played", "matches_played", "goals", "assists",
    "goal_contributions", "yellow_cards", "red_cards", "goals_per90",
    "assists_per90", "goal_contributions_per90",
]

_ROWS = [
    # id  name             pos       sub          age club  league            mv       min  mp  g  a  ga yc rc  g90  a90  ga90
    [1, "Bruno Fernandes", "Midfield", "AM", 30, "MUFC", "Premier League", 70000000, 3000, 34, 8, 10, 18, 5, 0, 0.24, 0.30, 0.54],
    [2, "Bruno Guimaraes", "Midfield", "CM", 27, "NUFC", "Premier League", 80000000, 2800, 32, 4, 6, 10, 6, 0, 0.13, 0.19, 0.32],
    [3, "Rodri", "Midfield", "DM", 28, "MCFC", "Premier League", 110000000, 1500, 17, 3, 2, 5, 3, 1, 0.18, 0.12, 0.30],
    [4, "Lautaro Martinez", "Attack", "CF", 28, "Inter", "Serie A", 90000000, 2600, 33, 18, 4, 22, 4, 0, 0.62, 0.14, 0.76],
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

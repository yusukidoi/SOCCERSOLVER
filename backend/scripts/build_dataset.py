"""Build the curated SoccerSolver dataset.

Source: dcaribou/transfermarkt-datasets (https://github.com/dcaribou/transfermarkt-datasets),
a clean, weekly-updated dataset built from public Transfermarkt data.

This script downloads three raw tables, joins them, aggregates one season of
domestic-league performance per player, and writes a single tidy CSV that the
backend consumes: ``backend/data/players.csv``.

Run from the ``backend`` directory:

    python scripts/build_dataset.py

Raw files are cached under ``data/.raw`` (git-ignored) so re-runs are fast.
The produced ``players.csv`` is committed so the app runs offline / in Docker
without needing network access at build time.
"""

from __future__ import annotations

import csv
import gzip
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.request import urlretrieve

# --- Configuration ---------------------------------------------------------

R2_BASE = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
RAW_FILES = ("players.csv.gz", "competitions.csv.gz", "appearances.csv.gz")

# Big-5 European leagues (Transfermarkt domestic competition ids).
BIG5: dict[str, str] = {
    "GB1": "Premier League",
    "ES1": "LaLiga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
}

# Target season 2025/26 (Transfermarkt seasons run Jul -> Jun).
SEASON_START = date(2025, 7, 1)
SEASON_END = date(2026, 6, 30)
AGE_REFERENCE = date(2026, 6, 30)

# Only keep players with enough game time for percentiles to be meaningful.
MIN_MINUTES = 300

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / ".raw"
OUTPUT = DATA_DIR / "players.csv"


def download_raw() -> None:
    """Download raw source tables into the cache dir if not already present."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename in RAW_FILES:
        target = RAW_DIR / filename
        if target.exists():
            print(f"  cached: {filename}")
            continue
        print(f"  downloading: {filename} ...")
        urlretrieve(f"{R2_BASE}/{filename}", target)


def load_league_names() -> dict[str, str]:
    """Map domestic competition id -> human-readable league name (Big-5 only)."""
    return dict(BIG5)


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def aggregate_appearances() -> dict[int, dict[str, int]]:
    """Sum a single season of Big-5 domestic-league performance per player."""
    stats: dict[int, dict[str, int]] = defaultdict(
        lambda: {
            "minutes_played": 0,
            "matches_played": 0,
            "goals": 0,
            "assists": 0,
            "yellow_cards": 0,
            "red_cards": 0,
        }
    )
    path = RAW_DIR / "appearances.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["competition_id"] not in BIG5:
                continue
            played = parse_date(row["date"])
            if played is None or not (SEASON_START <= played <= SEASON_END):
                continue
            player_id = int(row["player_id"])
            bucket = stats[player_id]
            bucket["minutes_played"] += int(row["minutes_played"] or 0)
            bucket["matches_played"] += 1
            bucket["goals"] += int(row["goals"] or 0)
            bucket["assists"] += int(row["assists"] or 0)
            bucket["yellow_cards"] += int(row["yellow_cards"] or 0)
            bucket["red_cards"] += int(row["red_cards"] or 0)
    return stats


def compute_age(dob: date | None) -> int | None:
    if dob is None:
        return None
    years = AGE_REFERENCE.year - dob.year
    if (AGE_REFERENCE.month, AGE_REFERENCE.day) < (dob.month, dob.day):
        years -= 1
    return years


def per90(value: int, minutes: int) -> float:
    if minutes <= 0:
        return 0.0
    return round(value / minutes * 90, 3)


def build_rows(
    leagues: dict[str, str], stats: dict[int, dict[str, int]]
) -> list[dict[str, object]]:
    """Join player profiles with season stats into the final tidy rows."""
    rows: list[dict[str, object]] = []
    path = RAW_DIR / "players.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            comp = row["current_club_domestic_competition_id"]
            if comp not in leagues:
                continue
            player_id = int(row["player_id"])
            perf = stats.get(player_id)
            if perf is None or perf["minutes_played"] < MIN_MINUTES:
                continue
            market_value = row["market_value_in_eur"]
            if not market_value:
                continue
            position = row["position"] or "Unknown"
            if position in ("", "Missing"):
                continue
            age = compute_age(parse_date(row["date_of_birth"]))
            minutes = perf["minutes_played"]
            goals, assists = perf["goals"], perf["assists"]
            rows.append(
                {
                    "player_id": player_id,
                    "name": row["name"],
                    "position": position,
                    "sub_position": row["sub_position"] or position,
                    "age": age if age is not None else "",
                    "club": row["current_club_name"],
                    "league": leagues[comp],
                    "market_value_eur": int(market_value),
                    "minutes_played": minutes,
                    "matches_played": perf["matches_played"],
                    "goals": goals,
                    "assists": assists,
                    "goal_contributions": goals + assists,
                    "yellow_cards": perf["yellow_cards"],
                    "red_cards": perf["red_cards"],
                    "goals_per90": per90(goals, minutes),
                    "assists_per90": per90(assists, minutes),
                    "goal_contributions_per90": per90(goals + assists, minutes),
                }
            )
    return rows


def write_csv(rows: list[dict[str, object]]) -> None:
    rows.sort(key=lambda r: r["market_value_eur"], reverse=True)
    fieldnames = list(rows[0].keys())
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    print("1/4 Downloading raw source tables ...")
    download_raw()
    print("2/4 Loading league names ...")
    leagues = load_league_names()
    print("3/4 Aggregating season performance ...")
    stats = aggregate_appearances()
    print("4/4 Joining and writing curated dataset ...")
    rows = build_rows(leagues, stats)
    if not rows:
        print("ERROR: no rows produced; check season window / filters.", file=sys.stderr)
        return 1
    write_csv(rows)
    by_league: dict[str, int] = defaultdict(int)
    for row in rows:
        by_league[str(row["league"])] += 1
    print(f"\nWrote {len(rows)} players to {OUTPUT.relative_to(DATA_DIR.parent)}")
    for league, count in sorted(by_league.items()):
        print(f"  {league:<16} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

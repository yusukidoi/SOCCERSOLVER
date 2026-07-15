"""Build the curated SoccerSolver dataset.

Source: dcaribou/transfermarkt-datasets (https://github.com/dcaribou/transfermarkt-datasets),
a clean, weekly-updated dataset built from public Transfermarkt data.

This script downloads three raw tables, joins them, aggregates one season of
domestic-league performance per player, and writes a single tidy CSV that the
backend consumes: ``backend/data/players.csv``.

Run from the ``backend`` directory:

    python scripts/build_dataset.py

Optional FBref enrichment (requires network + ``pip install soccerdata``):

    python scripts/enrich_fbref.py
    python scripts/build_dataset.py --with-advanced

Raw files are cached under ``data/.raw`` (git-ignored) so re-runs are fast.
The produced ``players.csv`` is committed so the app runs offline / in Docker
without needing network access at build time.
"""

from __future__ import annotations

import argparse
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
LAST_N_MATCHES = 5

# Only keep players with enough game time for percentiles to be meaningful.
MIN_MINUTES = 300

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / ".raw"
ADVANCED_STATS = DATA_DIR / "advanced_stats.csv"
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


def _empty_bucket() -> dict[str, int]:
    return {
        "minutes_played": 0,
        "matches_played": 0,
        "goals": 0,
        "assists": 0,
        "yellow_cards": 0,
        "red_cards": 0,
    }


def _sum_matches(matches: list[dict[str, int]]) -> dict[str, int]:
    bucket = _empty_bucket()
    for match in matches:
        bucket["minutes_played"] += match["minutes_played"]
        bucket["matches_played"] += 1
        bucket["goals"] += match["goals"]
        bucket["assists"] += match["assists"]
        bucket["yellow_cards"] += match["yellow_cards"]
        bucket["red_cards"] += match["red_cards"]
    return bucket


def aggregate_appearances() -> tuple[dict[int, dict[str, int]], dict[int, dict[str, int]]]:
    """Sum season stats and last-N-match form per player from appearance logs."""
    season: dict[int, dict[str, int]] = defaultdict(_empty_bucket)
    match_log: dict[int, list[tuple[date, dict[str, int]]]] = defaultdict(list)
    path = RAW_DIR / "appearances.csv.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["competition_id"] not in BIG5:
                continue
            played = parse_date(row["date"])
            if played is None or not (SEASON_START <= played <= SEASON_END):
                continue
            player_id = int(row["player_id"])
            appearance = {
                "minutes_played": int(row["minutes_played"] or 0),
                "goals": int(row["goals"] or 0),
                "assists": int(row["assists"] or 0),
                "yellow_cards": int(row["yellow_cards"] or 0),
                "red_cards": int(row["red_cards"] or 0),
            }
            match_log[player_id].append((played, appearance))
            bucket = season[player_id]
            bucket["minutes_played"] += appearance["minutes_played"]
            bucket["matches_played"] += 1
            bucket["goals"] += appearance["goals"]
            bucket["assists"] += appearance["assists"]
            bucket["yellow_cards"] += appearance["yellow_cards"]
            bucket["red_cards"] += appearance["red_cards"]

    last_n: dict[int, dict[str, int]] = {}
    for player_id, entries in match_log.items():
        entries.sort(key=lambda item: item[0])
        recent = [appearance for _, appearance in entries[-LAST_N_MATCHES:]]
        last_n[player_id] = _sum_matches(recent)
    return season, last_n


def compute_age(dob: date | None) -> int | None:
    if dob is None:
        return None
    years = AGE_REFERENCE.year - dob.year
    if (AGE_REFERENCE.month, AGE_REFERENCE.day) < (dob.month, dob.day):
        years -= 1
    return years


def per90(value: int | float, minutes: int) -> float:
    if minutes <= 0:
        return 0.0
    return round(float(value) / minutes * 90, 3)


def load_advanced_stats() -> dict[int, dict[str, float]]:
    """Optional FBref enrichment keyed by Transfermarkt player id."""
    if not ADVANCED_STATS.exists():
        return {}
    loaded: dict[int, dict[str, float]] = {}
    with ADVANCED_STATS.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            player_id = int(row["player_id"])
            loaded[player_id] = {
                "progressive_passes_per90": float(row.get("progressive_passes_per90") or 0),
                "defensive_actions_per90": float(row.get("defensive_actions_per90") or 0),
            }
    return loaded


def build_rows(
    leagues: dict[str, str],
    season_stats: dict[int, dict[str, int]],
    last_n_stats: dict[int, dict[str, int]],
    advanced: dict[int, dict[str, float]],
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
            perf = season_stats.get(player_id)
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
            last5 = last_n_stats.get(player_id, _empty_bucket())
            last5_minutes = last5["minutes_played"]
            last5_goals, last5_assists = last5["goals"], last5["assists"]
            highest_mv = int(row["highest_market_value_in_eur"] or market_value)
            current_mv = int(market_value)
            peak_pct = round(current_mv / highest_mv * 100) if highest_mv > 0 else 100
            adv = advanced.get(player_id, {})
            rows.append(
                {
                    "player_id": player_id,
                    "name": row["name"],
                    "position": position,
                    "sub_position": row["sub_position"] or position,
                    "age": age if age is not None else "",
                    "club": row["current_club_name"],
                    "league": leagues[comp],
                    "market_value_eur": current_mv,
                    "highest_market_value_eur": highest_mv,
                    "market_value_pct_of_peak": peak_pct,
                    "minutes_played": minutes,
                    "matches_played": perf["matches_played"],
                    "avg_minutes_per_match": round(minutes / perf["matches_played"], 1)
                    if perf["matches_played"]
                    else 0.0,
                    "goals": goals,
                    "assists": assists,
                    "goal_contributions": goals + assists,
                    "yellow_cards": perf["yellow_cards"],
                    "red_cards": perf["red_cards"],
                    "goals_per90": per90(goals, minutes),
                    "assists_per90": per90(assists, minutes),
                    "goal_contributions_per90": per90(goals + assists, minutes),
                    "last5_matches": last5["matches_played"],
                    "last5_minutes": last5_minutes,
                    "last5_goals": last5_goals,
                    "last5_assists": last5_assists,
                    "last5_goal_contributions": last5_goals + last5_assists,
                    "last5_goals_per90": per90(last5_goals, last5_minutes),
                    "last5_assists_per90": per90(last5_assists, last5_minutes),
                    "last5_goal_contributions_per90": per90(
                        last5_goals + last5_assists, last5_minutes
                    ),
                    "progressive_passes_per90": adv.get("progressive_passes_per90", 0.0),
                    "defensive_actions_per90": adv.get("defensive_actions_per90", 0.0),
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
    parser = argparse.ArgumentParser(description="Build curated players.csv")
    parser.add_argument(
        "--with-advanced",
        action="store_true",
        help="Merge optional data/advanced_stats.csv (from enrich_fbref.py)",
    )
    args = parser.parse_args()

    print("1/4 Downloading raw source tables ...")
    download_raw()
    print("2/4 Loading league names ...")
    leagues = load_league_names()
    print("3/4 Aggregating season performance + last-5 form ...")
    season_stats, last_n_stats = aggregate_appearances()
    advanced = load_advanced_stats() if args.with_advanced else {}
    if args.with_advanced and not advanced:
        print("  warning: --with-advanced set but advanced_stats.csv missing or empty")
    print("4/4 Joining and writing curated dataset ...")
    rows = build_rows(leagues, season_stats, last_n_stats, advanced)
    if not rows:
        print("ERROR: no rows produced; check season window / filters.", file=sys.stderr)
        return 1
    write_csv(rows)
    by_league: dict[str, int] = defaultdict(int)
    with_advanced = sum(1 for row in rows if float(row["progressive_passes_per90"]) > 0)
    for row in rows:
        by_league[str(row["league"])] += 1
    print(f"\nWrote {len(rows)} players to {OUTPUT.relative_to(DATA_DIR.parent)}")
    print(f"  last-{LAST_N_MATCHES} match form computed for all players")
    if with_advanced:
        print(f"  advanced stats merged for {with_advanced} players")
    for league, count in sorted(by_league.items()):
        print(f"  {league:<16} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

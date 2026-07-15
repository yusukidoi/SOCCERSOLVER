"""Optional FBref enrichment — merges advanced stats into advanced_stats.csv.

Run from the ``backend`` directory when you have network access:

    pip install soccerdata pandas
    python scripts/enrich_fbref.py
    python scripts/build_dataset.py --with-advanced

FBref scraping can fail (CAPTCHA / rate limits). When it does, the app still
works with Transfermarkt-only data; last-5 form and market-value peak come from
appearances + player profiles.

Matching uses normalised player name + league. Coverage will be partial — that
is expected and surfaced via confidence reasons on the profile.
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT = DATA_DIR / "advanced_stats.csv"
PLAYERS_CSV = DATA_DIR / "players.csv"

LEAGUE_TO_FBREF: dict[str, str] = {
    "Premier League": "ENG-Premier League",
    "LaLiga": "ESP-La Liga",
    "Serie A": "ITA-Serie A",
    "Bundesliga": "GER-Bundesliga",
    "Ligue 1": "FRA-Ligue 1",
}


def normalise_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9 ]", "", text.casefold())
    return " ".join(text.split())


def main() -> int:
    try:
        import soccerdata as sd
    except ImportError:
        print("Install soccerdata first: pip install soccerdata pandas", file=sys.stderr)
        return 1

    if not PLAYERS_CSV.exists():
        print("Run build_dataset.py first to create players.csv", file=sys.stderr)
        return 1

    targets: dict[tuple[str, str], list[int]] = {}
    with PLAYERS_CSV.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (normalise_name(row["name"]), row["league"])
            targets.setdefault(key, []).append(int(row["player_id"]))

    rows: list[dict[str, object]] = []
    matched = 0

    for league, fbref_league in LEAGUE_TO_FBREF.items():
        print(f"Fetching FBref misc stats for {league} ...")
        try:
            fbref = sd.FBref(fbref_league, "2526")
            frame = fbref.read_player_season_stats(stat_type="misc")
        except Exception as exc:  # noqa: BLE001 — optional enrichment path
            print(f"  skipped {league}: {exc}")
            continue

        frame = frame.reset_index()
        for _, record in frame.iterrows():
            player_name = str(record.get("player", ""))
            key = (normalise_name(player_name), league)
            player_ids = targets.get(key)
            if not player_ids:
                continue
            minutes = float(record.get(("Playing Time", "Min"), 0) or 0)
            if minutes <= 0:
                continue
            prog = float(record.get(("Progression", "PrgP"), 0) or 0)
            tackles = float(record.get(("Performance", "Tkl"), 0) or 0)
            interceptions = float(record.get(("Performance", "Int"), 0) or 0)
            blocks = float(record.get(("Performance", "Blocks"), 0) or 0)
            defensive = tackles + interceptions + blocks
            for player_id in player_ids:
                rows.append(
                    {
                        "player_id": player_id,
                        "progressive_passes_per90": round(prog / minutes * 90, 3),
                        "defensive_actions_per90": round(defensive / minutes * 90, 3),
                    }
                )
                matched += 1

    if not rows:
        print("No rows matched — FBref may be blocked. App works without this file.", file=sys.stderr)
        return 1

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["player_id", "progressive_passes_per90", "defensive_actions_per90"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} advanced stat rows ({matched} matches) to {OUTPUT.name}")
    print("Re-run: python scripts/build_dataset.py --with-advanced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# SoccerSolver — Player Intelligence Tool

Turn raw football player statistics into a tool a sporting director can actually use:
**search players, read a contextualised profile, and compare two players** to support a
signing or contract decision.

Built with **React + TypeScript** (frontend) and **Python + FastAPI** (backend).

---

## Status

Work in progress — built incrementally. See the step-by-step commit history for context.

## Features

- **Player search** — find a player by name with position, club, league and market value.
- **Individual profile** — player data plus performance metrics contextualised against the
  positional average in the same league (percentiles / above-below reading), not raw numbers.
- **Two-player comparison** — side-by-side visual diff so you can see in seconds who is
  better at what, with market-value context.

## Tech stack

| Layer    | Choice                                             |
| -------- | -------------------------------------------------- |
| Frontend | React + TypeScript (Vite)                          |
| Backend  | FastAPI + Pydantic                                 |
| Data     | Public football stats CSV (source documented below) |
| Runtime  | Docker Compose (`docker-compose up`)               |

## Project structure

```
SOCCERSOLVER/
├── backend/          # FastAPI service
│   ├── app/
│   │   ├── api/          # HTTP routes (thin)
│   │   ├── services/     # business logic (percentiles, comparison, averages)
│   │   ├── repositories/ # data access abstraction over the CSV
│   │   ├── models/       # Pydantic schemas
│   │   └── core/         # configuration
│   ├── data/             # dataset
│   └── tests/            # pytest business-logic tests
├── frontend/         # React + TypeScript app
├── docker-compose.yml
└── .env.example
```

## Running locally

> Documented as the project is built. The end goal is a single command:
>
> ```bash
> docker-compose up
> ```

## Data source

The dataset is derived from [**dcaribou/transfermarkt-datasets**](https://github.com/dcaribou/transfermarkt-datasets)
— a clean, weekly-updated dataset built from public [Transfermarkt](https://www.transfermarkt.com/)
data (used here under its open, non-commercial terms for a technical exercise).

A reproducible prep script, [`backend/scripts/build_dataset.py`](backend/scripts/build_dataset.py),
downloads three raw tables (`players`, `competitions`, `appearances`), joins them, and produces the
curated `backend/data/players.csv` used by the app:

- **Scope:** Big-5 European leagues (Premier League, LaLiga, Serie A, Bundesliga, Ligue 1),
  **2025/26** season, players with ≥ 300 league minutes → **2,059 players**.
- **Identity & context:** name, position, sub-position, age, club, league, market value (EUR).
- **Performance:** minutes, matches, goals, assists, goal contributions, cards, and per-90 rates.

The curated CSV is committed so the app runs offline (and in Docker) without network access.
To regenerate it:

```bash
cd backend
python scripts/build_dataset.py
```

> **Why derive instead of using a raw dump?** The prep script keeps only current, relevant
> players and pre-computes the fields the product needs, so the API stays fast and the data
> access layer works from a small, well-shaped file.

## Product & technical decisions

_To be documented as the project is built._

## What I'd improve with more time / left out

_To be documented at the end._

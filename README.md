# SoccerSolver — Player Intelligence Tool

Turn raw football player statistics into a tool a sporting director can actually use:
**search players, read a contextualised profile, and compare two players** to support a
signing or contract decision.

Built with **React + TypeScript** (frontend) and **Python + FastAPI** (backend).

---

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
│   ├── scripts/          # reproducible dataset builder
│   ├── data/             # curated players.csv
│   └── tests/            # pytest business-logic tests
├── frontend/         # React + TypeScript app (Vite)
│   └── src/
│       ├── api/          # typed API client
│       ├── components/   # radar, metric bars, comparison rows, cards
│       ├── pages/        # Search, Profile, Comparison
│       └── lib/          # formatting + hooks
├── docker-compose.yml
└── .env.example
```

## Running locally

### Option A — Docker (recommended)

The only requirement is Docker. From the repository root:

```bash
docker-compose up --build
```

Then open **http://localhost:5173**. The backend API is on **http://localhost:8000**
(interactive docs at http://localhost:8000/docs). No `.env` is required — the compose file
ships with working defaults. To override ports or URLs, copy `.env.example` to `.env`.

### Option B — Run each service directly

**Backend** (Python 3.12+):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev
```

The dev server prints a local URL (default http://localhost:5173) and expects the backend at
`http://localhost:8000` (override with `VITE_API_BASE_URL`).

### Tests

```bash
cd backend
pytest
```

## API

| Method | Endpoint                      | Purpose                                          |
| ------ | ----------------------------- | ------------------------------------------------ |
| GET    | `/health`                     | Liveness check                                   |
| GET    | `/players/search?q=&limit=`   | Search players by name (search view)             |
| GET    | `/players/{id}/profile`       | Player + metrics contextualised vs peers         |
| GET    | `/comparison?one=&two=`       | Two players compared metric by metric            |

Errors use meaningful codes: `404` (unknown player), `422` (invalid/missing query),
`400` (comparing a player with itself).

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

## Product decisions (what I showed, how, and why)

- **Context over raw numbers.** A sporting director doesn't need "12 goals", they need "is that
  good for a winger in this league?". Every metric on the profile is expressed as a **percentile
  against the player's peer group** (same broad position, same league) and shown against the peer
  average. The radar overlays the player on a 50th-percentile baseline, so *above/below average*
  reads in one glance.
- **Comparison as a difference, not two tables.** The comparison view uses a single **diverging bar
  per metric** split between the two players, marks the leader with a ▲, and shows a **wins tally**
  ("X leads N metrics"). The goal was the brief's "who is better at what in seconds".
- **Market value everywhere it helps a decision.** Value appears on every search result, on the
  profile (with its percentile in the peer group), and as its own comparison row — because value
  only means something *relative* to a player's league and position.
- **Per-90 metrics** are included alongside totals so a high-minutes starter and a rotation player
  are compared fairly.
- **Peer group = league + broad position.** Broad position (Attack/Midfield/Defender/Goalkeeper)
  keeps peer groups large enough for percentiles to be stable, while the detailed sub-position
  (e.g. "Left Winger") is still shown for identification.

## Technical decisions

- **Separation of concerns (backend).** Routes are thin; all logic lives in a `services/` layer
  (percentiles, averages, comparison) as **pure functions** that receive the peer group as input.
  This makes the logic I/O-free and directly unit-testable.
- **Data access is abstracted.** Endpoints depend on a `PlayerRepository` interface, not the CSV.
  The `CsvPlayerRepository` loads the file once into memory and indexes by id and by
  (league, position). Swapping in a database means adding one implementation — nothing else changes.
- **Reproducible dataset.** Rather than commit an opaque dump, a documented script derives a small,
  well-shaped `players.csv` from a public source, so the data is explainable and regenerable.
- **Type safety end to end.** Full Python type hints + Pydantic models on the backend; the
  frontend's TypeScript interfaces mirror those models, and the API client is fully typed.
- **Minimal frontend dependencies.** React Router for the three views, Recharts for the radar, and
  plain `fetch` (with `AbortController` to cancel stale requests) — no heavy data-fetching library,
  to keep the app easy to read and explain.
- **One-command startup.** Docker Compose builds both services; the frontend is served as a static
  nginx bundle with SPA fallback, and works with zero configuration.

## What I'd improve with more time / consciously left out

### Recently added (post-challenge upgrades)

- **Position-specific metrics** — Attack, Midfield, Defender, and Goalkeeper each surface
  different metrics (e.g. defenders include discipline cards with lower-is-better polarity).
- **Peer confidence labels** — profiles and comparisons flag when percentiles may be noisy
  because the peer group is small (`high` / `medium` / `low` by sample size).
- **Comparison deltas** — each metric shows the absolute gap (e.g. `▲ +0.04` goals/90), not
  just who wins the proportional bar.
- **Cross-position comparison note** — when roles differ, a shared output-metric set is used
  and the UI explains that.
- **Similar players** — profile suggests up to 5 peers with the closest performance shape
  (cosine similarity on position metrics), with one-click compare.

### Still on the roadmap

- **Richer metrics.** Blend FBref data (shots, xG, progressive passes, defensive actions) for a
  more complete radar — especially position-specific metrics (a centre-back's radar shouldn't be
  about goals).
- **Code-splitting.** Recharts makes the JS bundle ~600KB; lazy-loading the chart-heavy views
  would cut initial load.
- **Frontend tests + caching.** No component tests and no request caching (e.g. React Query).
- **Persistence & scale.** The in-memory CSV repository is perfect for this dataset size but would
  become a real database (and paginated search) for a production catalogue.
- **Accessibility & polish.** Keyboard navigation for the search dropdown and fuller ARIA labelling
  would be next.

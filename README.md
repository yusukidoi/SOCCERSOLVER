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

_To be documented in the dataset step._

## Product & technical decisions

_To be documented as the project is built._

## What I'd improve with more time / left out

_To be documented at the end._

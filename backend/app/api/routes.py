"""HTTP routes. Kept thin: fetch from the repository, delegate to the service."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_player_repository
from app.models.analytics import PlayerComparison, PlayerProfile
from app.models.player import PlayerSummary
from app.repositories.base import PlayerRepository
from app.services.analytics import build_comparison, build_profile

router = APIRouter()

RepositoryDep = Annotated[PlayerRepository, Depends(get_player_repository)]


@router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/players/search", response_model=list[PlayerSummary], tags=["players"])
def search_players(
    repository: RepositoryDep,
    q: Annotated[str, Query(min_length=1, description="Name to search for")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[PlayerSummary]:
    """Search players by name for the search view."""
    return [player.summary() for player in repository.search(q, limit)]


@router.get("/players/{player_id}/profile", response_model=PlayerProfile, tags=["players"])
def player_profile(player_id: int, repository: RepositoryDep) -> PlayerProfile:
    """Return a player with metrics contextualised against their peer group."""
    player = repository.get(player_id)
    if player is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Player not found")
    peers = repository.filter_by_league_position(player.league, player.position)
    return build_profile(player, peers)


@router.get("/comparison", response_model=PlayerComparison, tags=["comparison"])
def compare_players(
    repository: RepositoryDep,
    one: Annotated[int, Query(description="First player id")],
    two: Annotated[int, Query(description="Second player id")],
) -> PlayerComparison:
    """Compare two players side by side."""
    if one == two:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Pick two different players")
    player_one = repository.get(one)
    player_two = repository.get(two)
    missing = [pid for pid, p in ((one, player_one), (two, player_two)) if p is None]
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Player(s) not found: {missing}")
    assert player_one is not None and player_two is not None  # narrowed by the check above
    return build_comparison(
        player_one,
        repository.filter_by_league_position(player_one.league, player_one.position),
        player_two,
        repository.filter_by_league_position(player_two.league, player_two.position),
    )

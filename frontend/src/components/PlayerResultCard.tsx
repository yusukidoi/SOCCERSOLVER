import { Link } from "react-router-dom";
import type { PlayerSummary } from "../types";
import { formatMarketValue } from "../lib/format";

interface Props {
  player: PlayerSummary;
  selected?: boolean;
}

export default function PlayerResultCard({ player, selected = false }: Props) {
  return (
    <Link
      id={`result-${player.player_id}`}
      to={`/players/${player.player_id}`}
      className={`result-card${selected ? " result-card--selected" : ""}`}
      role="option"
      aria-selected={selected}
    >
      <div className="result-card__main">
        <span className="result-card__name">{player.name}</span>
        <span className="result-card__sub">
          {player.sub_position}
          {player.age !== null ? ` · ${player.age} yrs` : ""}
        </span>
      </div>
      <div className="result-card__meta">
        <span>{player.club}</span>
        <span className="badge">{player.league}</span>
      </div>
      <div className="result-card__value">{formatMarketValue(player.market_value_eur)}</div>
    </Link>
  );
}

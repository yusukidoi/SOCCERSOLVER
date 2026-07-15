import { Link, useNavigate } from "react-router-dom";
import type { SimilarPlayer } from "../types";
import { formatMarketValue } from "../lib/format";

interface Props {
  players: SimilarPlayer[];
  currentPlayerId: number;
}

/** Peers with the closest performance profile — scouting alternatives. */
export default function SimilarPlayers({ players, currentPlayerId }: Props) {
  const navigate = useNavigate();

  if (players.length === 0) {
    return null;
  }

  return (
    <div className="card similar">
      <h2 className="section-title">Similar players</h2>
      <p className="muted section-hint">
        Closest performance profile in the same league and position.
      </p>
      <ul className="similar__list">
        {players.map(({ player, similarity }) => (
          <li key={player.player_id} className="similar__item">
            <Link to={`/players/${player.player_id}`} className="similar__main">
              <span className="similar__name">{player.name}</span>
              <span className="similar__meta muted">
                {player.sub_position} · {player.club} · {formatMarketValue(player.market_value_eur)}
              </span>
            </Link>
            <div className="similar__actions">
              <span className="similar__score">{similarity}% match</span>
              <button
                className="button button--ghost"
                onClick={() => navigate(`/compare?one=${currentPlayerId}&two=${player.player_id}`)}
              >
                Compare
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

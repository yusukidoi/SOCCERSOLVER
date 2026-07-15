import { Link, useNavigate } from "react-router-dom";
import type { SimilarPlayer } from "../types";
import { formatMarketValue } from "../lib/format";

interface Props {
  players: SimilarPlayer[];
  valueAlternatives: SimilarPlayer[];
  currentPlayerId: number;
}

function SimilarList({
  items,
  currentPlayerId,
  showSavings,
}: {
  items: SimilarPlayer[];
  currentPlayerId: number;
  showSavings?: boolean;
}) {
  const navigate = useNavigate();

  return (
    <ul className="similar__list">
      {items.map(({ player, similarity, value_savings_eur }) => (
        <li key={player.player_id} className="similar__item">
          <Link to={`/players/${player.player_id}`} className="similar__main">
            <span className="similar__name">{player.name}</span>
            <span className="similar__meta muted">
              {player.sub_position} · {player.club} · {formatMarketValue(player.market_value_eur)}
              {showSavings && value_savings_eur !== null && (
                <> · saves {formatMarketValue(value_savings_eur)}</>
              )}
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
  );
}

/** Peers with the closest performance profile — scouting alternatives. */
export default function SimilarPlayers({ players, valueAlternatives, currentPlayerId }: Props) {
  if (players.length === 0) {
    return null;
  }

  return (
    <div className="similar">
      {valueAlternatives.length > 0 && (
        <div className="card similar__section">
          <h2 className="section-title">Similar profile, lower value</h2>
          <p className="muted section-hint">
            Recruitment targets — comparable output at a lower market value.
          </p>
          <SimilarList
            items={valueAlternatives}
            currentPlayerId={currentPlayerId}
            showSavings
          />
        </div>
      )}

      <div className="card similar__section">
        <h2 className="section-title">Similar players</h2>
        <p className="muted section-hint">
          Closest performance profile in the same league and position.
        </p>
        <SimilarList items={players} currentPlayerId={currentPlayerId} />
      </div>
    </div>
  );
}

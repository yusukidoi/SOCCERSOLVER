import { useEffect, useState } from "react";
import { searchPlayers } from "../api/client";
import type { PlayerSummary } from "../types";
import { useDebounce } from "../lib/useDebounce";
import { formatMarketValue } from "../lib/format";

interface Props {
  label: string;
  accent: string;
  current: PlayerSummary | null;
  onSelect: (player: PlayerSummary) => void;
  onClear: () => void;
}

/** Search-and-select control for one comparison slot. */
export default function PlayerPicker({ label, accent, current, onSelect, onClear }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const debounced = useDebounce(query.trim(), 300);

  useEffect(() => {
    if (current || debounced.length === 0) {
      setResults([]);
      return;
    }
    const controller = new AbortController();
    searchPlayers(debounced, controller.signal)
      .then(setResults)
      .catch(() => setResults([]));
    return () => controller.abort();
  }, [debounced, current]);

  if (current) {
    return (
      <div className="picker picker--filled" style={{ borderColor: accent }}>
        <span className="picker__label" style={{ color: accent }}>{label}</span>
        <div className="picker__selected">
          <strong>{current.name}</strong>
          <span className="muted">
            {current.sub_position} · {current.club} · {formatMarketValue(current.market_value_eur)}
          </span>
        </div>
        <button className="button button--ghost" onClick={onClear}>Change</button>
      </div>
    );
  }

  return (
    <div className="picker" style={{ borderColor: accent }}>
      <span className="picker__label" style={{ color: accent }}>{label}</span>
      <input
        className="input"
        type="search"
        placeholder="Search a player…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      {results.length > 0 && (
        <ul className="picker__results">
          {results.map((player) => (
            <li key={player.player_id}>
              <button
                className="picker__option"
                onClick={() => {
                  setQuery("");
                  onSelect(player);
                }}
              >
                <span>{player.name}</span>
                <span className="muted">{player.club} · {player.league}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

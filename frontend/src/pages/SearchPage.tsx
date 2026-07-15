import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { searchPlayers } from "../api/client";
import type { PlayerSummary } from "../types";
import { useDebounce } from "../lib/useDebounce";
import PlayerResultCard from "../components/PlayerResultCard";
import Skeleton from "../components/Skeleton";

export default function SearchPage() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [highlight, setHighlight] = useState(-1);
  const debouncedQuery = useDebounce(query.trim(), 300);

  useEffect(() => {
    if (debouncedQuery.length === 0) {
      setResults([]);
      setStatus("idle");
      setHighlight(-1);
      return;
    }
    const controller = new AbortController();
    setStatus("loading");
    setHighlight(-1);
    searchPlayers(debouncedQuery, controller.signal)
      .then((players) => {
        setResults(players);
        setStatus("done");
        setHighlight(players.length > 0 ? 0 : -1);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus("error");
      });
    return () => controller.abort();
  }, [debouncedQuery]);

  const openHighlighted = () => {
    if (highlight < 0 || highlight >= results.length) return;
    navigate(`/players/${results[highlight].player_id}`);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (results.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlight((current) => Math.min(current + 1, results.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlight((current) => Math.max(current - 1, 0));
    } else if (event.key === "Enter" && highlight >= 0) {
      event.preventDefault();
      openHighlighted();
    }
  };

  return (
    <section className="search">
      <h1>Find a player</h1>
      <p className="muted">
        Search Europe's Big-5 leagues by name. Use ↑↓ and Enter to pick a result.
      </p>

      <input
        ref={inputRef}
        className="input search__input"
        type="search"
        role="combobox"
        aria-expanded={results.length > 0}
        aria-activedescendant={highlight >= 0 ? `result-${results[highlight]?.player_id}` : undefined}
        placeholder="Search by name — e.g. Haaland, Bellingham, Vinicius…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
      />

      <div className="search__results" role="listbox">
        {status === "loading" && (
          <>
            <Skeleton className="skeleton--card" lines={1} />
            <Skeleton className="skeleton--card" lines={1} />
            <Skeleton className="skeleton--card" lines={1} />
          </>
        )}
        {status === "error" && <p className="error-text">Something went wrong. Try again.</p>}
        {status === "done" && results.length === 0 && (
          <p className="muted">No players match “{debouncedQuery}”.</p>
        )}
        {results.map((player, index) => (
          <PlayerResultCard
            key={player.player_id}
            player={player}
            selected={index === highlight}
          />
        ))}
      </div>
    </section>
  );
}

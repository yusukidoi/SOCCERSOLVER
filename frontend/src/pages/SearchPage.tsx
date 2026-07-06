import { useEffect, useState } from "react";
import { searchPlayers } from "../api/client";
import type { PlayerSummary } from "../types";
import { useDebounce } from "../lib/useDebounce";
import PlayerResultCard from "../components/PlayerResultCard";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSummary[]>([]);
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");
  const debouncedQuery = useDebounce(query.trim(), 300);

  useEffect(() => {
    if (debouncedQuery.length === 0) {
      setResults([]);
      setStatus("idle");
      return;
    }
    const controller = new AbortController();
    setStatus("loading");
    searchPlayers(debouncedQuery, controller.signal)
      .then((players) => {
        setResults(players);
        setStatus("done");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setStatus("error");
      });
    return () => controller.abort();
  }, [debouncedQuery]);

  return (
    <section className="search">
      <h1>Find a player</h1>
      <p className="muted">
        Search Europe's Big-5 leagues by name, then open a profile or start a comparison.
      </p>

      <input
        className="input search__input"
        type="search"
        placeholder="Search by name — e.g. Haaland, Bellingham, Vinicius…"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        autoFocus
      />

      <div className="search__results">
        {status === "loading" && <p className="muted">Searching…</p>}
        {status === "error" && <p className="error-text">Something went wrong. Try again.</p>}
        {status === "done" && results.length === 0 && (
          <p className="muted">No players match “{debouncedQuery}”.</p>
        )}
        {results.map((player) => (
          <PlayerResultCard key={player.player_id} player={player} />
        ))}
      </div>
    </section>
  );
}

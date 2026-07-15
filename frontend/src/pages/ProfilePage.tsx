import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, getPlayerProfile } from "../api/client";
import type { PlayerProfile } from "../types";
import { formatMarketValue, ordinalPercentile } from "../lib/format";
import PerformanceRadar from "../components/PerformanceRadar";
import MetricBar from "../components/MetricBar";
import ConfidenceBadge from "../components/ConfidenceBadge";
import SimilarPlayers from "../components/SimilarPlayers";

export default function ProfilePage() {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<PlayerProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = Number(playerId);
    if (!Number.isFinite(id)) {
      setError("Invalid player id");
      return;
    }
    const controller = new AbortController();
    setProfile(null);
    setError(null);
    getPlayerProfile(id, controller.signal)
      .then(setProfile)
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Failed to load profile");
      });
    return () => controller.abort();
  }, [playerId]);

  if (error) {
    return (
      <section>
        <Link to="/" className="button button--ghost">← Back to search</Link>
        <p className="error-text" style={{ marginTop: "1rem" }}>{error}</p>
      </section>
    );
  }

  if (!profile) {
    return <p className="muted">Loading profile…</p>;
  }

  const {
    player,
    metrics,
    peer_group_label,
    peer_group_size,
    peer_confidence,
    market_value_percentile,
    similar_players,
  } = profile;

  return (
    <section className="profile">
      <Link to="/" className="button button--ghost">← Back to search</Link>

      <header className="profile__header card">
        <div>
          <h1>{player.name}</h1>
          <p className="profile__subline">
            <span className="badge">{player.sub_position}</span>
            {player.age !== null && <span>{player.age} yrs</span>}
            <span>{player.club}</span>
            <span className="badge">{player.league}</span>
          </p>
        </div>
        <div className="profile__value">
          <span className="profile__value-amount">{formatMarketValue(player.market_value_eur)}</span>
          <span className="muted">
            {ordinalPercentile(market_value_percentile)} pct of {peer_group_label}
          </span>
          <button
            className="button"
            onClick={() => navigate(`/compare?one=${player.player_id}`)}
          >
            Compare this player →
          </button>
        </div>
      </header>

      <div className="profile__grid">
        <div className="card">
          <h2 className="section-title">Performance shape</h2>
          <p className="muted section-hint">
            Percentile vs {peer_group_label}. Outer = better. Raw values sit in the breakdown.
          </p>
          <ConfidenceBadge level={peer_confidence} peerCount={peer_group_size} />
          <PerformanceRadar metrics={metrics} />
        </div>

        <div className="card">
          <h2 className="section-title">Metric breakdown</h2>
          <p className="muted section-hint">
            Actual value vs position average — percentile shows relative standing.
          </p>
          <div className="metric-list">
            {metrics.map((metric) => (
              <MetricBar key={metric.key} metric={metric} />
            ))}
          </div>
        </div>
      </div>

      <SimilarPlayers players={similar_players} currentPlayerId={player.player_id} />
    </section>
  );
}

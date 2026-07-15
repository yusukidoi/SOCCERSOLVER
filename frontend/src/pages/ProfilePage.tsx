import { lazy, Suspense, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, getPlayerProfile } from "../api/client";
import type { PlayerProfile } from "../types";
import { formatMarketValue, ordinalPercentile } from "../lib/format";
import MetricBar from "../components/MetricBar";
import ConfidenceBadge from "../components/ConfidenceBadge";
import ConfidenceDetail from "../components/ConfidenceDetail";
import RecommendationCard from "../components/RecommendationCard";
import TrendList from "../components/TrendList";
import TeamFitGrid from "../components/TeamFitGrid";
import SimilarPlayers from "../components/SimilarPlayers";
import ProfileSkeleton from "../components/ProfileSkeleton";
import Skeleton from "../components/Skeleton";

const PerformanceRadar = lazy(() => import("../components/PerformanceRadar"));

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
    return <ProfileSkeleton />;
  }

  const {
    player,
    metrics,
    peer_group_label,
    peer_group_size,
    peer_confidence,
    confidence,
    market_value_percentile,
    explainability,
    strengths,
    risks,
    trends,
    team_fit,
    recommendation,
    similar_players,
    value_alternatives,
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

      <div className="profile__insights card">
        <h2 className="section-title">Scouting summary</h2>
        <p className="muted section-hint">
          Built for trust — why they rank, what to watch, and a clear recommendation.
        </p>

        <div className="profile__insights-grid">
          <div>
            {recommendation && <RecommendationCard recommendation={recommendation} />}
            {explainability.length > 0 && (
              <div className="explainability">
                <h3 className="subsection-title">Why ranked highly</h3>
                <ul className="insight-list">
                  {explainability.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div>
            <ConfidenceDetail confidence={confidence} />
            <ConfidenceBadge level={peer_confidence} peerCount={peer_group_size} />

            <div className="strengths-risks">
              {strengths.length > 0 && (
                <div>
                  <h3 className="subsection-title">Strengths</h3>
                  <ul className="insight-list insight-list--strengths">
                    {strengths.map((item) => (
                      <li key={item}>✓ {item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {risks.length > 0 && (
                <div>
                  <h3 className="subsection-title">Risks</h3>
                  <ul className="insight-list insight-list--risks">
                    {risks.map((item) => (
                      <li key={item}>⚠ {item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <TrendList trends={trends} />
            <TeamFitGrid teamFit={team_fit} />
          </div>
        </div>
      </div>

      <div className="profile__grid">
        <div className="card">
          <h2 className="section-title">Performance shape</h2>
          <p className="muted section-hint">
            Percentile vs {peer_group_label}. Outer = better. Raw values sit in the breakdown.
          </p>
          <ConfidenceBadge level={peer_confidence} peerCount={peer_group_size} />
          <Suspense fallback={<Skeleton className="skeleton--chart" lines={1} />}>
            <PerformanceRadar metrics={metrics} />
          </Suspense>
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

      <SimilarPlayers
        players={similar_players}
        valueAlternatives={value_alternatives}
        currentPlayerId={player.player_id}
      />
    </section>
  );
}

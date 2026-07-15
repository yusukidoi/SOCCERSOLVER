import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError, comparePlayers, getPlayerProfile } from "../api/client";
import type { PlayerComparison, PlayerSummary } from "../types";
import { formatMarketValue } from "../lib/format";
import PlayerPicker from "../components/PlayerPicker";
import ComparisonRow from "../components/ComparisonRow";
import ConfidenceBadge from "../components/ConfidenceBadge";
import Skeleton from "../components/Skeleton";

function useSlot(id: number | null): PlayerSummary | null {
  const [player, setPlayer] = useState<PlayerSummary | null>(null);
  useEffect(() => {
    if (id === null) {
      setPlayer(null);
      return;
    }
    if (player?.player_id === id) return;
    const controller = new AbortController();
    getPlayerProfile(id, controller.signal)
      .then((profile) => setPlayer(profile.player))
      .catch(() => undefined);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);
  return player;
}

export default function ComparisonPage() {
  const [params, setParams] = useSearchParams();
  const oneId = params.get("one") ? Number(params.get("one")) : null;
  const twoId = params.get("two") ? Number(params.get("two")) : null;

  const one = useSlot(oneId);
  const two = useSlot(twoId);

  const [comparison, setComparison] = useState<PlayerComparison | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const setSlot = (slot: "one" | "two", value: number | null) => {
    const next = new URLSearchParams(params);
    if (value === null) next.delete(slot);
    else next.set(slot, String(value));
    setParams(next);
  };

  useEffect(() => {
    if (oneId === null || twoId === null) {
      setComparison(null);
      setError(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setError(null);
    setLoading(true);
    comparePlayers(oneId, twoId, controller.signal)
      .then((data) => {
        setComparison(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof ApiError ? err.message : "Failed to compare players");
        setLoading(false);
      });
    return () => controller.abort();
  }, [oneId, twoId]);

  const tally = useMemo(() => {
    if (!comparison) return { one: 0, two: 0 };
    return comparison.metrics.reduce(
      (acc, metric) => {
        if (metric.winner === "one") acc.one += 1;
        if (metric.winner === "two") acc.two += 1;
        return acc;
      },
      { one: 0, two: 0 },
    );
  }, [comparison]);

  return (
    <section className="cmp">
      <Link to="/" className="button button--ghost">← Back to search</Link>
      <h1>Compare players</h1>
      <p className="muted">Pick two players to see who leads on each metric.</p>

      <div className="cmp__pickers">
        <PlayerPicker
          label="Player 1"
          accent="#38bdf8"
          current={one}
          onSelect={(player) => setSlot("one", player.player_id)}
          onClear={() => setSlot("one", null)}
        />
        <PlayerPicker
          label="Player 2"
          accent="#f59e0b"
          current={two}
          onSelect={(player) => setSlot("two", player.player_id)}
          onClear={() => setSlot("two", null)}
        />
      </div>

      {error && <p className="error-text">{error}</p>}

      {loading && (
        <div className="card">
          <Skeleton lines={1} />
          <Skeleton className="skeleton--chart" lines={1} />
          <Skeleton lines={4} />
        </div>
      )}

      {comparison && (
        <>
          {comparison.comparison_note && (
            <p className="cmp__note">{comparison.comparison_note}</p>
          )}
          {comparison.one.league !== comparison.two.league && (
            <p className="cmp__note">
              Different leagues ({comparison.one.league} vs {comparison.two.league}) — percentiles
              are vs each player&apos;s own market. Raw values reflect different competition levels.
            </p>
          )}

          <div className="cmp__summary card">
            <div className="cmp__summary-side" style={{ color: "#38bdf8" }}>
              <strong>{comparison.one.name}</strong>
              <span className="cmp__wins">{tally.one} metrics</span>
              <ConfidenceBadge
                level={comparison.peer_confidence_one}
                peerCount={comparison.one_peer_group_size}
              />
            </div>
            <span className="muted">leads</span>
            <div className="cmp__summary-side cmp__summary-side--right" style={{ color: "#f59e0b" }}>
              <strong>{comparison.two.name}</strong>
              <span className="cmp__wins">{tally.two} metrics</span>
              <ConfidenceBadge
                level={comparison.peer_confidence_two}
                peerCount={comparison.two_peer_group_size}
              />
            </div>
          </div>

          <div className="card">
            <h2 className="section-title">Market value</h2>
            <p className="muted section-hint">
              Value and where each sits within their own league &amp; position.
            </p>
            <ComparisonRow
              label="Market value"
              oneValue={comparison.one.market_value_eur}
              twoValue={comparison.two.market_value_eur}
              onePercentile={comparison.one_market_value_percentile}
              twoPercentile={comparison.two_market_value_percentile}
              winner={
                comparison.one.market_value_eur === comparison.two.market_value_eur
                  ? "tie"
                  : comparison.one.market_value_eur > comparison.two.market_value_eur
                    ? "one"
                    : "two"
              }
              delta={Math.abs(
                comparison.one.market_value_eur - comparison.two.market_value_eur,
              )}
              format={formatMarketValue}
              deltaFormat={formatMarketValue}
            />
          </div>

          <div className="card">
            <h2 className="section-title">Performance</h2>
            <p className="muted section-hint">
              Bar shows share; ▲ is the leader and the gap is the absolute difference.
            </p>
            <div className="cmp__rows">
              {comparison.metrics.map((metric) => (
                <ComparisonRow
                  key={metric.key}
                  label={metric.label}
                  oneValue={metric.one_value}
                  twoValue={metric.two_value}
                  onePercentile={metric.one_percentile}
                  twoPercentile={metric.two_percentile}
                  winner={metric.winner}
                  delta={metric.delta}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

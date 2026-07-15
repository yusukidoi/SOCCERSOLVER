import type { ConfidenceLevel } from "../types";

const LABELS: Record<ConfidenceLevel, string> = {
  high: "High confidence",
  medium: "Moderate confidence",
  low: "Low confidence",
};

const HINTS: Record<ConfidenceLevel, string> = {
  high: "Large peer group — percentiles are stable.",
  medium: "Moderate peer group — use percentiles with some caution.",
  low: "Small peer group — percentiles may be noisy.",
};

export default function ConfidenceBadge({
  level,
  peerCount,
}: {
  level: ConfidenceLevel;
  peerCount: number;
}) {
  return (
    <span className={`confidence confidence--${level}`} title={HINTS[level]}>
      {LABELS[level]} · {peerCount} peers
    </span>
  );
}

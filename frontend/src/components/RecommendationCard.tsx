import type { Recommendation } from "../types";

const VERDICT_LABELS: Record<Recommendation["verdict"], string> = {
  strong_signing: "Strong signing",
  good_signing: "Good signing",
  monitor: "Monitor",
  caution: "Proceed with caution",
};

export default function RecommendationCard({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  return (
    <div className={`recommendation recommendation--${recommendation.verdict}`}>
      <p className="recommendation__verdict">{VERDICT_LABELS[recommendation.verdict]}</p>
      <p className="muted section-hint">Reason</p>
      <ul className="insight-list">
        {recommendation.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

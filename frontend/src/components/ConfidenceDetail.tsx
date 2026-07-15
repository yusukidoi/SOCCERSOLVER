import type { ConfidenceAssessment } from "../types";

const LABELS = {
  high: "High confidence",
  medium: "Medium confidence",
  low: "Low confidence",
} as const;

export default function ConfidenceDetail({ confidence }: { confidence: ConfidenceAssessment }) {
  return (
    <div className={`confidence-block confidence-block--${confidence.level}`}>
      <p className="confidence-block__label">{LABELS[confidence.level]}</p>
      <p className="muted section-hint">Reasons:</p>
      <ul className="insight-list insight-list--compact">
        {confidence.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </div>
  );
}

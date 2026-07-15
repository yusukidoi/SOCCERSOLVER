import type { TeamFitRating } from "../types";

const RATING_LABELS: Record<TeamFitRating["rating"], string> = {
  excellent: "Excellent",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export default function TeamFitGrid({ teamFit }: { teamFit: TeamFitRating[] }) {
  if (teamFit.length === 0) return null;

  return (
    <div className="team-fit">
      <h3 className="subsection-title">Team fit</h3>
      <p className="muted section-hint">
        Style scores from output and availability — heuristic, not club-specific tactics.
      </p>
      <ul className="team-fit__grid">
        {teamFit.map((item) => (
          <li key={item.style} className={`team-fit__item team-fit__item--${item.rating}`}>
            <span className="team-fit__style">{item.style}</span>
            <span className="team-fit__rating">{RATING_LABELS[item.rating]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

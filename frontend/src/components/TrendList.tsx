import type { TrendItem } from "../types";

const ARROWS: Record<TrendItem["direction"], string> = {
  up: "↑",
  down: "↓",
  stable: "→",
};

export default function TrendList({ trends }: { trends: TrendItem[] }) {
  if (trends.length === 0) return null;

  return (
    <div className="trends">
      <h3 className="subsection-title">Last {5} matches</h3>
      <p className="muted section-hint">
        Recent form vs full-season rate — from appearance logs.
      </p>
      <ul className="trend-list">
        {trends.map((trend) => (
          <li key={trend.label} className={`trend trend--${trend.direction}`}>
            <span className="trend__arrow">{ARROWS[trend.direction]}</span>
            <span className="trend__label">{trend.label}</span>
            {trend.detail && <span className="trend__detail muted">{trend.detail}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}

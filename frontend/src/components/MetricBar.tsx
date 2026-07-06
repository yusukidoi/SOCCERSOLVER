import type { MetricContext } from "../types";
import { ordinalPercentile, percentileColor } from "../lib/format";

/** One metric row: raw value vs peer average, with a color-coded percentile bar. */
export default function MetricBar({ metric }: { metric: MetricContext }) {
  const color = percentileColor(metric.percentile);
  return (
    <div className="metric">
      <div className="metric__top">
        <span className="metric__label">{metric.label}</span>
        <span className="metric__value">
          {metric.value}
          <span className="muted"> · avg {metric.peer_average}</span>
        </span>
      </div>
      <div className="metric__track">
        <div
          className="metric__fill"
          style={{ width: `${metric.percentile}%`, background: color }}
        />
        <div className="metric__avg-mark" title="Position average (50th)" />
      </div>
      <span className="metric__pct" style={{ color }}>
        {ordinalPercentile(metric.percentile)} percentile
      </span>
    </div>
  );
}

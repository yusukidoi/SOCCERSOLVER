import type { Winner } from "../types";

interface Props {
  label: string;
  oneValue: number;
  twoValue: number;
  onePercentile?: number;
  twoPercentile?: number;
  winner: Winner;
  format?: (value: number) => string;
}

const ONE_COLOR = "#38bdf8";
const TWO_COLOR = "#f59e0b";

/**
 * One metric compared head to head: a single bar split proportionally between
 * the two players, the leader marked, with each value (and optional percentile).
 */
export default function ComparisonRow({
  label,
  oneValue,
  twoValue,
  onePercentile,
  twoPercentile,
  winner,
  format = (value) => String(value),
}: Props) {
  const total = oneValue + twoValue;
  const oneShare = total > 0 ? (oneValue / total) * 100 : 50;

  return (
    <div className="cmp-row">
      <div className={`cmp-row__side cmp-row__side--left ${winner === "one" ? "is-winner" : ""}`}>
        {winner === "one" && <span className="cmp-row__arrow">▲</span>}
        <span className="cmp-row__val">{format(oneValue)}</span>
        {onePercentile !== undefined && (
          <span className="cmp-row__pct">{onePercentile}th</span>
        )}
      </div>

      <div className="cmp-row__center">
        <span className="cmp-row__label">{label}</span>
        <div className="cmp-row__track">
          <div
            className="cmp-row__fill"
            style={{ width: `${oneShare}%`, background: ONE_COLOR }}
          />
          <div
            className="cmp-row__fill"
            style={{ width: `${100 - oneShare}%`, background: TWO_COLOR }}
          />
        </div>
      </div>

      <div className={`cmp-row__side cmp-row__side--right ${winner === "two" ? "is-winner" : ""}`}>
        {winner === "two" && <span className="cmp-row__arrow">▲</span>}
        <span className="cmp-row__val">{format(twoValue)}</span>
        {twoPercentile !== undefined && (
          <span className="cmp-row__pct">{twoPercentile}th</span>
        )}
      </div>
    </div>
  );
}

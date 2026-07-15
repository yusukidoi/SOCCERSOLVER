/** Format a euro market value compactly, e.g. 200000000 -> "€200.0M". */
export function formatMarketValue(value: number): string {
  if (value >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value}`;
}

/** Ordinal-style percentile label, e.g. 82 -> "82nd". */
export function ordinalPercentile(percentile: number): string {
  const suffix =
    percentile % 10 === 1 && percentile % 100 !== 11
      ? "st"
      : percentile % 10 === 2 && percentile % 100 !== 12
        ? "nd"
        : percentile % 10 === 3 && percentile % 100 !== 13
          ? "rd"
          : "th";
  return `${percentile}${suffix}`;
}

/** Color for a percentile: red (low) -> amber (mid) -> green (high). */
export function percentileColor(percentile: number): string {
  if (percentile >= 75) return "#16a34a";
  if (percentile >= 50) return "#65a30d";
  if (percentile >= 25) return "#d97706";
  return "#dc2626";
}

/** Show the absolute gap on comparison rows, e.g. "▲ +0.04". */
export function formatDelta(
  delta: number,
  winner: "one" | "two" | "tie",
  format?: (value: number) => string,
): string {
  if (winner === "tie" || delta === 0) return "Even";
  const value = format ? format(delta) : Number.isInteger(delta) ? String(delta) : delta.toFixed(2);
  return `▲ +${value}`;
}

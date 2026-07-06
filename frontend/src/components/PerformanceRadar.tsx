import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { MetricContext } from "../types";

interface Props {
  metrics: MetricContext[];
}

/**
 * Radar of the player's percentile per metric, overlaid on a 50th-percentile
 * baseline so "above / below the position average" is immediately visible.
 */
export default function PerformanceRadar({ metrics }: Props) {
  const data = metrics.map((metric) => ({
    label: metric.label,
    percentile: metric.percentile,
    average: 50,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
        <Radar
          name="Position average"
          dataKey="average"
          stroke="#64748b"
          fill="#64748b"
          fillOpacity={0.12}
        />
        <Radar
          name="Player percentile"
          dataKey="percentile"
          stroke="#38bdf8"
          fill="#38bdf8"
          fillOpacity={0.45}
        />
        <Tooltip
          contentStyle={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 8,
            color: "#e2e8f0",
          }}
          formatter={(value: number, name: string) => [`${value}`, name]}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}

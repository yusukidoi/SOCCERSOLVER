// Types mirror the backend Pydantic models (see backend/app/models).

export interface PlayerSummary {
  player_id: number;
  name: string;
  position: string;
  sub_position: string;
  age: number | null;
  club: string;
  league: string;
  market_value_eur: number;
}

export interface Player extends PlayerSummary {
  minutes_played: number;
  matches_played: number;
  goals: number;
  assists: number;
  goal_contributions: number;
  yellow_cards: number;
  red_cards: number;
  goals_per90: number;
  assists_per90: number;
  goal_contributions_per90: number;
}

export type ConfidenceLevel = "high" | "medium" | "low";

export interface MetricContext {
  key: string;
  label: string;
  value: number;
  peer_average: number;
  percentile: number;
  higher_is_better: boolean;
}

export interface PlayerProfile {
  player: Player;
  peer_group_label: string;
  peer_group_size: number;
  peer_confidence: ConfidenceLevel;
  market_value_percentile: number;
  metrics: MetricContext[];
}

export type Winner = "one" | "two" | "tie";

export interface ComparisonMetric {
  key: string;
  label: string;
  higher_is_better: boolean;
  one_value: number;
  two_value: number;
  one_percentile: number;
  two_percentile: number;
  winner: Winner;
  delta: number;
}

export interface PlayerComparison {
  one: Player;
  two: Player;
  one_market_value_percentile: number;
  two_market_value_percentile: number;
  one_peer_group_size: number;
  two_peer_group_size: number;
  peer_confidence_one: ConfidenceLevel;
  peer_confidence_two: ConfidenceLevel;
  comparison_note: string | null;
  metrics: ComparisonMetric[];
}

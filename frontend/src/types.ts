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
  avg_minutes_per_match: number;
  goals: number;
  assists: number;
  goal_contributions: number;
  yellow_cards: number;
  red_cards: number;
  goals_per90: number;
  assists_per90: number;
  goal_contributions_per90: number;
  highest_market_value_eur: number;
  market_value_pct_of_peak: number;
  last5_matches: number;
  last5_minutes: number;
  last5_goals: number;
  last5_assists: number;
  last5_goal_contributions: number;
  last5_goals_per90: number;
  last5_assists_per90: number;
  last5_goal_contributions_per90: number;
  progressive_passes_per90: number;
  defensive_actions_per90: number;
}

export type ConfidenceLevel = "high" | "medium" | "low";
export type TrendDirection = "up" | "down" | "stable";
export type FitRating = "excellent" | "high" | "medium" | "low";
export type RecommendationVerdict = "strong_signing" | "good_signing" | "monitor" | "caution";
export type ScenarioLevel = "higher" | "lower" | "similar";

export interface MetricContext {
  key: string;
  label: string;
  value: number;
  peer_average: number;
  percentile: number;
  higher_is_better: boolean;
}

export interface SimilarPlayer {
  player: PlayerSummary;
  similarity: number;
  lower_market_value: boolean;
  value_savings_eur: number | null;
}

export interface ConfidenceAssessment {
  level: ConfidenceLevel;
  reasons: string[];
}

export interface TrendItem {
  label: string;
  direction: TrendDirection;
  detail: string | null;
}

export interface TeamFitRating {
  style: string;
  rating: FitRating;
}

export interface Recommendation {
  verdict: RecommendationVerdict;
  reasons: string[];
}

export interface PlayerScenario {
  upside: ScenarioLevel;
  risk: ScenarioLevel;
  consistency: ScenarioLevel;
  summary: string;
}

export interface PlayerProfile {
  player: Player;
  peer_group_label: string;
  peer_group_size: number;
  peer_confidence: ConfidenceLevel;
  confidence: ConfidenceAssessment;
  market_value_percentile: number;
  metrics: MetricContext[];
  explainability: string[];
  strengths: string[];
  risks: string[];
  trends: TrendItem[];
  team_fit: TeamFitRating[];
  recommendation: Recommendation | null;
  similar_players: SimilarPlayer[];
  value_alternatives: SimilarPlayer[];
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
  scenario_one: PlayerScenario | null;
  scenario_two: PlayerScenario | null;
  metrics: ComparisonMetric[];
}

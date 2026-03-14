export interface Game {
  away: string;
  home: string;
  label: string;
}

export interface Injury {
  player: string;
  status: string;
  reason: string;
}

export interface Pick {
  player: string;
  team: string;
  opponent: string;
  game: string;
  stat: 'PTS' | 'REB' | 'AST';
  line: number;
  over_odds: number;
  book: string;
  model_prob: number;
  implied_prob: number;
  edge: number;
  ev: number;
  season_avg: number;
  last_5_avg: number;
  last_3_avg: number;
  is_home: 0 | 1;
  has_live_line: boolean;
}

export interface Parlay {
  legs: string[];
  combined_prob: number;
  players: string[];
}

export interface ModelStats {
  [stat: string]: {
    auc: number;
    hit_rate_70: number;
  };
}

export interface ResultDetail {
  player: string;
  stat: string;
  line: number;
  actual: number;
  hit: boolean;
}

export interface Results {
  picks_total: number;
  picks_hit: number;
  hit_rate: number;
  locks_hit: number;
  locks_total: number;
  parlay_3_hit: boolean;
  parlay_5_hit: boolean;
  details: ResultDetail[];
}

export interface DayPicks {
  date: string;
  generated_at: string;
  model_version: string;
  games: Game[];
  injuries: Injury[];
  picks: Pick[];
  locks: string[];
  parlay_3leg: Parlay;
  parlay_5leg: Parlay;
  model_stats: ModelStats;
  results: Results | null;
}

export interface HistorySummary {
  date: string;
  picks_total: number;
  picks_hit: number;
  hit_rate: number;
  parlay_3_hit: boolean;
  parlay_5_hit: boolean;
}

export interface Metrics {
  training: {
    total_logs: number;
    players: number;
    seasons: number;
    date_range: { start: string; end: string };
  };
  models: {
    [stat: string]: {
      auc: number;
      accuracy: number;
      brier_score: number;
      log_loss: number;
      hit_rates: { [threshold: string]: number };
    };
  };
  feature_importance: {
    PTS: { feature: string; importance: number }[];
    REB: { feature: string; importance: number }[];
    AST: { feature: string; importance: number }[];
  };
  calibration: {
    [stat: string]: { pred_prob: number; actual_rate: number }[];
  };
}

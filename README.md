# NBA ML Parlay Model

## Overview

Machine learning approach to NBA player prop betting, replacing the v3.1 
Normal CDF model with XGBoost trained on 3+ seasons of historical data.

Based on CRISP-DM framework (Cross-Industry Standard Process for Data Mining).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                       │
│  collect_data.py                                         │
│                                                          │
│  nba_api ──→ Game logs, advanced stats, team stats       │
│  ESPN    ──→ Schedule, injuries                          │
│  Odds API──→ Historical sportsbook lines                 │
│              ↓                                           │
│         parlay_ml.db (SQLite)                            │
│         9 tables, ~100K+ rows                            │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                 FEATURE ENGINEERING                       │
│  collect_data.py --features                              │
│                                                          │
│  Rolling averages (3/5/10/20 game windows)               │
│  Volatility (std dev over 10 games)                      │
│  Trends (last 3 vs last 10)                              │
│  Opponent defensive stats                                │
│  Context (home/away, B2B, rest days)                     │
│  Interaction terms (usage × pace, etc.)                  │
│  Position encoding                                       │
│              ↓                                           │
│         features_YYYY_YY.csv                             │
│         50+ features per sample                          │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                    MODEL TRAINING                        │
│  train_model.py                                          │
│                                                          │
│  Separate XGBoost model per stat (PTS, REB, AST...)      │
│  Out-of-time validation (train 23-25, test 25-26)        │
│  L1/L2 regularization for feature selection              │
│  Early stopping to prevent overfitting                   │
│  Probability calibration                                 │
│              ↓                                           │
│         models/model_pts.pkl                             │
│         models/model_reb.pkl                             │
│         models/model_ast.pkl                             │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│                    INFERENCE                              │
│  parlay_engine_v4.py (future)                            │
│                                                          │
│  Today's data ──→ Feature engineering ──→ model.predict() │
│                                              ↓            │
│                                    P(over) per pick       │
│                                              ↓            │
│                                    Edge = P - implied     │
│                                              ↓            │
│                                    Rank + build parlays   │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Step 1: Install dependencies
```bash
pip install nba_api requests beautifulsoup4 pandas xgboost scikit-learn
```

### Step 2: Collect data (takes 2-4 hours per season due to API rate limits)
```bash
# Collect 3 seasons of data
python3 collect_data.py --seasons 2023-24 2024-25 2025-26

# Or just current season for testing
python3 collect_data.py --seasons 2025-26

# Skip play-by-play to save time
python3 collect_data.py --seasons 2025-26 --skip-pbp

# Include daily odds snapshot
python3 collect_data.py --update --odds-key YOUR_API_KEY
```

### Step 3: Train models
```bash
# Train PTS, REB, AST models
python3 train_model.py --train-seasons 2023-24 2024-25 --test-season 2025-26

# Train all stat types
python3 train_model.py --stats PTS REB AST STL BLK 3PM
```

### Step 4: Daily workflow
```bash
# 1. Update today's data
python3 collect_data.py --update

# 2. Snapshot today's odds
python3 collect_data.py --update --odds-key YOUR_API_KEY

# 3. Run parlay engine with ML model (v4 — future)
python3 parlay_engine_v4.py
```

## Database Schema

| Table | Description | Key Fields |
|-------|-------------|------------|
| `player_game_logs` | Core data — 1 row per player per game | pts, reb, ast, usg_pct, ts_pct |
| `team_game_stats` | Team totals per game | off_rating, def_rating, pace |
| `team_season_stats` | Season-level team stats | opp_pts, opp_fg_pct, def_rating |
| `schedule` | Full schedule with rest days | days_rest, is_b2b |
| `injuries` | Historical injury reports | status, reason, report_date |
| `odds_snapshots` | Sportsbook lines over time | line, over_odds, book |
| `play_by_play` | Detailed play-by-play | event_type, score_margin |
| `player_info` | Static player metadata | position, height, experience |
| `collection_log` | Tracks collection progress | task, status, rows_collected |

## Feature Categories

### Category 1: Rolling Player Performance
- `pts_last_3`, `pts_last_5`, `pts_last_10`, `pts_last_20`
- `pts_std_10` (volatility)
- `pts_season_avg`
- `pts_trend` (last 3 minus last 10 — hot/cold streak)
- Same for REB, AST, STL, BLK, 3PM, MIN, USG%, TS%

### Category 2: Opponent/Matchup
- `opp_def_rating` — opponent's defensive efficiency
- `opp_pace` — opponent's pace of play
- `opp_pts_allowed` — points allowed per game
- `opp_opp_fg_pct` — opponent's FG% allowed

### Category 3: Context
- `is_home` — home court advantage
- `days_rest` — days since last game
- `is_b2b` — second night of back-to-back
- `games_in_last_7` — fatigue indicator

### Category 4: Market
- `sportsbook_line` — the actual line from DraftKings/FanDuel
- `over_odds` — American odds for the over
- `implied_probability` — book's implied probability

### Category 5: Interactions
- `usage_x_pace` — high usage + fast pace = more scoring
- `min_x_opp_def` — minutes weighted by opponent quality
- Position dummies (guard, forward, center)

## Notes

- **API Rate Limits**: nba_api needs ~0.7s between calls. Full collection 
  for 3 seasons takes 6-12 hours. Use `--skip-pbp` to cut this in half.
- **Historical Odds**: The hardest data to get. Start without it and add
  market features later as you collect daily snapshots.
- **Concept Drift**: The NBA changes every year. Retrain monthly with 
  `python3 train_model.py` using the latest data.
- **Feature Selection**: We include 50+ features and let XGBoost's L1 
  regularization (reg_alpha=1.0) handle selection. Check `top_features` 
  in training output to see what the model actually uses.

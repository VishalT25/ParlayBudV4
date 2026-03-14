#!/usr/bin/env python3
"""
train_model.py — NBA ML Parlay Model: Feature Engineering + XGBoost Training

Works with data collected by collect_bbref.py.

Pipeline:
  1. Load game logs + season stats + team stats from SQLite
  2. Engineer rolling features (last 3/5/10 games), opponent features, context
  3. Create binary target: did player go over the estimated line?
  4. Train XGBoost with L1/L2 regularization per stat type
  5. Out-of-time validation (train 2023-25, test 2025-26)
  6. Save models for integration with parlay_engine

Usage:
  pip install xgboost scikit-learn pandas
  python3 train_model.py
  python3 train_model.py --stats PTS REB AST STL BLK 3PM
"""

import os
import sys
import json
import sqlite3
import pickle
import argparse
import logging
import warnings
from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

try:
    import xgboost as xgb
    from sklearn.metrics import (
        brier_score_loss, log_loss, roc_auc_score, accuracy_score,
    )
    from sklearn.calibration import calibration_curve
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("❌ Install deps: pip install xgboost scikit-learn")

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger("train")

DB_PATH = "parlay_ml.db"

STAT_MAP = {
    'PTS': 'pts', 'REB': 'reb', 'AST': 'ast',
    'STL': 'stl', 'BLK': 'blk', '3PM': 'fg3',
}

LINE_OFFSET = {
    'PTS': 2.5, 'REB': 1.5, 'AST': 1.0,
    'STL': 0.3, 'BLK': 0.3, '3PM': 0.5,
}


def load_data(db_path):
    conn = sqlite3.connect(db_path)
    log.info("Loading data...")
    game_logs = pd.read_sql("SELECT * FROM player_game_logs WHERE mp_float > 0", conn)
    advanced = pd.read_sql("SELECT * FROM season_stats_advanced", conn)
    team_stats = pd.read_sql("SELECT * FROM team_stats", conn)
    pergame = pd.read_sql("SELECT * FROM season_stats_pergame", conn)
    conn.close()
    log.info(f"  Game logs: {len(game_logs)} rows, {game_logs['player'].nunique()} players")
    log.info(f"  Advanced: {len(advanced)}, Teams: {len(team_stats)}, PerGame: {len(pergame)}")
    return game_logs, advanced, team_stats, pergame


def engineer_features(game_logs, advanced, team_stats, pergame):
    log.info("Engineering features...")
    df = game_logs.copy()
    df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
    df = df.dropna(subset=['game_date'])
    df = df.sort_values(['player', 'season', 'game_date']).reset_index(drop=True)

    # ── Rolling windows ──
    roll_cols = ['pts', 'reb', 'ast', 'stl', 'blk', 'fg3', 'tov',
                 'mp_float', 'fga', 'fta', 'fg_pct', 'fg3_pct', 'ft_pct',
                 'game_score', 'plus_minus', 'orb', 'drb']

    log.info("  Rolling averages (3/5/10)...")
    for col in roll_cols:
        if col not in df.columns:
            continue
        g = df.groupby('player')[col]
        for w in [3, 5, 10]:
            df[f'{col}_avg_{w}'] = g.transform(lambda x: x.shift(1).rolling(w, min_periods=1).mean())
        df[f'{col}_std_10'] = g.transform(lambda x: x.shift(1).rolling(10, min_periods=3).std())
        df[f'{col}_season_avg'] = g.transform(lambda x: x.shift(1).expanding(min_periods=1).mean())

    # ── Trends ──
    log.info("  Trends...")
    for col in ['pts', 'reb', 'ast', 'fg3', 'stl', 'blk']:
        a3, a10 = f'{col}_avg_3', f'{col}_avg_10'
        if a3 in df.columns and a10 in df.columns:
            df[f'{col}_trend'] = df[a3] - df[a10]

    # ── Efficiency ──
    df['ts_proxy'] = df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])).replace(0, np.nan)
    df['ts_proxy_avg_5'] = df.groupby('player')['ts_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())
    df['usage_proxy'] = df['fga'] / df['mp_float'].replace(0, np.nan)
    df['usage_proxy_avg_5'] = df.groupby('player')['usage_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())

    # ── Context ──
    log.info("  Context...")
    df['is_home'] = df['is_home'].fillna(0).astype(int)
    df['is_b2b'] = df['is_b2b'].fillna(0).astype(int)
    df['days_rest'] = df['days_rest'].fillna(3)
    df['game_number'] = df['game_number'].fillna(1)
    df['rest_0_1'] = (df['days_rest'] <= 1).astype(int)
    df['rest_3plus'] = (df['days_rest'] >= 3).astype(int)
    df['won'] = df['result'].str.startswith('W', na=False).astype(int)
    df['win_streak_5'] = df.groupby('player')['won'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).sum())

    # ── Advanced stats merge ──
    log.info("  Merging advanced stats...")
    if len(advanced) > 0:
        adv_cols = ['player', 'season', 'per', 'ts_pct', 'usg_pct',
                    'ast_pct', 'stl_pct', 'blk_pct', 'tov_pct',
                    'reb_pct', 'orb_pct', 'drb_pct',
                    'obpm', 'dbpm', 'bpm', 'vorp',
                    'ows', 'dws', 'ws', 'ws_per_48']
        avail = [c for c in adv_cols if c in advanced.columns]
        adv_merge = advanced[avail].drop_duplicates(subset=['player', 'season'])
        df = df.merge(adv_merge, on=['player', 'season'], how='left', suffixes=('', '_adv'))

    # ── Opponent features ──
    log.info("  Opponent stats...")
    if len(team_stats) > 0:
        opp = team_stats[team_stats['stat_type'] == 'opponent'].copy()
        if len(opp) > 0:
            opp_m = opp[['team', 'season', 'pts', 'fg_pct', 'fg3_pct',
                         'reb', 'ast', 'stl', 'blk', 'tov']].copy()
            opp_m.columns = ['opponent', 'season', 'opp_pts_allowed', 'opp_fg_pct_allowed',
                             'opp_fg3_pct_allowed', 'opp_reb_allowed', 'opp_ast_allowed',
                             'opp_stl_rate', 'opp_blk_rate', 'opp_tov_forced']
            df = df.merge(opp_m, on=['opponent', 'season'], how='left')

        own = team_stats[team_stats['stat_type'] == 'team'].copy()
        if len(own) > 0:
            own_m = own[['team', 'season', 'pts', 'fga']].copy()
            own_m.columns = ['opponent', 'season', 'opp_team_pts', 'opp_team_fga']
            df = df.merge(own_m, on=['opponent', 'season'], how='left')

    # ── Interactions ──
    log.info("  Interactions...")
    if 'usg_pct' in df.columns and 'opp_team_fga' in df.columns:
        df['usage_x_opp_pace'] = df['usg_pct'] * df['opp_team_fga']
    if 'pts_avg_5' in df.columns and 'opp_pts_allowed' in df.columns:
        df['pts_avg_x_opp_allowed'] = df['pts_avg_5'] * df['opp_pts_allowed']
    if 'reb_avg_5' in df.columns and 'opp_reb_allowed' in df.columns:
        df['reb_avg_x_opp_allowed'] = df['reb_avg_5'] * df['opp_reb_allowed']
    if 'ast_avg_5' in df.columns and 'opp_ast_allowed' in df.columns:
        df['ast_avg_x_opp_allowed'] = df['ast_avg_5'] * df['opp_ast_allowed']

    # ── Position encoding ──
    if 'pos' in df.columns:
        df['is_guard'] = df['pos'].str.contains('G', na=False).astype(int)
        df['is_forward'] = df['pos'].str.contains('F', na=False).astype(int)
        df['is_center'] = df['pos'].str.contains('C', na=False).astype(int)

    df = df[df['game_number'] >= 4].copy()
    n_feat = len([c for c in df.columns if df[c].dtype in ['float64', 'int64']])
    log.info(f"  ✅ {n_feat} numeric features, {len(df)} rows")
    return df


def get_feature_columns(df):
    exclude = {
        'id', 'pts', 'reb', 'ast', 'stl', 'blk', 'fg3', 'tov',
        'fg', 'fga', 'fg_pct', 'fg3a', 'fg3_pct', 'ft', 'fta', 'ft_pct',
        'orb', 'drb', 'pf', 'mp_float', 'game_score', 'plus_minus',
        'target', 'line', 'actual_value', 'ts_proxy', 'usage_proxy', 'won', 'started',
    }
    return [c for c in df.columns
            if c not in exclude
            and df[c].dtype in ['float64', 'int64', 'float32', 'int32']
            and df[c].isnull().sum() / len(df) < 0.8]


def create_dataset(df, stat):
    col = STAT_MAP.get(stat)
    if col not in df.columns:
        return pd.DataFrame()
    result = df.copy()
    avg_col = f'{col}_season_avg'
    if avg_col not in result.columns:
        return pd.DataFrame()
    offset = LINE_OFFSET.get(stat, 1.5)
    result['line'] = (result[avg_col] - offset).round(0) + 0.5
    result['line'] = result['line'].clip(lower=0.5)
    result['actual_value'] = result[col]
    result['target'] = (result[col] > result['line']).astype(int)
    return result.dropna(subset=['target', 'line'])


def train_one_stat(train_df, test_df, features, stat):
    log.info(f"\n{'='*60}")
    log.info(f"  TRAINING: {stat}")
    log.info(f"{'='*60}")

    X_train = train_df[features].fillna(-999).values
    y_train = train_df['target'].values
    X_test = test_df[features].fillna(-999).values
    y_test = test_df['target'].values

    log.info(f"  Train: {len(X_train)} ({y_train.mean():.1%} positive)")
    log.info(f"  Test:  {len(X_test)} ({y_test.mean():.1%} positive)")
    log.info(f"  Features: {len(features)}")

    model = xgb.XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        reg_alpha=1.0, reg_lambda=2.0,
        min_child_weight=10, gamma=0.1,
        objective='binary:logistic', eval_metric='logloss',
        random_state=42, n_jobs=-1, use_label_encoder=False,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob) if len(set(y_test)) > 1 else 0
    brier = brier_score_loss(y_test, y_prob)
    ll = log_loss(y_test, y_prob)

    log.info(f"\n  📊 Accuracy: {acc:.3f} | AUC: {auc:.3f} | Brier: {brier:.4f} | LogLoss: {ll:.4f}")

    # Feature importance
    imp = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    log.info(f"\n  🔑 TOP 15 FEATURES:")
    for i, (f, v) in enumerate(imp.head(15).items()):
        log.info(f"    {i+1:2d}. {f:40s} {v:.4f} {'█' * int(v * 200)}")

    # Calibration
    try:
        pt, pp = calibration_curve(y_test, y_prob, n_bins=8, strategy='uniform')
        log.info(f"\n  📐 CALIBRATION:")
        for t, p in zip(pt, pp):
            d = t - p
            m = '✅' if abs(d) < 0.05 else '⚠️' if abs(d) < 0.10 else '❌'
            log.info(f"    Predicted: {p:.2f} → Actual: {t:.2f} ({d:+.2f}) {m}")
    except Exception:
        pass

    # Profit sim
    log.info(f"\n  💰 HIT RATE BY CONFIDENCE:")
    for thr in [0.55, 0.60, 0.65, 0.70, 0.75]:
        mask = y_prob >= thr
        if mask.sum() == 0:
            continue
        hits = y_test[mask].sum()
        total = mask.sum()
        log.info(f"    P >= {thr:.0%}: {hits}/{total} = {hits/total:.1%}")

    metrics = {
        'stat': stat, 'accuracy': float(acc), 'roc_auc': float(auc),
        'brier_score': float(brier), 'log_loss': float(ll),
        'train_samples': int(len(X_train)), 'test_samples': int(len(X_test)),
        'n_features': len(features), 'positive_rate': float(y_test.mean()),
        'top_features': {k: float(v) for k, v in imp.head(20).items()},
    }
    return model, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DB_PATH)
    parser.add_argument('--stats', nargs='+', default=['PTS', 'REB', 'AST'])
    parser.add_argument('--train-seasons', nargs='+', default=['2023-24', '2024-25'])
    parser.add_argument('--test-season', default='2025-26')
    parser.add_argument('--output-dir', default='models')
    args = parser.parse_args()

    if not HAS_ML:
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    print("=" * 60)
    print("  🧠 NBA ML PARLAY MODEL — TRAINING")
    print(f"  Train: {', '.join(args.train_seasons)}")
    print(f"  Test:  {args.test_season}")
    print(f"  Stats: {', '.join(args.stats)}")
    print("=" * 60)

    game_logs, advanced, team_stats, pergame = load_data(args.db)
    df = engineer_features(game_logs, advanced, team_stats, pergame)
    features = get_feature_columns(df)
    log.info(f"\n📋 {len(features)} features selected")

    all_metrics = {}
    for stat in args.stats:
        stat_df = create_dataset(df, stat)
        if len(stat_df) == 0:
            log.warning(f"No data for {stat}")
            continue

        train_df = stat_df[stat_df['season'].isin(args.train_seasons)]
        test_df = stat_df[stat_df['season'] == args.test_season]

        if len(train_df) < 100 or len(test_df) < 50:
            log.warning(f"Not enough data for {stat}")
            continue

        model, metrics = train_one_stat(train_df, test_df, features, stat)
        all_metrics[stat] = metrics

        path = os.path.join(args.output_dir, f'model_{stat.lower()}.pkl')
        with open(path, 'wb') as f:
            pickle.dump({
                'model': model, 'features': features, 'stat': stat,
                'metrics': metrics, 'trained_at': datetime.now().isoformat(),
                'train_seasons': args.train_seasons, 'test_season': args.test_season,
            }, f)
        log.info(f"  💾 Saved → {path}")

    print(f"\n{'='*60}")
    print("  📊 SUMMARY")
    print(f"{'='*60}")
    print(f"\n  {'Stat':<6} {'Acc':>7} {'AUC':>7} {'Brier':>8} {'LogLoss':>8} {'N':>7}")
    print(f"  {'-'*45}")
    for s, m in all_metrics.items():
        print(f"  {s:<6} {m['accuracy']:>7.3f} {m['roc_auc']:>7.3f} "
              f"{m['brier_score']:>8.4f} {m['log_loss']:>8.4f} {m['test_samples']:>7}")

    with open(os.path.join(args.output_dir, 'metrics.json'), 'w') as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n✅ Models saved to {args.output_dir}/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
parlay_engine_v4.py — ML-Powered NBA Parlay Engine

XGBoost replaces Normal CDF. Professor's CRISP-DM framework:
  - 132 features per pick (rolling avgs, opponent defense, interactions)
  - Separate models per stat type
  - Probability calibration verified
  - Out-of-time validated on 2025-26 season

Usage:
  python3 parlay_engine_v4.py
  python3 parlay_engine_v4.py --fetch-odds
  python3 parlay_engine_v4.py --min-prob 0.65
"""

import os, sys, re, json, math, pickle, sqlite3, argparse, logging, time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# ============================================================
# CONFIG
# ============================================================

# ⬇️ FLIP THIS TO True TO FETCH LIVE SPORTSBOOK ODDS ⬇️
FETCH_ODDS = False   # True = pull live lines from Odds API
                     # False = preview mode (ML probabilities only)

DB_PATH = "parlay_ml.db"
MODELS_DIR = "models"
ODDS_API_KEY = "1352e9cd8058c67615efe0896a44f5f1"
SEASON = "2025-26"
MIN_PROB = 0.60      # minimum ML probability to show a pick
MIN_EDGE = 0.05      # minimum edge (model_prob - implied) for live odds mode
ACTIVE_STATS = ["PTS", "REB", "AST"]  # STL/BLK excluded (poor model performance)
STAT_MAP = {'PTS': 'pts', 'REB': 'reb', 'AST': 'ast', 'STL': 'stl', 'BLK': 'blk', '3PM': 'fg3'}
LINE_OFFSET = {'PTS': 2.5, 'REB': 1.5, 'AST': 1.0, 'STL': 0.3, 'BLK': 0.3, '3PM': 0.5}

ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_ABBR = {"GS": "GSW", "SA": "SAS", "NY": "NYK", "NO": "NOP", "WSH": "WAS"}
BBREF_ABBR = {"BRK": "BKN", "CHO": "CHA", "PHO": "PHX"}
MARKET_MAP = {"player_points": "PTS", "player_rebounds": "REB", "player_assists": "AST", "player_threes": "3PM"}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("v4")

W = 100  # output width


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Pick:
    player: str
    team: str
    opponent: str
    game: str
    stat: str
    line: float
    over_odds: int
    book: str
    model_prob: float
    implied_prob: float
    edge: float
    ev: float
    season_avg: float
    last_5_avg: float
    last_3_avg: float
    is_home: int
    is_b2b: int
    days_rest: float
    has_live_line: bool


# ============================================================
# LOAD MODELS
# ============================================================

def load_models(models_dir):
    models = {}
    for stat in ACTIVE_STATS:
        path = os.path.join(models_dir, f"model_{stat.lower()}.pkl")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = pickle.load(f)
                models[stat] = data
                m = data.get('metrics', {})
                log.info(f"  {stat}: AUC={m.get('roc_auc',0):.3f}, trained {data.get('trained_at','?')[:10]}")
    return models


# ============================================================
# ESPN: GAMES + INJURIES
# ============================================================

def fetch_games():
    if not HAS_REQUESTS:
        return {}
    today = datetime.now().strftime("%Y%m%d")
    try:
        r = requests.get(ESPN_SCOREBOARD, params={"dates": today}, headers=HEADERS, timeout=15)
        data = r.json()
    except Exception as e:
        log.warning(f"ESPN games failed: {e}")
        return {}

    games = {}
    for ev in data.get("events", []):
        comp = ev.get("competitions", [{}])[0]
        home = away = ""
        for t in comp.get("competitors", []):
            a = t.get("team", {}).get("abbreviation", "")
            a = ESPN_ABBR.get(a, a)
            if t.get("homeAway") == "home":
                home = a
            else:
                away = a
        if home and away:
            games[f"{away} @ {home}"] = (away, home)
    return games


def fetch_injuries():
    if not HAS_REQUESTS:
        return {}
    injuries = {}
    try:
        r = requests.get("https://www.espn.com/nba/injuries", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                a = cells[0].find('a')
                name = a.get_text(strip=True) if a else cells[0].get_text(strip=True)
                if not name or len(name) < 3 or name.upper() in ('NAME', 'PLAYER'):
                    continue
                status = cells[3].get_text(strip=True)
                if status.upper() == "OUT":
                    injuries[name] = "OUT"
    except Exception as e:
        log.warning(f"Injury scrape failed: {e}")
    return injuries


# ============================================================
# ODDS API
# ============================================================

def american_to_implied(odds):
    if odds < 0:
        return -odds / (-odds + 100.0)
    return 100.0 / (odds + 100.0)


def fetch_odds(api_key):
    if not HAS_REQUESTS or not api_key:
        return {}
    print("\n🌐 Fetching live sportsbook lines...")
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/basketball_nba/events",
                         params={"apiKey": api_key}, timeout=15)
        events = r.json()
        rem = r.headers.get("x-requests-remaining", "?")
        print(f"   {len(events)} events (API calls left: {rem})")
    except Exception as e:
        log.warning(f"Odds failed: {e}")
        return {}

    markets = "player_points,player_rebounds,player_assists,player_threes"
    lines = {}
    for i, ev in enumerate(events):
        if i > 0:
            time.sleep(1.5)
        try:
            r2 = requests.get(
                f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{ev['id']}/odds",
                params={"apiKey": api_key, "regions": "us", "markets": markets,
                        "oddsFormat": "american"}, timeout=15)
            for bm in r2.json().get('bookmakers', []):
                book = bm.get('title', '')
                for mkt in bm.get('markets', []):
                    stat = MARKET_MAP.get(mkt.get('key', ''))
                    if not stat:
                        continue
                    outs = {}
                    for o in mkt.get('outcomes', []):
                        p = o.get('description', '')
                        if p not in outs:
                            outs[p] = {'line': o.get('point', 0)}
                        if o.get('name') == 'Over':
                            outs[p]['over'] = o.get('price', -110)
                    for p, v in outs.items():
                        key = f"{p}|{stat}"
                        if key not in lines or v.get('line', 999) < lines[key]['line']:
                            lines[key] = {'line': v['line'], 'over_odds': v.get('over', -110), 'book': book}
        except Exception:
            continue
    print(f"   ✅ {len(lines)} prop lines")
    return lines


# ============================================================
# FEATURE ENGINEERING (must match training exactly)
# ============================================================

def build_features(db_path, season, tonight_players):
    """Build feature vectors for tonight's players using their game history."""
    conn = sqlite3.connect(db_path)
    gl = pd.read_sql("SELECT * FROM player_game_logs WHERE mp_float > 0 AND season = ? ORDER BY game_date",
                      conn, params=(season,))
    adv = pd.read_sql("SELECT * FROM season_stats_advanced WHERE season = ?", conn, params=(season,))
    ts = pd.read_sql("SELECT * FROM team_stats WHERE season = ?", conn, params=(season,))
    conn.close()

    if len(gl) == 0:
        return pd.DataFrame()

    df = gl.copy()
    df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
    df = df.dropna(subset=['game_date']).sort_values(['player', 'game_date']).reset_index(drop=True)

    # Rolling features
    roll_cols = ['pts', 'reb', 'ast', 'stl', 'blk', 'fg3', 'tov',
                 'mp_float', 'fga', 'fta', 'fg_pct', 'fg3_pct', 'ft_pct',
                 'game_score', 'plus_minus', 'orb', 'drb']
    for col in roll_cols:
        if col not in df.columns:
            continue
        g = df.groupby('player')[col]
        for w in [3, 5, 10]:
            df[f'{col}_avg_{w}'] = g.transform(lambda x: x.shift(1).rolling(w, min_periods=1).mean())
        df[f'{col}_std_10'] = g.transform(lambda x: x.shift(1).rolling(10, min_periods=3).std())
        df[f'{col}_season_avg'] = g.transform(lambda x: x.shift(1).expanding(min_periods=1).mean())

    # Trends
    for col in ['pts', 'reb', 'ast', 'fg3', 'stl', 'blk']:
        a3, a10 = f'{col}_avg_3', f'{col}_avg_10'
        if a3 in df.columns and a10 in df.columns:
            df[f'{col}_trend'] = df[a3] - df[a10]

    # Efficiency
    df['ts_proxy'] = df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])).replace(0, np.nan)
    df['ts_proxy_avg_5'] = df.groupby('player')['ts_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())
    df['usage_proxy'] = df['fga'] / df['mp_float'].replace(0, np.nan)
    df['usage_proxy_avg_5'] = df.groupby('player')['usage_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())

    # Context
    df['is_home'] = df['is_home'].fillna(0).astype(int)
    df['is_b2b'] = df['is_b2b'].fillna(0).astype(int)
    df['days_rest'] = df['days_rest'].fillna(3)
    df['game_number'] = df['game_number'].fillna(1)
    df['rest_0_1'] = (df['days_rest'] <= 1).astype(int)
    df['rest_3plus'] = (df['days_rest'] >= 3).astype(int)
    df['won'] = df['result'].str.startswith('W', na=False).astype(int)
    df['win_streak_5'] = df.groupby('player')['won'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).sum())

    # Advanced stats
    if len(adv) > 0:
        acols = ['player', 'season', 'per', 'ts_pct', 'usg_pct', 'ast_pct', 'stl_pct',
                 'blk_pct', 'tov_pct', 'reb_pct', 'orb_pct', 'drb_pct',
                 'obpm', 'dbpm', 'bpm', 'vorp', 'ows', 'dws', 'ws', 'ws_per_48']
        avail = [c for c in acols if c in adv.columns]
        df = df.merge(adv[avail].drop_duplicates(subset=['player', 'season']),
                      on=['player', 'season'], how='left', suffixes=('', '_adv'))

    # Opponent stats
    if len(ts) > 0:
        opp = ts[ts['stat_type'] == 'opponent'].copy()
        if len(opp) > 0:
            om = opp[['team', 'season', 'pts', 'fg_pct', 'fg3_pct', 'reb', 'ast', 'stl', 'blk', 'tov']].copy()
            om.columns = ['opponent', 'season', 'opp_pts_allowed', 'opp_fg_pct_allowed',
                          'opp_fg3_pct_allowed', 'opp_reb_allowed', 'opp_ast_allowed',
                          'opp_stl_rate', 'opp_blk_rate', 'opp_tov_forced']
            df = df.merge(om, on=['opponent', 'season'], how='left')
        own = ts[ts['stat_type'] == 'team'].copy()
        if len(own) > 0:
            ownm = own[['team', 'season', 'pts', 'fga']].copy()
            ownm.columns = ['opponent', 'season', 'opp_team_pts', 'opp_team_fga']
            df = df.merge(ownm, on=['opponent', 'season'], how='left')

    # Interactions
    if 'usg_pct' in df.columns and 'opp_team_fga' in df.columns:
        df['usage_x_opp_pace'] = df['usg_pct'] * df['opp_team_fga']
    if 'pts_avg_5' in df.columns and 'opp_pts_allowed' in df.columns:
        df['pts_avg_x_opp_allowed'] = df['pts_avg_5'] * df['opp_pts_allowed']
    if 'reb_avg_5' in df.columns and 'opp_reb_allowed' in df.columns:
        df['reb_avg_x_opp_allowed'] = df['reb_avg_5'] * df['opp_reb_allowed']
    if 'ast_avg_5' in df.columns and 'opp_ast_allowed' in df.columns:
        df['ast_avg_x_opp_allowed'] = df['ast_avg_5'] * df['opp_ast_allowed']

    # Position
    if 'pos' in df.columns:
        df['is_guard'] = df['pos'].str.contains('G', na=False).astype(int)
        df['is_forward'] = df['pos'].str.contains('F', na=False).astype(int)
        df['is_center'] = df['pos'].str.contains('C', na=False).astype(int)

    # Get latest row per player (current feature state going into tonight)
    latest = df.sort_values('game_date').groupby('player').last().reset_index()

    # Override opponent for tonight's matchup
    for pname, info in tonight_players.items():
        mask = latest['player'].apply(lambda x: normalize_name(x) == normalize_name(pname))
        if mask.any():
            latest.loc[mask, 'opponent'] = info.get('opponent', '')
            latest.loc[mask, 'is_home'] = info.get('is_home', 0)

    return latest


# ============================================================
# NAME MATCHING
# ============================================================

def normalize_name(n):
    n = n.lower().strip()
    for s in [' jr.', ' jr', ' iii', ' ii', ' iv', ' sr.', ' sr']:
        n = n.replace(s, '')
    for k, v in {'ć':'c','č':'c','ž':'z','š':'s','đ':'d','ö':'o','ü':'u',
                  'ä':'a','é':'e','è':'e','ñ':'n','í':'i'}.items():
        n = n.replace(k, v)
    return re.sub(r'[^a-z\s]', '', n).strip()

def fuzzy_match(a, b):
    n1, n2 = normalize_name(a), normalize_name(b)
    if n1 == n2:
        return True
    p1, p2 = n1.split(), n2.split()
    if p1 and p2 and p1[-1] == p2[-1] and p1[0] and p2[0] and p1[0][0] == p2[0][0]:
        return True
    return False


# ============================================================
# GENERATE PICKS
# ============================================================

def generate_picks(features_df, models, live_odds, injuries, tonight_players, min_prob):
    picks = []

    for stat in ACTIVE_STATS:
        if stat not in models:
            continue
        md = models[stat]
        model = md['model']
        fcols = md['features']
        scol = STAT_MAP[stat]

        for pname, info in tonight_players.items():
            # Skip injured
            if any(fuzzy_match(pname, inj) for inj in injuries):
                continue

            # Find in features
            mask = features_df['player'].apply(lambda x: fuzzy_match(x, pname))
            rows = features_df[mask]
            if len(rows) == 0:
                continue
            row = rows.iloc[0]

            # Build feature vector
            X = []
            for col in fcols:
                val = row.get(col, np.nan)
                X.append(-999 if pd.isna(val) else float(val))
            X = np.array([X])

            try:
                proba = model.predict_proba(X)[0][1]
            except Exception:
                continue

            if proba < min_prob:
                continue

            savg = row.get(f'{scol}_season_avg', 0) or 0
            l5 = row.get(f'{scol}_avg_5', savg) or savg
            l3 = row.get(f'{scol}_avg_3', savg) or savg

            # Find live odds
            okey = f"{pname}|{stat}"
            live = live_odds.get(okey)
            if not live:
                for ok, ov in live_odds.items():
                    on, os_ = ok.split("|")
                    if os_ == stat and fuzzy_match(pname, on):
                        live = ov
                        break

            if live:
                line = live['line']
                odds = live['over_odds']
                book = live['book']
                impl = american_to_implied(odds)
                has_live = True
            else:
                offset = LINE_OFFSET.get(stat, 1.5)
                line = round(savg - offset, 0) + 0.5
                line = max(0.5, line)
                odds = -110
                impl = 0.5
                book = "estimated"
                has_live = False

            edge = proba - impl
            dec_odds = 1.0 / impl if impl > 0 else 1.0
            ev = proba * dec_odds - 1.0

            picks.append(Pick(
                player=pname, team=info.get('team', ''), opponent=info.get('opponent', ''),
                game=info.get('game', ''), stat=stat, line=line, over_odds=odds, book=book,
                model_prob=proba, implied_prob=impl, edge=edge, ev=ev,
                season_avg=savg, last_5_avg=l5, last_3_avg=l3,
                is_home=info.get('is_home', 0), is_b2b=0,
                days_rest=row.get('days_rest', 3) or 3, has_live_line=has_live,
            ))

    picks.sort(key=lambda p: p.model_prob, reverse=True)
    return picks


# ============================================================
# POST-ML SAFETY FILTERS (learned from real betting results)
# ============================================================

# Confidence caps per stat — the model is overconfident on REB/AST
# REB calibration showed predicted 80% → actual 77%, breaks above that
# Reed Sheppard 0 REB (model said 90.5%), Yabusele 0 REB (model said 90%)
PROB_CAP = {
    "PTS": 0.90,   # PTS model is best calibrated
    "REB": 0.78,   # REB model breaks above ~78%
    "AST": 0.80,   # AST model slightly overconfident at top
}

def apply_probability_corrections(picks: List[Pick]) -> List[Pick]:
    """
    Fix #1: Cap model probabilities per stat type.
    Fix #2: If last_3_avg < line, hard cap probability at 60%.
    Fix #3: If last_5_avg < line, reduce probability by 10%.
    
    These corrections address the model being trained on estimated lines
    (season_avg - offset) rather than real sportsbook lines.
    """
    corrected = []
    for p in picks:
        prob = p.model_prob

        # FIX 1: Hard cap per stat type
        cap = PROB_CAP.get(p.stat, 0.85)
        prob = min(prob, cap)

        # FIX 2: Last 3 games don't clear the line → hard cap at 60%
        # Evidence: every miss across Feb 19-23 had L3 below line
        # Mar 16: Reed Sheppard L3=4.3 on 2.5 line → hit. 
        #         Yabusele L3=7.7 on 3.5 line → 0 REB (outlier, but L3 was fine)
        #         OG Anunoby L3=2.7 on 1.5 → miss (1 AST, L3 barely above)
        if p.last_3_avg < p.line:
            prob = min(prob, 0.58)  # below our min_prob threshold = effectively filtered

        # FIX 3: Last 5 below line → reduce by 10 percentage points
        if p.last_5_avg < p.line and p.last_3_avg >= p.line:
            prob = prob * 0.90  # 10% haircut

        # FIX 4: Huge gap between season avg and line = suspicious
        # (live bet or book knows something)
        margin = (p.season_avg or 0) - p.line
        if p.stat == "PTS" and margin > 12:
            prob = min(prob, 0.70)  # SGA 31.7 avg on 18.5 line = sus
        if p.stat == "REB" and margin > 5:
            prob = min(prob, 0.70)
        if p.stat == "AST" and margin > 4:
            prob = min(prob, 0.70)

        # Recalculate edge and EV with corrected probability
        edge = prob - p.implied_prob
        dec_odds = 1.0 / p.implied_prob if p.implied_prob > 0 else 1.0
        ev = prob * dec_odds - 1.0

        corrected.append(Pick(
            player=p.player, team=p.team, opponent=p.opponent,
            game=p.game, stat=p.stat, line=p.line,
            over_odds=p.over_odds, book=p.book,
            model_prob=prob, implied_prob=p.implied_prob,
            edge=edge, ev=ev,
            season_avg=p.season_avg, last_5_avg=p.last_5_avg,
            last_3_avg=p.last_3_avg, is_home=p.is_home,
            is_b2b=p.is_b2b, days_rest=p.days_rest,
            has_live_line=p.has_live_line,
        ))

    corrected.sort(key=lambda p: p.model_prob, reverse=True)
    return corrected


def apply_safety_filters(picks: List[Pick], has_live: bool) -> dict:
    """
    Apply v3.1 battle-tested filters on top of ML + probability corrections.
    
    Returns dict with filtered locks, parlays, and flagged all-picks.
    
    Filters (calibrated from Feb 19-23 real results):
    1. Odds >= +200 → exclude from locks/parlays (33% hit rate)
    2. Last 3 avg must clear line (every miss had L3 below)
    3. Season margin >= 3.5 for PTS, >= 1.5 for REB/AST
    4. No role players in locks (min avgs enforced)
    5. Max 1 pick per game in parlays
    6. No duplicate players across parlays
    """

    # ── Build locks ──
    min_avg = {"PTS": 15.0, "REB": 5.0, "AST": 3.0}
    min_margin = {"PTS": 3.5, "REB": 1.5, "AST": 1.5}

    locks = []
    lock_players = set()
    lock_games = set()
    for p in picks:
        if p.player in lock_players or p.game in lock_games:
            continue
        if p.model_prob < 0.65:
            continue
        # Odds filter
        if has_live and p.over_odds >= 200:
            continue
        # Recent form must clear line
        if p.last_3_avg < p.line:
            continue
        # Season margin
        margin = (p.season_avg or 0) - p.line
        if margin < min_margin.get(p.stat, 1.5):
            continue
        # No role players
        if (p.season_avg or 0) < min_avg.get(p.stat, 5.0):
            continue
        locks.append(p)
        lock_players.add(p.player)
        lock_games.add(p.game)
        if len(locks) >= 6:
            break

    # ── Build 3-leg parlay ──
    p3 = []
    p3_players = set()
    p3_games = set()
    for p in picks:
        if p.player in p3_players or p.game in p3_games:
            continue
        if p.model_prob < 0.65:
            continue
        if has_live and p.over_odds >= 200:
            continue
        if p.last_3_avg < p.line:
            continue
        if (p.season_avg or 0) - p.line < 1.0:
            continue
        p3.append(p)
        p3_players.add(p.player)
        p3_games.add(p.game)
        if len(p3) >= 3:
            break

    # ── Build 5-leg parlay ──
    p5 = []
    p5_players = set()
    p5_games = set()
    for p in picks:
        if p.player in p5_players or p.game in p5_games:
            continue
        if p.model_prob < 0.62:
            continue
        if has_live and p.over_odds >= 200:
            continue
        if p.last_3_avg < p.line:
            continue
        p5.append(p)
        p5_players.add(p.player)
        p5_games.add(p.game)
        if len(p5) >= 5:
            break

    return {
        "all_picks": picks,
        "locks": locks,
        "parlay_3": p3,
        "parlay_5": p5,
    }


# ============================================================
# JSON EXPORT
# ============================================================

def export_json(filtered, games, injuries, models, tonight_players, args):
    """Write picks to parlaybudv4/static/picks/{date}.json"""
    from datetime import timezone
    picks     = filtered['all_picks']
    locks     = filtered['locks']
    p3        = filtered['parlay_3']
    p5        = filtered['parlay_5']
    today_str = datetime.now().strftime("%Y-%m-%d")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir    = os.path.join(script_dir, "parlaybudv4", "static", "picks")
    os.makedirs(out_dir, exist_ok=True)
    out_path   = os.path.join(out_dir, f"{today_str}.json")

    def pick_to_dict(p: Pick) -> dict:
        margin = (p.season_avg or 0) - p.line
        odds_ok   = not (p.has_live_line and p.over_odds >= 200)
        l3_ok     = p.last_3_avg >= p.line
        l5_ok     = p.last_5_avg >= p.line
        min_avg   = {"PTS": 15.0, "REB": 5.0, "AST": 3.0}
        min_marg  = {"PTS": 3.5, "REB": 1.5, "AST": 1.5}
        margin_ok = margin >= min_marg.get(p.stat, 1.5)
        avg_ok    = (p.season_avg or 0) >= min_avg.get(p.stat, 5.0)
        unusual   = (p.stat == "PTS" and margin > 12) or \
                    (p.stat == "REB" and margin > 5)  or \
                    (p.stat == "AST" and margin > 4)
        warnings = []
        if not odds_ok:  warnings.append("ODDS_TRAP")
        if not l3_ok:    warnings.append("L3_BELOW_LINE")
        if not l5_ok:    warnings.append("L5_BELOW_LINE")
        if unusual:      warnings.append("UNUSUAL_LINE")
        passes_lock   = bool(odds_ok and l3_ok and margin_ok and avg_ok and p.model_prob >= 0.65)
        passes_parlay = bool(odds_ok and l3_ok and p.model_prob >= 0.62)
        return {
            "player": p.player, "team": p.team, "opponent": p.opponent,
            "game": p.game, "stat": p.stat, "line": float(p.line),
            "over_odds": int(p.over_odds), "book": p.book,
            "model_prob": round(float(p.model_prob), 4),
            "implied_prob": round(float(p.implied_prob), 4),
            "edge": round(float(p.edge), 4), "ev": round(float(p.ev), 4),
            "season_avg": round(float(p.season_avg or 0), 1),
            "last_5_avg": round(float(p.last_5_avg), 1),
            "last_3_avg": round(float(p.last_3_avg), 1),
            "is_home": int(p.is_home), "has_live_line": bool(p.has_live_line),
            "warnings": warnings,
            "passes_lock_filter": passes_lock,
            "passes_parlay_filter": passes_parlay,
            "filter_details": {
                "odds_ok": bool(odds_ok), "l3_clears_line": bool(l3_ok),
                "l5_clears_line": bool(l5_ok), "season_margin": round(float(margin), 2),
                "season_margin_ok": bool(margin_ok), "min_avg_ok": bool(avg_ok),
                "unusual_line": bool(unusual),
            },
        }

    def parlay_dict(legs: list) -> dict:
        import math
        combined = math.prod(p.model_prob for p in legs) if legs else 0
        leg_strs = [f"{p.stat} O{p.line} ({p.model_prob:.0%})" for p in legs]
        return {
            "legs": leg_strs,
            "combined_prob": round(combined, 4),
            "players": [p.player for p in legs],
        }

    # model_stats
    model_stats = {}
    for stat, m in models.items():
        mt = m.get('metrics', {})
        # hit_rate_70: fraction of predictions >= 0.70 threshold that actually hit
        # If not stored, fall back to accuracy
        model_stats[stat] = {
            "auc": round(mt.get('roc_auc', 0), 3),
            "hit_rate_70": round(mt.get('hit_rate_70', mt.get('accuracy', 0)), 3),
        }

    games_list = [{"away": away, "home": home, "label": label}
                  for label, (away, home) in games.items()]

    injuries_list = [{"player": name, "status": status, "reason": ""}
                     for name, status in injuries.items()]

    payload = {
        "date": today_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_version": "v4-xgboost",
        "games": games_list,
        "injuries": injuries_list,
        "picks": [pick_to_dict(p) for p in picks],
        "locks": [p.player for p in locks],
        "parlay_3leg": parlay_dict(p3),
        "parlay_5leg": parlay_dict(p5),
        "model_stats": model_stats,
        "results": None,
    }

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ JSON written → {out_path}")
    print(f"   {len(picks)} picks | {len(locks)} locks | {len(p3)}-leg + {len(p5)}-leg parlays")


# ============================================================
# OUTPUT
# ============================================================

def print_results(filtered, injuries, has_live, min_prob):
    picks = filtered['all_picks']
    locks = filtered['locks']
    p3 = filtered['parlay_3']
    p5 = filtered['parlay_5']

    print(f"\n{'='*W}")
    mode = "LIVE ODDS" if has_live else "PREVIEW (no live odds)"
    print(f"  🏀 PARLAY ENGINE V4.1 — ML + SAFETY FILTERS ({mode})")
    print(f"  📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"  🧠 XGBoost (23K+ games) + v3.1 battle-tested filters")
    print(f"  📏 Min P(over): {min_prob:.0%} | Prob caps: PTS {PROB_CAP['PTS']:.0%}, REB {PROB_CAP['REB']:.0%}, AST {PROB_CAP['AST']:.0%}")
    if has_live:
        print(f"  📏 Min edge: {MIN_EDGE:.0%} | Odds cap: +200 | L3 must clear line")
    print(f"{'='*W}")

    # Injuries
    if injuries:
        out = {k: v for k, v in injuries.items() if "OUT" in v.upper()}
        if out:
            print(f"\n⚠️  {len(out)} players OUT (top names):")
            for name in sorted(out.keys())[:20]:
                print(f"  ❌ {name}")
            if len(out) > 20:
                print(f"  ... and {len(out)-20} more")

    if not picks:
        print("\n  ⚠️  No picks found above threshold")
        return

    # ── All candidates ──
    if has_live:
        ev_picks = [p for p in picks if p.edge >= MIN_EDGE and p.has_live_line]
        print(f"\n📊 {len(ev_picks)} +EV PICKS (P>={min_prob:.0%}, edge>={MIN_EDGE:.0%}, live lines)")
    else:
        ev_picks = [p for p in picks if p.model_prob >= min_prob]
        print(f"\n📊 {len(ev_picks)} PICKS (P>={min_prob:.0%})")

    # Show top 25
    show = ev_picks[:25]
    print(f"\n{'#':>3}  {'Player':<24} {'Stat':<4} {'Line':>6} {'P(over)':>8} {'Avg5':>6} {'Avg3':>6} {'Opp':>5} {'Edge':>7} {'Book':<12}")
    print("-" * W)
    for i, p in enumerate(show, 1):
        edge_str = f"{p.edge:+.1%}" if p.has_live_line else "  N/A"
        bk = p.book[:12] if p.has_live_line else "est"
        print(f"{i:>3}. {p.player:<24} {p.stat:<4} {p.line:>6.1f} {p.model_prob:>7.1%} "
              f"{p.last_5_avg:>6.1f} {p.last_3_avg:>6.1f} {p.opponent:>5} {edge_str:>7} {bk:<12}")

    # ── LOCKS (pre-filtered by apply_safety_filters) ──
    if locks:
        print(f"\n{'='*W}")
        lbl = "LOCKS (ML + safety filters)" if has_live else "PREVIEW LOCKS"
        print(f"  🔒 {lbl}")
        print(f"  Filters: L3 > line ✓ | Season margin ✓ | Odds < +200 ✓ | Stars only ✓")
        print(f"{'='*W}")
        for i, p in enumerate(locks, 1):
            odds_str = f"({p.over_odds:+d})" if p.has_live_line and p.over_odds != -110 else ""
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat} {odds_str}")
            print(f"     ML P(over): {p.model_prob:.1%} | Season: {p.season_avg:.1f} | Last 5: {p.last_5_avg:.1f} | Last 3: {p.last_3_avg:.1f}")
            if p.has_live_line:
                print(f"     Edge: {p.edge:+.1%} | EV: {p.ev:+.1%} | {p.book}")
            print(f"     vs {p.opponent} | {'Home' if p.is_home else 'Away'} | {p.game}")
    else:
        print(f"\n  ⚠️  No picks passed all safety filters for locks")

    # ── 3-LEG SAFE PARLAY ──
    if len(p3) >= 3:
        combo_prob = 1.0
        for p in p3:
            combo_prob *= p.model_prob

        print(f"\n{'='*W}")
        print(f"  🎯 3-LEG SAFE PARLAY (all filters passed)")
        print(f"  Combined P(hit): {combo_prob:.1%}")
        print(f"{'='*W}")
        for i, p in enumerate(p3, 1):
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat}")
            print(f"     ML: {p.model_prob:.1%} | L3: {p.last_3_avg:.1f} | L5: {p.last_5_avg:.1f} | vs {p.opponent}")
    else:
        print(f"\n  ⚠️  Not enough picks passed filters for 3-leg parlay")

    # ── 5-LEG PREMIUM PARLAY ──
    if len(p5) >= 5:
        combo_prob = 1.0
        for p in p5:
            combo_prob *= p.model_prob

        print(f"\n{'='*W}")
        print(f"  🔥 5-LEG PREMIUM PARLAY (all filters passed)")
        print(f"  Combined P(hit): {combo_prob:.1%}")
        print(f"{'='*W}")
        for i, p in enumerate(p5, 1):
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat}")
            print(f"     ML: {p.model_prob:.1%} | L3: {p.last_3_avg:.1f} | L5: {p.last_5_avg:.1f} | vs {p.opponent}")

    # Methodology
    print(f"\n{'='*W}")
    print("  ℹ️  V4.1 METHODOLOGY")
    print(f"{'='*W}")
    print(f"""
  • XGBoost trained on 23K+ games (2023-25), validated on 2025-26
  • 132 features: rolling avgs, opponent defense, usage, interactions, rest
  • Post-ML corrections applied:
    - Probability caps: PTS {PROB_CAP['PTS']:.0%}, REB {PROB_CAP['REB']:.0%}, AST {PROB_CAP['AST']:.0%}
    - L3 avg < line → capped at 58% (effectively filtered)
    - L5 avg < line → 10% probability haircut
    - Unusual line gap → capped at 70%
  • Safety filters (from Feb 19-23 real results):
    - Odds >= +200 excluded from locks/parlays
    - Season margin >= 3.5 (PTS), >= 1.5 (REB/AST) for locks
    - Min season avg: 15 PTS, 5 REB, 3 AST for locks (no role players)
    - Max 1 pick per game (correlation protection)
    - L3 avg must clear line for all locks/parlay legs
""")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="NBA ML Parlay Engine V4")
    parser.add_argument('--fetch-odds', action='store_true', help='Fetch live sportsbook lines')
    parser.add_argument('--min-prob', type=float, default=MIN_PROB, help='Min model probability')
    parser.add_argument('--db', default=DB_PATH)
    parser.add_argument('--models', default=MODELS_DIR)
    parser.add_argument('--season', default=SEASON)
    parser.add_argument('--odds-key', default=ODDS_API_KEY)
    parser.add_argument('--json-output', action='store_true', help='Write picks JSON for the dashboard')
    args = parser.parse_args()

    print("=" * W)
    print("  🏀 PARLAY ENGINE V4 — Loading...")
    print("=" * W)

    # Load models
    print("\n📦 Loading ML models...")
    if not HAS_XGB:
        print("❌ xgboost not installed. Run: pip install xgboost")
        sys.exit(1)
    models = load_models(args.models)
    if not models:
        print("❌ No models found. Run train_model.py first.")
        sys.exit(1)

    # Fetch games
    print()
    games = fetch_games()
    if not games:
        print("❌ No games today")
        sys.exit(0)
    for g in games:
        print(f"   🏀 {g}")

    # Fetch injuries
    print()
    injuries = fetch_injuries()

    # Build tonight's player list from games
    tonight_players = {}
    conn = sqlite3.connect(args.db)
    for label, (away, home) in games.items():
        # Find players on these teams from our DB
        for team_abbr, is_home, opp in [(home, 1, away), (away, 0, home)]:
            players = pd.read_sql(
                "SELECT DISTINCT player, team FROM player_game_logs "
                "WHERE team = ? AND season = ? AND mp_float >= 15 "
                "GROUP BY player HAVING COUNT(*) >= 5",
                conn, params=(team_abbr, args.season))

            # Also check BBRef abbreviation variants
            if len(players) == 0:
                for bbref, std in BBREF_ABBR.items():
                    if std == team_abbr:
                        players = pd.read_sql(
                            "SELECT DISTINCT player, team FROM player_game_logs "
                            "WHERE team = ? AND season = ? AND mp_float >= 15 "
                            "GROUP BY player HAVING COUNT(*) >= 5",
                            conn, params=(bbref, args.season))
                        if len(players) > 0:
                            break

            for _, row in players.iterrows():
                tonight_players[row['player']] = {
                    'team': team_abbr, 'opponent': opp,
                    'is_home': is_home, 'game': label,
                }
    conn.close()
    print(f"\n📊 {len(tonight_players)} players in tonight's games")

    # Build features
    print("\n🧠 Engineering features...")
    features_df = build_features(args.db, args.season, tonight_players)
    if len(features_df) == 0:
        print("❌ No features. Run collect_bbref.py --seasons 2025-26 --game-logs first.")
        sys.exit(1)
    print(f"   ✅ Features built for {len(features_df)} players")

    # Fetch odds (controlled by FETCH_ODDS toggle at top of file, or --fetch-odds flag)
    live_odds = {}
    has_live = False
    should_fetch = FETCH_ODDS or args.fetch_odds
    if should_fetch:
        live_odds = fetch_odds(args.odds_key)
        has_live = len(live_odds) > 0
    else:
        print("\n⚡ Skipping odds (FETCH_ODDS=False)")
        print("   Flip FETCH_ODDS=True at top of file or use --fetch-odds flag")

    # Generate picks
    print("\n🎯 Generating picks...")
    picks = generate_picks(features_df, models, live_odds, injuries,
                           tonight_players, args.min_prob)
    print(f"   ✅ {len(picks)} raw picks generated")

    # Apply post-ML corrections (probability caps, L3 override, suspicious line detection)
    print("\n🔧 Applying probability corrections...")
    picks = apply_probability_corrections(picks)
    # Re-filter to min_prob after corrections (some will drop below threshold)
    picks = [p for p in picks if p.model_prob >= args.min_prob]
    print(f"   ✅ {len(picks)} picks after corrections")

    # Apply safety filters (odds cap, margin checks, no role players, etc.)
    print("🛡️  Applying safety filters...")
    filtered = apply_safety_filters(picks, has_live)
    print(f"   ✅ {len(filtered['locks'])} locks, {len(filtered['parlay_3'])}-leg parlay, {len(filtered['parlay_5'])}-leg parlay")

    # Print results
    print_results(filtered, injuries, has_live, args.min_prob)

    # Export JSON for dashboard
    if args.json_output:
        export_json(filtered, games, injuries, models, tonight_players, args)


if __name__ == "__main__":
    main()

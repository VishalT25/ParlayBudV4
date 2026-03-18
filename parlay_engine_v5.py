#!/usr/bin/env python3
"""
parlay_engine_v5.py — HYBRID: DARKO + XGBoost + Battle-Tested Filters

Combines the best of everything:
  - v3.1: DARKO projections (opponent-adjusted, daily updated)
  - v3.1: Season averages from NBAstuffer
  - v3.1: Battle-tested filters (odds cap, L3>line, season margin, no role players)
  - v4:   XGBoost ML model (trained on 23K+ games, 132 features)
  - v4:   Rolling averages (L3, L5, L10), trends, opponent defense
  - NEW:  4-source probability blend (DARKO + season + ML + market)

The key insight: DARKO was our best single predictor in v3.1 (74% hit rate).
The ML model adds value as an ADDITIONAL signal, not a replacement.

Probability blend:
  p_darko   = Normal CDF from DARKO projection (opponent-adjusted)
  p_season  = Normal CDF from season average
  p_ml      = XGBoost predict_proba (132 features, 23K training samples)
  p_market  = Implied from sportsbook odds (when available)

  model_prob = 0.40 * p_darko + 0.25 * p_ml + 0.20 * p_season + 0.15 * p_market
  (weights tunable — DARKO gets highest weight because it was the best predictor)

Usage:
  python3 parlay_engine_v5.py                    # preview mode
  python3 parlay_engine_v5.py --fetch-odds       # with live lines

Requirements:
  - DARKO CSV in script directory (download daily from DARKO website)
  - parlay_ml.db (from collect_bbref.py)
  - models/ directory (from train_model.py)
  - pip install requests beautifulsoup4 pandas xgboost
"""

import csv
import re
import sys
import os
import json
import math
import pickle
import sqlite3
import time as _time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime

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
    print("⚠️  xgboost not installed — running without ML model")

# ============================================================
# 🔑 CONFIGURATION
# ============================================================

# ⬇️ FLIP THIS TO True TO FETCH LIVE SPORTSBOOK ODDS ⬇️
FETCH_ODDS = True

ODDS_API_KEY = "1352e9cd8058c67615efe0896a44f5f1"
DB_PATH = "parlay_ml.db"
MODELS_DIR = "models"
SEASON = "2025-26"

# Probability blend weights (must sum to ~1.0)
# DARKO gets highest weight — it was the best single predictor at 74% hit rate
W_DARKO = 0.35       # opponent-adjusted daily projection
W_ML = 0.25          # XGBoost (132 features, but trained on estimated lines)
W_SEASON = 0.20      # season average (stable but not opponent-adjusted)
W_MARKET = 0.20      # sportsbook implied (when available, else redistributed)

MIN_EDGE = 0.05
MIN_PROB = 0.60

# Stat variance estimates (for Normal CDF)
STAT_STDDEV = {"PTS": 8.5, "REB": 3.5, "AST": 2.5, "BLK": 1.0, "STL": 0.8, "3PM": 1.2}

# Minimum thresholds to consider
MIN_THRESH = {"PTS": 14.0, "REB": 6.0, "AST": 4.0, "BLK": 1.0, "STL": 1.0, "3PM": 1.5}
MIN_MINUTES = 24.0

# Safety filter thresholds (calibrated from Feb 19-23 real results)
LOCK_MIN_MARGIN = {"PTS": 3.5, "REB": 1.5, "AST": 1.5}
LOCK_MIN_AVG = {"PTS": 15.0, "REB": 5.0, "AST": 3.0}
PROB_CAP = {"PTS": 0.90, "REB": 0.78, "AST": 0.80}

ACTIVE_STATS = ["PTS", "REB", "AST"]
STAT_MAP_ML = {'PTS': 'pts', 'REB': 'reb', 'AST': 'ast'}

# ESPN + team mappings
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
ESPN_ABBR = {"GS": "GSW", "SA": "SAS", "NY": "NYK", "NO": "NOP", "WSH": "WAS"}
BBREF_ABBR = {"BRK": "BKN", "CHO": "CHA", "PHO": "PHX"}
MARKET_MAP = {"player_points": "PTS", "player_rebounds": "REB",
              "player_assists": "AST", "player_threes": "3PM"}
TEAM_FULL_TO_ABBR = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
           "Referer": "https://www.nba.com/", "Origin": "https://www.nba.com"}

W = 110  # output width


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class DarkoProjection:
    player: str
    team: str
    team_abbr: str
    minutes: float
    pts: float
    reb: float
    ast: float
    blk: float
    stl: float
    fg3a: float
    fg3m_est: float

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
    # 4-source probabilities
    p_darko: float
    p_season: float
    p_ml: float
    p_market: float
    # Blended
    model_prob: float
    implied_prob: float
    edge: float
    ev: float
    # Context
    darko_val: float
    season_avg: float
    last_5_avg: float
    last_3_avg: float
    is_home: int
    has_live_line: bool
    # Flags
    warnings: list


# ============================================================
# MATH
# ============================================================

def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def compute_p_over(projection, line, std_dev):
    if std_dev <= 0:
        return 1.0 if projection > line else 0.0
    z = (projection - line) / std_dev
    return normal_cdf(z)

def american_to_implied(odds):
    if odds < 0:
        return -odds / (-odds + 100.0)
    return 100.0 / (odds + 100.0)


# ============================================================
# DATA LOADERS
# ============================================================

def load_darko_csv(filepath):
    projections = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                team_full = row['Team'].strip()
                team_abbr = TEAM_FULL_TO_ABBR.get(team_full, team_full[:3].upper())
                reb = float(row['DREB']) + float(row['OREB'])
                fg3a = float(row['FG3A'])
                projections.append(DarkoProjection(
                    player=row['Player'].strip(), team=team_full, team_abbr=team_abbr,
                    minutes=float(row['Minutes']), pts=float(row['PTS']),
                    reb=reb, ast=float(row['AST']), blk=float(row['BLK']),
                    stl=float(row['STL']), fg3a=fg3a, fg3m_est=fg3a * 0.35,
                ))
            except (ValueError, KeyError):
                continue
    return projections

def load_ml_models(models_dir):
    models = {}
    for stat in ACTIVE_STATS:
        path = os.path.join(models_dir, f"model_{stat.lower()}.pkl")
        if os.path.exists(path):
            with open(path, 'rb') as f:
                models[stat] = pickle.load(f)
    return models

def build_ml_features(db_path, season):
    """Build ML feature DataFrame from parlay_ml.db (same as v4/train_model)."""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        gl = pd.read_sql("SELECT * FROM player_game_logs WHERE mp_float > 0 AND season = ? ORDER BY game_date",
                          conn, params=(season,))
    except Exception:
        conn.close()
        return pd.DataFrame()

    adv = pd.read_sql("SELECT * FROM season_stats_advanced WHERE season = ?", conn, params=(season,))
    ts = pd.read_sql("SELECT * FROM team_stats WHERE season = ?", conn, params=(season,))
    conn.close()

    if len(gl) == 0:
        return pd.DataFrame()

    df = gl.copy()
    df['game_date'] = pd.to_datetime(df['game_date'], errors='coerce')
    df = df.dropna(subset=['game_date']).sort_values(['player', 'game_date']).reset_index(drop=True)

    # Rolling features (must match training exactly)
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

    for col in ['pts', 'reb', 'ast', 'fg3', 'stl', 'blk']:
        a3, a10 = f'{col}_avg_3', f'{col}_avg_10'
        if a3 in df.columns and a10 in df.columns:
            df[f'{col}_trend'] = df[a3] - df[a10]

    df['ts_proxy'] = df['pts'] / (2 * (df['fga'] + 0.44 * df['fta'])).replace(0, np.nan)
    df['ts_proxy_avg_5'] = df.groupby('player')['ts_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())
    df['usage_proxy'] = df['fga'] / df['mp_float'].replace(0, np.nan)
    df['usage_proxy_avg_5'] = df.groupby('player')['usage_proxy'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=2).mean())

    df['is_home'] = df['is_home'].fillna(0).astype(int)
    df['is_b2b'] = df['is_b2b'].fillna(0).astype(int)
    df['days_rest'] = df['days_rest'].fillna(3)
    df['game_number'] = df['game_number'].fillna(1)
    df['rest_0_1'] = (df['days_rest'] <= 1).astype(int)
    df['rest_3plus'] = (df['days_rest'] >= 3).astype(int)
    df['won'] = df['result'].str.startswith('W', na=False).astype(int)
    df['win_streak_5'] = df.groupby('player')['won'].transform(
        lambda x: x.shift(1).rolling(5, min_periods=1).sum())

    if len(adv) > 0:
        acols = ['player', 'season', 'per', 'ts_pct', 'usg_pct', 'ast_pct', 'stl_pct',
                 'blk_pct', 'tov_pct', 'reb_pct', 'orb_pct', 'drb_pct',
                 'obpm', 'dbpm', 'bpm', 'vorp', 'ows', 'dws', 'ws', 'ws_per_48']
        avail = [c for c in acols if c in adv.columns]
        df = df.merge(adv[avail].drop_duplicates(subset=['player', 'season']),
                      on=['player', 'season'], how='left', suffixes=('', '_adv'))

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

    if 'usg_pct' in df.columns and 'opp_team_fga' in df.columns:
        df['usage_x_opp_pace'] = df['usg_pct'] * df['opp_team_fga']
    if 'pts_avg_5' in df.columns and 'opp_pts_allowed' in df.columns:
        df['pts_avg_x_opp_allowed'] = df['pts_avg_5'] * df['opp_pts_allowed']
    if 'reb_avg_5' in df.columns and 'opp_reb_allowed' in df.columns:
        df['reb_avg_x_opp_allowed'] = df['reb_avg_5'] * df['opp_reb_allowed']
    if 'ast_avg_5' in df.columns and 'opp_ast_allowed' in df.columns:
        df['ast_avg_x_opp_allowed'] = df['ast_avg_5'] * df['opp_ast_allowed']

    if 'pos' in df.columns:
        df['is_guard'] = df['pos'].str.contains('G', na=False).astype(int)
        df['is_forward'] = df['pos'].str.contains('F', na=False).astype(int)
        df['is_center'] = df['pos'].str.contains('C', na=False).astype(int)

    # Return latest row per player
    latest = df.sort_values('game_date').groupby('player').last().reset_index()
    return latest


# ============================================================
# ESPN + ODDS (reused from v3/v4)
# ============================================================

def fetch_games():
    if not HAS_REQUESTS: return {}
    today = datetime.now().strftime("%Y%m%d")
    try:
        r = requests.get(ESPN_SCOREBOARD, params={"dates": today}, headers=HEADERS, timeout=15)
        data = r.json()
    except: return {}
    games = {}
    for ev in data.get("events", []):
        comp = ev.get("competitions", [{}])[0]
        h = a = ""
        for t in comp.get("competitors", []):
            ab = ESPN_ABBR.get(t.get("team",{}).get("abbreviation",""), t.get("team",{}).get("abbreviation",""))
            if t.get("homeAway") == "home": h = ab
            else: a = ab
        if h and a: games[f"{a} @ {h}"] = (a, h)
    return games

def fetch_injuries():
    if not HAS_REQUESTS: return {}
    injuries = {}

    # ── ESPN injuries JSON API (catches OUT + Suspension + Doubtful) ──
    EXCLUDE_STATUSES = {"out", "suspension", "suspended", "doubtful"}
    try:
        r = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries",
            headers=HEADERS, timeout=15)
        data = r.json()
        for team in data.get("injuries", []):
            for inj in team.get("injuries", []):
                status = inj.get("status", "").lower()
                if not any(s in status for s in EXCLUDE_STATUSES):
                    continue
                athlete = inj.get("athlete", {})
                name = athlete.get("displayName", "")
                if not name:
                    name = f"{athlete.get('firstName','')} {athlete.get('lastName','')}".strip()
                if name and len(name) > 3:
                    injuries[name] = "OUT"
    except: pass

    return injuries

def _odds_cache_path(script_dir):
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(script_dir, f"odds_cache_{today}.json")

def load_cached_odds(script_dir):
    path = _odds_cache_path(script_dir)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def save_cached_odds(lines, script_dir):
    path = _odds_cache_path(script_dir)
    with open(path, "w") as f:
        json.dump(lines, f, indent=2)

def fetch_odds(api_key, script_dir=None, force=False):
    if not HAS_REQUESTS or not api_key: return {}

    # Use cache if available and not forced
    if script_dir and not force:
        cached = load_cached_odds(script_dir)
        if cached is not None:
            print(f"\n💾 Using cached odds ({len(cached)} lines) — run with --force-odds to refresh")
            return cached

    print("\n🌐 Fetching live sportsbook lines...")
    try:
        r = requests.get("https://api.the-odds-api.com/v4/sports/basketball_nba/events",
                         params={"apiKey": api_key}, timeout=15)
        events = r.json()
        rem = r.headers.get("x-requests-remaining", "?")
        print(f"   {len(events)} events (API calls left: {rem})")
    except: return {}

    mkts = "player_points,player_rebounds,player_assists,player_threes"
    lines = {}
    for i, ev in enumerate(events):
        if i > 0: _time.sleep(1.5)
        try:
            r2 = requests.get(f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{ev['id']}/odds",
                params={"apiKey": api_key, "regions": "us", "markets": mkts, "oddsFormat": "american"}, timeout=15)
            for bm in r2.json().get('bookmakers', []):
                bk = bm.get('title','')
                for mkt in bm.get('markets', []):
                    stat = MARKET_MAP.get(mkt.get('key',''))
                    if not stat: continue
                    outs = {}
                    for o in mkt.get('outcomes', []):
                        p = o.get('description','')
                        if p not in outs: outs[p] = {'line': o.get('point',0)}
                        if o.get('name') == 'Over': outs[p]['over'] = o.get('price', -110)
                        elif o.get('name') == 'Under': outs[p]['under'] = o.get('price', -110)
                    for p, v in outs.items():
                        key = f"{p}|{stat}"
                        if key not in lines or v.get('line',999) < lines[key]['line']:
                            lines[key] = {'line': v['line'], 'over_odds': v.get('over',-110), 'book': bk}
        except: continue
    print(f"   ✅ {len(lines)} prop lines")

    # Save to cache for reuse today
    if script_dir and lines:
        save_cached_odds(lines, script_dir)
        print(f"   💾 Cached to odds_cache_{datetime.now().strftime('%Y-%m-%d')}.json")

    return lines

def fetch_season_stats():
    """Fetch season stats from NBAstuffer (reused from v3)."""
    if not HAS_REQUESTS: return {}
    try:
        r = requests.get("https://www.nbastuffer.com/2025-2026-nba-player-stats/", headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.text, 'html.parser')
        stats = {}
        table = None
        for t in soup.find_all('table'):
            if 'PPG' in t.get_text() or 'PpG' in t.get_text():
                table = t; break
        if not table: return {}
        rows = table.find_all('tr')
        header = [c.get_text(strip=True).upper() for c in rows[0].find_all(['th','td'])]
        def find_col(*names):
            for n in names:
                if n in header: return header.index(n)
            return None
        ni=find_col('NAME','PLAYER'); pi=find_col('PPG','PpG'); ri=find_col('RPG','RpG')
        ai=find_col('APG','ApG'); si=find_col('SPG','SpG'); bi=find_col('BPG','BpG')
        mi=find_col('MPG','MpG'); f3i=find_col('3PA'); f3pi=find_col('3P%')
        for row in rows[1:]:
            cells = row.find_all(['td','th'])
            if len(cells) < 10: continue
            def sf(i):
                if i is None or i >= len(cells): return 0.0
                t = cells[i].get_text(strip=True).replace('%','').replace(',','')
                try: return float(t) if t else 0.0
                except: return 0.0
            name = cells[ni].get_text(strip=True) if ni is not None else ""
            if not name or len(name)<3 or name.upper() in ('NAME','PLAYER'): continue
            stats[name.lower()] = {"pts":sf(pi),"reb":sf(ri),"ast":sf(ai),"stl":sf(si),
                                    "blk":sf(bi),"mpg":sf(mi),"fg3a":sf(f3i),"fg3_pct":sf(f3pi)}
        return stats
    except: return {}


# ============================================================
# NAME MATCHING
# ============================================================

def normalize_name(n):
    n = n.lower().strip()
    for s in [' jr.',' jr',' iii',' ii',' iv',' sr.',' sr']: n = n.replace(s,'')
    for k,v in {'ć':'c','č':'c','ž':'z','š':'s','đ':'d','ö':'o','ü':'u',
                'ä':'a','é':'e','è':'e','ñ':'n','í':'i'}.items(): n = n.replace(k,v)
    return re.sub(r'[^a-z\s]','',n).strip()

def fuzzy_match(a, b):
    n1, n2 = normalize_name(a), normalize_name(b)
    if n1 == n2: return True
    p1, p2 = n1.split(), n2.split()
    if p1 and p2 and p1[-1]==p2[-1] and p1[0] and p2[0] and p1[0][0]==p2[0][0]: return True
    return False

def find_ml_row(ml_df, player_name):
    if ml_df is None or len(ml_df) == 0: return None
    mask = ml_df['player'].apply(lambda x: fuzzy_match(x, player_name))
    rows = ml_df[mask]
    return rows.iloc[0] if len(rows) > 0 else None

def find_season_stat(db_stats, player_name):
    key = player_name.lower()
    if key in db_stats: return db_stats[key]
    for k, v in db_stats.items():
        if fuzzy_match(player_name, k): return v
    return None


# ============================================================
# CORE: 4-SOURCE PROBABILITY BLEND
# ============================================================

def generate_picks(darko, ml_models, ml_features, db_stats, live_odds,
                   injuries, games):
    """
    For each player × stat:
    1. p_darko  = Normal CDF from DARKO projection
    2. p_season = Normal CDF from season average
    3. p_ml     = XGBoost predict_proba (if model available)
    4. p_market = Sportsbook implied probability (if live odds available)
    5. Blend → final probability → edge → EV
    6. Apply safety filters
    """
    picks = []
    tonight_teams = set()
    for t1, t2 in games.values():
        tonight_teams.add(t1); tonight_teams.add(t2)

    def find_game(team):
        for lbl, (t1,t2) in games.items():
            if team in (t1,t2): return lbl
        return None

    stat_vals_map = {"PTS":"pts","REB":"reb","AST":"ast","BLK":"blk","STL":"stl","3PM":"fg3m_est"}

    for proj in darko:
        if proj.team_abbr not in tonight_teams: continue
        if any(fuzzy_match(proj.player, inj) for inj in injuries): continue
        if proj.minutes < MIN_MINUTES: continue
        game = find_game(proj.team_abbr)
        if not game: continue

        # Determine opponent
        away, home = games[game]
        opponent = home if proj.team_abbr == away else away
        is_home = 1 if proj.team_abbr == home else 0

        # Season stats
        db = find_season_stat(db_stats, proj.player)

        # ML features row
        ml_row = find_ml_row(ml_features, proj.player)

        darko_vals = {"PTS": proj.pts, "REB": proj.reb, "AST": proj.ast}

        for stat in ACTIVE_STATS:
            darko_val = darko_vals.get(stat, 0)
            if darko_val < MIN_THRESH.get(stat, 0): continue

            # Season average
            season_val = 0
            if db:
                s_map = {"PTS":"pts","REB":"reb","AST":"ast"}
                season_val = db.get(s_map.get(stat,""), 0)

            # Find sportsbook line
            odds_key = f"{proj.player}|{stat}"
            live = live_odds.get(odds_key)
            if not live:
                for ok, ov in live_odds.items():
                    on, os_ = ok.split("|")
                    if os_ == stat and fuzzy_match(proj.player, on):
                        live = ov; break

            if live:
                line = live['line']
                over_odds = live['over_odds']
                book = live['book']
                has_live = True
            else:
                # Estimate line from DARKO
                offsets = {"PTS":3.0,"REB":1.5,"AST":1.0}
                line = max(0.5, round((darko_val - offsets.get(stat,2.0)) * 2) / 2)
                over_odds = -110
                book = "estimated"
                has_live = False

            # ── SOURCE 1: DARKO probability ──
            std = STAT_STDDEV.get(stat, 5.0)
            p_darko = compute_p_over(darko_val, line, std)

            # ── SOURCE 2: Season average probability ──
            p_season = compute_p_over(season_val, line, std) if season_val > 0 else p_darko

            # ── SOURCE 3: ML model probability ──
            p_ml = 0.5  # default: no information
            if ml_row is not None and stat in ml_models:
                md = ml_models[stat]
                model = md['model']
                fcols = md['features']
                try:
                    X = []
                    for col in fcols:
                        val = ml_row.get(col, np.nan)
                        X.append(-999 if pd.isna(val) else float(val))
                    p_ml = model.predict_proba(np.array([X]))[0][1]
                    p_ml = min(p_ml, PROB_CAP.get(stat, 0.85))  # apply cap
                except:
                    p_ml = 0.5

            # ── SOURCE 4: Market implied probability ──
            p_market = american_to_implied(over_odds) if has_live else 0.5

            # ── BLEND ──
            if has_live:
                # All 4 sources available
                model_prob = (W_DARKO * p_darko + W_ML * p_ml +
                              W_SEASON * p_season + W_MARKET * p_market)
            else:
                # No market — redistribute weight
                w_total = W_DARKO + W_ML + W_SEASON
                model_prob = ((W_DARKO/w_total) * p_darko +
                              (W_ML/w_total) * p_ml +
                              (W_SEASON/w_total) * p_season)

            model_prob = max(0.01, min(0.99, model_prob))

            # ── Edge + EV ──
            implied = p_market if has_live else 0.5
            edge = model_prob - implied
            dec = 1.0 / implied if implied > 0 else 1.0
            ev = model_prob * dec - 1.0

            # ── ML rolling averages for context ──
            scol = STAT_MAP_ML.get(stat, stat.lower())
            l5 = float(ml_row.get(f'{scol}_avg_5', season_val)) if ml_row is not None else season_val
            l3 = float(ml_row.get(f'{scol}_avg_3', season_val)) if ml_row is not None else season_val
            if pd.isna(l5): l5 = season_val
            if pd.isna(l3): l3 = season_val

            # ── Warnings / safety flags ──
            warnings = []
            if has_live and over_odds >= 200: warnings.append("ODDS_TRAP")
            if l3 > 0 and l3 < line: warnings.append("L3_BELOW")
            if l5 > 0 and l5 < line: warnings.append("L5_BELOW")
            margin = (season_val - line) if season_val > 0 else (darko_val - line)
            if stat == "PTS" and margin > 12: warnings.append("SUS_LINE")
            if stat == "REB" and margin > 5: warnings.append("SUS_LINE")

            # ── L3 below line → cap probability (Fix #2 from v4.1) ──
            if "L3_BELOW" in warnings:
                model_prob = min(model_prob, 0.58)
                edge = model_prob - implied
                ev = model_prob * dec - 1.0

            if model_prob < MIN_PROB: continue

            picks.append(Pick(
                player=proj.player, team=proj.team_abbr, opponent=opponent,
                game=game, stat=stat, line=line, over_odds=over_odds, book=book,
                p_darko=p_darko, p_season=p_season, p_ml=p_ml, p_market=p_market,
                model_prob=model_prob, implied_prob=implied, edge=edge, ev=ev,
                darko_val=darko_val, season_avg=season_val, last_5_avg=l5, last_3_avg=l3,
                is_home=is_home, has_live_line=has_live, warnings=warnings,
            ))

    picks.sort(key=lambda p: p.model_prob, reverse=True)
    return picks


def build_locks_and_parlays(picks, has_live):
    """Apply safety filters and build locks + parlays."""
    # LOCKS
    locks = []
    lp, lg = set(), set()
    for p in picks:
        if p.player in lp or p.game in lg: continue
        if p.model_prob < 0.65: continue
        if "ODDS_TRAP" in p.warnings or "L3_BELOW" in p.warnings: continue
        if "SUS_LINE" in p.warnings: continue
        margin = (p.season_avg - p.line) if p.season_avg > 0 else (p.darko_val - p.line)
        if margin < LOCK_MIN_MARGIN.get(p.stat, 1.5): continue
        if (p.season_avg or 0) < LOCK_MIN_AVG.get(p.stat, 5.0): continue
        locks.append(p); lp.add(p.player); lg.add(p.game)
        if len(locks) >= 6: break

    # 3-LEG
    p3, p3p, p3g = [], set(), set()
    for p in picks:
        if p.player in p3p or p.game in p3g: continue
        if p.model_prob < 0.65: continue
        if "ODDS_TRAP" in p.warnings or "L3_BELOW" in p.warnings: continue
        p3.append(p); p3p.add(p.player); p3g.add(p.game)
        if len(p3) >= 3: break

    # 5-LEG
    p5, p5p, p5g = [], set(), set()
    for p in picks:
        if p.player in p5p or p.game in p5g: continue
        if p.model_prob < 0.62: continue
        if "ODDS_TRAP" in p.warnings or "L3_BELOW" in p.warnings: continue
        p5.append(p); p5p.add(p.player); p5g.add(p.game)
        if len(p5) >= 5: break

    return locks, p3, p5


# ============================================================
# OUTPUT
# ============================================================

def print_results(picks, locks, p3, p5, injuries, has_live):
    print(f"\n{'='*W}")
    mode = "LIVE ODDS" if has_live else "PREVIEW"
    print(f"  🏀 PARLAY ENGINE V5 — HYBRID: DARKO + ML + FILTERS ({mode})")
    print(f"  📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"  🧮 Blend: {W_DARKO:.0%} DARKO + {W_ML:.0%} ML + {W_SEASON:.0%} Season + {W_MARKET:.0%} Market")
    print(f"  🛡️  Filters: L3>line, odds<+200, margin, stars only")
    print(f"{'='*W}")

    # Injuries
    if injuries:
        out = {k:v for k,v in injuries.items() if "OUT" in v.upper()}
        if out:
            print(f"\n⚠️  {len(out)} players OUT")

    # Filter to displayable picks
    if has_live:
        show = [p for p in picks if p.edge >= MIN_EDGE and p.has_live_line][:25
        ]
    else:
        show = picks[:25]

    print(f"\n📊 {len(show)} top picks")
    print(f"\n{'#':>3}  {'Player':<22} {'Stat':<4} {'Line':>5} {'Prob':>6} {'DARKO':>6} {'ML':>5} {'Seas':>5} {'L3':>5} {'Edge':>6} {'Flags':<12}")
    print("-" * W)
    for i, p in enumerate(show, 1):
        edge_s = f"{p.edge:+.1%}" if p.has_live_line else " N/A"
        flags = ",".join(p.warnings)[:12] if p.warnings else "✅"
        print(f"{i:>3}. {p.player:<22} {p.stat:<4} {p.line:>5.1f} {p.model_prob:>5.1%} "
              f"{p.p_darko:>5.1%} {p.p_ml:>5.1%} {p.season_avg:>5.1f} {p.last_3_avg:>5.1f} {edge_s:>6} {flags:<12}")

    # LOCKS
    if locks:
        print(f"\n{'='*W}")
        print(f"  🔒 LOCKS ({len(locks)} picks — all safety filters passed)")
        print(f"{'='*W}")
        for i, p in enumerate(locks, 1):
            odds_s = f"({p.over_odds:+d})" if p.has_live_line and p.over_odds != -110 else ""
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat} {odds_s}")
            print(f"     Blend: {p.model_prob:.1%} = DARKO {p.p_darko:.1%} + ML {p.p_ml:.1%} + Season {p.p_season:.1%}")
            print(f"     Season: {p.season_avg:.1f} | L5: {p.last_5_avg:.1f} | L3: {p.last_3_avg:.1f} | DARKO: {p.darko_val:.1f}")
            if p.has_live_line:
                print(f"     Edge: {p.edge:+.1%} | EV: {p.ev:+.1%} | {p.book}")
            print(f"     vs {p.opponent} | {'Home' if p.is_home else 'Away'} | {p.game}")
    else:
        print(f"\n  ⚠️  No picks passed all safety filters for locks")

    # PARLAYS
    for label, legs in [("🎯 3-LEG SAFE", p3), ("🔥 5-LEG PREMIUM", p5)]:
        if len(legs) >= (3 if "3" in label else 5):
            combo = 1.0
            for p in legs: combo *= p.model_prob
            print(f"\n{'='*W}")
            print(f"  {label} PARLAY — Combined: {combo:.1%}")
            print(f"{'='*W}")
            for i, p in enumerate(legs, 1):
                print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat}")
                print(f"     Blend: {p.model_prob:.1%} | L3: {p.last_3_avg:.1f} | L5: {p.last_5_avg:.1f} | vs {p.opponent}")

    # Methodology
    print(f"\n{'='*W}")
    print("  ℹ️  V5 HYBRID METHODOLOGY")
    print(f"{'='*W}")
    print(f"""
  • 4-source probability blend:
    - DARKO ({W_DARKO:.0%}): opponent-adjusted daily projection (best single predictor)
    - XGBoost ({W_ML:.0%}): 132 features, trained on 23K+ games
    - Season avg ({W_SEASON:.0%}): stable baseline from NBAstuffer
    - Market ({W_MARKET:.0%}): sportsbook implied probability (when available)
  • Safety filters (from Feb 19-23 real results):
    - L3 avg must clear line (hard cap at 58% if not)
    - Odds >= +200 excluded from locks/parlays (33% hit rate)
    - Season margin >= 3.5 PTS / 1.5 REB,AST for locks
    - Min season avg: 15 PTS / 5 REB / 3 AST (no role players)
    - Max 1 pick per game (correlation protection)
    - REB probability capped at 78% (model overconfident)
""")


# ============================================================
# JSON EXPORT
# ============================================================

def export_json(picks, locks, p3, p5, games, injuries, ml_models, args):
    """Write picks to parlaybudv4/static/picks/{date}.json for the dashboard."""
    import argparse
    from datetime import timezone

    today_str = datetime.now().strftime("%Y-%m-%d")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir    = os.path.join(script_dir, "parlaybudv4", "static", "picks")
    os.makedirs(out_dir, exist_ok=True)
    out_path   = os.path.join(out_dir, f"{today_str}.json")

    # Normalise v5 warning codes → frontend-expected names
    WARN_MAP = {
        "ODDS_TRAP":  "ODDS_TRAP",
        "L3_BELOW":   "L3_BELOW_LINE",
        "L5_BELOW":   "L5_BELOW_LINE",
        "SUS_LINE":   "UNUSUAL_LINE",
    }

    def normalise_warnings(ws):
        return [WARN_MAP.get(w, w) for w in ws]

    def pick_to_dict(p: Pick) -> dict:
        norm_warn = normalise_warnings(p.warnings)
        margin    = float(p.season_avg - p.line) if p.season_avg else float(p.darko_val - p.line)
        odds_ok   = not ("ODDS_TRAP" in p.warnings)
        l3_ok     = "L3_BELOW" not in p.warnings
        l5_ok     = "L5_BELOW" not in p.warnings
        unusual   = "SUS_LINE" in p.warnings
        min_avg   = LOCK_MIN_AVG
        min_marg  = LOCK_MIN_MARGIN
        margin_ok = margin >= min_marg.get(p.stat, 1.5)
        avg_ok    = float(p.season_avg or 0) >= min_avg.get(p.stat, 5.0)
        passes_lock   = bool(odds_ok and l3_ok and margin_ok and avg_ok and p.model_prob >= 0.65)
        passes_parlay = bool(odds_ok and l3_ok and p.model_prob >= 0.62)
        return {
            "player":       p.player,
            "team":         p.team,
            "opponent":     p.opponent,
            "game":         p.game,
            "stat":         p.stat,
            "line":         float(p.line),
            "over_odds":    int(p.over_odds),
            "book":         p.book,
            "model_prob":   round(float(p.model_prob), 4),
            "implied_prob": round(float(p.implied_prob), 4),
            "edge":         round(float(p.edge), 4),
            "ev":           round(float(p.ev), 4),
            "season_avg":   round(float(p.season_avg or 0), 1),
            "last_5_avg":   round(float(p.last_5_avg), 1),
            "last_3_avg":   round(float(p.last_3_avg), 1),
            "is_home":      int(p.is_home),
            "has_live_line": bool(p.has_live_line),
            "warnings":     norm_warn,
            "passes_lock_filter":   passes_lock,
            "passes_parlay_filter": passes_parlay,
            "filter_details": {
                "odds_ok":         bool(odds_ok),
                "l3_clears_line":  bool(l3_ok),
                "l5_clears_line":  bool(l5_ok),
                "season_margin":   round(float(margin), 2),
                "season_margin_ok": bool(margin_ok),
                "min_avg_ok":      bool(avg_ok),
                "unusual_line":    bool(unusual),
            },
        }

    def parlay_dict(legs):
        combined = math.prod(p.model_prob for p in legs) if legs else 0.0
        return {
            "legs":          [f"{p.stat} O{p.line} ({p.model_prob:.0%})" for p in legs],
            "combined_prob": round(float(combined), 4),
            "players":       [p.player for p in legs],
        }

    model_stats = {}
    for stat, m in ml_models.items():
        mt = m.get("metrics", {})
        model_stats[stat] = {
            "auc":         round(float(mt.get("roc_auc", 0)), 3),
            "hit_rate_70": round(float(mt.get("hit_rate_70", mt.get("accuracy", 0))), 3),
        }

    games_list    = [{"away": away, "home": home, "label": label}
                     for label, (away, home) in games.items()]
    injuries_list = [{"player": name, "status": status, "reason": ""}
                     for name, status in injuries.items()]

    payload = {
        "date":          today_str,
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "model_version": "v5-hybrid",
        "games":         games_list,
        "injuries":      injuries_list,
        "picks":         [pick_to_dict(p) for p in picks],
        "locks":         [p.player for p in locks],
        "parlay_3leg":   parlay_dict(p3),
        "parlay_5leg":   parlay_dict(p5),
        "model_stats":   model_stats,
        "results":       None,
    }

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ JSON written → {out_path}")
    print(f"   {len(picks)} picks | {len(locks)} locks | {len(p3)}-leg + {len(p5)}-leg parlays")


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse as _argparse
    parser = _argparse.ArgumentParser(description="NBA ML Parlay Engine V5 — DARKO + XGBoost Hybrid")
    parser.add_argument('--fetch-odds',  action='store_true', help='Fetch live sportsbook lines (uses cache if available)')
    parser.add_argument('--force-odds',  action='store_true', help='Bypass cache and re-fetch fresh odds from API')
    parser.add_argument('--json-output', action='store_true', help='Write picks JSON for the dashboard')
    parser.add_argument('--min-prob',    type=float, default=MIN_PROB, help='Min model probability')
    parser.add_argument('--db',          default=DB_PATH)
    parser.add_argument('--models',      default=MODELS_DIR)
    parser.add_argument('--season',      default=SEASON)
    parser.add_argument('--odds-key',    default=ODDS_API_KEY)
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 80)
    print("  🏀 PARLAY ENGINE V5 — HYBRID: DARKO + ML + FILTERS")
    print("=" * 80)

    # 1. Load DARKO
    darko_files = [f for f in os.listdir(script_dir) if f.lower().startswith('darko') and f.lower().endswith('.csv')]
    if not darko_files:
        print("❌ No DARKO CSV found"); sys.exit(1)
    darko_path = os.path.join(script_dir, sorted(darko_files)[-1])
    print(f"\n📊 DARKO: {os.path.basename(darko_path)}")
    darko = load_darko_csv(darko_path)
    print(f"   {len(darko)} projections")

    # 2. Load ML models
    print("\n📦 Loading ML models...")
    ml_models = load_ml_models(os.path.join(script_dir, args.models)) if HAS_XGB else {}
    if ml_models:
        for stat in ml_models:
            m = ml_models[stat].get('metrics', {})
            print(f"   {stat}: AUC={m.get('roc_auc',0):.3f}")
    else:
        print("   ⚠️  No ML models — running DARKO + Season only")

    # 3. Build ML features from DB
    print("\n🧠 Building ML features...")
    db_path = os.path.join(script_dir, args.db)
    ml_features = build_ml_features(db_path, args.season) if HAS_XGB and ml_models else pd.DataFrame()
    if len(ml_features) > 0:
        print(f"   ✅ Features for {len(ml_features)} players")
    else:
        print("   ⚠️  No ML features — ML weight will use 0.5 default")

    # 4. Games + injuries
    print()
    games = fetch_games()
    if not games:
        print("❌ No games today"); sys.exit(0)
    for g in games: print(f"   🏀 {g}")
    print()
    injuries = fetch_injuries()

    # 5. Season stats
    print("📊 Fetching season stats...")
    db_stats = fetch_season_stats()
    print(f"   {len(db_stats)} players")

    # 6. Live odds
    live_odds = {}
    has_live = False
    if FETCH_ODDS or args.fetch_odds or args.force_odds:
        live_odds = fetch_odds(args.odds_key, script_dir=script_dir, force=args.force_odds)
        has_live = len(live_odds) > 0
    else:
        print("\n⚡ Skipping odds (FETCH_ODDS=False)")

    # 7. Generate picks
    print("\n🎯 Generating picks...")
    picks = generate_picks(darko, ml_models, ml_features, db_stats, live_odds, injuries, games)
    print(f"   ✅ {len(picks)} picks")

    # 8. Build locks + parlays with safety filters
    locks, p3, p5 = build_locks_and_parlays(picks, has_live)
    print(f"   🔒 {len(locks)} locks, {len(p3)}-leg parlay, {len(p5)}-leg parlay")

    # 9. Output
    print_results(picks, locks, p3, p5, injuries, has_live)

    # 10. Export JSON for dashboard
    if args.json_output:
        export_json(picks, locks, p3, p5, games, injuries, ml_models, args)


if __name__ == "__main__":
    main()

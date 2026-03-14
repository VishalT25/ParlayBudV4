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
FETCH_ODDS = True   # True = pull live lines from Odds API
                     # False = preview mode (ML probabilities only)

DB_PATH = "parlay_ml.db"
MODELS_DIR = "models"
ODDS_API_KEY = "805d66ea970d21583170a3b1c459c851"
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
# OUTPUT
# ============================================================

def print_results(picks, injuries, has_live, min_prob):
    print(f"\n{'='*W}")
    mode = "LIVE ODDS" if has_live else "PREVIEW (no live odds)"
    print(f"  🏀 PARLAY ENGINE V4 — ML MODEL ({mode})")
    print(f"  📅 {datetime.now().strftime('%A, %B %d, %Y')}")
    print(f"  🧠 Model: XGBoost (trained on 23K+ games, 132 features)")
    print(f"  📏 Min P(over): {min_prob:.0%}")
    if has_live:
        print(f"  📏 Min edge: {MIN_EDGE:.0%}")
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

    # ── LOCKS ──
    locks = []
    seen_players = set()
    seen_games = set()
    for p in ev_picks:
        if p.player in seen_players or p.game in seen_games:
            continue
        if p.stat != 'PTS':  # PTS model is strongest
            continue
        if p.model_prob < 0.65:
            continue
        # Margin check: season avg must clear line by 3.5+
        if p.season_avg > 0 and (p.season_avg - p.line) < 3.5:
            continue
        if has_live and p.over_odds >= 200:
            continue
        locks.append(p)
        seen_players.add(p.player)
        seen_games.add(p.game)
        if len(locks) >= 6:
            break

    if locks:
        print(f"\n{'='*W}")
        lbl = "LOCKS (ML + live lines)" if has_live else "PREVIEW LOCKS (verify lines on DraftKings)"
        print(f"  🔒 {lbl}")
        print(f"{'='*W}")
        for i, p in enumerate(locks, 1):
            odds_str = f"({p.over_odds:+d})" if p.has_live_line and p.over_odds != -110 else ""
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat} {odds_str}")
            print(f"     ML P(over): {p.model_prob:.1%} | Season: {p.season_avg:.1f} | Last 5: {p.last_5_avg:.1f} | Last 3: {p.last_3_avg:.1f}")
            if p.has_live_line:
                print(f"     Edge: {p.edge:+.1%} | EV: {p.ev:+.1%} | {p.book}")
            print(f"     vs {p.opponent} | {'Home' if p.is_home else 'Away'} | {p.game}")

    # ── 3-LEG SAFE PARLAY ──
    parlay_pool = []
    p_seen = set()
    g_seen = set()
    for p in ev_picks:
        if p.player in p_seen or p.game in g_seen:
            continue
        if p.model_prob < 0.65:
            continue
        if has_live and p.over_odds >= 200:
            continue
        parlay_pool.append(p)
        p_seen.add(p.player)
        g_seen.add(p.game)

    if len(parlay_pool) >= 3:
        p3 = parlay_pool[:3]
        combo_prob = 1.0
        for p in p3:
            combo_prob *= p.model_prob

        print(f"\n{'='*W}")
        print(f"  🎯 3-LEG SAFE PARLAY")
        print(f"  Combined P(hit): {combo_prob:.1%}")
        print(f"{'='*W}")
        for i, p in enumerate(p3, 1):
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat}")
            print(f"     ML: {p.model_prob:.1%} | Avg5: {p.last_5_avg:.1f} | vs {p.opponent} | {p.game}")

    if len(parlay_pool) >= 5:
        p5 = parlay_pool[:5]
        combo_prob = 1.0
        for p in p5:
            combo_prob *= p.model_prob

        print(f"\n{'='*W}")
        print(f"  🔥 5-LEG PREMIUM PARLAY")
        print(f"  Combined P(hit): {combo_prob:.1%}")
        print(f"{'='*W}")
        for i, p in enumerate(p5, 1):
            print(f"\n  {i}. {p.player} ({p.team}) — Over {p.line:.1f} {p.stat}")
            print(f"     ML: {p.model_prob:.1%} | Avg5: {p.last_5_avg:.1f} | vs {p.opponent} | {p.game}")

    # Methodology
    print(f"\n{'='*W}")
    print("  ℹ️  V4 METHODOLOGY")
    print(f"{'='*W}")
    print(f"""
  • Model: XGBoost trained on {23415} games (2023-25), validated on 2025-26
  • Features: 132 (rolling avgs, opponent defense, usage, interactions, rest)
  • P(over) = model.predict_proba() — NOT Normal CDF
  • Calibration: predicted 70% → actual 73% (verified on 2,568 picks)
  • Edge = P(over) - implied_prob from sportsbook
  • PTS/REB/AST only (STL/BLK models unreliable — excluded)
  • Season margin >= 3.5 required for locks
  • Max 1 pick per game (correlation protection)
  • Odds >= +200 excluded when live lines available
""")


# ============================================================
# JSON EXPORT (for SvelteKit dashboard)
# ============================================================

def export_json(picks, injuries, games, has_live, models, args, min_prob):
    """Export picks in the dashboard JSON schema to parlaybudv4/static/picks/."""
    from datetime import timezone

    today = datetime.now().strftime("%Y-%m-%d")

    if args.json_output == 'auto':
        script_dir = os.path.dirname(os.path.abspath(__file__))
        out_path = os.path.join(script_dir, 'parlaybudv4', 'static', 'picks', f'{today}.json')
    else:
        out_path = args.json_output

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    # Mirror print_results logic to compute ev_picks
    if has_live:
        ev_picks = [p for p in picks if p.edge >= MIN_EDGE and p.has_live_line]
    else:
        ev_picks = [p for p in picks if p.model_prob >= min_prob]

    # Compute locks (same rules as print_results)
    lock_names = []
    seen_players: set = set()
    seen_games: set = set()
    for p in ev_picks:
        if p.player in seen_players or p.game in seen_games:
            continue
        if p.stat != 'PTS':
            continue
        if p.model_prob < 0.65:
            continue
        if p.season_avg > 0 and (p.season_avg - p.line) < 3.5:
            continue
        if has_live and p.over_odds >= 200:
            continue
        lock_names.append(p.player)
        seen_players.add(p.player)
        seen_games.add(p.game)
        if len(lock_names) >= 6:
            break

    # Compute parlay pool
    parlay_pool = []
    p_seen: set = set()
    g_seen: set = set()
    for p in ev_picks:
        if p.player in p_seen or p.game in g_seen:
            continue
        if p.model_prob < 0.65:
            continue
        if has_live and p.over_odds >= 200:
            continue
        parlay_pool.append(p)
        p_seen.add(p.player)
        g_seen.add(p.game)

    def make_parlay(pool, n):
        if len(pool) < n:
            return {"legs": [], "combined_prob": 0.0, "players": []}
        legs = pool[:n]
        combined_prob = 1.0
        for lp in legs:
            combined_prob *= lp.model_prob
        return {
            "legs": [f"{lp.player} {lp.stat} O{lp.line}" for lp in legs],
            "combined_prob": round(combined_prob, 4),
            "players": [lp.player for lp in legs],
        }

    # Model stats from loaded model metadata
    model_stats = {}
    for stat, data in models.items():
        m = data.get('metrics', {})
        model_stats[stat] = {
            "auc": round(float(m.get('roc_auc', 0)), 3),
            "hit_rate_70": round(float(m.get('hit_rate_70', 0)), 3),
        }

    output = {
        "date": today,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_version": "v4-xgboost",
        "games": [
            {"away": away, "home": home, "label": label}
            for label, (away, home) in games.items()
        ],
        "injuries": [
            {"player": name, "status": status, "reason": ""}
            for name, status in injuries.items()
        ],
        "picks": [
            {
                "player": p.player,
                "team": p.team,
                "opponent": p.opponent,
                "game": p.game,
                "stat": p.stat,
                "line": p.line,
                "over_odds": p.over_odds,
                "book": p.book,
                "model_prob": round(p.model_prob, 4),
                "implied_prob": round(p.implied_prob, 4),
                "edge": round(p.edge, 4),
                "ev": round(p.ev, 4),
                "season_avg": round(p.season_avg, 1),
                "last_5_avg": round(p.last_5_avg, 1),
                "last_3_avg": round(p.last_3_avg, 1),
                "is_home": p.is_home,
                "has_live_line": p.has_live_line,
            }
            for p in ev_picks[:30]
        ],
        "locks": lock_names,
        "parlay_3leg": make_parlay(parlay_pool, 3),
        "parlay_5leg": make_parlay(parlay_pool, 5),
        "model_stats": model_stats,
        "results": None,
    }

    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ JSON exported → {out_path}")
    return out_path


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
    parser.add_argument('--json-output', nargs='?', const='auto', default=None,
                        metavar='PATH',
                        help='Export picks to JSON. Omit PATH to use default: '
                             'parlaybudv4/static/picks/YYYY-MM-DD.json')
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
    print(f"   ✅ {len(picks)} picks generated")

    # Print results
    print_results(picks, injuries, has_live, args.min_prob)

    # Export JSON for dashboard
    if args.json_output is not None:
        export_json(picks, injuries, games, has_live, models, args, args.min_prob)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
collect_bbref.py — NBA ML Parlay Model: Data Collection via Basketball Reference

Collects:
  1. Season per-game stats
  2. Season advanced stats
  3. Season play-by-play stats
  4. Season shooting stats
  5. Individual player game logs
  6. Team per-game and opponent per-game stats

Usage:
  pip install requests beautifulsoup4 pandas lxml
  python3 collect_bbref.py --seasons 2025-26
  python3 collect_bbref.py --seasons 2023-24 2024-25 2025-26 --game-logs
"""

import sys
import re
import time
import sqlite3
import argparse
import logging
import unicodedata
import html as html_lib
from datetime import datetime
from typing import Optional
from io import StringIO

import pandas as pd

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

DB_PATH = "parlay_ml.db"
RATE_LIMIT_DELAY = 3.5
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
log = logging.getLogger("bbref")

BBREF_BASE = "https://www.basketball-reference.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
}

NBA_TEAMS = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BRK": "Brooklyn Nets",
    "CHO": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHO": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}

BBREF_ABBR_MAP = {
    "BRK": "BKN",
    "CHO": "CHA",
    "PHO": "PHX",
}

request_count = 0
last_request_time = 0.0
session = None


def season_to_year(season: str) -> int:
    return int("20" + season.split("-")[1]) if "-" in season else int(season)


def init_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    return unicodedata.normalize("NFKC", str(text)).strip()


def dedupe_columns(columns) -> list[str]:
    seen = {}
    out = []
    for col in columns:
        if isinstance(col, tuple):
            parts = [str(x).strip() for x in col if "Unnamed" not in str(x)]
            name = parts[-1] if parts else str(col[-1]).strip()
        else:
            name = str(col).strip()
        name = re.sub(r"\s+", " ", name)
        idx = seen.get(name, 0)
        out.append(name if idx == 0 else f"{name}.{idx}")
        seen[name] = idx + 1
    return out


def fetch_html(url: str) -> Optional[str]:
    global request_count, last_request_time, session

    if session is None:
        session = init_session()

    elapsed = time.time() - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=30)
            last_request_time = time.time()
            request_count += 1

            if resp.status_code == 429:
                wait = 60 * (attempt + 1)
                log.warning(f"Rate limited (429) for {url}. Waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                wait = 15 * (attempt + 1)
                log.warning(f"Forbidden (403) for {url}. Waiting {wait}s before retry...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text.replace("<!--", "").replace("-->", "")

        except Exception as e:
            wait = RATE_LIMIT_DELAY * (attempt + 2) * 2
            log.warning(f"Fetch failed (attempt {attempt + 1}/3) for {url}: {e}")
            if attempt < 2:
                time.sleep(wait)

    log.error(f"Failed to fetch {url} after 3 attempts")
    return None


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    html = fetch_html(url)
    if not html:
        return None
    return BeautifulSoup(html, "lxml")

def parse_table(soup: BeautifulSoup, table_id: str) -> Optional[pd.DataFrame]:
    table = soup.find("table", {"id": table_id})
    if not table:
        log.debug(f"Table '{table_id}' not found")
        return None

    try:
        thead = table.find("thead")
        header_rows = len(thead.find_all("tr")) if thead else 1

        if header_rows >= 2:
            df = pd.read_html(StringIO(str(table)), header=[0, 1])[0]
        else:
            df = pd.read_html(StringIO(str(table)), header=0)[0]

        df.columns = dedupe_columns(df.columns)

        if "Rk" in df.columns:
            df = df[df["Rk"].astype(str) != "Rk"]

        for col in ("Date", "Player", "Team", "Tm", "Opp", "Result", "Unnamed: 5", "Unnamed: 7"):
            if col in df.columns:
                df[col] = df[col].astype(str).map(normalize_text)

        return df.reset_index(drop=True)
    except Exception as e:
        log.warning(f"Failed to parse table '{table_id}': {e}")
        return None

def extract_slug_map_from_raw_html(raw_html: str) -> dict[str, str]:
    """
    Extract player name -> BBRef slug from raw HTML, without relying on BeautifulSoup DOM traversal.

    Matches links like:
      /players/d/doncilu01.html">Luka Doncic</a>
    """
    slug_map = {}

    pattern = re.compile(
        r'href="/players/[a-z]/([a-z0-9]+)\.html"[^>]*>([^<]+)</a>',
        re.IGNORECASE
    )

    for slug, raw_name in pattern.findall(raw_html):
        name = normalize_text(html_lib.unescape(raw_name))
        if name and len(name) > 2:
            slug_map[name] = slug

    return slug_map

def extract_player_slugs_from_html(html: str) -> dict[str, str]:
    """
    Extract BBRef player slug map from raw season page HTML.
    Example match:
      <th ... data-stat="player" ...><a href="/players/b/brunsja01.html">Jalen Brunson</a>
    """
    slug_map = {}

    pattern = re.compile(
        r'<(?:th|td)[^>]*data-stat="player"[^>]*>\s*'
        r'<a[^>]*href="/players/[a-z]/([a-z0-9]+)\.html"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL
    )

    for slug, raw_name in pattern.findall(html):
        name = html_lib.unescape(re.sub(r"<.*?>", "", raw_name)).strip()
        name = normalize_text(name)
        if name and len(name) > 2:
            slug_map[name] = slug

    return slug_map

def get_row_value(row: pd.Series, *names, default=None):
    for name in names:
        if name in row.index:
            val = row[name]
            if not pd.isna(val):
                return val
    return default


def _safe_float(val) -> Optional[float]:
    try:
        if pd.isna(val) or val == "" or val is None:
            return None
        if isinstance(val, str):
            val = val.replace("%", "").replace(",", "").strip()
            if val == "":
                return None
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    try:
        if pd.isna(val) or val == "" or val is None:
            return None
        if isinstance(val, str):
            val = val.replace(",", "").strip()
            if val == "":
                return None
        return int(float(val))
    except (ValueError, TypeError):
        return None


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS season_stats_pergame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        player_slug TEXT,
        pos TEXT,
        age INTEGER,
        team TEXT,
        games INTEGER,
        games_started INTEGER,
        mpg REAL,
        fgm REAL, fga REAL, fg_pct REAL,
        fg3m REAL, fg3a REAL, fg3_pct REAL,
        fg2m REAL, fg2a REAL, fg2_pct REAL,
        efg_pct REAL,
        ftm REAL, fta REAL, ft_pct REAL,
        orb REAL, drb REAL, reb REAL,
        ast REAL, stl REAL, blk REAL,
        tov REAL, pf REAL, pts REAL,
        season TEXT NOT NULL,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player, team, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS season_stats_advanced (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        pos TEXT,
        age INTEGER,
        team TEXT,
        games INTEGER,
        mpg REAL,
        per REAL,
        ts_pct REAL,
        fg3a_rate REAL,
        fta_rate REAL,
        orb_pct REAL, drb_pct REAL, reb_pct REAL,
        ast_pct REAL,
        stl_pct REAL,
        blk_pct REAL,
        tov_pct REAL,
        usg_pct REAL,
        ows REAL, dws REAL, ws REAL,
        ws_per_48 REAL,
        obpm REAL, dbpm REAL, bpm REAL,
        vorp REAL,
        season TEXT NOT NULL,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player, team, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS season_stats_pbp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        pos TEXT,
        age INTEGER,
        team TEXT,
        games INTEGER,
        mpg REAL,
        pct_pg REAL, pct_sg REAL, pct_sf REAL, pct_pf REAL, pct_c REAL,
        on_court_plus_minus REAL,
        on_off_diff REAL,
        bad_pass_tov REAL,
        lost_ball_tov REAL,
        shoot_fouls_committed REAL,
        shoot_fouls_drawn REAL,
        and_ones REAL,
        blocked_att REAL,
        season TEXT NOT NULL,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player, team, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS season_stats_shooting (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        pos TEXT,
        team TEXT,
        games INTEGER,
        mpg REAL,
        pct_fga_0_3 REAL,
        pct_fga_3_10 REAL,
        pct_fga_10_16 REAL,
        pct_fga_16_3p REAL,
        pct_fga_3p REAL,
        fg_pct_0_3 REAL,
        fg_pct_3_10 REAL,
        fg_pct_10_16 REAL,
        fg_pct_16_3p REAL,
        fg_pct_3p REAL,
        corner_3_pct REAL,
        corner_3_pct_fga REAL,
        pct_ast_fg2 REAL,
        pct_ast_fg3 REAL,
        dunk_pct_fga REAL,
        dunks_made REAL,
        season TEXT NOT NULL,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player, team, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS player_game_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player TEXT NOT NULL,
        player_slug TEXT,
        season TEXT NOT NULL,
        game_date TEXT NOT NULL,
        team TEXT,
        is_home INTEGER,
        opponent TEXT,
        result TEXT,
        started INTEGER,
        mp TEXT,
        mp_float REAL,
        fg INTEGER, fga INTEGER, fg_pct REAL,
        fg3 INTEGER, fg3a INTEGER, fg3_pct REAL,
        ft INTEGER, fta INTEGER, ft_pct REAL,
        orb INTEGER, drb INTEGER, reb INTEGER,
        ast INTEGER, stl INTEGER, blk INTEGER,
        tov INTEGER, pf INTEGER, pts INTEGER,
        game_score REAL,
        plus_minus REAL,
        days_rest INTEGER,
        is_b2b INTEGER,
        game_number INTEGER,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player, game_date, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS team_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team TEXT NOT NULL,
        season TEXT NOT NULL,
        stat_type TEXT,
        wins INTEGER, losses INTEGER,
        mpg REAL,
        fgm REAL, fga REAL, fg_pct REAL,
        fg3m REAL, fg3a REAL, fg3_pct REAL,
        ftm REAL, fta REAL, ft_pct REAL,
        orb REAL, drb REAL, reb REAL,
        ast REAL, stl REAL, blk REAL,
        tov REAL, pf REAL, pts REAL,
        off_rating REAL,
        def_rating REAL,
        net_rating REAL,
        pace REAL,
        ts_pct REAL,
        efg_pct REAL,
        tov_pct REAL,
        orb_pct REAL,
        ft_rate REAL,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(team, season, stat_type)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS team_game_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team TEXT NOT NULL,
        season TEXT NOT NULL,
        game_date TEXT NOT NULL,
        is_home INTEGER,
        opponent TEXT,
        result TEXT,
        pts INTEGER, opp_pts INTEGER,
        fg INTEGER, fga INTEGER, fg_pct REAL,
        fg3 INTEGER, fg3a INTEGER, fg3_pct REAL,
        ft INTEGER, fta INTEGER, ft_pct REAL,
        orb INTEGER, drb INTEGER, reb INTEGER,
        ast INTEGER, stl INTEGER, blk INTEGER,
        tov INTEGER, pf INTEGER,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(team, game_date, season)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS collection_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task TEXT NOT NULL,
        status TEXT DEFAULT 'started',
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT,
        rows_collected INTEGER DEFAULT 0,
        notes TEXT
    )
    """)

    conn.commit()
    log.info(f"Database initialized: {db_path}")
    return conn


def collect_season_pergame(conn: sqlite3.Connection, season: str):
    year = season_to_year(season)
    log.info(f"📊 Collecting per-game stats for {season}...")

    url = f"{BBREF_BASE}/leagues/NBA_{year}_per_game.html"

    raw_html = fetch_html(url)
    if not raw_html:
        return

    soup = BeautifulSoup(raw_html, "lxml")

    df = parse_table(soup, "per_game_stats")
    if df is None or df.empty:
        log.warning("  No per-game table found")
        return

    # FIX: BBRef uses data-stat="name_display" here
    slug_map = {}
    table_el = soup.find("table", {"id": "per_game_stats"})
    if table_el:
        player_cells = table_el.select('tbody td[data-stat="name_display"]')
        log.info(f"  Found {len(player_cells)} name_display cells")

        for cell in player_cells:
            name = normalize_text(cell.get_text(" ", strip=True))
            slug = normalize_text(cell.get("data-append-csv", ""))

            if not slug:
                link = cell.find("a", href=True)
                if link and "/players/" in link["href"]:
                    slug = link["href"].split("/")[-1].replace(".html", "")

            if name and slug:
                slug_map[name] = slug

    log.info(f"  Extracted {len(slug_map)} player slugs")
    if slug_map:
        log.info(f"  Sample slugs: {list(slug_map.items())[:10]}")

    c = conn.cursor()
    inserted = 0
    missing_slug_count = 0

    for _, row in df.iterrows():
        player = normalize_text(get_row_value(row, "Player", default=""))
        if not player or player == "Player":
            continue

        team = normalize_text(get_row_value(row, "Tm", "Team", default=""))
        team = BBREF_ABBR_MAP.get(team, team)

        slug = slug_map.get(player, "")
        if not slug:
            missing_slug_count += 1

        try:
            c.execute("""
                INSERT OR REPLACE INTO season_stats_pergame
                (player, player_slug, pos, age, team, games, games_started, mpg,
                 fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, fg2m, fg2a, fg2_pct,
                 efg_pct, ftm, fta, ft_pct, orb, drb, reb,
                 ast, stl, blk, tov, pf, pts, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player, slug, normalize_text(get_row_value(row, "Pos", default="")), _safe_int(get_row_value(row, "Age")),
                team, _safe_int(get_row_value(row, "G")), _safe_int(get_row_value(row, "GS")),
                _safe_float(get_row_value(row, "MP")),
                _safe_float(get_row_value(row, "FG")), _safe_float(get_row_value(row, "FGA")),
                _safe_float(get_row_value(row, "FG%")),
                _safe_float(get_row_value(row, "3P")), _safe_float(get_row_value(row, "3PA")),
                _safe_float(get_row_value(row, "3P%")),
                _safe_float(get_row_value(row, "2P")), _safe_float(get_row_value(row, "2PA")),
                _safe_float(get_row_value(row, "2P%")),
                _safe_float(get_row_value(row, "eFG%")),
                _safe_float(get_row_value(row, "FT")), _safe_float(get_row_value(row, "FTA")),
                _safe_float(get_row_value(row, "FT%")),
                _safe_float(get_row_value(row, "ORB")), _safe_float(get_row_value(row, "DRB")),
                _safe_float(get_row_value(row, "TRB")),
                _safe_float(get_row_value(row, "AST")), _safe_float(get_row_value(row, "STL")),
                _safe_float(get_row_value(row, "BLK")),
                _safe_float(get_row_value(row, "TOV")), _safe_float(get_row_value(row, "PF")),
                _safe_float(get_row_value(row, "PTS")),
                season,
            ))
            inserted += 1
        except Exception as e:
            log.debug(f"  Skip {player}: {e}")

    conn.commit()
    log.info(f"  ✅ {inserted} players' per-game stats")
    log.info(f"  Missing slugs for {missing_slug_count} rows")

def collect_season_advanced(conn: sqlite3.Connection, season: str):
    year = season_to_year(season)
    log.info(f"📊 Collecting advanced stats for {season}...")

    url = f"{BBREF_BASE}/leagues/NBA_{year}_advanced.html"
    soup = fetch_page(url)
    if not soup:
        return

    df = parse_table(soup, "advanced")
    if df is None or df.empty:
        log.warning("  No advanced table found")
        return

    c = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        player = normalize_text(get_row_value(row, "Player", default=""))
        if not player or player == "Player":
            continue

        team = normalize_text(get_row_value(row, "Tm", "Team", default=""))
        team = BBREF_ABBR_MAP.get(team, team)

        try:
            c.execute("""
                INSERT OR REPLACE INTO season_stats_advanced
                (player, pos, age, team, games, mpg,
                 per, ts_pct, fg3a_rate, fta_rate,
                 orb_pct, drb_pct, reb_pct, ast_pct, stl_pct, blk_pct,
                 tov_pct, usg_pct, ows, dws, ws, ws_per_48,
                 obpm, dbpm, bpm, vorp, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player, normalize_text(get_row_value(row, "Pos", default="")), _safe_int(get_row_value(row, "Age")),
                team, _safe_int(get_row_value(row, "G")), _safe_float(get_row_value(row, "MP")),
                _safe_float(get_row_value(row, "PER")), _safe_float(get_row_value(row, "TS%")),
                _safe_float(get_row_value(row, "3PAr")), _safe_float(get_row_value(row, "FTr")),
                _safe_float(get_row_value(row, "ORB%")), _safe_float(get_row_value(row, "DRB%")),
                _safe_float(get_row_value(row, "TRB%")), _safe_float(get_row_value(row, "AST%")),
                _safe_float(get_row_value(row, "STL%")), _safe_float(get_row_value(row, "BLK%")),
                _safe_float(get_row_value(row, "TOV%")), _safe_float(get_row_value(row, "USG%")),
                _safe_float(get_row_value(row, "OWS")), _safe_float(get_row_value(row, "DWS")),
                _safe_float(get_row_value(row, "WS")), _safe_float(get_row_value(row, "WS/48")),
                _safe_float(get_row_value(row, "OBPM")), _safe_float(get_row_value(row, "DBPM")),
                _safe_float(get_row_value(row, "BPM")), _safe_float(get_row_value(row, "VORP")),
                season,
            ))
            inserted += 1
        except Exception as e:
            log.debug(f"  Skip {player}: {e}")

    conn.commit()
    log.info(f"  ✅ {inserted} players' advanced stats")


def collect_season_pbp(conn: sqlite3.Connection, season: str):
    year = season_to_year(season)
    log.info(f"📊 Collecting play-by-play stats for {season}...")

    url = f"{BBREF_BASE}/leagues/NBA_{year}_play-by-play.html"
    soup = fetch_page(url)
    if not soup:
        return

    df = parse_table(soup, "pbp_stats")
    if df is None or df.empty:
        log.warning("  No PBP table found")
        return

    c = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        player = normalize_text(get_row_value(row, "Player", default=""))
        if not player or player == "Player":
            continue

        team = normalize_text(get_row_value(row, "Tm", "Team", default=""))
        team = BBREF_ABBR_MAP.get(team, team)

        try:
            c.execute("""
                INSERT OR REPLACE INTO season_stats_pbp
                (player, pos, age, team, games, mpg,
                 pct_pg, pct_sg, pct_sf, pct_pf, pct_c,
                 on_court_plus_minus, on_off_diff,
                 bad_pass_tov, lost_ball_tov,
                 shoot_fouls_committed, shoot_fouls_drawn,
                 and_ones, blocked_att, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player, normalize_text(get_row_value(row, "Pos", default="")), _safe_int(get_row_value(row, "Age")),
                team, _safe_int(get_row_value(row, "G")), _safe_float(get_row_value(row, "MP")),
                _safe_float(get_row_value(row, "PG%")),
                _safe_float(get_row_value(row, "SG%")),
                _safe_float(get_row_value(row, "SF%")),
                _safe_float(get_row_value(row, "PF%")),
                _safe_float(get_row_value(row, "C%")),
                _safe_float(get_row_value(row, "OnCourt")),
                _safe_float(get_row_value(row, "On-Off")),
                _safe_float(get_row_value(row, "BadPass")),
                _safe_float(get_row_value(row, "LostBall")),
                _safe_float(get_row_value(row, "Shoot")),
                _safe_float(get_row_value(row, "Shoot.1")),
                _safe_float(get_row_value(row, "And1")),
                _safe_float(get_row_value(row, "Blkd")),
                season,
            ))
            inserted += 1
        except Exception as e:
            log.debug(f"  Skip {player}: {e}")

    conn.commit()
    log.info(f"  ✅ {inserted} players' PBP stats")


def collect_season_shooting(conn: sqlite3.Connection, season: str):
    year = season_to_year(season)
    log.info(f"📊 Collecting shooting stats for {season}...")

    url = f"{BBREF_BASE}/leagues/NBA_{year}_shooting.html"
    soup = fetch_page(url)
    if not soup:
        return

    df = parse_table(soup, "shooting")
    if df is None or df.empty:
        log.warning("  No shooting table found")
        return

    c = conn.cursor()
    inserted = 0

    for _, row in df.iterrows():
        player = normalize_text(get_row_value(row, "Player", default=""))
        if not player or player == "Player":
            continue

        team = normalize_text(get_row_value(row, "Tm", "Team", default=""))
        team = BBREF_ABBR_MAP.get(team, team)

        try:
            c.execute("""
                INSERT OR REPLACE INTO season_stats_shooting
                (player, pos, team, games, mpg,
                 pct_fga_0_3, pct_fga_3_10, pct_fga_10_16, pct_fga_16_3p, pct_fga_3p,
                 fg_pct_0_3, fg_pct_3_10, fg_pct_10_16, fg_pct_16_3p, fg_pct_3p,
                 corner_3_pct, corner_3_pct_fga,
                 pct_ast_fg2, pct_ast_fg3, dunk_pct_fga, dunks_made, season)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player, normalize_text(get_row_value(row, "Pos", default="")), team,
                _safe_int(get_row_value(row, "G")), _safe_float(get_row_value(row, "MP")),
                _safe_float(get_row_value(row, "0-3")),
                _safe_float(get_row_value(row, "3-10")),
                _safe_float(get_row_value(row, "10-16")),
                _safe_float(get_row_value(row, "16-3P")),
                _safe_float(get_row_value(row, "3P")),
                _safe_float(get_row_value(row, "0-3.1")),
                _safe_float(get_row_value(row, "3-10.1")),
                _safe_float(get_row_value(row, "10-16.1")),
                _safe_float(get_row_value(row, "16-3P.1")),
                _safe_float(get_row_value(row, "3P.1")),
                _safe_float(get_row_value(row, "3P%.1", "%3PA.1")),
                _safe_float(get_row_value(row, "%3PA")),
                _safe_float(get_row_value(row, "2P.2", "2P")),
                _safe_float(get_row_value(row, "3P.2")),
                _safe_float(get_row_value(row, "%FGA")),
                _safe_float(get_row_value(row, "#")),
                season,
            ))
            inserted += 1
        except Exception as e:
            log.debug(f"  Skip {player}: {e}")

    conn.commit()
    log.info(f"  ✅ {inserted} players' shooting stats")


def collect_player_game_log(conn: sqlite3.Connection, player_name: str, player_slug: str, season: str) -> int:
    year = season_to_year(season)
    url = f"{BBREF_BASE}/players/{player_slug[0]}/{player_slug}/gamelog/{year}"

    raw_html = fetch_html(url)
    if not raw_html:
        log.warning(f"No page for {player_name} ({player_slug})")
        return 0

    df = None

    # First try: exact table id
    try:
        tables = pd.read_html(StringIO(raw_html), attrs={"id": "pgl_basic"})
        if tables:
            df = tables[0]
    except Exception:
        pass

    # Second try: scan all tables and pick the regular-season game log
    if df is None:
        try:
            all_tables = pd.read_html(StringIO(raw_html))
            for t in all_tables:
                cols = [str(c) for c in t.columns]
                if "Date" in cols and "Opp" in cols and "MP" in cols and "PTS" in cols:
                    df = t
                    break
        except Exception:
            pass

    if df is None or df.empty:
        log.warning(f"No game log dataframe for {player_name} ({player_slug}) -> {url}")
        return 0

    # Normalize columns like the other parser does
    df.columns = dedupe_columns(df.columns)
    if "Rk" in df.columns:
        df = df[df["Rk"].astype(str) != "Rk"]

    c = conn.cursor()
    inserted = 0

    inactive_markers = {
        "Inactive",
        "Did Not Play",
        "Did Not Dress",
        "Not With Team",
        "Player Suspended",
    }

    for _, row in df.iterrows():
        raw_date = normalize_text(str(get_row_value(row, "Date", default="")))
        dt = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(dt):
            continue
        game_date = dt.date().isoformat()

        mp_raw = normalize_text(str(get_row_value(row, "MP", default="")))
        pts_raw = normalize_text(str(get_row_value(row, "PTS", default="")))
        gs_raw = normalize_text(str(get_row_value(row, "GS", default="")))

        if mp_raw in inactive_markers or pts_raw in inactive_markers or gs_raw in inactive_markers:
            continue

        opponent = normalize_text(str(get_row_value(row, "Opp", default="")))
        opponent = BBREF_ABBR_MAP.get(opponent, opponent)

        team = normalize_text(str(get_row_value(row, "Tm", "Team", default="")))
        team = BBREF_ABBR_MAP.get(team, team)

        home_away = normalize_text(str(get_row_value(row, "Unnamed: 5", default="")))
        is_home = 0 if home_away == "@" else 1

        result = normalize_text(str(get_row_value(row, "Unnamed: 7", "Result", default="")))
        started = 1 if gs_raw == "1" else 0

        mp_float = None
        if ":" in mp_raw:
            try:
                mm, ss = mp_raw.split(":", 1)
                mp_float = int(mm) + int(ss) / 60.0
            except ValueError:
                mp_float = None
        else:
            mp_float = _safe_float(mp_raw)

        try:
            c.execute("""
                INSERT OR IGNORE INTO player_game_logs
                (player, player_slug, season, game_date, team, is_home, opponent,
                 result, started, mp, mp_float,
                 fg, fga, fg_pct, fg3, fg3a, fg3_pct, ft, fta, ft_pct,
                 orb, drb, reb, ast, stl, blk, tov, pf, pts,
                 game_score, plus_minus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_name, player_slug, season, game_date, team, is_home, opponent,
                result, started, mp_raw, mp_float,
                _safe_int(get_row_value(row, "FG")), _safe_int(get_row_value(row, "FGA")),
                _safe_float(get_row_value(row, "FG%")),
                _safe_int(get_row_value(row, "3P")), _safe_int(get_row_value(row, "3PA")),
                _safe_float(get_row_value(row, "3P%")),
                _safe_int(get_row_value(row, "FT")), _safe_int(get_row_value(row, "FTA")),
                _safe_float(get_row_value(row, "FT%")),
                _safe_int(get_row_value(row, "ORB")), _safe_int(get_row_value(row, "DRB")),
                _safe_int(get_row_value(row, "TRB")),
                _safe_int(get_row_value(row, "AST")), _safe_int(get_row_value(row, "STL")),
                _safe_int(get_row_value(row, "BLK")),
                _safe_int(get_row_value(row, "TOV")), _safe_int(get_row_value(row, "PF")),
                _safe_int(get_row_value(row, "PTS")),
                _safe_float(get_row_value(row, "GmSc")),
                _safe_float(get_row_value(row, "+/-")),
            ))
            inserted += 1
        except Exception as e:
            log.warning(f"Insert failed for {player_name} {game_date}: {e}")

    conn.commit()
    if inserted == 0:
        log.warning(f"{player_name} ({player_slug}) parsed but inserted 0 rows")
    else:
        log.info(f"  {player_name}: inserted {inserted} game rows")
    return inserted

def collect_all_game_logs(conn: sqlite3.Connection, season: str, min_ppg: float = 10.0):
    log.info(f"📊 Collecting individual game logs for {season} (min {min_ppg} PPG)...")
    c = conn.cursor()

    players = c.execute("""
        SELECT player, player_slug, MAX(pts) AS pts
        FROM season_stats_pergame
        WHERE season = ?
          AND pts >= ?
          AND games >= 10
          AND COALESCE(player_slug, '') != ''
          AND team != 'TOT'
        GROUP BY player, player_slug
        ORDER BY pts DESC
    """, (season, min_ppg)).fetchall()

    log.info(f"  {len(players)} players qualify (>= {min_ppg} PPG with valid slug)")
    total_rows = 0

    for i, (player_name, slug, ppg) in enumerate(players, start=1):
        existing = c.execute(
            "SELECT COUNT(*) FROM player_game_logs WHERE player = ? AND season = ?",
            (player_name, season)
        ).fetchone()[0]
        if existing >= 10:
            continue

        rows = collect_player_game_log(conn, player_name, slug, season)
        total_rows += rows

        if i % 10 == 0:
            log.info(f"  ... {i}/{len(players)} players, {total_rows} game rows")

    log.info(f"  ✅ {total_rows} game log rows collected")


def collect_team_stats(conn: sqlite3.Connection, season: str):
    year = season_to_year(season)
    log.info(f"📊 Collecting team stats for {season}...")

    url = f"{BBREF_BASE}/leagues/NBA_{year}.html"
    soup = fetch_page(url)
    if not soup:
        return

    c = conn.cursor()

    for table_id, stat_type in [("per_game-team", "team"), ("per_game-opponent", "opponent")]:
        df = parse_table(soup, table_id)
        if df is None:
            for alt in {
                "per_game-team": ["team-stats-per_game", "team_stats"],
                "per_game-opponent": ["opponent-stats-per_game", "opp_stats"],
            }.get(table_id, []):
                df = parse_table(soup, alt)
                if df is not None:
                    break

        if df is None or df.empty:
            log.warning(f"  No {stat_type} table found")
            continue

        inserted = 0
        for _, row in df.iterrows():
            team = normalize_text(str(get_row_value(row, "Team", default=""))).replace("*", "")
            if not team or team in ("League Average", "Team"):
                continue

            team_abbr = None
            for abbr, full in NBA_TEAMS.items():
                if full.lower() == team.lower() or abbr.lower() == team.lower():
                    team_abbr = BBREF_ABBR_MAP.get(abbr, abbr)
                    break
            if not team_abbr:
                team_abbr = team[:3].upper()

            try:
                c.execute("""
                    INSERT OR REPLACE INTO team_stats
                    (team, season, stat_type, wins, losses, mpg,
                     fgm, fga, fg_pct, fg3m, fg3a, fg3_pct,
                     ftm, fta, ft_pct, orb, drb, reb,
                     ast, stl, blk, tov, pf, pts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    team_abbr, season, stat_type,
                    _safe_int(get_row_value(row, "W")), _safe_int(get_row_value(row, "L")),
                    _safe_float(get_row_value(row, "MP")),
                    _safe_float(get_row_value(row, "FG")), _safe_float(get_row_value(row, "FGA")),
                    _safe_float(get_row_value(row, "FG%")),
                    _safe_float(get_row_value(row, "3P")), _safe_float(get_row_value(row, "3PA")),
                    _safe_float(get_row_value(row, "3P%")),
                    _safe_float(get_row_value(row, "FT")), _safe_float(get_row_value(row, "FTA")),
                    _safe_float(get_row_value(row, "FT%")),
                    _safe_float(get_row_value(row, "ORB")), _safe_float(get_row_value(row, "DRB")),
                    _safe_float(get_row_value(row, "TRB")),
                    _safe_float(get_row_value(row, "AST")), _safe_float(get_row_value(row, "STL")),
                    _safe_float(get_row_value(row, "BLK")),
                    _safe_float(get_row_value(row, "TOV")), _safe_float(get_row_value(row, "PF")),
                    _safe_float(get_row_value(row, "PTS")),
                ))
                inserted += 1
            except Exception as e:
                log.debug(f"  Skip team {team}: {e}")

        conn.commit()
        log.info(f"  ✅ {inserted} teams' {stat_type} stats")


def compute_rest_days(conn: sqlite3.Connection, season: str):
    log.info("  Computing rest days and B2B flags...")
    c = conn.cursor()

    players = c.execute(
        "SELECT DISTINCT player FROM player_game_logs WHERE season = ?",
        (season,)
    ).fetchall()

    for (player,) in players:
        games = c.execute(
            "SELECT id, game_date FROM player_game_logs WHERE player = ? AND season = ? ORDER BY game_date",
            (player, season)
        ).fetchall()

        prev_date = None
        for i, (row_id, gdate) in enumerate(games, start=1):
            try:
                current = datetime.strptime(gdate, "%Y-%m-%d")
            except ValueError:
                continue

            days_rest = None
            is_b2b = 0
            if prev_date is not None:
                days_rest = (current - prev_date).days
                is_b2b = 1 if days_rest == 1 else 0

            c.execute(
                "UPDATE player_game_logs SET days_rest = ?, is_b2b = ?, game_number = ? WHERE id = ?",
                (days_rest, is_b2b, i, row_id)
            )
            prev_date = current

    conn.commit()
    log.info("  ✅ Rest days computed")


def main():
    parser = argparse.ArgumentParser(description="NBA ML Data Collector (Basketball Reference)")
    parser.add_argument("--seasons", nargs="+", default=["2025-26"])
    parser.add_argument("--db", type=str, default=DB_PATH)
    parser.add_argument("--game-logs", action="store_true", help="Also collect individual player game logs")
    parser.add_argument("--min-ppg", type=float, default=10.0, help="Min PPG for game log collection")
    args = parser.parse_args()

    if not HAS_DEPS:
        print("❌ Install deps: pip install requests beautifulsoup4 pandas lxml")
        sys.exit(1)

    conn = init_db(args.db)

    print("=" * 70)
    print("  🏀 NBA ML PARLAY MODEL — DATA COLLECTION (Basketball Reference)")
    print(f"  Seasons: {', '.join(args.seasons)}")
    print(f"  Database: {args.db}")
    print(f"  Rate limit: {RATE_LIMIT_DELAY}s between requests (20/min)")
    print(f"  Game logs: {'YES' if args.game_logs else 'NO (use --game-logs)'}")
    print("=" * 70)

    for season in args.seasons:
        year = season_to_year(season)
        print(f"\n{'=' * 70}")
        print(f"  📅 Season: {season} (BBRef year: {year})")
        print(f"{'=' * 70}")

        collect_season_pergame(conn, season)
        collect_season_advanced(conn, season)
        collect_season_pbp(conn, season)
        collect_season_shooting(conn, season)
        collect_team_stats(conn, season)

        if args.game_logs:
            collect_all_game_logs(conn, season, min_ppg=args.min_ppg)
            compute_rest_days(conn, season)

    c = conn.cursor()
    print(f"\n{'=' * 70}")
    print("  📊 COLLECTION SUMMARY")
    print(f"{'=' * 70}")

    tables = [
        "season_stats_pergame",
        "season_stats_advanced",
        "season_stats_pbp",
        "season_stats_shooting",
        "player_game_logs",
        "team_stats",
    ]

    for table in tables:
        try:
            count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:<30} {count:>6} rows")
        except Exception:
            print(f"  {table:<30}      0 rows")

    total = 0
    for table in tables:
        try:
            total += c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            pass

    conn.close()
    print(f"\n  Total: {total} rows across all tables")
    print(f"  Total API requests made: {request_count}")
    print(f"\n✅ Done! Database saved to {args.db}")

    if not args.game_logs:
        print("\n💡 To also collect individual game logs:")
        print(f"   python3 collect_bbref.py --seasons {' '.join(args.seasons)} --game-logs")


if __name__ == "__main__":
    main()
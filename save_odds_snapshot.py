#!/usr/bin/env python3
"""
save_odds_snapshot.py — Save today's sportsbook lines to database

Run this BEFORE games start each day. Captures opening/closing lines
for future model retraining with real sportsbook data.

After 2-3 weeks of daily snapshots, retrain with:
  python3 train_model.py --use-real-lines

Usage:
  python3 save_odds_snapshot.py
  python3 save_odds_snapshot.py --key YOUR_API_KEY
  python3 save_odds_snapshot.py --twice   # run morning + pre-game to capture line movement
"""

import os
import sys
import time
import sqlite3
import argparse
import logging
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("odds")

DB_PATH = "parlay_ml.db"
ODDS_API_KEY = "805d66ea970d21583170a3b1c459c851"

MARKET_MAP = {
    "player_points": "PTS",
    "player_rebounds": "REB",
    "player_assists": "AST",
    "player_threes": "3PM",
    "player_blocks": "BLK",
    "player_steals": "STL",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def ensure_table(conn):
    """Create odds_snapshots table if it doesn't exist."""
    conn.execute("""
    CREATE TABLE IF NOT EXISTS odds_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_name TEXT NOT NULL,
        stat_type TEXT NOT NULL,
        line REAL NOT NULL,
        over_odds INTEGER,
        under_odds INTEGER,
        book TEXT,
        game_id TEXT,
        home_team TEXT,
        away_team TEXT,
        game_date TEXT NOT NULL,
        snapshot_time TEXT NOT NULL,
        is_opening INTEGER DEFAULT 0,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()


def fetch_and_save(conn, api_key):
    """Fetch all player props from Odds API and save to database."""
    today = datetime.now().strftime("%Y-%m-%d")
    snap_time = datetime.now().isoformat()

    # Check if we already have a snapshot today
    c = conn.cursor()
    existing = c.execute(
        "SELECT COUNT(*) FROM odds_snapshots WHERE game_date = ?", (today,)
    ).fetchone()[0]
    is_opening = 1 if existing == 0 else 0

    if existing > 0:
        log.info(f"  Already have {existing} lines for today — saving as closing lines")

    # Fetch events
    log.info("Fetching NBA events...")
    try:
        r = requests.get(
            "https://api.the-odds-api.com/v4/sports/basketball_nba/events",
            params={"apiKey": api_key},
            headers=HEADERS,
            timeout=15
        )
        r.raise_for_status()
        events = r.json()
        remaining = r.headers.get("x-requests-remaining", "?")
        log.info(f"  {len(events)} events (API calls left: {remaining})")
    except Exception as e:
        log.error(f"  Events fetch failed: {e}")
        return 0

    markets = "player_points,player_rebounds,player_assists,player_threes,player_blocks,player_steals"
    total = 0

    for i, ev in enumerate(events):
        eid = ev["id"]
        home = ev.get("home_team", "")
        away = ev.get("away_team", "")

        if i > 0:
            time.sleep(1.5)  # rate limit

        log.info(f"  📡 {away} @ {home}...")

        try:
            r2 = requests.get(
                f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{eid}/odds",
                params={
                    "apiKey": api_key,
                    "regions": "us",
                    "markets": markets,
                    "oddsFormat": "american",
                },
                headers=HEADERS,
                timeout=15
            )
            r2.raise_for_status()
            data = r2.json()
        except Exception as e:
            log.warning(f"  Props fetch failed for {eid}: {e}")
            continue

        for bookmaker in data.get("bookmakers", []):
            book = bookmaker.get("title", "Unknown")

            for market in bookmaker.get("markets", []):
                stat = MARKET_MAP.get(market.get("key", ""))
                if not stat:
                    continue

                # Group outcomes by player
                players = {}
                for o in market.get("outcomes", []):
                    pname = o.get("description", "")
                    direction = o.get("name", "")
                    price = o.get("price", 0)
                    point = o.get("point", 0)

                    if pname not in players:
                        players[pname] = {"line": point}
                    if direction == "Over":
                        players[pname]["over"] = price
                    elif direction == "Under":
                        players[pname]["under"] = price

                for pname, vals in players.items():
                    if not pname or "line" not in vals:
                        continue

                    c.execute("""
                        INSERT INTO odds_snapshots
                        (player_name, stat_type, line, over_odds, under_odds,
                         book, game_id, home_team, away_team,
                         game_date, snapshot_time, is_opening)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pname, stat, vals["line"],
                        vals.get("over", -110), vals.get("under", -110),
                        book, eid, home, away,
                        today, snap_time, is_opening,
                    ))
                    total += 1

    conn.commit()
    return total


def print_summary(conn):
    """Show what's in the database."""
    c = conn.cursor()

    total = c.execute("SELECT COUNT(*) FROM odds_snapshots").fetchone()[0]
    dates = c.execute("SELECT COUNT(DISTINCT game_date) FROM odds_snapshots").fetchone()[0]
    latest = c.execute("SELECT MAX(game_date) FROM odds_snapshots").fetchone()[0]

    print(f"\n📊 ODDS DATABASE SUMMARY")
    print(f"   Total lines saved:  {total:,}")
    print(f"   Unique game dates:  {dates}")
    print(f"   Latest snapshot:    {latest}")

    if dates >= 14:
        print(f"\n   ✅ Enough data to retrain with real lines!")
        print(f"   Run: python3 train_model.py --use-real-lines")
    elif dates > 0:
        print(f"\n   ⏳ Need {14 - dates} more days of snapshots before retraining")
        print(f"   Keep running save_odds_snapshot.py daily!")


def main():
    parser = argparse.ArgumentParser(description="Save daily odds snapshot")
    parser.add_argument("--key", default=ODDS_API_KEY, help="Odds API key")
    parser.add_argument("--db", default=DB_PATH, help="Database path")
    args = parser.parse_args()

    print("=" * 60)
    print("  📊 ODDS SNAPSHOT — Saving today's lines to database")
    print(f"  📅 {datetime.now().strftime('%A, %B %d, %Y %H:%M')}")
    print("=" * 60)

    conn = sqlite3.connect(args.db)
    ensure_table(conn)

    total = fetch_and_save(conn, args.key)
    log.info(f"\n✅ Saved {total} prop lines to database")

    print_summary(conn)
    conn.close()


if __name__ == "__main__":
    main()

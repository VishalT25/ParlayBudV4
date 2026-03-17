#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODAY=$(date +%Y-%m-%d)

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🏀  ParlayBud V4 — Daily Pipeline          ║"
echo "║   $(date '+%Y-%m-%d %H:%M %Z')                     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Update game logs ──
echo "📥 Step 1/4 — Refreshing game logs..."
python3 "$SCRIPT_DIR/collect_bbref.py" --seasons 2025-26 --game-logs || echo "⚠️  BBRef failed, using cached data"
echo ""

# ── Step 2: Save odds snapshot to DB (for future retraining) ──
echo "📊 Step 2/4 — Saving odds to database..."
python3 "$SCRIPT_DIR/save_odds_snapshot.py" || echo "⚠️  Odds snapshot failed, continuing..."
echo ""

# ── Step 3: Generate picks ──
echo "🧠 Step 3/4 — Running ML engine..."
python3 "$SCRIPT_DIR/parlay_engine_v4.py" --fetch-odds
echo ""

# ── Step 4: Push to GitHub ──
echo "🚀 Step 4/4 — Pushing to GitHub..."
cd "$SCRIPT_DIR"
git add parlaybudv4/static/picks/
git commit -m "picks: $TODAY"
git push

echo ""
echo "✅ Done! Dashboard updating on Vercel now (~30 sec)."
echo "   JSON: $JSON_PATH"
echo ""
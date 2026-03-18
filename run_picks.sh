#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  ParlayBud V4 — Daily Picks Pipeline
#  Run this ~15 min before tip-off:
#    chmod +x run_picks.sh   (first time only)
#    ./run_picks.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODAY=$(date +%Y-%m-%d)
JSON_PATH="$SCRIPT_DIR/parlaybudv4/static/picks/$TODAY.json"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🏀  ParlayBud V4 - Daily Pipeline          ║"
echo "║   $(date '+%Y-%m-%d %H:%M %Z')                     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 0: Fetch DARKO projections ──
echo "📊 Step 0/4 — Fetching DARKO projections..."
python3 "$SCRIPT_DIR/fetch_darko.py" --output-dir "$SCRIPT_DIR" || echo "⚠️  DARKO fetch failed, using cached"
echo ""

# ── Step 1: Update game logs (recent games only) ──────────────
echo "📥 Step 1/4 - Refreshing season game logs..."
python3 "$SCRIPT_DIR/collect_bbref.py" --seasons 2025-26 --game-logs
echo ""

# ── Step 2: Save odds snapshot to DB (for future retraining) ──
echo "📊 Step 2/4 - Saving odds to database..."
# Pass --skip-if-exists by default; --force-odds bypasses it
if [[ " $* " == *" --force-odds "* ]]; then
  python3 "$SCRIPT_DIR/save_odds_snapshot.py" || echo "⚠️  Odds snapshot failed, continuing..."
else
  python3 "$SCRIPT_DIR/save_odds_snapshot.py" --skip-if-exists || echo "⚠️  Odds snapshot failed, continuing..."
fi
echo ""

# ── Step 3: Generate picks → JSON ────────────────────────────
echo "🧠 Step 3/4 - Running ML engine + fetching odds..."
python3 "$SCRIPT_DIR/parlay_engine_v5.py" --fetch-odds --json-output "$@"
echo ""

# ── Step 3: Push to GitHub → Vercel auto-deploys ─────────────
echo "🚀 Step 4/4 - Pushing to GitHub..."
cd "$SCRIPT_DIR"
git add parlaybudv4/static/picks/
git commit -m "picks: $TODAY"
git push

echo ""
echo "✅ Done! Dashboard updating on Vercel now (~30 sec)."
echo "   JSON: $JSON_PATH"
echo ""
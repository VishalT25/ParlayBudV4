---
name: ParlayBud V4 Project
description: SvelteKit NBA parlay dashboard project structure, GitHub repo, and daily workflow
type: project
---

GitHub repo: https://github.com/VishalT25/ParlayBudV4 (private, user: VishalT25)
Local path: /Users/vtham/Desktop/Projects/ParlayBud/ParlayBudV3/
SvelteKit app: parlaybudv4/ subdirectory

**Why:** ML models are Python (XGBoost), can't run on Vercel. Pre-compute picks locally → push JSON → Vercel serves static dashboard.

**How to apply:** The git root is ParlayBudV3/, not parlaybudv4/. Vercel should be configured to deploy from the parlaybudv4/ subdirectory. The JSON picks files live in parlaybudv4/static/picks/YYYY-MM-DD.json.

Daily workflow uses `./run_picks.sh` which:
1. collect_bbref.py --seasons 2025-26 --game-logs
2. parlay_engine_v4.py --fetch-odds --json-output
3. git add parlaybudv4/static/picks/ && git commit && git push

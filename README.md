# 🏀 ParlayBud
 
An NBA player prop prediction engine that combines machine learning with real-time sportsbook data to find +EV (positive expected value) bets.
 
Built as a project for my Machine Learning course at Western University, inspired by my love for NBA analytics and the [DARKO](https://apanalytics.shinyapps.io/DARKO/) projection system.
 
## The idea
 
Sportsbooks set player prop lines (e.g. "Donovan Mitchell Over 24.5 Points") based on their own models. If I can build a model that estimates the probability of a player going over more accurately than the book's implied probability, I have an edge.
 
That's the whole thesis: **find spots where my model says 73% but the book says 55%.**
 
## How it works
 
The engine blends four probability sources for every pick:
 
| Source | Weight | What it does |
|--------|--------|-------------|
| **DARKO** | 35% | Professional opponent-adjusted projections, updated daily. This is the best single predictor I've found. |
| **XGBoost** | 25% | My ML model — trained on 34,000+ game logs across 3 NBA seasons with 132 engineered features. Captures things DARKO doesn't: hot/cold streaks, back-to-back fatigue, usage × pace interactions. |
| **Season average** | 20% | Simple but stable. A player's season-long average is a good sanity check against the other sources. |
| **Market odds** | 20% | When live sportsbook lines are available, the book's implied probability. Markets are generally efficient, so I respect them. |
 
On top of the probability blend, I apply safety filters that I calibrated from real betting results over several days of tracking:
 
- **Odds ≥ +200 → excluded from parlays** (these hit only 33% in my tracking — the books know something)
- **Last 3 games must clear the line** (every miss I tracked had recent form below the line)
- **Season margin ≥ 3.5 points for PTS locks** (thin margins = too much variance)
- **No role players in locks** (high game-to-game variance)
- **Max 1 pick per game** (correlated risk)
 
## The ML model
 
Following the **CRISP-DM** framework from my ML course:
 
**Business understanding:** Build a binary classifier — does Player X go over Line Y? One model per stat type (PTS, REB, AST) because feature importances are completely different for each.
 
**Data collection:** 3 seasons of game logs scraped from Basketball Reference (34,763 rows, 279 players), plus advanced stats (usage rate, true shooting %, PER, BPM), team defensive ratings, and shooting splits by distance.
 
**Feature engineering:** 132 features per prediction including:
- Rolling averages over 3, 5, and 10 game windows
- Volatility (standard deviation over last 10 games)  
- Trend detection (last 3 avg minus last 10 avg — is the player heating up or cooling down?)
- Opponent defensive stats (points allowed, pace, FG% allowed)
- Interaction terms (usage rate × opponent pace — my professor specifically called this out)
- Context: home/away, back-to-back, days of rest
- Position encoding
 
**Modeling:** XGBoost with L1/L2 regularization for automatic feature selection. Early stopping to prevent overfitting. The professor emphasized tree-based ensembles for tabular data, and he's right — they handle the non-linear interactions naturally.
 
**Validation:** Out-of-time split (train on 2023-25, test on 2025-26). No random splits — the NBA changes year to year due to trades, rule changes, and pace trends, so the model has to prove it works on truly unseen future data.
 
**Results:**
 
| Confidence | PTS Hit Rate | REB Hit Rate | AST Hit Rate |
|-----------|-------------|-------------|-------------|
| P ≥ 55% | 66.3% | 65.9% | 66.8% |
| P ≥ 65% | 70.4% | 70.5% | 71.4% |
| P ≥ 70% | 73.3% | 72.8% | 74.3% |
| P ≥ 75% | 76.2% | 77.2% | 77.1% |
 
The calibration is solid — when the model says 70%, the actual hit rate is ~73%. It's slightly conservative at the top end, which I'd rather have than overconfident.
 
I found that STL and BLK models are basically unreliable (too much randomness in those stats), so the engine only uses PTS, REB, and AST.
 
## Architecture
 
```
Basketball Reference ──→ collect_bbref.py ──→ parlay_ml.db (SQLite)
DARKO website ──────────→ fetch_darko.py ──→ DARKO CSV
Odds API ───────────────→ save_odds_snapshot.py ──→ odds in DB
 
                    ↓ daily
 
train_model.py ──→ models/model_pts.pkl (XGBoost, weekly retrain)
                   models/model_reb.pkl
                   models/model_ast.pkl
 
                    ↓ game day
 
parlay_engine_v5.py
  ├── Loads DARKO projections
  ├── Loads ML models + builds features from DB
  ├── Fetches season stats from NBAstuffer
  ├── Fetches injuries from ESPN
  ├── Fetches live odds from Odds API
  ├── Blends 4 probability sources
  ├── Applies safety filters
  └── Outputs: locks, 3-leg parlay, 5-leg parlay
 
                    ↓
 
Next.js dashboard on Vercel (parlaybudv4/)
```
 
## Daily workflow
 
```bash
# Run everything with one script (~15 min before tip-off)
./run_picks.sh
```
 
Or step by step:
```bash
# 1. Download today's DARKO projections
python3 fetch_darko.py
 
# 2. Update game logs from Basketball Reference
python3 collect_bbref.py --seasons 2025-26 --game-logs
 
# 3. Save today's odds to the database (for future retraining)
python3 save_odds_snapshot.py
 
# 4. Generate picks
python3 parlay_engine_v5.py
```
 
Weekly (Sunday mornings):
```bash
# Retrain models with the latest data
python3 train_model.py --stats PTS REB AST
```
 
## Setup from scratch
 
```bash
# Install Python dependencies
pip install requests beautifulsoup4 pandas xgboost scikit-learn playwright
 
# Install Playwright browser (for DARKO auto-download)
python -m playwright install chromium
 
# Collect 3 seasons of historical data (~35 min)
python3 collect_bbref.py --seasons 2023-24 2024-25 2025-26 --game-logs
 
# Train the models
python3 train_model.py --stats PTS REB AST
 
# You're ready — run picks for tonight
python3 parlay_engine_v5.py
```
 
## What I learned
 
This project taught me more about ML than any assignment:
 
- **"Getting better data is always better than getting better models"** — my professor was right. Adding DARKO as a feature did more for accuracy than any amount of hyperparameter tuning.
- **Out-of-time validation is non-negotiable** for time series data. A random 80/20 split gave me AUC 0.72. The honest out-of-time split gave 0.63. The random split was lying to me.
- **Regularization matters.** 132 features on noisy sports data is a recipe for overfitting. L1 regularization (built into XGBoost) effectively zeroed out ~60% of features.
- **Domain knowledge beats feature count.** The "last 3 game average must clear the line" filter came from watching my picks hit or miss over 4 days of real tracking — not from the model. Sometimes a simple rule outperforms a complex model.
- **Markets are efficient but not perfect.** When the sportsbook offers +200 odds on what looks like an easy over, they almost always know something you don't. Respecting the market saved me from multiple traps.
 
## Disclaimer
 
This is a student project for educational purposes. Sports betting involves risk. Don't bet what you can't afford to lose. The model's 70-76% hit rate sounds good, but parlays are still hard to hit — a 3-leg parlay at 70% per leg only hits 34% of the time.
 
## Acknowledgments
 
- [DARKO](https://apanalytics.shinyapps.io/DARKO/) by Kostya Medvedovsky — the best public NBA projection system
- [Basketball Reference](https://www.basketball-reference.com/) — the gold standard for NBA statistics
- My ML professor for the CRISP-DM framework and the advice to "use XGBoost for tabular data"
- [The Odds API](https://the-odds-api.com/) for free sportsbook data
 
---
 
*Built by Vishal Thamaraimanalan — CS @ Western University*
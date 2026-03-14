# ParlayBud V4 — Claude Code Master Prompt

## Project Overview

Build a full-stack NBA parlay prediction dashboard called **ParlayBud** that displays daily ML-powered player prop picks and parlay suggestions. The system uses XGBoost models trained on 3 seasons of NBA data (34,000+ game logs) to predict player prop outcomes (PTS, REB, AST) with 70-76% hit rates at high confidence thresholds.

**Tech Stack:**
- Frontend: Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- Backend: Next.js API routes (serverless functions)
- Database: SQLite (parlay_ml.db) for player stats, Vercel KV or JSON files for daily picks
- Hosting: Vercel (free tier)
- ML Models: Pre-trained XGBoost models (Python pickle files) — inference runs via a Python API endpoint or pre-computed daily
- Charts: Recharts for visualizations

## Architecture

Since Vercel serverless functions run on Node.js and our ML models are Python/XGBoost, the architecture is:

1. **Daily cron job (local or GitHub Actions):** Run the Python pipeline locally or via GitHub Actions:
   - `collect_bbref.py --seasons 2025-26 --game-logs` (update data)
   - `parlay_engine_v4.py --fetch-odds` (generate picks)
   - Output picks to `picks/YYYY-MM-DD.json`
   - Push JSON to the repo (or upload to Vercel KV / a free JSON hosting service)

2. **Next.js frontend:** Reads the daily picks JSON and renders a beautiful dashboard

3. **Alternative (all-in-one):** Use a free Python hosting service (Railway, Render) for a FastAPI backend that runs the ML inference, and have Next.js call it. But this adds complexity — start with pre-computed JSON.

## Data Flow

```
[Local Machine / GitHub Actions]
  │
  ├── collect_bbref.py → updates parlay_ml.db
  ├── parlay_engine_v4.py → generates picks
  └── outputs picks/2026-03-14.json
        │
        ▼
[Git Push / API Upload]
        │
        ▼
[Vercel Next.js App]
  ├── /                    → Dashboard (today's picks)
  ├── /history             → Past picks + results tracking
  ├── /model               → Model performance metrics
  └── /api/picks/[date]    → JSON API for picks data
```

## Daily Picks JSON Schema

Each day's picks file (`picks/YYYY-MM-DD.json`) should have this structure:

```json
{
  "date": "2026-03-14",
  "generated_at": "2026-03-14T15:30:00Z",
  "model_version": "v4-xgboost",
  "games": [
    {"away": "CLE", "home": "DAL", "label": "CLE @ DAL"}
  ],
  "injuries": [
    {"player": "Luka Doncic", "status": "OUT", "reason": "ankle"}
  ],
  "picks": [
    {
      "player": "Donovan Mitchell",
      "team": "CLE",
      "opponent": "DAL",
      "game": "CLE @ DAL",
      "stat": "PTS",
      "line": 24.5,
      "over_odds": -115,
      "book": "DraftKings",
      "model_prob": 0.726,
      "implied_prob": 0.535,
      "edge": 0.191,
      "ev": 0.356,
      "season_avg": 28.6,
      "last_5_avg": 26.2,
      "last_3_avg": 28.0,
      "is_home": 0,
      "has_live_line": true
    }
  ],
  "locks": ["Donovan Mitchell", "Jaylen Brown"],
  "parlay_3leg": {
    "legs": ["Donovan Mitchell PTS O24.5", "Jaylen Brown PTS O23.5", "Karl-Anthony Towns REB O9.5"],
    "combined_prob": 0.38,
    "players": ["Donovan Mitchell", "Jaylen Brown", "Karl-Anthony Towns"]
  },
  "parlay_5leg": {
    "legs": ["..."],
    "combined_prob": 0.18,
    "players": ["..."]
  },
  "model_stats": {
    "PTS": {"auc": 0.626, "hit_rate_70": 0.733},
    "REB": {"auc": 0.617, "hit_rate_70": 0.728},
    "AST": {"auc": 0.658, "hit_rate_70": 0.743}
  },
  "results": null
}
```

After games finish, update the `results` field:
```json
{
  "results": {
    "picks_total": 15,
    "picks_hit": 11,
    "hit_rate": 0.733,
    "locks_hit": 4,
    "locks_total": 5,
    "parlay_3_hit": true,
    "parlay_5_hit": false,
    "details": [
      {"player": "Donovan Mitchell", "stat": "PTS", "line": 24.5, "actual": 31, "hit": true}
    ]
  }
}
```

## Pages to Build

### 1. Dashboard (`/`) — Main Page
The hero of the app. Shows today's picks at a glance.

**Layout:**
- Top banner: Date, model version, games tonight count
- Stats bar: Overall hit rate, today's pick count, model confidence range
- **Locks section:** 3-6 highest confidence picks displayed as cards with:
  - Player name + team logo/abbr
  - Stat type (PTS/REB/AST) with line
  - Model probability as a circular progress indicator
  - Edge % (green if positive)
  - Season avg, Last 5, Last 3 in a mini sparkline or bar
  - Opponent + home/away indicator
  - Book name and odds (if available)
- **3-Leg Safe Parlay:** Displayed as a connected card group showing the 3 legs with combined probability
- **5-Leg Premium Parlay:** Same format
- **All Picks table:** Sortable/filterable table of all picks with columns: Player, Stat, Line, P(over), Edge, Season Avg, L5, L3, Opponent, Book
- **Injuries sidebar:** Collapsible list of OUT players

**Design:**
- Dark theme (navy/charcoal background, like a sportsbook)
- Accent colors: green for hits/positive edge, red for misses/negative, amber for caution
- Card-based layout with subtle glassmorphism
- Mobile responsive — cards stack vertically on small screens
- Use team colors as subtle accents on pick cards

### 2. History (`/history`) — Past Performance
- Calendar view or date picker to browse past days
- For each past day: picks made, results, hit rate
- Running hit rate chart (Recharts line chart) showing daily hit % over time
- Cumulative profit/loss tracker (assuming flat $10 per bet)
- Best/worst days highlighted
- Filter by stat type (PTS only, REB only, etc.)

### 3. Model Info (`/model`) — Transparency Page
- Training data summary: 34,763 game logs, 279 players, 3 seasons
- Per-stat model metrics: AUC, accuracy, Brier score, log loss
- Feature importance bar chart (top 20 features from XGBoost)
- Calibration chart: predicted probability vs actual hit rate
- Hit rate by confidence threshold table (the P>=55% through P>=75% breakdown)
- Methodology explanation (CRISP-DM, out-of-time validation, etc.)

### 4. API Routes
- `GET /api/picks/today` → redirects to current date
- `GET /api/picks/[date]` → returns picks JSON for a specific date
- `GET /api/history` → returns array of all past dates with summary stats

## Component Library

Use **shadcn/ui** components:
- `Card`, `CardHeader`, `CardContent` for pick cards
- `Table` for the all-picks table
- `Badge` for stat types (PTS = blue, REB = orange, AST = green)
- `Progress` for probability bars
- `Tabs` for filtering
- `Tooltip` for explanations

Custom components to build:
- `PickCard` — displays one pick with all its data
- `ParlayCard` — displays a multi-leg parlay
- `ProbabilityRing` — circular progress showing model probability
- `EdgeBadge` — colored badge showing edge %
- `PlayerStatMini` — compact display of season/L5/L3 averages
- `HitRateChart` — Recharts line chart for history
- `CalibrationChart` — scatter plot of predicted vs actual
- `FeatureImportanceChart` — horizontal bar chart

## Color Scheme

```css
--background: #0f172a;       /* slate-900 */
--card: #1e293b;             /* slate-800 */
--card-hover: #334155;       /* slate-700 */
--primary: #3b82f6;          /* blue-500 */
--accent-green: #22c55e;     /* green-500 — hits, positive edge */
--accent-red: #ef4444;       /* red-500 — misses, negative */
--accent-amber: #f59e0b;     /* amber-500 — caution */
--text: #f8fafc;             /* slate-50 */
--text-muted: #94a3b8;       /* slate-400 */
```

## Stat Type Colors
- PTS: `#3b82f6` (blue)
- REB: `#f97316` (orange)  
- AST: `#22c55e` (green)

## Implementation Notes

1. **Start with static JSON files** in `/public/picks/` directory. This is the simplest MVP — no backend needed, just `fetch('/picks/2026-03-14.json')`.

2. **The Python scripts run locally on your Mac.** After generating picks, copy the JSON to the Next.js project's public folder and push to Vercel. Later, automate this with GitHub Actions.

3. **For the model performance page**, export the training metrics from `models/metrics.json` and include it as a static JSON file.

4. **Mobile-first design.** Most sports bettors check on their phones. The dashboard should look great on mobile with stacked cards.

5. **Don't include actual betting functionality.** This is an analysis/prediction tool only. Include a disclaimer: "For entertainment purposes only. Not financial advice."

6. **Loading states:** Show skeleton loaders while picks are loading. Show "No games today" state when appropriate.

7. **Team logos:** Use ESPN's CDN for team logos: `https://a.espncdn.com/i/teamlogos/nba/500/{team_abbr_lowercase}.png`

## Sample Pick Card Design (for reference)

```
┌─────────────────────────────────────┐
│  🏀 Donovan Mitchell        CLE     │
│  ───────────────────────────────── │
│  PTS Over 24.5              -115   │
│                                     │
│  ┌──────┐  Season: 28.6            │
│  │ 72.6%│  Last 5: 26.2            │
│  │██████│  Last 3: 28.0            │
│  └──────┘                           │
│                                     │
│  Edge: +19.1%    vs DAL (Away)     │
│  Book: DraftKings                   │
└─────────────────────────────────────┘
```

## File Structure

```
parlaybudv4/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              # Dashboard
│   ├── history/
│   │   └── page.tsx          # History page
│   ├── model/
│   │   └── page.tsx          # Model info page
│   └── api/
│       └── picks/
│           └── [date]/
│               └── route.ts  # Picks API
├── components/
│   ├── pick-card.tsx
│   ├── parlay-card.tsx
│   ├── probability-ring.tsx
│   ├── edge-badge.tsx
│   ├── picks-table.tsx
│   ├── hit-rate-chart.tsx
│   ├── injuries-list.tsx
│   └── navbar.tsx
├── lib/
│   ├── types.ts              # TypeScript interfaces matching JSON schema
│   └── utils.ts              # Helper functions
├── public/
│   ├── picks/                # Daily picks JSON files
│   │   ├── 2026-03-13.json
│   │   └── 2026-03-14.json
│   └── metrics.json          # Model training metrics
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

## Getting Started Commands

```bash
npx create-next-app@latest parlaybudv4 --typescript --tailwind --eslint --app --src-dir=false
cd parlaybudv4
npx shadcn-ui@latest init
npx shadcn-ui@latest add card table badge progress tabs tooltip
npm install recharts
npm run dev
```

## Vercel Deployment

```bash
npm install -g vercel
vercel
# Follow prompts — free tier works perfectly for this
```

## Future Enhancements (not for MVP)
- WebSocket for live game score updates
- Push notifications when picks hit
- Integration with Notte odds API for Canadian books
- User accounts to track personal betting history
- Dark/light theme toggle
- Odds comparison across books

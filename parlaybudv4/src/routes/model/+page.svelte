<script lang="ts">
  import type { PageData } from './$types';
  import { getStatColor } from '$lib/utils';
  import BarChart from '$lib/components/BarChart.svelte';

  export let data: PageData;

  $: metrics = data.metrics;

  let activeImportanceTab: 'PTS' | 'REB' | 'AST' = 'PTS';

  const thresholds = ['0.55', '0.60', '0.65', '0.70', '0.75'];

  const statList: ('PTS' | 'REB' | 'AST')[] = ['PTS', 'REB', 'AST'];

  // Calibration SVG constants
  const calibPad = { top: 20, right: 20, bottom: 50, left: 55 };
  const calibCW = 500 - calibPad.left - calibPad.right;
  const calibCH = 280 - calibPad.top - calibPad.bottom;
  const calibTicks = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

  function calibX(prob: number): number {
    return calibPad.left + ((prob - 0.5) / 0.5) * calibCW;
  }
  function calibY(rate: number): number {
    return calibPad.top + calibCH - ((rate - 0.5) / 0.5) * calibCH;
  }
</script>

<svelte:head>
  <title>ParlayBud — Model</title>
</svelte:head>

<div class="page">
  <div class="container">

    <div class="page-title-row">
      <div>
        <h1 class="page-title">Model Intelligence</h1>
        <p class="page-subtitle">XGBoost ensemble trained on 3 seasons of NBA game logs</p>
      </div>
      <div class="model-version-badge">
        <span class="mv-icon">🤖</span>
        <span class="mv-text">v4-xgboost</span>
      </div>
    </div>

    <!-- Training Data Cards -->
    <div class="training-grid">
      <div class="training-card glass">
        <div class="tc-icon">📊</div>
        <div class="tc-val">{metrics.training.total_logs.toLocaleString()}</div>
        <div class="tc-label">Game Logs</div>
        <div class="tc-sub">Training samples</div>
      </div>
      <div class="training-card glass">
        <div class="tc-icon">🏀</div>
        <div class="tc-val">{metrics.training.players}</div>
        <div class="tc-label">Players</div>
        <div class="tc-sub">Tracked athletes</div>
      </div>
      <div class="training-card glass">
        <div class="tc-icon">📅</div>
        <div class="tc-val">{metrics.training.seasons}</div>
        <div class="tc-label">Seasons</div>
        <div class="tc-sub">2022–2025</div>
      </div>
      <div class="training-card glass">
        <div class="tc-icon">🗓️</div>
        <div class="tc-val">2+ yrs</div>
        <div class="tc-label">Data Range</div>
        <div class="tc-sub">{metrics.training.date_range.start} → {metrics.training.date_range.end}</div>
      </div>
    </div>

    <!-- Model Metrics Table -->
    <div class="section-card glass">
      <div class="section-header-bar">
        <h2 class="section-title">
          <span class="section-icon">📈</span>
          Model Performance Metrics
        </h2>
        <div class="metrics-legend">
          <span class="ml-item">
            <span class="ml-dot" style="background: #3b82f6;"></span>
            AUC measures discriminative ability
          </span>
        </div>
      </div>
      <div class="metrics-table-wrap">
        <table class="metrics-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>AUC</th>
              <th>Accuracy</th>
              <th>Brier Score</th>
              <th>Log Loss</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {#each statList as stat}
              {@const m = metrics.models[stat]}
              {@const color = getStatColor(stat)}
              <tr class="metrics-row">
                <td>
                  <span class="stat-pill" style="background: {color}15; color: {color}; border-color: {color}30;">{stat}</span>
                </td>
                <td>
                  <div class="metric-with-bar">
                    <span class="metric-val">{m.auc.toFixed(3)}</span>
                    <div class="metric-bar-track">
                      <div class="metric-bar-fill" style="width: {m.auc * 100}%; background: {color};"></div>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="metric-val highlight" style="color: {color};">{(m.accuracy * 100).toFixed(1)}%</span>
                </td>
                <td>
                  <span class="metric-val">{m.brier_score.toFixed(3)}</span>
                </td>
                <td>
                  <span class="metric-val">{m.log_loss.toFixed(3)}</span>
                </td>
                <td>
                  <span class="status-good">✓ Production</span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Hit Rate by Threshold -->
    <div class="section-card glass">
      <div class="section-header-bar">
        <h2 class="section-title">
          <span class="section-icon">🎯</span>
          Hit Rate by Confidence Threshold
        </h2>
        <div class="threshold-note">Higher threshold = fewer but more accurate picks</div>
      </div>
      <div class="threshold-table-wrap">
        <table class="threshold-table">
          <thead>
            <tr>
              <th>Threshold</th>
              {#each statList as stat}
                <th style="color: {getStatColor(stat)};">{stat}</th>
              {/each}
              <th>Interpretation</th>
            </tr>
          </thead>
          <tbody>
            {#each thresholds as thresh}
              <tr class="thresh-row" class:highlight-row={thresh === '0.70'}>
                <td>
                  <span class="thresh-badge" class:target={thresh === '0.70'}>
                    {(parseFloat(thresh) * 100).toFixed(0)}%+
                    {#if thresh === '0.70'}<span class="target-tag">TARGET</span>{/if}
                  </span>
                </td>
                {#each statList as stat}
                  {@const rate = metrics.models[stat].hit_rates[thresh]}
                  {@const color = getStatColor(stat)}
                  <td>
                    <span class="rate-cell" style="color: {rate >= 0.7 ? '#22c55e' : rate >= 0.65 ? '#f59e0b' : '#94a3b8'};">
                      {(rate * 100).toFixed(1)}%
                    </span>
                  </td>
                {/each}
                <td class="interp-cell">
                  {#if thresh === '0.55'}Baseline filter
                  {:else if thresh === '0.60'}Standard picks
                  {:else if thresh === '0.65'}High confidence
                  {:else if thresh === '0.70'}Locks threshold
                  {:else}Elite only{/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Feature Importance -->
    <div class="section-card glass">
      <div class="section-header-bar">
        <h2 class="section-title">
          <span class="section-icon">🔬</span>
          Feature Importance
        </h2>
        <div class="importance-tabs">
          {#each statList as stat}
            <button
              class="imp-tab"
              class:active={activeImportanceTab === stat}
              on:click={() => activeImportanceTab = stat}
              style={activeImportanceTab === stat ? `color: ${getStatColor(stat)}; border-color: ${getStatColor(stat)}30; background: ${getStatColor(stat)}10;` : ''}
            >{stat}</button>
          {/each}
        </div>
      </div>
      <div class="importance-content">
        <BarChart
          data={metrics.feature_importance[activeImportanceTab]}
          color={getStatColor(activeImportanceTab)}
        />
      </div>
    </div>

    <!-- Calibration -->
    <div class="section-card glass">
      <div class="section-header-bar">
        <h2 class="section-title">
          <span class="section-icon">⚖️</span>
          Model Calibration (PTS)
        </h2>
        <div class="calib-note">Predicted probability vs actual hit rate — closer to diagonal = better calibration</div>
      </div>
      <div class="calibration-wrap">
        <svg viewBox="0 0 500 280" class="calib-svg" preserveAspectRatio="xMidYMid meet">
          <!-- Grid -->
          {#each calibTicks as tick}
            <line x1={calibX(tick)} y1={calibPad.top} x2={calibX(tick)} y2={calibPad.top + calibCH} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
            <line x1={calibPad.left} y1={calibY(tick)} x2={calibPad.left + calibCW} y2={calibY(tick)} stroke="rgba(255,255,255,0.04)" stroke-width="1" />
            <text x={calibX(tick)} y={calibPad.top + calibCH + 18} text-anchor="middle" fill="#475569" font-size="10" font-family="Inter">{(tick * 100).toFixed(0)}%</text>
            <text x={calibPad.left - 8} y={calibY(tick) + 4} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">{(tick * 100).toFixed(0)}%</text>
          {/each}

          <!-- Perfect calibration line -->
          <line
            x1={calibPad.left} y1={calibPad.top + calibCH}
            x2={calibPad.left + calibCW} y2={calibPad.top}
            stroke="rgba(255,255,255,0.2)" stroke-width="1.5" stroke-dasharray="6 4"
          />
          <text x={calibPad.left + calibCW - 2} y={calibPad.top + 14} fill="rgba(255,255,255,0.3)" font-size="10" font-family="Inter" text-anchor="end">Perfect</text>

          <!-- Actual calibration points + lines -->
          {#each metrics.calibration.PTS as pt, i}
            {#if i > 0}
              <line
                x1={calibX(metrics.calibration.PTS[i-1].pred_prob)}
                y1={calibY(metrics.calibration.PTS[i-1].actual_rate)}
                x2={calibX(pt.pred_prob)}
                y2={calibY(pt.actual_rate)}
                stroke="#3b82f6" stroke-width="2"
              />
            {/if}
            <circle
              cx={calibX(pt.pred_prob)}
              cy={calibY(pt.actual_rate)}
              r="5" fill="#3b82f6" stroke="#0f172a" stroke-width="2"
              style="filter: drop-shadow(0 0 4px rgba(59,130,246,0.6));"
            />
          {/each}

          <!-- Axis labels -->
          <text x={calibPad.left + calibCW/2} y={275} text-anchor="middle" fill="#64748b" font-size="11" font-family="Inter">Predicted Probability</text>
          <text x={14} y={calibPad.top + calibCH/2} text-anchor="middle" fill="#64748b" font-size="11" font-family="Inter" transform="rotate(-90, 14, {calibPad.top + calibCH/2})">Actual Hit Rate</text>
        </svg>
      </div>
    </div>

    <!-- Methodology -->
    <div class="methodology-card glass">
      <div class="section-header-bar">
        <h2 class="section-title">
          <span class="section-icon">📋</span>
          Methodology
        </h2>
      </div>
      <div class="methodology-content">
        <div class="meth-grid">
          <div class="meth-item">
            <div class="meth-step">01</div>
            <div class="meth-info">
              <div class="meth-title">Data Collection</div>
              <div class="meth-desc">NBA game logs collected from 2022–2025 across 279 active players. Includes box scores, pace factors, opponent ratings, rest days, and home/away splits.</div>
            </div>
          </div>
          <div class="meth-item">
            <div class="meth-step">02</div>
            <div class="meth-info">
              <div class="meth-title">Feature Engineering</div>
              <div class="meth-desc">Rolling averages (L3, L5, L10, season), matchup difficulty scores, usage rate trends, back-to-back flags, altitude adjustments, and line gap analysis.</div>
            </div>
          </div>
          <div class="meth-item">
            <div class="meth-step">03</div>
            <div class="meth-info">
              <div class="meth-title">XGBoost Training</div>
              <div class="meth-desc">Separate gradient-boosted models for PTS, REB, and AST. Binary classification: will player exceed the sportsbook line? Calibrated with Platt scaling.</div>
            </div>
          </div>
          <div class="meth-item">
            <div class="meth-step">04</div>
            <div class="meth-info">
              <div class="meth-title">Edge Calculation</div>
              <div class="meth-desc">Edge = model probability − implied probability from odds. Only picks with edge &gt; 8% are included. EV calculated using Kelly-inspired formula.</div>
            </div>
          </div>
          <div class="meth-item">
            <div class="meth-step">05</div>
            <div class="meth-info">
              <div class="meth-title">Pick Selection</div>
              <div class="meth-desc">Top picks ranked by EV. Locks = model probability &geq; 70%. Parlays built from highest-probability correlated picks with combined probability displayed.</div>
            </div>
          </div>
          <div class="meth-item">
            <div class="meth-step">06</div>
            <div class="meth-info">
              <div class="meth-title">Continuous Validation</div>
              <div class="meth-desc">Results tracked daily. AUC, Brier score, and hit rates monitored for drift. Model retrained monthly with new data. Out-of-sample validation maintained.</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<style>
.page { padding-top: 2rem; }

.page-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-muted);
}

.model-version-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: var(--radius-sm);
}

.mv-icon { font-size: 1.2rem; }

.mv-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
}

/* Training Cards */
.training-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.training-card {
  padding: 1.25rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: all var(--transition);
}

.training-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.tc-icon { font-size: 1.75rem; margin-bottom: 4px; }

.tc-val {
  font-size: 1.75rem;
  font-weight: 900;
  font-family: 'Orbitron', sans-serif;
  color: var(--primary);
  line-height: 1;
}

.tc-label {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin-top: 2px;
}

.tc-sub {
  font-size: 11px;
  color: var(--text-dim);
}

/* Section Cards */
.section-card {
  margin-bottom: 1.5rem;
  overflow: hidden;
}

.section-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--card-border);
  flex-wrap: wrap;
  gap: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
}

.section-icon { font-size: 1.1rem; }

.metrics-legend, .threshold-note, .calib-note {
  font-size: 11px;
  color: var(--text-dim);
}

.ml-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.ml-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* Metrics Table */
.metrics-table-wrap {
  overflow-x: auto;
  padding: 0 0 0 0;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.metrics-table th {
  padding: 10px 16px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: rgba(0,0,0,0.1);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.metrics-row {
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition);
}

.metrics-row:hover { background: rgba(255,255,255,0.02); }
.metrics-row:last-child { border-bottom: none; }

.metrics-table td {
  padding: 12px 16px;
  vertical-align: middle;
}

.stat-pill {
  display: inline-block;
  font-size: 12px;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid;
  letter-spacing: 0.5px;
}

.metric-with-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric-val {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  min-width: 44px;
}

.metric-val.highlight {
  font-size: 15px;
}

.metric-bar-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.05);
  border-radius: 3px;
  overflow: hidden;
  min-width: 60px;
}

.metric-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
}

.status-good {
  font-size: 11px;
  color: #22c55e;
  background: rgba(34,197,94,0.1);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(34,197,94,0.2);
}

/* Threshold Table */
.threshold-table-wrap { overflow-x: auto; }

.threshold-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.threshold-table th {
  padding: 10px 16px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: rgba(0,0,0,0.1);
  text-align: left;
}

.thresh-row {
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition);
}

.thresh-row:hover { background: rgba(255,255,255,0.02); }
.thresh-row:last-child { border-bottom: none; }

.threshold-table td {
  padding: 11px 16px;
  vertical-align: middle;
}

.thresh-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
}

.thresh-badge.target {
  color: var(--text);
}

.target-tag {
  font-size: 9px;
  background: rgba(245,158,11,0.15);
  color: #f59e0b;
  border: 1px solid rgba(245,158,11,0.25);
  padding: 1px 5px;
  border-radius: 4px;
  letter-spacing: 0.5px;
  font-weight: 800;
}

.highlight-row {
  background: rgba(245,158,11,0.04);
}

.rate-cell {
  font-size: 14px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.interp-cell {
  font-size: 12px;
  color: var(--text-dim);
}

/* Feature Importance */
.importance-tabs {
  display: flex;
  gap: 4px;
}

.imp-tab {
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all var(--transition);
}

.imp-tab:hover { color: var(--text); background: rgba(255,255,255,0.04); }

.imp-tab.active {
  color: var(--primary);
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.25);
}

.importance-content {
  padding: 1.25rem 1.5rem;
}

/* Calibration */
.calibration-wrap {
  padding: 1rem 1.5rem 1.5rem;
}

.calib-svg {
  width: 100%;
  height: auto;
  max-height: 300px;
  display: block;
}

/* Methodology */
.methodology-card {
  margin-bottom: 2rem;
  overflow: hidden;
}

.methodology-content {
  padding: 1.5rem;
}

.meth-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.meth-item {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.meth-step {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  font-weight: 900;
  color: rgba(59,130,246,0.4);
  flex-shrink: 0;
  line-height: 1;
  margin-top: 2px;
}

.meth-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 5px;
}

.meth-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .training-grid { grid-template-columns: repeat(2, 1fr); }
  .meth-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .training-grid { grid-template-columns: repeat(2, 1fr); }
  .section-header-bar { flex-direction: column; align-items: flex-start; }
  .page-title { font-size: 1.4rem; }
}

@media (max-width: 480px) {
  .training-grid { grid-template-columns: 1fr 1fr; }
  .tc-val { font-size: 1.3rem; }
}
</style>

<script lang="ts">
  import type { PageData } from './$types';
  import type { HistorySummary } from '$lib/types';
  import { formatDate, formatDateShort } from '$lib/utils';
  import HitRateChart from '$lib/components/HitRateChart.svelte';

  export let data: PageData;

  $: history = data.history as HistorySummary[];

  // Summary stats
  $: totalPicks = history.reduce((s, d) => s + d.picks_total, 0);
  $: totalHit = history.reduce((s, d) => s + d.picks_hit, 0);
  $: overallHitRate = totalPicks > 0 ? totalHit / totalPicks : 0;
  $: bestDay = history.length > 0 ? history.reduce((best, d) => d.hit_rate > best.hit_rate ? d : best) : null;
  $: worstDay = history.length > 0 ? history.reduce((worst, d) => d.hit_rate < worst.hit_rate ? d : worst) : null;
  $: parlay3Wins = history.filter(d => d.parlay_3_hit).length;
  $: parlay5Wins = history.filter(d => d.parlay_5_hit).length;

  // P&L calculation: $10 per bet, -110 odds => win $9.09, lose $10
  const winAmount = 9.09;
  const loseAmount = 10;

  $: pnl = (() => {
    let running = 0;
    const points: { date: string; cumulative: number; daily: number }[] = [];
    const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));
    for (const day of sorted) {
      const daily = day.picks_hit * winAmount - (day.picks_total - day.picks_hit) * loseAmount;
      running += daily;
      points.push({ date: day.date, cumulative: running, daily });
    }
    return points;
  })();

  $: totalPnL = pnl.length > 0 ? pnl[pnl.length - 1].cumulative : 0;

  // Chart data
  $: chartData = history.map(d => ({ date: d.date, hit_rate: d.hit_rate }));

  // P&L chart (SVG inline)
  const W = 800, H = 160;
  const PAD = { top: 15, right: 20, bottom: 35, left: 60 };
  $: innerW = W - PAD.left - PAD.right;
  $: innerH = H - PAD.top - PAD.bottom;

  $: pnlSorted = [...pnl].sort((a, b) => a.date.localeCompare(b.date));
  $: pnlMin = pnlSorted.length > 0 ? Math.min(0, ...pnlSorted.map(p => p.cumulative)) : -50;
  $: pnlMax = pnlSorted.length > 0 ? Math.max(0, ...pnlSorted.map(p => p.cumulative)) : 50;

  function pnlX(i: number): number {
    if (pnlSorted.length <= 1) return PAD.left + innerW / 2;
    return PAD.left + (i / (pnlSorted.length - 1)) * innerW;
  }

  function pnlY(val: number): number {
    const range = pnlMax - pnlMin || 1;
    return PAD.top + innerH - ((val - pnlMin) / range) * innerH;
  }

  $: pnlPoints = pnlSorted.map((p, i) => ({ x: pnlX(i), y: pnlY(p.cumulative), ...p }));

  $: pnlPath = (() => {
    if (pnlPoints.length === 0) return '';
    let d = `M ${pnlPoints[0].x} ${pnlPoints[0].y}`;
    for (let i = 1; i < pnlPoints.length; i++) {
      const prev = pnlPoints[i - 1];
      const curr = pnlPoints[i];
      const cpx = (prev.x + curr.x) / 2;
      d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
    }
    return d;
  })();

  $: zeroY = pnlY(0);
</script>

<svelte:head>
  <title>ParlayBud — History</title>
</svelte:head>

<div class="page">
  <div class="container">
    <div class="page-title-row">
      <div>
        <h1 class="page-title">Performance History</h1>
        <p class="page-subtitle">Track record across all analyzed games</p>
      </div>
    </div>

    {#if history.length === 0}
      <div class="empty-state glass">
        <div class="empty-icon">📅</div>
        <h2>No Historical Data</h2>
        <p>Results will appear here once picks have been graded.</p>
      </div>
    {:else}
      <!-- Summary Cards -->
      <div class="summary-grid">
        <div class="summary-card glass primary-card">
          <div class="summary-label">Overall Hit Rate</div>
          <div class="summary-big" style="color: {overallHitRate >= 0.7 ? '#22c55e' : overallHitRate >= 0.6 ? '#f59e0b' : '#ef4444'};">
            {(overallHitRate * 100).toFixed(1)}%
          </div>
          <div class="summary-detail">{totalHit} / {totalPicks} picks hit</div>
          <div class="hit-bar">
            <div class="hit-fill" style="width: {overallHitRate * 100}%; background: {overallHitRate >= 0.7 ? '#22c55e' : '#f59e0b'};"></div>
          </div>
        </div>

        <div class="summary-card glass">
          <div class="summary-label">Days Tracked</div>
          <div class="summary-big">{history.length}</div>
          <div class="summary-detail">{totalPicks} total picks analyzed</div>
        </div>

        <div class="summary-card glass">
          <div class="summary-label">Best Day</div>
          {#if bestDay}
            <div class="summary-big" style="color: #22c55e;">{(bestDay.hit_rate * 100).toFixed(0)}%</div>
            <div class="summary-detail">{formatDateShort(bestDay.date)} • {bestDay.picks_hit}/{bestDay.picks_total} picks</div>
          {:else}
            <div class="summary-big">—</div>
          {/if}
        </div>

        <div class="summary-card glass">
          <div class="summary-label">Parlay Record</div>
          <div class="summary-row">
            <div class="parlay-stat">
              <span class="parlay-n">3-Leg</span>
              <span class="parlay-record" style="color: #22c55e;">{parlay3Wins}/{history.length}</span>
            </div>
            <div class="parlay-divider"></div>
            <div class="parlay-stat">
              <span class="parlay-n">5-Leg</span>
              <span class="parlay-record" style="color: #f59e0b;">{parlay5Wins}/{history.length}</span>
            </div>
          </div>
        </div>

        <div class="summary-card glass" class:positive={totalPnL >= 0} class:negative={totalPnL < 0}>
          <div class="summary-label">P&L ($10/pick)</div>
          <div class="summary-big" style="color: {totalPnL >= 0 ? '#22c55e' : '#ef4444'};">
            {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
          </div>
          <div class="summary-detail">Flat betting simulation</div>
        </div>
      </div>

      <!-- Hit Rate Chart -->
      <div class="chart-card glass">
        <div class="chart-card-header">
          <h2 class="chart-title">Daily Hit Rate</h2>
          <div class="chart-legend">
            <span class="legend-item">
              <span class="legend-dot" style="background: #f59e0b;"></span>
              70% target
            </span>
            <span class="legend-item">
              <span class="legend-dot" style="background: #3b82f6;"></span>
              Actual rate
            </span>
          </div>
        </div>
        <HitRateChart data={chartData} />
      </div>

      <!-- P&L Chart -->
      <div class="chart-card glass">
        <div class="chart-card-header">
          <h2 class="chart-title">Cumulative P&L</h2>
          <span class="pnl-total" style="color: {totalPnL >= 0 ? '#22c55e' : '#ef4444'};">
            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
          </span>
        </div>
        <div class="pnl-chart-wrap">
          <svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" class="pnl-svg">
            <defs>
              <linearGradient id="pnlGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color={totalPnL >= 0 ? '#22c55e' : '#ef4444'} stop-opacity="0.2" />
                <stop offset="100%" stop-color={totalPnL >= 0 ? '#22c55e' : '#ef4444'} stop-opacity="0" />
              </linearGradient>
            </defs>

            <!-- Zero line -->
            <line x1={PAD.left} y1={zeroY} x2={PAD.left + innerW} y2={zeroY}
              stroke="rgba(255,255,255,0.2)" stroke-width="1" stroke-dasharray="4 4" />
            <text x={PAD.left - 6} y={zeroY + 4} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">$0</text>

            <!-- Y labels -->
            <text x={PAD.left - 6} y={PAD.top + 10} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">${pnlMax.toFixed(0)}</text>
            {#if pnlMin < 0}
              <text x={PAD.left - 6} y={PAD.top + innerH} text-anchor="end" fill="#475569" font-size="10" font-family="Inter">-${Math.abs(pnlMin).toFixed(0)}</text>
            {/if}

            <!-- Area -->
            {#if pnlPoints.length > 1}
              <path
                d="{pnlPath} L {pnlPoints[pnlPoints.length-1].x} {zeroY} L {pnlPoints[0].x} {zeroY} Z"
                fill="url(#pnlGrad)"
              />
              <path d={pnlPath} fill="none" stroke={totalPnL >= 0 ? '#22c55e' : '#ef4444'} stroke-width="2.5" stroke-linecap="round" />
            {/if}

            <!-- Points -->
            {#each pnlPoints as pt}
              <circle cx={pt.x} cy={pt.y} r="4" fill={pt.cumulative >= 0 ? '#22c55e' : '#ef4444'} stroke="#0f172a" stroke-width="2" />
            {/each}

            <!-- X labels -->
            {#each pnlPoints as pt, i}
              {#if i === 0 || i === pnlPoints.length - 1}
                <text x={pt.x} y={PAD.top + innerH + 20} text-anchor="middle" fill="#475569" font-size="10" font-family="Inter">
                  {formatDateShort(pt.date)}
                </text>
              {/if}
            {/each}
          </svg>
        </div>
      </div>

      <!-- History Table -->
      <div class="history-table-wrap glass">
        <div class="history-table-header">
          <h2 class="chart-title">Day-by-Day Results</h2>
        </div>
        <div class="table-scroll">
          <table class="history-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Picks</th>
                <th>Hit</th>
                <th>Hit Rate</th>
                <th>3-Leg</th>
                <th>5-Leg</th>
                <th>Daily P&L</th>
              </tr>
            </thead>
            <tbody>
              {#each history as day, i}
                {@const dailyPnl = pnl.find(p => p.date === day.date)}
                <tr class="h-row" style="animation-delay: {i * 40}ms;">
                  <td class="date-cell">{formatDateShort(day.date)}</td>
                  <td class="numeric-cell">{day.picks_total}</td>
                  <td class="numeric-cell">{day.picks_hit}</td>
                  <td class="numeric-cell">
                    <span class="rate-badge" style="color: {day.hit_rate >= 0.7 ? '#22c55e' : day.hit_rate >= 0.6 ? '#f59e0b' : '#ef4444'}; background: {day.hit_rate >= 0.7 ? 'rgba(34,197,94,0.12)' : day.hit_rate >= 0.6 ? 'rgba(245,158,11,0.12)' : 'rgba(239,68,68,0.12)'};">
                      {(day.hit_rate * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td class="center-cell">
                    <span class="result-icon">{day.parlay_3_hit ? '✅' : '❌'}</span>
                  </td>
                  <td class="center-cell">
                    <span class="result-icon">{day.parlay_5_hit ? '✅' : '❌'}</span>
                  </td>
                  <td class="numeric-cell">
                    {#if dailyPnl}
                      <span style="color: {dailyPnl.daily >= 0 ? '#22c55e' : '#ef4444'}; font-weight: 700;">
                        {dailyPnl.daily >= 0 ? '+' : ''}${dailyPnl.daily.toFixed(2)}
                      </span>
                    {:else}
                      —
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
.page { padding-top: 2rem; }

.page-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.5rem;
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

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  margin-top: 1rem;
}

.empty-icon { font-size: 3rem; margin-bottom: 1rem; display: block; }

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-card {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

.summary-big {
  font-size: 2rem;
  font-weight: 900;
  font-family: 'Orbitron', sans-serif;
  color: var(--text);
  line-height: 1.1;
}

.summary-detail {
  font-size: 11px;
  color: var(--text-muted);
}

.hit-bar {
  height: 4px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  margin-top: 8px;
  overflow: hidden;
}

.hit-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}

.summary-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.parlay-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.parlay-n {
  font-size: 9px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.parlay-record {
  font-size: 1.3rem;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
}

.parlay-divider {
  width: 1px;
  height: 32px;
  background: rgba(255,255,255,0.08);
}

/* Charts */
.chart-card {
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  overflow: hidden;
}

.chart-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.chart-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text);
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text-muted);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.pnl-total {
  font-size: 1.1rem;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
}

.pnl-chart-wrap {
  width: 100%;
}

.pnl-svg {
  width: 100%;
  height: auto;
  display: block;
}

/* History Table */
.history-table-wrap {
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.history-table-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--card-border);
}

.table-scroll { overflow-x: auto; }

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.history-table thead tr {
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.history-table th {
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-align: left;
  background: rgba(0,0,0,0.15);
}

.h-row {
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition);
  animation: fadeIn 0.3s ease forwards;
}

.h-row:hover { background: rgba(255,255,255,0.02); }
.h-row:last-child { border-bottom: none; }

.history-table td {
  padding: 10px 14px;
  vertical-align: middle;
}

.date-cell { font-weight: 600; color: var(--text); }
.numeric-cell { text-align: right; font-variant-numeric: tabular-nums; color: var(--text-muted); }
.center-cell { text-align: center; }

.rate-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 12px;
}

.result-icon { font-size: 14px; }

@media (max-width: 1100px) {
  .summary-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 768px) {
  .summary-grid { grid-template-columns: repeat(2, 1fr); }
  .page-title { font-size: 1.4rem; }
}

@media (max-width: 480px) {
  .summary-grid { grid-template-columns: 1fr 1fr; }
  .summary-big { font-size: 1.5rem; }
}
</style>

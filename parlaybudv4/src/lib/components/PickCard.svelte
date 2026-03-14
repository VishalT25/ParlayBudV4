<script lang="ts">
  import type { Pick } from '$lib/types';
  import { getTeamLogoUrl, getTeamColor, getStatColor, formatOdds } from '$lib/utils';
  import ProbabilityRing from './ProbabilityRing.svelte';
  import EdgeBadge from './EdgeBadge.svelte';

  export let pick: Pick;
  export let isLock: boolean = false;
  export let history: { attempts: number; hits: number; recent: boolean[] } | undefined = undefined;

  $: hitRate = history && history.attempts > 0 ? history.hits / history.attempts : null;
  $: teamColor = getTeamColor(pick.team);
  $: statColor = getStatColor(pick.stat);
  $: logoUrl = getTeamLogoUrl(pick.team);

  // Mini bar chart calculations
  $: maxVal = Math.max(pick.season_avg, pick.last_5_avg, pick.last_3_avg, pick.line) * 1.15;
  $: bars = [
    { label: 'Szn', value: pick.season_avg, color: '#94a3b8' },
    { label: 'L5', value: pick.last_5_avg, color: '#60a5fa' },
    { label: 'L3', value: pick.last_3_avg, color: '#34d399' }
  ];
</script>

<div class="pick-card glass" class:is-lock={isLock} style="border-left-color: {teamColor};">
  {#if isLock}
    <div class="lock-ribbon">🔒 LOCK</div>
  {/if}

  {#if pick.has_live_line}
    <div class="live-badge">
      <span class="live-dot"></span>
      LIVE
    </div>
  {/if}

  <div class="card-header">
    <div class="player-info">
      <div class="team-logo-wrap" style="background: {teamColor}20; border-color: {teamColor}40;">
        <img
          src={logoUrl}
          alt={pick.team}
          class="team-logo"
          on:error={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
        />
      </div>
      <div class="player-details">
        <h3 class="player-name">{pick.player}</h3>
        <div class="meta-row">
          <span class="team-badge" style="background: {teamColor}25; color: {teamColor}; border-color: {teamColor}40;">{pick.team}</span>
          <span class="vs-text">vs {pick.opponent}</span>
          <span class="location">{pick.is_home ? '🏠 Home' : '✈️ Away'}</span>
        </div>
      </div>
    </div>
    <div class="prob-section">
      <ProbabilityRing prob={pick.model_prob} size={88} />
    </div>
  </div>

  <div class="card-body">
    <div class="bet-line">
      <div class="stat-info">
        <span class="stat-badge-styled" style="background: {statColor}20; color: {statColor}; border-color: {statColor}40;">
          {pick.stat}
        </span>
        <span class="line-value">O {pick.line}</span>
        <span class="odds-value">{formatOdds(pick.over_odds)}</span>
      </div>
      <div class="book-info">
        <span class="book-label">{pick.book}</span>
      </div>
    </div>

    <!-- Mini bar chart -->
    <div class="mini-chart">
      <div class="chart-bars">
        {#each bars as bar}
          <div class="bar-item">
            <div class="bar-track">
              <div
                class="bar-fill"
                style="width: {(bar.value / maxVal) * 100}%; background: {bar.color};"
              ></div>
              <!-- Line indicator -->
              <div
                class="line-marker"
                style="left: {(pick.line / maxVal) * 100}%;"
              ></div>
            </div>
            <div class="bar-label-row">
              <span class="bar-label">{bar.label}</span>
              <span class="bar-value" style="color: {bar.color};">{bar.value.toFixed(1)}</span>
            </div>
          </div>
        {/each}
      </div>
      <div class="line-legend">
        <span class="line-dash"></span>
        <span class="line-text">Line: {pick.line}</span>
      </div>
    </div>

    <div class="card-footer">
      <EdgeBadge edge={pick.edge} />
      <div class="ev-value">
        EV: <span style="color: #22c55e;">+{(pick.ev * 100).toFixed(1)}%</span>
      </div>
    </div>

    {#if history && history.attempts > 0}
      <div class="past-record">
        <div class="past-header">
          <span class="past-label">Past {history.attempts}</span>
          <span
            class="past-rate"
            style="color: {hitRate !== null && hitRate >= 0.7 ? '#22c55e' : hitRate !== null && hitRate >= 0.55 ? '#f59e0b' : '#ef4444'};"
          >
            {history.hits}/{history.attempts}
            <span class="past-pct">({hitRate !== null ? (hitRate * 100).toFixed(0) : 0}%)</span>
          </span>
        </div>
        <div class="dot-row">
          {#each history.recent as hit}
            <span class="result-dot" class:dot-hit={hit} class:dot-miss={!hit}></span>
          {/each}
          {#if history.attempts === 0}
            <span class="no-history">No previous data</span>
          {/if}
        </div>
      </div>
    {:else if history !== undefined}
      <div class="past-record past-record--empty">
        <span class="past-label">No previous data for this prop</span>
      </div>
    {/if}
  </div>
</div>

<style>
.pick-card {
  position: relative;
  border-left: 3px solid var(--primary);
  padding: 1rem 1.25rem;
  transition: all var(--transition);
  overflow: hidden;
  animation: fadeIn 0.4s ease forwards;
}

.pick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.08);
  background: rgba(37, 51, 73, 0.9);
}

.pick-card.is-lock {
  box-shadow: 0 0 30px rgba(245,158,11,0.1);
}

.lock-ribbon {
  position: absolute;
  top: 10px;
  right: -22px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #000;
  font-size: 9px;
  font-weight: 900;
  padding: 3px 28px;
  transform: rotate(35deg);
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(245,158,11,0.4);
}

.live-badge {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  color: #ef4444;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 1px;
  padding: 2px 8px;
  border-radius: 12px;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
  animation: live-blink 1.2s infinite;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 8px;
}

.player-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.team-logo-wrap {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  border: 1px solid;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.team-logo {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.player-details {
  min-width: 0;
}

.player-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
  margin-bottom: 5px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.team-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid;
  letter-spacing: 0.3px;
}

.vs-text {
  font-size: 11px;
  color: var(--text-muted);
}

.location {
  font-size: 10px;
  color: var(--text-dim);
}

.prob-section {
  flex-shrink: 0;
}

.card-body {
  margin-top: 14px;
}

.bet-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.stat-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-badge-styled {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border: 1px solid;
}

.line-value {
  font-size: 20px;
  font-weight: 800;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.odds-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.book-info {
  display: flex;
  align-items: center;
}

.book-label {
  font-size: 11px;
  color: var(--text-dim);
  background: rgba(255,255,255,0.05);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.06);
}

/* Mini bar chart */
.mini-chart {
  background: rgba(0,0,0,0.2);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.04);
}

.chart-bars {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bar-track {
  position: relative;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: visible;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
}

.line-marker {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 12px;
  background: rgba(255,255,255,0.5);
  border-radius: 1px;
  transform: translateX(-1px);
}

.bar-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--text-dim);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.bar-value {
  font-size: 10px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.line-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}

.line-dash {
  width: 12px;
  height: 2px;
  background: rgba(255,255,255,0.5);
  border-radius: 1px;
}

.line-text {
  font-size: 9px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ev-value {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}

/* Past record strip */
.past-record {
  margin-top: 10px;
  padding: 8px 10px;
  background: rgba(0,0,0,0.25);
  border-radius: 7px;
  border: 1px solid rgba(255,255,255,0.05);
}

.past-record--empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.past-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.past-label {
  font-size: 9px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.past-rate {
  font-size: 11px;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.past-pct {
  font-size: 9px;
  font-weight: 600;
  opacity: 0.8;
}

.dot-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  align-items: center;
}

.result-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-hit {
  background: var(--accent-green);
  box-shadow: 0 0 4px rgba(34,197,94,0.5);
}

.dot-miss {
  background: var(--accent-red);
  box-shadow: 0 0 4px rgba(239,68,68,0.3);
}

.no-history {
  font-size: 10px;
  color: var(--text-dim);
}

@keyframes live-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>

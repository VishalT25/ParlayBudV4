<script lang="ts">
  import type { Pick, LivePickStatus } from '$lib/types';
  import { getTeamLogoUrl, getTeamColor, getStatColor, formatOdds, getBookStyle } from '$lib/utils';
  import ProbabilityRing from './ProbabilityRing.svelte';
  import EdgeBadge from './EdgeBadge.svelte';

  export let pick: Pick;
  export let isLock: boolean = false;
  export let history: { attempts: number; hits: number; recent: boolean[] } | undefined = undefined;
  export let liveStatus: LivePickStatus | null = null;

  function fmtTipoff(iso?: string): string {
    if (!iso) return 'Upcoming';
    return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZoneName: 'short' });
  }

  $: isHit  = liveStatus?.gameStatus === 'final' && (liveStatus.value ?? 0) >= pick.line;
  $: isMiss = liveStatus?.gameStatus === 'final' && (liveStatus.value ?? 0) <  pick.line;

  $: hitRate = history && history.attempts > 0 ? history.hits / history.attempts : null;
  $: teamColor = getTeamColor(pick.team);
  $: statColor = getStatColor(pick.stat);
  $: logoUrl = getTeamLogoUrl(pick.team);
  $: bookStyle = getBookStyle(pick.book);

  let logoFailed = false;
  $: { logoUrl; logoFailed = false; }

  const WARNING_CONFIG: Record<string, { label: string; color: string; tooltip: string }> = {
    'ODDS_TRAP':     { label: '⚠️ +200 Trap',      color: '#ef4444', tooltip: 'Odds ≥ +200 historically hit only 33%' },
    'L3_BELOW_LINE': { label: '⚠️ Cold',            color: '#f59e0b', tooltip: 'Last 3 game avg is below the line' },
    'L5_BELOW_LINE': { label: '📉 Trending Down',   color: '#f59e0b', tooltip: 'Last 5 game avg is below the line' },
    'UNUSUAL_LINE':  { label: '🔍 Verify Line',     color: '#a855f7', tooltip: 'Line seems unusually low — may be a live bet' },
  };

  // Mini bar chart calculations
  $: maxVal = Math.max(pick.season_avg, pick.last_5_avg, pick.last_3_avg, pick.line) * 1.15;
  $: bars = [
    { label: 'Szn', value: pick.season_avg, color: '#94a3b8' },
    { label: 'L5', value: pick.last_5_avg, color: '#60a5fa' },
    { label: 'L3', value: pick.last_3_avg, color: '#34d399' }
  ];
</script>

<div class="pick-card glass" class:is-lock={isLock} style="border-left-color: {teamColor};">
  <div class="card-header">
    <div class="player-info">
      <div class="team-logo-wrap" style="background: {teamColor}20; border-color: {teamColor}40;">
        {#if logoUrl && !logoFailed}
          <img
            src={logoUrl}
            alt={pick.team}
            class="team-logo"
            on:error={() => { logoFailed = true; }}
          />
        {:else}
          <span class="team-abbr" style="color: {teamColor};">{pick.team}</span>
        {/if}
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
        <span class="book-label" style="background: {bookStyle.bg}; color: {bookStyle.color}; border-color: {bookStyle.border};">{pick.book}</span>
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

    {#if pick.warnings && pick.warnings.length > 0}
      <div class="warnings-row">
        {#each pick.warnings as w}
          {#if WARNING_CONFIG[w]}
            <span class="warn-badge" style="color: {WARNING_CONFIG[w].color}; background: {WARNING_CONFIG[w].color}18; border-color: {WARNING_CONFIG[w].color}35;" title={WARNING_CONFIG[w].tooltip}>
              {WARNING_CONFIG[w].label}
            </span>
          {/if}
        {/each}
      </div>
    {/if}
    {#if isLock && pick.passes_lock_filter && (!pick.warnings || pick.warnings.length === 0)}
      <div class="verified-row">
        <span class="verified-badge">✅ ML {(pick.model_prob * 100).toFixed(0)}%+</span>
        <span class="verified-badge">✅ Odds OK</span>
        <span class="verified-badge">✅ Recent Form</span>
        <span class="verified-badge">✅ Season Margin</span>
      </div>
    {/if}

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

    {#if liveStatus}
      <div
        class="live-strip"
        class:live-strip--pre={liveStatus.gameStatus === 'pre'}
        class:live-strip--live={liveStatus.gameStatus === 'live'}
        class:live-strip--hit={isHit}
        class:live-strip--miss={isMiss}
      >
        {#if liveStatus.gameStatus === 'pre'}
          <span class="ls-icon">🕐</span>
          <span class="ls-main">Tipoff {fmtTipoff(liveStatus.gameTime)}</span>
        {:else if liveStatus.gameStatus === 'live'}
          <div class="ls-live-dot"></div>
          <span class="ls-main">
            <strong>{liveStatus.value} {pick.stat}</strong>
            <span class="ls-need">/ need {pick.line}</span>
          </span>
          <span class="ls-score">
            {liveStatus.awayTeam} {liveStatus.awayScore} – {liveStatus.homeTeam} {liveStatus.homeScore}
            <span class="ls-period">Q{liveStatus.period} {liveStatus.clock}</span>
          </span>
        {:else}
          <span class="ls-result-icon">{isHit ? '✓' : '✗'}</span>
          <span class="ls-main">
            <strong>{isHit ? 'Hit' : 'Miss'}</strong>
            — {liveStatus.value} {pick.stat}
          </span>
          <span class="ls-final">FINAL</span>
        {/if}
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


.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
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

.team-abbr {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.5px;
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

/* Live status strip */
.live-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 7px 10px;
  border-radius: 7px;
  font-size: 11px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  flex-wrap: wrap;
}

.live-strip--pre {
  color: var(--text-dim);
}

.live-strip--live {
  background: rgba(239,68,68,0.08);
  border-color: rgba(239,68,68,0.25);
  color: var(--text-muted);
}

.live-strip--hit {
  background: rgba(34,197,94,0.1);
  border-color: rgba(34,197,94,0.3);
  color: #22c55e;
}

.live-strip--miss {
  background: rgba(239,68,68,0.1);
  border-color: rgba(239,68,68,0.3);
  color: #ef4444;
}

.ls-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ef4444;
  flex-shrink: 0;
  animation: ls-blink 1.2s infinite;
}

@keyframes ls-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.ls-icon { font-size: 11px; }

.ls-main {
  flex: 1;
  font-weight: 600;
}

.ls-need {
  font-weight: 400;
  color: var(--text-dim);
  margin-left: 2px;
}

.ls-score {
  font-size: 10px;
  color: var(--text-dim);
  white-space: nowrap;
}

.ls-period {
  margin-left: 5px;
  color: #ef4444;
  font-weight: 600;
}

.ls-result-icon {
  font-size: 13px;
  font-weight: 900;
  flex-shrink: 0;
}

.ls-final {
  margin-left: auto;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.8px;
  opacity: 0.5;
}

.warnings-row {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.warn-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 5px;
  border: 1px solid;
  cursor: default;
}
.verified-row {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.verified-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(34,197,94,0.1);
  color: #22c55e;
  border: 1px solid rgba(34,197,94,0.25);
}

</style>

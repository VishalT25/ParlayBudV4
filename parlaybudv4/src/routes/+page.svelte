<script lang="ts">
  import { onDestroy } from 'svelte';
  import type { PageData } from './$types';
  import type { Pick, LivePickStatus } from '$lib/types';
  import { formatDate } from '$lib/utils';
  import PickCard from '$lib/components/PickCard.svelte';
  import ParlayCard from '$lib/components/ParlayCard.svelte';
  import InjuriesList from '$lib/components/InjuriesList.svelte';
  import PicksTable from '$lib/components/PicksTable.svelte';
  import DateNav from '$lib/components/DateNav.svelte';

  export let data: PageData;

  $: picks = data.picks;
  $: isDemo = data.isDemo ?? false;
  $: legHistory = data.legHistory ?? {};

  function getHistory(player: string, stat: string) {
    return legHistory[`${player}|${stat}`];
  }

  // ── Live status polling ────────────────────────────────────────────────────
  let liveData: Record<string, unknown> = {};
  let liveInterval: ReturnType<typeof setInterval> | null = null;
  let prevPollDate = '';

  async function fetchLive() {
    try {
      const res = await fetch(`/api/live?date=${data.date}`);
      if (res.ok) liveData = await res.json();
    } catch { /* silent fail */ }
  }

  function stopPolling() {
    if (liveInterval) { clearInterval(liveInterval); liveInterval = null; }
    liveData = {};
  }

  // Re-evaluate whenever data.date or data.today changes
  $: if (data.date !== prevPollDate) {
    stopPolling();
    prevPollDate = data.date;
    if (data.date === data.today) {
      fetchLive();
      liveInterval = setInterval(fetchLive, 60_000);
    }
  }

  onDestroy(stopPolling);

  function getPickLiveStatus(pick: Pick): LivePickStatus | null {
    const raw = liveData[pick.player.toLowerCase()] as Record<string, unknown> | undefined;
    if (raw) {
      const statKey = pick.stat.toLowerCase() as 'pts' | 'reb' | 'ast';
      return {
        value: (raw[statKey] as number) ?? 0,
        gameStatus: raw.gameStatus as 'pre' | 'live' | 'final',
        period:    raw.period    as number | undefined,
        clock:     raw.clock     as string | undefined,
        homeTeam:  raw.homeTeam  as string | undefined,
        awayTeam:  raw.awayTeam  as string | undefined,
        homeScore: raw.homeScore as number | undefined,
        awayScore: raw.awayScore as number | undefined,
      };
    }
    // Pre-game fallback — keyed by team abbr
    const pre = liveData[`__pre_${pick.team}`] as Record<string, unknown> | undefined;
    if (pre) {
      return {
        value: 0,
        gameStatus: 'pre',
        gameTime:  pre.gameTime  as string | undefined,
        homeTeam:  pre.homeTeam  as string | undefined,
        awayTeam:  pre.awayTeam  as string | undefined,
      };
    }
    return null;
  }

  $: lockPicks = picks
    ? picks.picks.filter((p: Pick) => picks!.locks.includes(p.player))
    : [];

  $: otherPicks = picks
    ? picks.picks.filter((p: Pick) => !picks!.locks.includes(p.player))
    : [];

  $: avgProb = picks
    ? picks.picks.reduce((s: number, p: Pick) => s + p.model_prob, 0) / picks.picks.length
    : 0;

  $: minProb = picks ? Math.min(...picks.picks.map((p: Pick) => p.model_prob)) : 0;
  $: maxProb = picks ? Math.max(...picks.picks.map((p: Pick) => p.model_prob)) : 0;
</script>

<svelte:head>
  <title>ParlayBud — Dashboard</title>
</svelte:head>

<div class="page">
  <div class="container">

    <!-- Date Navigation (always shown) -->
    <DateNav
      date={data.date}
      today={data.today}
      prevDate={data.prevDate}
      nextDate={data.nextDate}
      availableDates={data.availableDates}
    />

    {#if !picks}
      <!-- Empty State -->
      <div class="empty-state glass">
        <div class="empty-icon">🏀</div>
        <h2 class="empty-title">No Picks Available</h2>
        <p class="empty-desc">{data.date === data.today ? "Today's" : 'No'} ML model picks {data.date === data.today ? "haven't been generated yet. Check back after 2 PM EST when game lines are posted." : `available for ${data.date}.`}</p>
        <div class="empty-hint">Looking for: <code>/picks/{data.date}.json</code></div>
      </div>
    {:else}
      <!-- Demo Banner -->
      {#if isDemo}
        <div class="demo-banner">
          <span class="demo-icon">⚡</span>
          <span>Showing demo data for <strong>{picks.date}</strong> — No picks found for today</span>
        </div>
      {/if}

      <!-- Header Banner -->
      <div class="page-header glass">
        <div class="header-main">
          <div class="header-date-section">
            <div class="header-badge">
              <span class="header-badge-dot"></span>
              ML PREDICTIONS
            </div>
            <h1 class="header-date">{formatDate(picks.date)}</h1>
            <div class="header-meta">
              <span class="meta-chip">
                <span class="meta-icon">🤖</span>
                {picks.model_version}
              </span>
              <span class="meta-chip">
                <span class="meta-icon">🕐</span>
                Generated {new Date(picks.generated_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
          <div class="header-games">
            <div class="games-label">Games Tonight</div>
            <div class="games-list">
              {#each picks.games as game}
                <div class="game-chip">
                  <span class="game-away">{game.away}</span>
                  <span class="game-at">@</span>
                  <span class="game-home">{game.home}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-card glass">
          <div class="stat-label">Today's Picks</div>
          <div class="stat-value">{picks.picks.length}</div>
          <div class="stat-sub">total selections</div>
        </div>
        <div class="stat-card glass">
          <div class="stat-label">Avg Confidence</div>
          <div class="stat-value" style="color: #22c55e;">{(avgProb * 100).toFixed(1)}%</div>
          <div class="stat-sub">model probability</div>
        </div>
        <div class="stat-card glass">
          <div class="stat-label">Confidence Range</div>
          <div class="stat-value" style="font-size: 1.2rem;">{(minProb * 100).toFixed(1)}–{(maxProb * 100).toFixed(1)}%</div>
          <div class="stat-sub">min to max</div>
        </div>
        <div class="stat-card glass">
          <div class="stat-label">Locks Today</div>
          <div class="stat-value" style="color: #f59e0b;">🔒 {picks.locks.length}</div>
          <div class="stat-sub">high confidence</div>
        </div>
        <div class="stat-card glass">
          <div class="stat-label">Model AUC</div>
          <div class="stat-value" style="color: #3b82f6;">{picks.model_stats.PTS.auc.toFixed(3)}</div>
          <div class="stat-sub">PTS model</div>
        </div>
      </div>

      <!-- Two-column layout -->
      <div class="two-col-layout">
        <!-- Left Column -->
        <div class="left-col">

          <!-- Locks Section -->
          <section class="locks-section">
            <div class="section-header locks-header">
              <div class="section-title-group">
                <span class="section-icon locks-icon">🔒</span>
                <h2 class="section-title">Today's Locks</h2>
                <span class="lock-count-badge">{lockPicks.length}</span>
              </div>
              <div class="locks-subtitle">Highest conviction picks</div>
            </div>
            <div class="locks-grid">
              {#each lockPicks as pick}
                <PickCard {pick} isLock={true} history={getHistory(pick.player, pick.stat)} liveStatus={getPickLiveStatus(pick)} />
              {/each}
            </div>
          </section>

          <!-- Parlays Section -->
          <section class="parlays-section">
            <div class="section-header">
              <div class="section-title-group">
                <span class="section-icon">🎯</span>
                <h2 class="section-title">Today's Parlays</h2>
              </div>
            </div>
            <div class="parlays-grid">
              <ParlayCard parlay={picks.parlay_3leg} type="3-Leg Safe" picks={picks.picks} />
              <ParlayCard parlay={picks.parlay_5leg} type="5-Leg Premium" picks={picks.picks} />
            </div>
          </section>

          <!-- All Picks Table -->
          <section class="all-picks-section">
            <div class="section-header">
              <div class="section-title-group">
                <span class="section-icon">📊</span>
                <h2 class="section-title">All Picks</h2>
              </div>
            </div>
            <PicksTable picks={picks.picks} />
          </section>

          <!-- Other Picks -->
          {#if otherPicks.length > 0}
            <section class="other-picks-section">
              <div class="section-header">
                <div class="section-title-group">
                  <span class="section-icon">🎲</span>
                  <h2 class="section-title">Additional Picks</h2>
                  <span class="count-badge">{otherPicks.length}</span>
                </div>
              </div>
              <div class="other-picks-grid">
                {#each otherPicks as pick}
                  <PickCard {pick} isLock={false} history={getHistory(pick.player, pick.stat)} liveStatus={getPickLiveStatus(pick)} />
                {/each}
              </div>
            </section>
          {/if}

        </div>

        <!-- Right Column -->
        <div class="right-col">

          <!-- Games Tonight -->
          <div class="sidebar-widget glass">
            <div class="widget-header">
              <span class="widget-icon">🏟️</span>
              <span class="widget-title">Games Tonight</span>
            </div>
            <div class="games-widget-list">
              {#each picks.games as game}
                <div class="game-row">
                  <div class="game-teams">
                    <span class="game-team away">{game.away}</span>
                    <span class="game-separator">@</span>
                    <span class="game-team home">{game.home}</span>
                  </div>
                  <span class="game-picks-count">
                    {picks.picks.filter((p: Pick) => p.game === game.label).length} picks
                  </span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Model Performance Snapshot -->
          <div class="sidebar-widget glass">
            <div class="widget-header">
              <span class="widget-icon">🧠</span>
              <span class="widget-title">Model Stats</span>
            </div>
            <div class="model-stats-grid">
              {#each Object.entries(picks.model_stats) as [stat, stats]}
                <div class="model-stat-row">
                  <span class="model-stat-label stat-{stat.toLowerCase()}">{stat}</span>
                  <div class="model-stat-values">
                    <div class="model-kv">
                      <span class="model-k">AUC</span>
                      <span class="model-v">{stats.auc.toFixed(3)}</span>
                    </div>
                    <div class="model-kv">
                      <span class="model-k">Hit@70</span>
                      <span class="model-v" style="color: #22c55e;">{(stats.hit_rate_70 * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <!-- Injuries -->
          <InjuriesList injuries={picks.injuries} />

        </div>
      </div>
    {/if}
  </div>
</div>

<style>
.page {
  padding-top: 2rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  margin-top: 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.5rem;
}

.empty-desc {
  color: var(--text-muted);
  font-size: 14px;
  max-width: 400px;
  margin: 0 auto 1rem;
  line-height: 1.6;
}

.empty-hint {
  font-size: 12px;
  color: var(--text-dim);
}

.empty-hint code {
  background: rgba(255,255,255,0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

/* Demo Banner */
.demo-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(245,158,11,0.1);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: var(--radius-sm);
  color: var(--accent-amber);
  font-size: 13px;
  margin-bottom: 1.5rem;
}

.demo-icon { font-size: 1rem; }

/* Header */
.page-header {
  padding: 1.5rem 2rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, rgba(30,41,59,0.9) 0%, rgba(15,23,42,0.9) 100%);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary), var(--accent-green), var(--primary));
}

.header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2rem;
  flex-wrap: wrap;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.25);
  color: var(--primary);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 1.5px;
  padding: 4px 10px;
  border-radius: 20px;
  margin-bottom: 8px;
}

.header-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  animation: pulse 2s infinite;
}

.header-date {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 10px;
}

.header-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(255,255,255,0.05);
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.06);
}

.meta-icon { font-size: 0.8rem; }

.header-games {
  text-align: right;
}

.games-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 8px;
}

.games-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.game-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
}

.game-away { font-weight: 700; color: var(--text); }
.game-at { color: var(--text-dim); font-size: 10px; }
.game-home { font-weight: 700; color: var(--text); }

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  padding: 1rem;
  text-align: center;
  transition: all var(--transition);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.stat-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text);
  font-family: 'Orbitron', sans-serif;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-sub {
  font-size: 10px;
  color: var(--text-dim);
}

/* Two Column Layout */
.two-col-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 1.5rem;
  align-items: start;
}

.left-col {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.right-col {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: sticky;
  top: 80px;
}

/* Section Headers */
.section-header {
  margin-bottom: 1rem;
}

.section-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  font-size: 1.2rem;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text);
}

.locks-header .section-title {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.locks-icon {
  filter: drop-shadow(0 0 8px rgba(245,158,11,0.5));
}

.lock-count-badge, .count-badge {
  background: rgba(245,158,11,0.15);
  color: #f59e0b;
  border: 1px solid rgba(245,158,11,0.3);
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 12px;
}

.locks-subtitle {
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 4px;
  margin-left: 2px;
}

/* Grids */
.locks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.parlays-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.other-picks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

/* Sidebar widgets */
.sidebar-widget {
  overflow: hidden;
}

.widget-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--card-border);
}

.widget-icon { font-size: 1rem; }

.widget-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
}

.games-widget-list {
  display: flex;
  flex-direction: column;
}

.game-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition);
}

.game-row:hover { background: rgba(255,255,255,0.02); }
.game-row:last-child { border-bottom: none; }

.game-teams {
  display: flex;
  align-items: center;
  gap: 6px;
}

.game-team {
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
}

.game-separator {
  font-size: 10px;
  color: var(--text-dim);
}

.game-picks-count {
  font-size: 10px;
  color: var(--text-dim);
  background: rgba(255,255,255,0.04);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Model Stats */
.model-stats-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.model-stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

.model-stat-row:last-child { border-bottom: none; }

.model-stat-label {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  border-radius: 4px;
}

.model-stat-label.stat-pts {
  background: rgba(59,130,246,0.15);
  color: var(--pts-color);
}
.model-stat-label.stat-reb {
  background: rgba(249,115,22,0.15);
  color: var(--reb-color);
}
.model-stat-label.stat-ast {
  background: rgba(34,197,94,0.15);
  color: var(--ast-color);
}

.model-stat-values {
  display: flex;
  gap: 16px;
}

.model-kv {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.model-k {
  font-size: 9px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.model-v {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

/* Responsive */
@media (max-width: 1100px) {
  .two-col-layout {
    grid-template-columns: 1fr;
  }
  .right-col {
    position: static;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .stats-bar {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .parlays-grid {
    grid-template-columns: 1fr;
  }
  .right-col {
    grid-template-columns: 1fr;
  }
  .stats-bar {
    grid-template-columns: repeat(2, 1fr);
  }
  .header-main {
    flex-direction: column;
  }
  .header-games {
    text-align: left;
  }
  .games-list {
    align-items: flex-start;
  }
  .page-header {
    padding: 1.25rem 1rem;
  }
  .header-date {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .stats-bar {
    grid-template-columns: 1fr 1fr;
  }
  .stat-value {
    font-size: 1.2rem;
  }
}
</style>

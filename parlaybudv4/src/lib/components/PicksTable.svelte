<script lang="ts">
  import type { Pick } from '$lib/types';
  import { formatOdds, formatPct, getStatColor, getEdgeColor } from '$lib/utils';

  export let picks: Pick[];

  type SortKey = keyof Pick;
  let sortKey: SortKey = 'model_prob';
  let sortDir: 1 | -1 = -1;
  let activeFilter: 'All' | 'PTS' | 'REB' | 'AST' = 'All';

  $: filtered = activeFilter === 'All' ? picks : picks.filter(p => p.stat === activeFilter);

  $: sorted = [...filtered].sort((a, b) => {
    const av = a[sortKey];
    const bv = b[sortKey];
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * sortDir;
    return String(av).localeCompare(String(bv)) * sortDir;
  });

  function setSort(key: SortKey) {
    if (sortKey === key) {
      sortDir = sortDir === 1 ? -1 : 1;
    } else {
      sortKey = key;
      sortDir = -1;
    }
  }

  function getSortIcon(key: SortKey): string {
    if (sortKey !== key) return '↕';
    return sortDir === -1 ? '↓' : '↑';
  }

  function getProbColor(prob: number): string {
    if (prob >= 0.72) return '#22c55e';
    if (prob >= 0.65) return '#86efac';
    if (prob >= 0.60) return '#f59e0b';
    return '#94a3b8';
  }
</script>

<div class="table-wrapper">
  <div class="table-controls">
    <div class="filter-tabs">
      {#each ['All', 'PTS', 'REB', 'AST'] as filter}
        <button
          class="filter-tab"
          class:active={activeFilter === filter}
          on:click={() => activeFilter = filter as typeof activeFilter}
          style={activeFilter === filter && filter !== 'All' ? `color: ${getStatColor(filter)}; border-color: ${getStatColor(filter)}40; background: ${getStatColor(filter)}10;` : ''}
        >
          {filter}
          {#if filter !== 'All'}
            <span class="tab-count">{picks.filter(p => p.stat === filter).length}</span>
          {:else}
            <span class="tab-count">{picks.length}</span>
          {/if}
        </button>
      {/each}
    </div>
    <div class="table-meta">
      <span class="meta-text">{sorted.length} picks</span>
    </div>
  </div>

  <div class="table-scroll">
    <table class="picks-table">
      <thead>
        <tr>
          <th class="sortable" on:click={() => setSort('player')}>
            Player <span class="sort-icon">{getSortIcon('player')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('team')}>
            Team <span class="sort-icon">{getSortIcon('team')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('stat')}>
            Stat <span class="sort-icon">{getSortIcon('stat')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('line')}>
            Line <span class="sort-icon">{getSortIcon('line')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('model_prob')}>
            P(Over) <span class="sort-icon">{getSortIcon('model_prob')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('edge')}>
            Edge <span class="sort-icon">{getSortIcon('edge')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('ev')}>
            EV <span class="sort-icon">{getSortIcon('ev')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('season_avg')}>
            Szn Avg <span class="sort-icon">{getSortIcon('season_avg')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('last_5_avg')}>
            L5 <span class="sort-icon">{getSortIcon('last_5_avg')}</span>
          </th>
          <th class="sortable" on:click={() => setSort('last_3_avg')}>
            L3 <span class="sort-icon">{getSortIcon('last_3_avg')}</span>
          </th>
          <th>Opp</th>
          <th>Book</th>
        </tr>
      </thead>
      <tbody>
        {#each sorted as pick, i}
          {@const probColor = getProbColor(pick.model_prob)}
          {@const edgeColor = getEdgeColor(pick.edge)}
          {@const statColor = getStatColor(pick.stat)}
          <tr class="table-row" style="animation-delay: {i * 30}ms">
            <td class="player-cell">
              <span class="player-name">{pick.player}</span>
            </td>
            <td>
              <span class="team-chip" style="color: {statColor}; border-color: {statColor}20; background: {statColor}10;">{pick.team}</span>
            </td>
            <td>
              <span class="stat-chip" style="color: {statColor}; background: {statColor}15; border-color: {statColor}30;">{pick.stat}</span>
            </td>
            <td class="numeric">
              <span class="line-val">O {pick.line}</span>
              <span class="odds-val">{formatOdds(pick.over_odds)}</span>
            </td>
            <td class="numeric">
              <span class="prob-val" style="color: {probColor};">{formatPct(pick.model_prob)}</span>
            </td>
            <td class="numeric">
              <span class="edge-val" style="color: {edgeColor};">+{formatPct(pick.edge)}</span>
            </td>
            <td class="numeric">
              <span class="ev-val" style="color: #22c55e;">+{(pick.ev * 100).toFixed(1)}%</span>
            </td>
            <td class="numeric">{pick.season_avg.toFixed(1)}</td>
            <td class="numeric">{pick.last_5_avg.toFixed(1)}</td>
            <td class="numeric">{pick.last_3_avg.toFixed(1)}</td>
            <td class="opp-cell">{pick.opponent}</td>
            <td class="book-cell">
              <span class="book-badge">{pick.book}</span>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
.table-wrapper {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid var(--card-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.table-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--card-border);
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tabs {
  display: flex;
  gap: 4px;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all var(--transition);
}

.filter-tab:hover {
  color: var(--text);
  background: rgba(255,255,255,0.05);
}

.filter-tab.active {
  color: var(--primary);
  background: rgba(59,130,246,0.1);
  border-color: rgba(59,130,246,0.25);
}

.tab-count {
  font-size: 10px;
  background: rgba(255,255,255,0.08);
  padding: 0 4px;
  border-radius: 4px;
  min-width: 16px;
  text-align: center;
}

.table-meta {
  font-size: 11px;
  color: var(--text-dim);
}

.table-scroll {
  overflow-x: auto;
}

.picks-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

thead tr {
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

th {
  padding: 10px 12px;
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-dim);
  letter-spacing: 0.5px;
  text-transform: uppercase;
  white-space: nowrap;
  background: rgba(0,0,0,0.15);
}

th.sortable {
  cursor: pointer;
  transition: color var(--transition);
  user-select: none;
}

th.sortable:hover {
  color: var(--text-muted);
}

.sort-icon {
  font-size: 10px;
  margin-left: 2px;
  opacity: 0.6;
}

.table-row {
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background var(--transition);
  animation: fadeIn 0.3s ease forwards;
}

.table-row:hover {
  background: rgba(255,255,255,0.03);
}

.table-row:last-child {
  border-bottom: none;
}

td {
  padding: 10px 12px;
  vertical-align: middle;
  white-space: nowrap;
}

.player-cell .player-name {
  font-weight: 600;
  color: var(--text);
}

.team-chip, .stat-chip {
  display: inline-block;
  font-size: 10px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid;
  letter-spacing: 0.3px;
}

.numeric {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.line-val {
  font-weight: 700;
  color: var(--text);
}

.odds-val {
  font-size: 10px;
  color: var(--text-dim);
  margin-left: 4px;
}

.prob-val, .edge-val, .ev-val {
  font-weight: 700;
}

.opp-cell {
  color: var(--text-muted);
  font-size: 12px;
}

.book-badge {
  font-size: 10px;
  color: var(--text-dim);
  background: rgba(255,255,255,0.04);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.06);
}
</style>

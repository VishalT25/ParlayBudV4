<script lang="ts">
  import type { Injury } from '$lib/types';

  export let injuries: Injury[];

  let collapsed = false;

  function getStatusColor(status: string): string {
    if (status === 'OUT') return '#ef4444';
    if (status === 'QUESTIONABLE') return '#f59e0b';
    if (status === 'PROBABLE') return '#22c55e';
    return '#94a3b8';
  }

  function getStatusBg(status: string): string {
    if (status === 'OUT') return 'rgba(239,68,68,0.12)';
    if (status === 'QUESTIONABLE') return 'rgba(245,158,11,0.12)';
    if (status === 'PROBABLE') return 'rgba(34,197,94,0.12)';
    return 'rgba(148,163,184,0.12)';
  }
</script>

<div class="injuries-widget glass">
  <button class="injuries-header" on:click={() => collapsed = !collapsed}>
    <div class="header-left">
      <span class="header-icon">🚨</span>
      <span class="header-title">Injury Report</span>
      <span class="injuries-count">{injuries.length}</span>
    </div>
    <span class="collapse-icon" class:rotated={collapsed}>▼</span>
  </button>

  {#if !collapsed}
    <div class="injuries-list">
      {#each injuries as injury}
        {@const color = getStatusColor(injury.status)}
        {@const bg = getStatusBg(injury.status)}
        <div class="injury-item">
          <div class="injury-info">
            <span class="injury-player">{injury.player}</span>
            <span class="injury-reason">{injury.reason}</span>
          </div>
          <span class="status-badge" style="color: {color}; background: {bg}; border-color: {color}30;">
            {injury.status}
          </span>
        </div>
      {/each}

      {#if injuries.length === 0}
        <div class="no-injuries">
          <span>✅ No significant injuries</span>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
.injuries-widget {
  overflow: hidden;
}

.injuries-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.875rem 1rem;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--transition);
  border-bottom: 1px solid var(--card-border);
}

.injuries-header:hover {
  background: rgba(255,255,255,0.03);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 1rem;
}

.header-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.3px;
}

.injuries-count {
  background: rgba(239,68,68,0.15);
  color: #ef4444;
  border: 1px solid rgba(239,68,68,0.25);
  font-size: 10px;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.collapse-icon {
  font-size: 10px;
  color: var(--text-dim);
  transition: transform var(--transition);
}

.collapse-icon.rotated {
  transform: rotate(-90deg);
}

.injuries-list {
  display: flex;
  flex-direction: column;
}

.injury-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.625rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  gap: 8px;
  transition: background var(--transition);
}

.injury-item:hover {
  background: rgba(255,255,255,0.02);
}

.injury-item:last-child {
  border-bottom: none;
}

.injury-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.injury-player {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.injury-reason {
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 1px;
}

.status-badge {
  font-size: 9px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid;
  letter-spacing: 0.5px;
  white-space: nowrap;
  flex-shrink: 0;
}

.no-injuries {
  padding: 1rem;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
}
</style>

<script lang="ts">
  import type { Parlay, Pick } from '$lib/types';
  import { getStatColor } from '$lib/utils';

  export let parlay: Parlay;
  export let type: '3-Leg Safe' | '5-Leg Premium';
  export let picks: Pick[];

  $: is3Leg = type === '3-Leg Safe';
  $: accentColor = is3Leg ? '#22c55e' : '#f59e0b';
  $: n = parlay.legs.length;
  // Payout multiplier using -110 odds per leg: (1.909)^n
  $: payoutMultiplier = Math.pow(1.909, n);
  $: combinedPct = Math.round(parlay.combined_prob * 100);

  function getPickForPlayer(playerName: string): Pick | undefined {
    return picks.find(p => p.player === playerName);
  }
</script>

<div class="parlay-card glass" style="border-color: {accentColor}20; --accent: {accentColor};">
  <div class="parlay-header" style="border-bottom-color: {accentColor}20;">
    <div class="type-section">
      <span class="type-icon">{is3Leg ? '🛡️' : '💎'}</span>
      <div class="type-info">
        <span class="type-label">{type}</span>
        <span class="type-sub">{n} Leg Parlay</span>
      </div>
    </div>
    <div class="prob-pill" style="background: {accentColor}15; border-color: {accentColor}30; color: {accentColor};">
      <span class="prob-pct">{combinedPct}%</span>
      <span class="prob-label">Combined</span>
    </div>
  </div>

  <div class="legs-container">
    {#each parlay.legs as leg, i}
      {@const playerPick = getPickForPlayer(parlay.players[i])}
      <div class="leg-item">
        <div class="leg-connector">
          <div class="leg-dot" style="background: {accentColor}; box-shadow: 0 0 8px {accentColor}60;"></div>
          {#if i < parlay.legs.length - 1}
            <div class="leg-line" style="background: linear-gradient(to bottom, {accentColor}40, {accentColor}10);"></div>
          {/if}
        </div>
        <div class="leg-content">
          <div class="leg-player">{parlay.players[i]}</div>
          <div class="leg-detail">
            {#if playerPick}
              <span class="leg-stat-badge" style="background: {getStatColor(playerPick.stat)}20; color: {getStatColor(playerPick.stat)}; border-color: {getStatColor(playerPick.stat)}30;">
                {playerPick.stat}
              </span>
            {/if}
            <span class="leg-line-text">{leg.split(' ').slice(-2).join(' ')}</span>
            {#if playerPick}
              <span class="leg-prob" style="color: {accentColor};">{Math.round(playerPick.model_prob * 100)}%</span>
            {/if}
          </div>
        </div>
      </div>
    {/each}
  </div>

  <div class="parlay-footer" style="border-top-color: {accentColor}20;">
    <div class="payout-info">
      <span class="payout-label">Est. Payout</span>
      <span class="payout-multiplier" style="color: {accentColor};">{payoutMultiplier.toFixed(1)}x</span>
    </div>
    <div class="parlay-note">
      <span class="note-text">$10 → <strong style="color: {accentColor};">${(10 * payoutMultiplier).toFixed(2)}</strong></span>
    </div>
  </div>
</div>

<style>
.parlay-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--card-border);
  overflow: hidden;
  transition: all var(--transition);
}

.parlay-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}

.parlay-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid;
}

.type-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-icon {
  font-size: 1.5rem;
}

.type-info {
  display: flex;
  flex-direction: column;
}

.type-label {
  font-size: 14px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: 0.3px;
}

.type-sub {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}

.prob-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid;
}

.prob-pct {
  font-size: 18px;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
  line-height: 1;
}

.prob-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  opacity: 0.8;
  margin-top: 2px;
}

.legs-container {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
}

.leg-item {
  display: flex;
  gap: 12px;
  position: relative;
}

.leg-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 12px;
}

.leg-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;
}

.leg-line {
  width: 2px;
  flex: 1;
  min-height: 16px;
  margin: 3px 0;
}

.leg-content {
  flex: 1;
  padding-bottom: 12px;
}

.leg-player {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
}

.leg-detail {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
  flex-wrap: wrap;
}

.leg-stat-badge {
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  border: 1px solid;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.leg-line-text {
  font-size: 11px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.leg-prob {
  font-size: 11px;
  font-weight: 700;
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

.parlay-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  border-top: 1px solid;
  background: rgba(0,0,0,0.15);
}

.payout-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.payout-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.payout-multiplier {
  font-size: 22px;
  font-weight: 900;
  font-family: 'Orbitron', sans-serif;
}

.parlay-note {
  font-size: 12px;
  color: var(--text-muted);
}
</style>

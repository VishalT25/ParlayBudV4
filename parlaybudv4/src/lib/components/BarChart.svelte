<script lang="ts">
  export let data: { feature: string; importance: number }[];
  export let color: string = '#3b82f6';

  $: topData = data.slice(0, 10);
  $: maxVal = Math.max(...topData.map(d => d.importance));

  function formatFeature(f: string): string {
    return f.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
</script>

<div class="bar-chart">
  {#each topData as item, i}
    {@const widthPct = (item.importance / maxVal) * 100}
    <div class="bar-row" style="animation-delay: {i * 60}ms;">
      <div class="feature-label" title={formatFeature(item.feature)}>
        {formatFeature(item.feature)}
      </div>
      <div class="bar-track">
        <div
          class="bar-fill"
          style="width: {widthPct}%; background: linear-gradient(90deg, {color}, {color}99);"
        ></div>
      </div>
      <div class="importance-val">{(item.importance * 100).toFixed(1)}%</div>
    </div>
  {/each}
</div>

<style>
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-row {
  display: grid;
  grid-template-columns: 180px 1fr 48px;
  align-items: center;
  gap: 10px;
  animation: fadeIn 0.4s ease forwards;
  opacity: 0;
}

.feature-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-track {
  height: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 5px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}

.importance-val {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 600px) {
  .bar-row {
    grid-template-columns: 120px 1fr 42px;
    gap: 8px;
  }
  .feature-label { font-size: 11px; }
}
</style>

<script lang="ts">
  import { getEdgeColor } from '$lib/utils';

  export let edge: number;

  $: color = getEdgeColor(edge);
  $: pct = (edge * 100).toFixed(1);
</script>

<div class="edge-badge" style="color: {color}; border-color: {color}40; background: {color}15;">
  <span class="edge-arrow">▲</span>
  <span class="edge-value">+{pct}% edge</span>
</div>

<style>
.edge-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 20px;
  border: 1px solid;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.edge-arrow {
  font-size: 8px;
}

.edge-value {
  font-variant-numeric: tabular-nums;
}
</style>

<script lang="ts">
  import { getProbabilityTier } from '$lib/utils';

  export let prob: number;
  export let size: number = 80;

  $: tier = getProbabilityTier(prob);
  $: pct = Math.round(prob * 100);
  $: radius = (size - 10) / 2;
  $: circumference = 2 * Math.PI * radius;
  $: dashoffset = circumference * (1 - prob);
  $: color = tier.color;
</script>

<div class="ring-wrapper">
  <svg width={size} height={size} viewBox="0 0 {size} {size}">
    <!-- Background track -->
    <circle
      cx={size/2} cy={size/2} r={radius}
      fill="none"
      stroke="rgba(255,255,255,0.06)"
      stroke-width="6"
    />
    <!-- Progress arc -->
    <circle
      cx={size/2} cy={size/2} r={radius}
      fill="none"
      stroke={color}
      stroke-width="6"
      stroke-linecap="round"
      stroke-dasharray={circumference}
      stroke-dashoffset={dashoffset}
      transform="rotate(-90 {size/2} {size/2})"
      style="filter: drop-shadow(0 0 6px {color}80); transition: stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1);"
    />
    <!-- Center text -->
    <text
      x={size/2} y={size/2 + 1}
      text-anchor="middle"
      dominant-baseline="middle"
      fill={color}
      font-family="'Orbitron', sans-serif"
      font-weight="700"
      font-size={size * 0.2}
    >{pct}%</text>
  </svg>
  <span class="tier-label" style="color: {color}">{tier.label}</span>
</div>

<style>
.ring-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.tier-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}
</style>

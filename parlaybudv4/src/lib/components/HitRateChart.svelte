<script lang="ts">
  import { formatDateShort } from '$lib/utils';

  export let data: { date: string; hit_rate: number }[];

  const W = 800;
  const H = 220;
  const PAD = { top: 20, right: 20, bottom: 50, left: 52 };
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const yMin = 0.5;
  const yMax = 1.0;

  $: sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));

  function xPos(i: number): number {
    if (sorted.length <= 1) return PAD.left + innerW / 2;
    return PAD.left + (i / (sorted.length - 1)) * innerW;
  }

  function yPos(val: number): number {
    return PAD.top + innerH - ((val - yMin) / (yMax - yMin)) * innerH;
  }

  $: points = sorted.map((d, i) => ({ x: xPos(i), y: yPos(d.hit_rate), ...d }));

  // Smooth cubic bezier path
  $: linePath = (() => {
    if (points.length === 0) return '';
    if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cpx = (prev.x + curr.x) / 2;
      d += ` C ${cpx} ${prev.y}, ${cpx} ${curr.y}, ${curr.x} ${curr.y}`;
    }
    return d;
  })();

  $: areaPath = (() => {
    if (points.length === 0) return '';
    const bottom = PAD.top + innerH;
    let d = linePath;
    d += ` L ${points[points.length - 1].x} ${bottom} L ${points[0].x} ${bottom} Z`;
    return d;
  })();

  // Y-axis gridlines
  const yTicks = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

  let tooltip: { x: number; y: number; date: string; rate: number } | null = null;

  function handleMouseOver(pt: typeof points[0]) {
    tooltip = { x: pt.x, y: pt.y, date: pt.date, rate: pt.hit_rate };
  }

  function handleMouseOut() {
    tooltip = null;
  }
</script>

<div class="chart-container">
  <svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" class="chart-svg">
    <defs>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.25" />
        <stop offset="100%" stop-color="#3b82f6" stop-opacity="0" />
      </linearGradient>
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
      </filter>
    </defs>

    <!-- Grid lines -->
    {#each yTicks as tick}
      {@const y = yPos(tick)}
      <line
        x1={PAD.left} y1={y}
        x2={PAD.left + innerW} y2={y}
        stroke={tick === 0.7 ? 'rgba(245,158,11,0.4)' : 'rgba(255,255,255,0.05)'}
        stroke-width={tick === 0.7 ? 1.5 : 1}
        stroke-dasharray={tick === 0.7 ? '6 4' : '0'}
      />
      <text x={PAD.left - 8} y={y + 4} text-anchor="end" fill="#475569" font-size="11" font-family="Inter, sans-serif">
        {(tick * 100).toFixed(0)}%
      </text>
    {/each}

    <!-- 70% target label -->
    <text x={PAD.left + innerW + 4} y={yPos(0.7) + 4} fill="#f59e0b" font-size="10" font-family="Inter, sans-serif" font-weight="600">Target</text>

    <!-- Area fill -->
    {#if points.length > 1}
      <path d={areaPath} fill="url(#areaGrad)" />
    {/if}

    <!-- Line -->
    {#if points.length > 1}
      <path
        d={linePath}
        fill="none"
        stroke="#3b82f6"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
        filter="url(#glow)"
      />
    {/if}

    <!-- X-axis labels -->
    {#each points as pt, i}
      {#if i === 0 || i === points.length - 1 || points.length <= 5}
        <text
          x={pt.x} y={PAD.top + innerH + 20}
          text-anchor="middle"
          fill="#475569"
          font-size="11"
          font-family="Inter, sans-serif"
        >{formatDateShort(pt.date)}</text>
      {/if}
    {/each}

    <!-- Data points -->
    {#each points as pt}
      <circle
        cx={pt.x} cy={pt.y} r="5"
        fill={pt.hit_rate >= 0.7 ? '#22c55e' : pt.hit_rate >= 0.6 ? '#f59e0b' : '#ef4444'}
        stroke="#0f172a"
        stroke-width="2"
        style="cursor: pointer;"
        on:mouseover={() => handleMouseOver(pt)}
        on:mouseout={handleMouseOut}
        on:focus={() => handleMouseOver(pt)}
        on:blur={handleMouseOut}
      />
    {/each}

    <!-- Tooltip -->
    {#if tooltip}
      {@const tw = 130}
      {@const th = 48}
      {@const tx = Math.min(tooltip.x - tw / 2, W - tw - 8)}
      {@const ty = tooltip.y - th - 12}
      <rect x={tx} y={ty} width={tw} height={th} rx="6" fill="#1e293b" stroke="rgba(255,255,255,0.1)" stroke-width="1" />
      <text x={tx + tw/2} y={ty + 16} text-anchor="middle" fill="#94a3b8" font-size="10" font-family="Inter, sans-serif">{formatDateShort(tooltip.date)}</text>
      <text x={tx + tw/2} y={ty + 34} text-anchor="middle" fill={tooltip.rate >= 0.7 ? '#22c55e' : '#f59e0b'} font-size="14" font-weight="700" font-family="Orbitron, sans-serif">{(tooltip.rate * 100).toFixed(1)}%</text>
    {/if}
  </svg>
</div>

<style>
.chart-container {
  width: 100%;
  overflow: hidden;
}

.chart-svg {
  width: 100%;
  height: auto;
  display: block;
}
</style>

<script lang="ts">
  import { formatDateShort } from '$lib/utils';

  export let date: string;
  export let today: string;
  export let prevDate: string;
  export let nextDate: string;
  export let availableDates: string[] = [];

  $: isToday = date === today;
  $: isFuture = date >= today;
  $: hasPrev = true; // always allow going back; page shows empty state if no data
  $: hasNext = !isFuture;

  $: prevHasData = availableDates.includes(prevDate);
  $: nextHasData = availableDates.includes(nextDate);
</script>

<div class="date-nav glass">
  <a
    href="/?date={prevDate}"
    class="nav-btn"
    class:faded={!prevHasData}
    aria-label="Previous day"
  >
    ‹
  </a>

  <div class="date-center">
    <div class="date-display">
      <span class="date-formatted">{formatDateShort(date)}</span>
      {#if isToday}
        <span class="today-chip">Today</span>
      {:else if isFuture}
        <span class="future-chip">Future</span>
      {/if}
    </div>
    {#if !isToday}
      <a href="/" class="back-today">↩ Back to today</a>
    {/if}
  </div>

  <a
    href={hasNext ? `/?date=${nextDate}` : null}
    class="nav-btn"
    class:disabled={!hasNext}
    class:faded={hasNext && !nextHasData}
    aria-label="Next day"
    aria-disabled={!hasNext}
  >
    ›
  </a>
</div>

<style>
.date-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  margin-bottom: 1.25rem;
  border-radius: var(--radius-sm);
  gap: 1rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 1.4rem;
  font-weight: 300;
  color: var(--text-muted);
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  text-decoration: none;
  transition: all var(--transition);
  flex-shrink: 0;
  line-height: 1;
}

.nav-btn:hover:not(.disabled) {
  color: var(--text);
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.15);
}

.nav-btn.disabled {
  opacity: 0.25;
  cursor: not-allowed;
  pointer-events: none;
}

.nav-btn.faded {
  opacity: 0.45;
}

.date-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.date-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-formatted {
  font-size: 15px;
  font-weight: 700;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.today-chip {
  font-size: 10px;
  font-weight: 700;
  background: rgba(34,197,94,0.15);
  color: var(--accent-green);
  border: 1px solid rgba(34,197,94,0.3);
  padding: 1px 7px;
  border-radius: 10px;
  letter-spacing: 0.3px;
}

.future-chip {
  font-size: 10px;
  font-weight: 700;
  background: rgba(148,163,184,0.12);
  color: var(--text-muted);
  border: 1px solid rgba(148,163,184,0.2);
  padding: 1px 7px;
  border-radius: 10px;
}

.back-today {
  font-size: 11px;
  color: var(--primary);
  text-decoration: none;
  opacity: 0.8;
  transition: opacity var(--transition);
}

.back-today:hover { opacity: 1; }
</style>

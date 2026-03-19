import type { PageLoad } from './$types';
import type { DayPicks } from '$lib/types';

export const load: PageLoad = async ({ fetch, url, depends }) => {
  depends('parlaybudlive'); // lets invalidate('parlaybudlive') re-run just this load

  // Shift back 3 hours: midnight–2:59am ET still shows the previous day's picks,
  // giving late games time to finish before the next day's picks take over.
  const adjusted = new Date(Date.now() - 3 * 60 * 60 * 1000);
  const today = adjusted.toLocaleDateString('en-CA', { timeZone: 'America/New_York' });

  const requestedDate = url.searchParams.get('date') || today;

  // Load the requested date's picks
  let picks: DayPicks | null = null;
  try {
    const res = await fetch(`/picks/${requestedDate}.json`);
    if (res.ok) picks = await res.json();
  } catch { /* no file for this date */ }

  // Scan the past 30 days before requestedDate for historical leg results
  const pastDates: string[] = [];
  const base = new Date(requestedDate + 'T12:00:00');
  for (let i = 1; i <= 30; i++) {
    const d = new Date(base.getTime() - i * 86400000);
    pastDates.push(d.toISOString().split('T')[0]);
  }

  // Fetch all past pick files in parallel (will 404 silently for missing dates)
  const pastDays = (
    await Promise.all(
      pastDates.map(async (date) => {
        try {
          const res = await fetch(`/picks/${date}.json`);
          if (!res.ok) return null;
          return (await res.json()) as DayPicks;
        } catch {
          return null;
        }
      })
    )
  ).filter(Boolean) as DayPicks[];

  // Build per-leg history: "Player|STAT" → { attempts, hits, results[] }
  type LegHistory = { attempts: number; hits: number; recent: boolean[] };
  const legMap: Record<string, LegHistory> = {};

  // Also collect all dates that had picks files (for nav availability hints)
  const availableDates: string[] = [];

  for (const day of pastDays) {
    availableDates.push(day.date);
    if (!day.results?.details) continue;
    for (const detail of day.results.details) {
      const key = `${detail.player}|${detail.stat}`;
      if (!legMap[key]) legMap[key] = { attempts: 0, hits: 0, recent: [] };
      legMap[key].attempts++;
      if (detail.hit) legMap[key].hits++;
      legMap[key].recent.unshift(detail.hit); // newest first
    }
  }

  // For recent days with null results, auto-compute hit rates from ESPN boxscore data
  const nullResultDays = pastDays
    .filter(d => !d.results && d.picks?.length > 0)
    .slice(0, 7); // only bother with last 7 days

  if (nullResultDays.length > 0) {
    const espnResults = await Promise.all(
      nullResultDays.map(async (day) => {
        try {
          const res = await fetch(`/api/live?date=${day.date}`);
          if (!res.ok) return null;
          return { day, liveData: (await res.json()) as Record<string, Record<string, unknown>> };
        } catch { return null; }
      })
    );

    for (const item of espnResults) {
      if (!item) continue;
      const { day, liveData } = item;
      for (const pick of day.picks) {
        const raw = liveData[pick.player.toLowerCase()];
        if (!raw || raw.gameStatus !== 'final') continue;
        const statKey = pick.stat.toLowerCase() as 'pts' | 'reb' | 'ast';
        const actual = (raw[statKey] as number) ?? 0;
        const hit = actual >= pick.line;
        const key = `${pick.player}|${pick.stat}`;
        if (!legMap[key]) legMap[key] = { attempts: 0, hits: 0, recent: [] };
        legMap[key].attempts++;
        if (hit) legMap[key].hits++;
        legMap[key].recent.unshift(hit);
      }
    }
  }

  // Trim recent to last 10 for display
  for (const key of Object.keys(legMap)) {
    legMap[key].recent = legMap[key].recent.slice(0, 10);
  }

  // Prev/next dates for navigation (just day-by-day, page shows empty state if no file)
  const prevDate = new Date(base.getTime() - 86400000).toISOString().split('T')[0];
  const nextDate = new Date(base.getTime() + 86400000).toISOString().split('T')[0];

  // Fetch live pick status for the displayed date (works for today AND past dates)
  let liveStatus: Record<string, unknown> = {};
  try {
    const lr = await fetch(`/api/live?date=${requestedDate}`);
    if (lr.ok) liveStatus = await lr.json();
  } catch { /* ESPN unavailable */ }

  return {
    picks,
    date: requestedDate,
    today,
    prevDate,
    nextDate,
    availableDates: availableDates.sort(),
    legHistory: legMap,
    liveStatus,
  };
};

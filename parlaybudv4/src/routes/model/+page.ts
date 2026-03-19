import type { PageLoad } from './$types';
import type { Metrics, DayPicks } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
  const res = await fetch('/metrics.json');
  const metrics: Metrics = await res.json();

  // Load past 30 days of picks to compute live per-stat performance
  const dates: string[] = [];
  for (let i = 1; i <= 30; i++) {
    const d = new Date(Date.now() - i * 86400000);
    dates.push(d.toISOString().split('T')[0]);
  }

  type StatPerf = { attempts: number; hits: number };
  const livePerf: Record<string, StatPerf> = { PTS: { attempts: 0, hits: 0 }, REB: { attempts: 0, hits: 0 }, AST: { attempts: 0, hits: 0 } };
  const daysWithoutResults: DayPicks[] = [];

  await Promise.all(dates.map(async (date) => {
    try {
      const r = await fetch(`/picks/${date}.json`);
      if (!r.ok) return;
      const day: DayPicks = await r.json();

      if (day.results?.details) {
        for (const d of day.results.details) {
          const s = d.stat as string;
          if (!livePerf[s]) continue;
          livePerf[s].attempts++;
          if (d.hit) livePerf[s].hits++;
        }
      } else if (day.picks?.length > 0) {
        daysWithoutResults.push(day);
      }
    } catch { /* ignore */ }
  }));

  // Auto-compute from ESPN for days without written results
  if (daysWithoutResults.length > 0) {
    await Promise.all(daysWithoutResults.map(async (day) => {
      try {
        const r = await fetch(`/api/live?date=${day.date}`);
        if (!r.ok) return;
        const liveData = await r.json() as Record<string, Record<string, unknown>>;
        const injuredNames = new Set<string>((liveData['__injured'] as string[] | undefined) ?? []);

        for (const pick of day.picks) {
          const key = pick.player.toLowerCase();
          if (injuredNames.has(key)) continue;
          const raw = liveData[key];
          if (!raw || raw.gameStatus !== 'final') continue;
          const statKey = pick.stat.toLowerCase() as 'pts' | 'reb' | 'ast';
          const actual = (raw[statKey] as number) ?? 0;
          const s = pick.stat as string;
          if (!livePerf[s]) continue;
          livePerf[s].attempts++;
          if (actual >= pick.line) livePerf[s].hits++;
        }
      } catch { /* ESPN unavailable */ }
    }));
  }

  return { metrics, livePerf };
};

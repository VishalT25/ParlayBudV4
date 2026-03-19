import type { PageLoad } from './$types';
import type { DayPicks, HistorySummary } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
  const history: HistorySummary[] = [];
  const fullData: DayPicks[] = [];

  // Try loading past 30 days
  const dates: string[] = [];
  for (let i = 1; i <= 30; i++) {
    const d = new Date(Date.now() - i * 86400000);
    dates.push(d.toISOString().split('T')[0]);
  }

  // Also try hardcoded demo dates
  const demoDates = ['2026-03-12', '2026-03-11', '2026-03-13'];
  const allDates = [...new Set([...dates, ...demoDates])].sort().reverse();

  const daysWithoutResults: DayPicks[] = [];

  await Promise.all(allDates.map(async (date) => {
    try {
      const res = await fetch(`/picks/${date}.json`);
      if (!res.ok) return;
      const data: DayPicks = await res.json();
      fullData.push(data);
      if (data.results) {
        history.push({
          date: data.date,
          picks_total: data.results.picks_total,
          picks_hit: data.results.picks_hit,
          hit_rate: data.results.hit_rate,
          parlay_3_hit: data.results.parlay_3_hit,
          parlay_5_hit: data.results.parlay_5_hit
        });
      } else if (data.picks?.length > 0) {
        daysWithoutResults.push(data);
      }
    } catch { /* ignore */ }
  }));

  // Auto-compute results for days without them using ESPN final data
  if (daysWithoutResults.length > 0) {
    await Promise.all(daysWithoutResults.map(async (day) => {
      try {
        const res = await fetch(`/api/live?date=${day.date}`);
        if (!res.ok) return;
        const liveData = await res.json() as Record<string, Record<string, unknown>>;
        const injuredNames = new Set<string>((liveData['__injured'] as string[] | undefined) ?? []);

        let total = 0, hit = 0;
        let parlay3Hit = true, parlay5Hit = true;

        for (const pick of day.picks) {
          const key = pick.player.toLowerCase();
          if (injuredNames.has(key)) continue;
          const raw = liveData[key];
          if (!raw || raw.gameStatus !== 'final') continue;
          const statKey = pick.stat.toLowerCase() as 'pts' | 'reb' | 'ast';
          const actual = (raw[statKey] as number) ?? 0;
          const isHit = actual >= pick.line;
          total++;
          if (isHit) hit++;
        }

        if (total === 0) return;

        // Check parlay legs using players array + picks lookup
        const parlayHit = (players: string[]) => players.every((playerName) => {
          const key = playerName.toLowerCase();
          if (injuredNames.has(key)) return true; // voided leg = doesn't kill parlay
          const raw = liveData[key];
          if (!raw || raw.gameStatus !== 'final') return true; // game not final = pass through
          // Find which stat/line for this player in the parlay
          const pick = day.picks.find(p => p.player === playerName);
          if (!pick) return true;
          const statKey = pick.stat.toLowerCase() as 'pts' | 'reb' | 'ast';
          return ((raw[statKey] as number) ?? 0) >= pick.line;
        });

        if (day.parlay_3leg?.players) parlay3Hit = parlayHit(day.parlay_3leg.players);
        if (day.parlay_5leg?.players) parlay5Hit = parlayHit(day.parlay_5leg.players);

        history.push({
          date: day.date,
          picks_total: total,
          picks_hit: hit,
          hit_rate: hit / total,
          parlay_3_hit: parlay3Hit,
          parlay_5_hit: parlay5Hit
        });
      } catch { /* ESPN unavailable for that date */ }
    }));
  }

  history.sort((a, b) => b.date.localeCompare(a.date));

  return { history, fullData };
};

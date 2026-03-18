import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const ESPN = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba';

export const GET: RequestHandler = async ({ url, fetch }) => {
  const date = url.searchParams.get('date') ?? new Date().toISOString().split('T')[0];
  const espnDate = date.replace(/-/g, '');

  try {
    const sbRes = await fetch(`${ESPN}/scoreboard?dates=${espnDate}`);
    if (!sbRes.ok) return json({});
    const sb = await sbRes.json();

    const result: Record<string, unknown> = {};
    const events: unknown[] = sb.events ?? [];

    await Promise.all(
      events.map(async (event: unknown) => {
        const ev = event as Record<string, unknown>;
        const status = ev.status as Record<string, unknown> | undefined;
        const statusType = (status?.type as Record<string, unknown> | undefined)?.name as string ?? '';
        const isLive  = statusType === 'STATUS_IN_PROGRESS';
        const isFinal = statusType === 'STATUS_FINAL';

        const competitions = (ev.competitions as unknown[]) ?? [];
        const competition = competitions[0] as Record<string, unknown> | undefined;
        if (!competition) return;

        const competitors = (competition.competitors as unknown[]) ?? [];
        const homeComp = competitors.find((c) => (c as Record<string, unknown>).homeAway === 'home') as Record<string, unknown> | undefined;
        const awayComp = competitors.find((c) => (c as Record<string, unknown>).homeAway === 'away') as Record<string, unknown> | undefined;
        const homeTeam = ((homeComp?.team as Record<string, unknown>)?.abbreviation as string) ?? '';
        const awayTeam = ((awayComp?.team as Record<string, unknown>)?.abbreviation as string) ?? '';

        if (!isLive && !isFinal) {
          // Pre-game — store scheduled time keyed by team abbr so PickCard can show tipoff
          const gameTime = ev.date as string | undefined;
          const entry = { gameStatus: 'pre', gameTime, homeTeam, awayTeam };
          result[`__pre_${homeTeam}`] = entry;
          result[`__pre_${awayTeam}`] = entry;
          return;
        }

        const homeScore = parseInt((homeComp?.score as string) ?? '0') || 0;
        const awayScore = parseInt((awayComp?.score as string) ?? '0') || 0;
        const period = (status?.period as number) ?? 0;
        const clock  = (status?.displayClock as string) ?? '';
        const gameStatus = isFinal ? 'final' : 'live';
        const eventId = ev.id as string;

        const bsRes = await fetch(`${ESPN}/summary?event=${eventId}`);
        if (!bsRes.ok) return;
        const bs = await bsRes.json();

        const teamRows: unknown[] = bs.boxscore?.players ?? [];
        const dnpNames: string[] = [];

        for (const teamData of teamRows) {
          const td = teamData as Record<string, unknown>;
          const statistics = ((td.statistics as unknown[])?.[0]) as Record<string, unknown> | undefined;
          if (!statistics) continue;

          const names = (statistics.names as string[]) ?? [];
          // ESPN returns uppercase stat names: 'PTS', 'REB', 'AST'
          const minIdx = names.findIndex(n => n.toUpperCase() === 'MIN');
          const ptsIdx = names.findIndex(n => n.toUpperCase() === 'PTS');
          const rebIdx = names.findIndex(n => n.toUpperCase() === 'REB');
          const astIdx = names.findIndex(n => n.toUpperCase() === 'AST');

          const athletes = (statistics.athletes as unknown[]) ?? [];
          for (const ath of athletes) {
            const a = ath as Record<string, unknown>;
            const athlete = a.athlete as Record<string, unknown> | undefined;
            const name = (athlete?.displayName as string) ?? '';
            if (!name) continue;

            const didNotPlay = !!(a.didNotPlay as boolean);
            const stats = (a.stats as string[]) ?? [];
            const minutes = stats[minIdx] ?? '0';
            const playedZero = minutes === '0' || minutes === '0:00' || minutes === '';

            // DNP — add to voided list, skip stats
            if (didNotPlay || (isFinal && playedZero && stats.length > 0)) {
              dnpNames.push(name.toLowerCase());
              continue;
            }

            const pts = parseInt(stats[ptsIdx] ?? '0') || 0;
            const reb = parseInt(stats[rebIdx] ?? '0') || 0;
            const ast = parseInt(stats[astIdx] ?? '0') || 0;

            result[name.toLowerCase()] = {
              pts, reb, ast,
              gameStatus,
              period,
              clock,
              homeTeam,
              awayTeam,
              homeScore,
              awayScore,
            };
          }
        }

        // Merge DNP players into the injured list
        if (dnpNames.length > 0) {
          const existing = (result['__injured'] as string[]) ?? [];
          result['__injured'] = [...new Set([...existing, ...dnpNames])];
        }
      })
    );

    // ── Fetch current injury list (updates on every refresh) ──
    try {
      const injRes = await fetch(`${ESPN}/injuries`);
      if (injRes.ok) {
        const injData = await injRes.json();
        const injured: string[] = [];
        const EXCLUDE = ['out', 'suspension', 'suspended', 'doubtful'];
        for (const team of injData.injuries ?? []) {
          for (const inj of team.injuries ?? []) {
            const status = (inj.status ?? '').toLowerCase();
            if (!EXCLUDE.some(s => status.includes(s))) continue;
            const athlete = inj.athlete ?? {};
            const name: string = athlete.displayName
              ?? `${athlete.firstName ?? ''} ${athlete.lastName ?? ''}`.trim();
            if (name.length > 3) injured.push(name.toLowerCase());
          }
        }
        result['__injured'] = injured;
      }
    } catch { /* injury fetch failure is non-fatal */ }

    return json(result);
  } catch {
    return json({});
  }
};

import type { PageLoad } from './$types';
import type { DayPicks } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
  const today = new Date().toISOString().split('T')[0];

  try {
    const res = await fetch(`/picks/${today}.json`);
    if (!res.ok) {
      // Try previous day as fallback for demo
      const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
      const res2 = await fetch(`/picks/${yesterday}.json`);
      if (res2.ok) {
        const data: DayPicks = await res2.json();
        return { picks: data, isDemo: true };
      }
      // Try 2026-03-13 as demo
      const demo = await fetch('/picks/2026-03-13.json');
      if (demo.ok) {
        return { picks: await demo.json() as DayPicks, isDemo: true };
      }
      return { picks: null, isDemo: false };
    }
    return { picks: await res.json() as DayPicks, isDemo: false };
  } catch {
    return { picks: null, isDemo: false };
  }
};

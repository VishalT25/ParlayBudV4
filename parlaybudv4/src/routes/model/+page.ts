import type { PageLoad } from './$types';
import type { Metrics } from '$lib/types';

export const load: PageLoad = async ({ fetch }) => {
  const res = await fetch('/metrics.json');
  const metrics: Metrics = await res.json();
  return { metrics };
};

const load = async ({ fetch }) => {
  const history = [];
  const fullData = [];
  const dates = [];
  for (let i = 1; i <= 14; i++) {
    const d = new Date(Date.now() - i * 864e5);
    dates.push(d.toISOString().split("T")[0]);
  }
  const demoDates = ["2026-03-12", "2026-03-11", "2026-03-13"];
  const allDates = [.../* @__PURE__ */ new Set([...dates, ...demoDates])].sort().reverse();
  await Promise.all(allDates.map(async (date) => {
    try {
      const res = await fetch(`/picks/${date}.json`);
      if (res.ok) {
        const data = await res.json();
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
        }
      }
    } catch {
    }
  }));
  history.sort((a, b) => b.date.localeCompare(a.date));
  return { history, fullData };
};
export {
  load
};

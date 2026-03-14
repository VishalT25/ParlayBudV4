const load = async ({ fetch, url }) => {
  const today = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
  const requestedDate = url.searchParams.get("date") || today;
  let picks = null;
  try {
    const res = await fetch(`/picks/${requestedDate}.json`);
    if (res.ok) picks = await res.json();
  } catch {
  }
  const pastDates = [];
  const base = /* @__PURE__ */ new Date(requestedDate + "T12:00:00");
  for (let i = 1; i <= 30; i++) {
    const d = new Date(base.getTime() - i * 864e5);
    pastDates.push(d.toISOString().split("T")[0]);
  }
  const pastDays = (await Promise.all(
    pastDates.map(async (date) => {
      try {
        const res = await fetch(`/picks/${date}.json`);
        if (!res.ok) return null;
        return await res.json();
      } catch {
        return null;
      }
    })
  )).filter(Boolean);
  const legMap = {};
  const availableDates = [];
  for (const day of pastDays) {
    availableDates.push(day.date);
    if (!day.results?.details) continue;
    for (const detail of day.results.details) {
      const key = `${detail.player}|${detail.stat}`;
      if (!legMap[key]) legMap[key] = { attempts: 0, hits: 0, recent: [] };
      legMap[key].attempts++;
      if (detail.hit) legMap[key].hits++;
      legMap[key].recent.unshift(detail.hit);
    }
  }
  for (const key of Object.keys(legMap)) {
    legMap[key].recent = legMap[key].recent.slice(0, 10);
  }
  const prevDate = new Date(base.getTime() - 864e5).toISOString().split("T")[0];
  const nextDate = new Date(base.getTime() + 864e5).toISOString().split("T")[0];
  return {
    picks,
    date: requestedDate,
    today,
    prevDate,
    nextDate,
    availableDates: availableDates.sort(),
    legHistory: legMap
  };
};
export {
  load
};

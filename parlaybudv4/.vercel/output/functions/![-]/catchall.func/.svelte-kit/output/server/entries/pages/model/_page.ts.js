const load = async ({ fetch }) => {
  const res = await fetch("/metrics.json");
  const metrics = await res.json();
  return { metrics };
};
export {
  load
};

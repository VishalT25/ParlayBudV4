import { json } from "@sveltejs/kit";
const GET = async ({ params, fetch }) => {
  const { date } = params;
  const res = await fetch(`/picks/${date}.json`);
  if (!res.ok) {
    return json({ error: "Picks not found for this date" }, { status: 404 });
  }
  const data = await res.json();
  return json(data);
};
export {
  GET
};

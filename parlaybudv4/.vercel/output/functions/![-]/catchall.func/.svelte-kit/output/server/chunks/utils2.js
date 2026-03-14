function formatDate(dateStr) {
  const date = /* @__PURE__ */ new Date(dateStr + "T12:00:00");
  return date.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}
function formatDateShort(dateStr) {
  const date = /* @__PURE__ */ new Date(dateStr + "T12:00:00");
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
function formatOdds(odds) {
  return odds > 0 ? `+${odds}` : `${odds}`;
}
function formatPct(val) {
  return `${(val * 100).toFixed(1)}%`;
}
function getStatColor(stat) {
  switch (stat) {
    case "PTS":
      return "#3b82f6";
    case "REB":
      return "#f97316";
    case "AST":
      return "#22c55e";
    default:
      return "#94a3b8";
  }
}
function getEdgeColor(edge) {
  if (edge >= 0.15) return "#22c55e";
  if (edge >= 0.08) return "#f59e0b";
  return "#ef4444";
}
function getTeamLogoUrl(team) {
  const map = {
    "CLE": "cavaliers",
    "DAL": "mavericks",
    "BOS": "celtics",
    "LAL": "lakers",
    "GSW": "warriors",
    "MIA": "heat",
    "PHX": "suns",
    "DEN": "nuggets",
    "MIL": "bucks",
    "PHI": "76ers",
    "NYK": "knicks",
    "MIN": "timberwolves",
    "OKC": "thunder",
    "SAC": "kings",
    "LAC": "clippers",
    "ATL": "hawks",
    "CHI": "bulls",
    "TOR": "raptors",
    "IND": "pacers",
    "NOP": "pelicans",
    "MEM": "grizzlies",
    "UTA": "jazz",
    "POR": "blazers",
    "HOU": "rockets",
    "SAS": "spurs",
    "ORL": "magic",
    "CHA": "hornets",
    "DET": "pistons",
    "BKN": "nets",
    "WAS": "wizards"
  };
  const name = map[team] || team.toLowerCase();
  return `https://a.espncdn.com/i/teamlogos/nba/500/${name}.png`;
}
function getTeamColor(team) {
  const colors = {
    "CLE": "#860038",
    "DAL": "#00538C",
    "BOS": "#007A33",
    "LAL": "#552583",
    "GSW": "#1D428A",
    "MIA": "#98002E",
    "PHX": "#1D1160",
    "DEN": "#0E2240",
    "MIL": "#00471B",
    "PHI": "#006BB6",
    "NYK": "#006BB6",
    "MIN": "#0C2340",
    "OKC": "#007AC1",
    "SAC": "#5A2D81",
    "LAC": "#C8102E",
    "ATL": "#C1D32F",
    "CHI": "#CE1141",
    "TOR": "#CE1141",
    "IND": "#002D62",
    "NOP": "#0C2340",
    "MEM": "#5D76A9",
    "UTA": "#002B5C",
    "POR": "#E03A3E",
    "HOU": "#CE1141",
    "SAS": "#C4CED4",
    "ORL": "#0077C0",
    "CHA": "#1D1160",
    "DET": "#C8102E",
    "BKN": "#000000",
    "WAS": "#002B5C"
  };
  return colors[team] || "#3b82f6";
}
function getProbabilityTier(prob) {
  if (prob >= 0.72) return { label: "Elite", color: "#22c55e" };
  if (prob >= 0.65) return { label: "High", color: "#86efac" };
  if (prob >= 0.6) return { label: "Solid", color: "#f59e0b" };
  return { label: "Moderate", color: "#94a3b8" };
}
export {
  getEdgeColor as a,
  getTeamColor as b,
  getStatColor as c,
  getTeamLogoUrl as d,
  formatPct as e,
  formatOdds as f,
  getProbabilityTier as g,
  formatDateShort as h,
  formatDate as i
};

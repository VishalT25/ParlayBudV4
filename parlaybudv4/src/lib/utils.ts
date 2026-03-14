export function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

export function formatDateShort(dateStr: string): string {
  const date = new Date(dateStr + 'T12:00:00');
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function formatOdds(odds: number): string {
  return odds > 0 ? `+${odds}` : `${odds}`;
}

export function formatPct(val: number): string {
  return `${(val * 100).toFixed(1)}%`;
}

export function getStatColor(stat: string): string {
  switch (stat) {
    case 'PTS': return '#3b82f6';
    case 'REB': return '#f97316';
    case 'AST': return '#22c55e';
    default: return '#94a3b8';
  }
}

export function getEdgeColor(edge: number): string {
  if (edge >= 0.15) return '#22c55e';
  if (edge >= 0.08) return '#f59e0b';
  return '#ef4444';
}

export function getTeamLogoUrl(team: string): string {
  const map: Record<string, string> = {
    'CLE': 'cavaliers', 'DAL': 'mavericks', 'BOS': 'celtics',
    'LAL': 'lakers', 'GSW': 'warriors', 'MIA': 'heat',
    'PHX': 'suns', 'DEN': 'nuggets', 'MIL': 'bucks',
    'PHI': '76ers', 'NYK': 'knicks', 'MIN': 'timberwolves',
    'OKC': 'thunder', 'SAC': 'kings', 'LAC': 'clippers',
    'ATL': 'hawks', 'CHI': 'bulls', 'TOR': 'raptors',
    'IND': 'pacers', 'NOP': 'pelicans', 'MEM': 'grizzlies',
    'UTA': 'jazz', 'POR': 'blazers', 'HOU': 'rockets',
    'SAS': 'spurs', 'ORL': 'magic', 'CHA': 'hornets',
    'DET': 'pistons', 'BKN': 'nets', 'WAS': 'wizards'
  };
  const name = map[team] || team.toLowerCase();
  return `https://a.espncdn.com/i/teamlogos/nba/500/${name}.png`;
}

export function getTeamColor(team: string): string {
  const colors: Record<string, string> = {
    'CLE': '#860038', 'DAL': '#00538C', 'BOS': '#007A33',
    'LAL': '#552583', 'GSW': '#1D428A', 'MIA': '#98002E',
    'PHX': '#1D1160', 'DEN': '#0E2240', 'MIL': '#00471B',
    'PHI': '#006BB6', 'NYK': '#006BB6', 'MIN': '#0C2340',
    'OKC': '#007AC1', 'SAC': '#5A2D81', 'LAC': '#C8102E',
    'ATL': '#C1D32F', 'CHI': '#CE1141', 'TOR': '#CE1141',
    'IND': '#002D62', 'NOP': '#0C2340', 'MEM': '#5D76A9',
    'UTA': '#002B5C', 'POR': '#E03A3E', 'HOU': '#CE1141',
    'SAS': '#C4CED4', 'ORL': '#0077C0', 'CHA': '#1D1160',
    'DET': '#C8102E', 'BKN': '#000000', 'WAS': '#002B5C'
  };
  return colors[team] || '#3b82f6';
}

export function today(): string {
  return new Date().toISOString().split('T')[0];
}

export function getProbabilityTier(prob: number): { label: string; color: string } {
  if (prob >= 0.72) return { label: 'Elite', color: '#22c55e' };
  if (prob >= 0.65) return { label: 'High', color: '#86efac' };
  if (prob >= 0.60) return { label: 'Solid', color: '#f59e0b' };
  return { label: 'Moderate', color: '#94a3b8' };
}

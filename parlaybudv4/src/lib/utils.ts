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
  const map: Record<string, number> = {
    'CLE': 1610612739, 'DAL': 1610612742, 'BOS': 1610612738,
    'LAL': 1610612747, 'GSW': 1610612744, 'MIA': 1610612748,
    'PHX': 1610612756, 'DEN': 1610612743, 'MIL': 1610612749,
    'PHI': 1610612755, 'NYK': 1610612752, 'MIN': 1610612750,
    'OKC': 1610612760, 'SAC': 1610612758, 'LAC': 1610612746,
    'ATL': 1610612737, 'CHI': 1610612741, 'TOR': 1610612761,
    'IND': 1610612754, 'NOP': 1610612740, 'MEM': 1610612763,
    'UTA': 1610612762, 'POR': 1610612757, 'HOU': 1610612745,
    'SAS': 1610612759, 'ORL': 1610612753, 'CHA': 1610612766,
    'DET': 1610612765, 'BKN': 1610612751, 'WAS': 1610612764
  };
  const id = map[team];
  if (!id) return '';
  return `https://cdn.nba.com/logos/nba/${id}/global/L/logo.svg`;
}

export function getBookStyle(book: string): { bg: string; color: string; border: string } {
  const b = book.toLowerCase().replace(/\s/g, '');
  if (b.includes('fanduel'))    return { bg: 'rgba(20,147,255,0.15)',  color: '#1493FF', border: 'rgba(20,147,255,0.35)' };
  if (b.includes('draftkings')) return { bg: 'rgba(83,211,56,0.15)',   color: '#53D338', border: 'rgba(83,211,56,0.35)' };
  if (b.includes('betmgm'))     return { bg: 'rgba(197,160,40,0.15)', color: '#C5A028', border: 'rgba(197,160,40,0.35)' };
  if (b.includes('caesars'))    return { bg: 'rgba(0,64,122,0.2)',     color: '#7BAFD4', border: 'rgba(123,175,212,0.35)' };
  if (b.includes('pointsbet'))  return { bg: 'rgba(227,24,55,0.15)',   color: '#E31837', border: 'rgba(227,24,55,0.35)' };
  if (b.includes('betrivers'))  return { bg: 'rgba(0,48,135,0.15)',    color: '#5B8FD4', border: 'rgba(91,143,212,0.35)' };
  if (b.includes('espnbet'))    return { bg: 'rgba(255,50,50,0.15)',   color: '#FF3232', border: 'rgba(255,50,50,0.35)' };
  if (b.includes('barstool'))   return { bg: 'rgba(255,255,255,0.1)',  color: '#CCCCCC', border: 'rgba(255,255,255,0.2)' };
  return { bg: 'rgba(255,255,255,0.05)', color: 'var(--text-dim)', border: 'rgba(255,255,255,0.06)' };
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

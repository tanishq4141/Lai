export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function getRiskColor(level: string | null): string {
  switch (level) {
    case 'low': return 'text-green-500';
    case 'medium': return 'text-yellow-500';
    case 'high': return 'text-orange-500';
    case 'critical': return 'text-red-500';
    default: return 'text-[var(--color-muted-foreground)]';
  }
}

export function getRiskBgColor(level: string | null): string {
  switch (level) {
    case 'low': return 'bg-green-500/10 text-green-500 border border-green-500/20';
    case 'medium': return 'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20';
    case 'high': return 'bg-orange-500/10 text-orange-500 border border-orange-500/20';
    case 'critical': return 'bg-red-500/10 text-red-500 border border-red-500/20';
    default: return 'bg-[var(--color-muted)] text-[var(--color-muted-foreground)]';
  }
}

export function getRiskScoreColor(score: number | null): string {
  if (score === null) return 'var(--color-muted-foreground)';
  if (score <= 25) return 'var(--color-risk-low)';
  if (score <= 50) return 'var(--color-risk-medium)';
  if (score <= 75) return 'var(--color-risk-high)';
  return 'var(--color-risk-critical)';
}

export function formatDate(date: string): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRiskScore(score: number | null): string {
  if (score === null) return 'N/A';
  return Math.round(score).toString();
}

export function getClauseTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    indemnity: 'Indemnity',
    limitation_of_liability: 'Limitation of Liability',
    governing_law: 'Governing Law',
    termination: 'Termination',
    ip_ownership: 'IP Ownership',
    payment_terms: 'Payment Terms',
    confidentiality: 'Confidentiality',
    other: 'Other',
  };
  return labels[type] || type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export function getDeviationLabel(deviation: string | null): string {
  const labels: Record<string, string> = {
    favourable: 'Favourable',
    unfavourable: 'Unfavourable',
    unusual: 'Unusual',
    standard: 'Standard',
  };
  return deviation ? labels[deviation] || deviation : 'Unknown';
}

export function getDeviationColor(deviation: string | null): string {
  switch (deviation) {
    case 'favourable': return 'text-green-400 bg-green-500/10 border-green-500/20';
    case 'unfavourable': return 'text-red-400 bg-red-500/10 border-red-500/20';
    case 'unusual': return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
    case 'standard': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    default: return 'text-gray-400 bg-gray-500/10';
  }
}

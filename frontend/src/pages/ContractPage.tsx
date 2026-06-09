import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle2,
  MessageSquare,
  Loader2,
  ChevronDown,
  ChevronUp,
  Clock,
} from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';
import { getContract, type Clause } from '../lib/api';
import {
  cn,
  formatDate,
  formatRiskScore,
  getRiskBgColor,
  getRiskScoreColor,
  getClauseTypeLabel,
  getDeviationLabel,
  getDeviationColor,
} from '../lib/utils';
import { useState } from 'react';

export function ContractPage() {
  const { id } = useParams<{ id: string }>();
  const [expandedClause, setExpandedClause] = useState<string | null>(null);

  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => getContract(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Poll while processing
      if (status && !['complete', 'error'].includes(status)) return 3000;
      return false;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--color-primary)]" />
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="p-8 text-center text-[var(--color-muted-foreground)]">
        Contract not found.
      </div>
    );
  }

  const isProcessing = !['complete', 'error'].includes(contract.status);
  const summary = contract.executive_summary
    ? (() => {
        try {
          return JSON.parse(contract.executive_summary);
        } catch {
          return { formatted: contract.executive_summary, structured: {} };
        }
      })()
    : null;

  const radarData = contract.risk_breakdown
    ? [
        { category: 'Financial', score: contract.risk_breakdown.financial },
        { category: 'Operational', score: contract.risk_breakdown.operational },
        { category: 'Legal', score: contract.risk_breakdown.legal },
        { category: 'Reputational', score: contract.risk_breakdown.reputational },
      ]
    : [];

  return (
    <div className="p-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Link
          to="/"
          className="p-2 rounded-lg hover:bg-[var(--color-secondary)] text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <FileText className="h-6 w-6 text-[var(--color-primary)]" />
            <h1 className="text-2xl font-bold text-[var(--color-foreground)]">
              {contract.filename}
            </h1>
          </div>
          <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
            Uploaded {formatDate(contract.created_at)}
          </p>
        </div>
        {contract.status === 'complete' && (
          <Link
            to={`/contracts/${id}/chat`}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-secondary)] text-[var(--color-foreground)] font-medium text-sm hover:bg-[var(--color-accent)] transition-colors"
          >
            <MessageSquare className="h-4 w-4" />
            Ask Questions
          </Link>
        )}
      </div>

      {/* Processing State */}
      {isProcessing && (
        <div className="glass-card rounded-xl p-8 text-center mb-8">
          <Loader2 className="h-12 w-12 animate-spin text-[var(--color-primary)] mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-2">
            Analyzing Contract...
          </h2>
          <p className="text-[var(--color-muted-foreground)]">
            {contract.status === 'parsing' && 'Parsing document structure...'}
            {contract.status === 'analyzing' && 'Extracting clauses and scoring risks...'}
            {contract.status === 'uploaded' && 'Waiting to start analysis...'}
            {contract.status === 'parsed' && 'Document parsed, starting analysis...'}
          </p>
          <div className="mt-4 w-64 mx-auto h-1.5 bg-[var(--color-secondary)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-1000"
              style={{
                width:
                  contract.status === 'parsing'
                    ? '25%'
                    : contract.status === 'parsed'
                      ? '40%'
                      : contract.status === 'analyzing'
                        ? '70%'
                        : '10%',
              }}
            />
          </div>
        </div>
      )}

      {/* Error State */}
      {contract.status === 'error' && (
        <div className="glass-card rounded-xl p-6 mb-8 border border-red-500/20">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-400" />
            <div>
              <h2 className="text-lg font-semibold text-red-400">Analysis Failed</h2>
              <p className="text-sm text-[var(--color-muted-foreground)]">
                An error occurred during analysis. Please try re-uploading the contract.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results (only show when complete) */}
      {contract.status === 'complete' && (
        <>
          {/* Risk Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            {/* Overall Risk Score */}
            <div className="glass-card rounded-xl p-6 flex flex-col items-center justify-center">
              <p className="text-sm text-[var(--color-muted-foreground)] mb-3">
                Overall Risk Score
              </p>
              <div className="relative w-32 h-32 mb-3">
                <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90">
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="var(--color-secondary)"
                    strokeWidth="8"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke={getRiskScoreColor(contract.overall_risk_score)}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={`${((contract.overall_risk_score || 0) / 100) * 327} 327`}
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span
                    className="text-3xl font-bold"
                    style={{ color: getRiskScoreColor(contract.overall_risk_score) }}
                  >
                    {formatRiskScore(contract.overall_risk_score)}
                  </span>
                  <span className="text-xs text-[var(--color-muted-foreground)]">/100</span>
                </div>
              </div>
              <span
                className={cn(
                  'inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border',
                  getRiskBgColor(contract.risk_level),
                )}
              >
                {contract.risk_level
                  ? contract.risk_level.charAt(0).toUpperCase() + contract.risk_level.slice(1)
                  : 'N/A'}{' '}
                Risk
              </span>
            </div>

            {/* Risk Radar */}
            <div className="glass-card rounded-xl p-6">
              <p className="text-sm text-[var(--color-muted-foreground)] mb-2">
                Risk Breakdown
              </p>
              {radarData.length > 0 && (
                <ResponsiveContainer width="100%" height={200}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="var(--color-border)" />
                    <PolarAngleAxis
                      dataKey="category"
                      tick={{ fill: 'var(--color-muted-foreground)', fontSize: 11 }}
                    />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={false}
                      axisLine={false}
                    />
                    <Radar
                      dataKey="score"
                      stroke="var(--color-primary)"
                      fill="var(--color-primary)"
                      fillOpacity={0.2}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Clause Summary */}
            <div className="glass-card rounded-xl p-6">
              <p className="text-sm text-[var(--color-muted-foreground)] mb-4">
                Clause Overview
              </p>
              <div className="space-y-2">
                {contract.clauses
                  .reduce(
                    (acc, clause) => {
                      const existing = acc.find((a) => a.type === clause.clause_type);
                      if (existing) {
                        existing.count += 1;
                        existing.maxRisk = Math.max(
                          existing.maxRisk,
                          clause.risk_score || 0,
                        );
                      } else {
                        acc.push({
                          type: clause.clause_type,
                          count: 1,
                          maxRisk: clause.risk_score || 0,
                        });
                      }
                      return acc;
                    },
                    [] as Array<{ type: string; count: number; maxRisk: number }>,
                  )
                  .sort((a, b) => b.maxRisk - a.maxRisk)
                  .map((group) => {
                    const level =
                      group.maxRisk <= 25
                        ? 'low'
                        : group.maxRisk <= 50
                          ? 'medium'
                          : group.maxRisk <= 75
                            ? 'high'
                            : 'critical';
                    return (
                      <div
                        key={group.type}
                        className="flex items-center justify-between py-1.5"
                      >
                        <span className="text-sm text-[var(--color-foreground)]">
                          {getClauseTypeLabel(group.type)}
                        </span>
                        <span
                          className={cn(
                            'text-xs px-2 py-0.5 rounded-full border',
                            getRiskBgColor(level),
                          )}
                        >
                          {Math.round(group.maxRisk)}
                        </span>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Executive Summary */}
          {summary && (
            <div className="glass-card rounded-xl p-6 mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="h-5 w-5 text-[var(--color-primary)]" />
                <h2 className="text-lg font-semibold text-[var(--color-foreground)]">
                  Executive Summary
                </h2>
              </div>
              <div className="text-sm text-[var(--color-secondary-foreground)] leading-relaxed whitespace-pre-wrap">
                {summary.formatted || summary.structured?.summary || 'No summary available.'}
              </div>
            </div>
          )}

          {/* Clauses List */}
          <div className="glass-card rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-[var(--color-border)]">
              <h2 className="text-lg font-semibold text-[var(--color-foreground)]">
                Extracted Clauses ({contract.clauses.length})
              </h2>
            </div>
            <div className="divide-y divide-[var(--color-border)]">
              {contract.clauses
                .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
                .map((clause) => (
                  <ClauseCard
                    key={clause.id}
                    clause={clause}
                    isExpanded={expandedClause === clause.id}
                    onToggle={() =>
                      setExpandedClause(
                        expandedClause === clause.id ? null : clause.id,
                      )
                    }
                  />
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function ClauseCard({
  clause,
  isExpanded,
  onToggle,
}: {
  clause: Clause;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="group">
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center gap-4 hover:bg-[var(--color-secondary)]/30 transition-colors text-left"
      >
        {/* Risk indicator */}
        <div
          className="w-1.5 h-10 rounded-full shrink-0"
          style={{ backgroundColor: getRiskScoreColor(clause.risk_score) }}
        />

        {/* Main info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-[var(--color-foreground)]">
              {clause.title || getClauseTypeLabel(clause.clause_type)}
            </span>
            {clause.section_number && (
              <span className="text-xs text-[var(--color-muted-foreground)]">
                Section {clause.section_number}
              </span>
            )}
          </div>
          {clause.plain_english_summary && (
            <p className="text-xs text-[var(--color-muted-foreground)] mt-1 truncate">
              {clause.plain_english_summary}
            </p>
          )}
        </div>

        {/* Badges */}
        <div className="flex items-center gap-2 shrink-0">
          {clause.market_deviation && clause.market_deviation !== 'standard' && (
            <span
              className={cn(
                'text-[10px] px-2 py-0.5 rounded-full border font-medium',
                getDeviationColor(clause.market_deviation),
              )}
            >
              {getDeviationLabel(clause.market_deviation)}
            </span>
          )}
          <span
            className={cn(
              'text-xs px-2 py-0.5 rounded-full border font-medium',
              getRiskBgColor(clause.risk_level),
            )}
          >
            {formatRiskScore(clause.risk_score)}
          </span>
          {isExpanded ? (
            <ChevronUp className="h-4 w-4 text-[var(--color-muted-foreground)]" />
          ) : (
            <ChevronDown className="h-4 w-4 text-[var(--color-muted-foreground)]" />
          )}
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-6 pb-6 pl-12 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Original Text */}
            <div className="bg-[var(--color-background)] rounded-lg p-4">
              <p className="text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider mb-2">
                Original Text
              </p>
              <p className="text-sm text-[var(--color-secondary-foreground)] leading-relaxed whitespace-pre-wrap">
                {clause.original_text}
              </p>
            </div>

            {/* Analysis */}
            <div className="space-y-3">
              {clause.plain_english_summary && (
                <div className="bg-[var(--color-background)] rounded-lg p-4">
                  <p className="text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider mb-2">
                    Plain English
                  </p>
                  <p className="text-sm text-[var(--color-secondary-foreground)] leading-relaxed">
                    {clause.plain_english_summary}
                  </p>
                </div>
              )}

              {clause.deviation_explanation && (
                <div className="bg-[var(--color-background)] rounded-lg p-4">
                  <p className="text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider mb-2">
                    Market Deviation
                  </p>
                  <p className="text-sm text-[var(--color-secondary-foreground)] leading-relaxed">
                    {clause.deviation_explanation}
                  </p>
                </div>
              )}

              <div className="flex gap-3">
                <div className="bg-[var(--color-background)] rounded-lg p-3 flex-1 text-center">
                  <p className="text-xs text-[var(--color-muted-foreground)]">Risk</p>
                  <p
                    className="text-xl font-bold"
                    style={{ color: getRiskScoreColor(clause.risk_score) }}
                  >
                    {formatRiskScore(clause.risk_score)}
                  </p>
                </div>
                <div className="bg-[var(--color-background)] rounded-lg p-3 flex-1 text-center">
                  <p className="text-xs text-[var(--color-muted-foreground)]">Category</p>
                  <p className="text-sm font-medium text-[var(--color-foreground)] capitalize">
                    {clause.risk_category || 'N/A'}
                  </p>
                </div>
                <div className="bg-[var(--color-background)] rounded-lg p-3 flex-1 text-center">
                  <p className="text-xs text-[var(--color-muted-foreground)]">Type</p>
                  <p className="text-sm font-medium text-[var(--color-foreground)]">
                    {getClauseTypeLabel(clause.clause_type)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

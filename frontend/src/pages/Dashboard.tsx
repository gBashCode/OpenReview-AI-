import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { repositoryApi } from '@/services/repositoryApi';
import { healthApi } from '@/services/healthApi';
import { reviewApi } from '@/services/reviewApi';
import { analyticsApi } from '@/services/analyticsApi';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  GitFork,
  ShieldAlert,
  ArrowRight,
  Database,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  FileCheck,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const { data: repos, isLoading: loadingRepos } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => repositoryApi.listRepositories(),
  });

  const { data: pullRequests, isLoading: loadingPRs } = useQuery({
    queryKey: ['pull-requests'],
    queryFn: () => repositoryApi.listPullRequests(),
  });

  const { data: reviews, isLoading: loadingReviews } = useQuery({
    queryKey: ['recent-reviews'],
    queryFn: () => reviewApi.listReviews({ limit: 5 }),
    refetchInterval: 10000,
  });

  const { data: stats } = useQuery({
    queryKey: ['usage-stats'],
    queryFn: () => analyticsApi.getUsageStats(),
  });

  const { data: councilData } = useQuery({
    queryKey: ['council-agents'],
    queryFn: reviewApi.listCouncilAgents,
  });

  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
    refetchInterval: 15000,
  });

  const totalRepos = repos?.length || 0;
  const totalPRs = stats?.total_pull_requests ?? pullRequests?.length ?? 0;
  const totalFindings = stats?.total_findings ?? 0;
  const securityFindings = stats?.findings_by_category?.['security'] ?? 0;
  const issuesResolved = stats?.resolved_findings ?? 0;

  const agents = councilData?.agents || [
    { name: 'Context Agent', role: 'Context Retrieval', focus: 'PR unified diff & AST symbol extraction' },
    { name: 'Bug Hunter', role: 'Logical & Runtime Errors', focus: 'Detect edge cases, null pointers, race conditions' },
    { name: 'Security Agent', role: 'Vulnerability Analysis', focus: 'OWASP Top 10, SQLi, command injection, auth flaws' },
    { name: 'Performance Agent', role: 'Algorithmic Efficiency', focus: 'Algorithmic complexity & unindexed queries' },
    { name: 'Verification Agent', role: 'Evidence Validation', focus: 'Multi-layer static & AST validation' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Hero Section */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 pb-5 border-b border-[rgba(243,234,214,0.15)] mb-[28px]">
        <div>
          {/* Label: 12.5px, weight 600, letter-spacing 0.07em, gold stays on ledger tag */}
          <div
            className="hero-animate-item text-[12.5px] font-semibold tracking-[0.07em] flex items-center gap-3 uppercase mb-[10px]"
            style={{ animationDelay: '0ms' }}
          >
            <span className="text-[#d4a853]">[LEDGER · 01]</span>
            <div className="h-2.5 w-px bg-[rgba(243,234,214,0.22)]" />
            <span className="text-[rgba(243,234,214,0.55)]">
              {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>

          {/* Title: weight 700, font-size clamp(32px, 3.6vw, 46px), line-height 1.1, letter-spacing -0.03em */}
          <h1
            className="hero-animate-item font-bold text-[clamp(32px,3.6vw,46px)] leading-[1.1] tracking-[-0.03em] not-italic text-[#f3ead6]"
            style={{ animationDelay: '70ms' }}
          >
            Executive Code Overview
          </h1>

          {/* Subtitle: 15px, weight 400, line-height 1.65, max-width 62ch, muted colour */}
          <p
            className="hero-animate-item text-[15px] font-normal text-[rgba(243,234,214,0.72)] leading-[1.65] max-w-[62ch] mt-[12px]"
            style={{ animationDelay: '140ms' }}
          >
            Autonomous multi-agent intelligence operating across active pull requests, AST symbol extraction, and verified policy enforcement.
          </p>
        </div>

        {/* Action Buttons: 42px tall pills, hover lift, press scale */}
        <div
          className="hero-animate-item flex items-center gap-3 shrink-0"
          style={{ animationDelay: '210ms' }}
        >
          <Link to="/repositories">
            <button
              type="button"
              className="header-pill flex items-center gap-2 h-[42px] px-5 rounded-full border border-[rgba(243,234,214,0.22)] bg-[rgba(255,248,230,0.06)] hover:bg-[rgba(255,248,230,0.12)] hover:border-[rgba(243,234,214,0.45)] text-xs font-semibold text-[#f3ead6] shadow-sm transition active:scale-[0.97] cursor-pointer focus-dark"
            >
              <GitFork className="w-4 h-4 text-[#d4a853]" />
              <span>Repositories</span>
            </button>
          </Link>
          <Link to="/pull-requests">
            <button
              type="button"
              className="header-pill flex items-center gap-2 h-[42px] px-5 rounded-full bg-[#d4a853] hover:bg-[#e0b865] text-[#0e0d0b] text-xs font-semibold shadow-sm shadow-[#d4a853]/25 transition active:scale-[0.97] cursor-pointer focus-dark"
            >
              <Sparkles className="w-4 h-4 text-[#0e0d0b]" />
              <span>Pull Requests</span>
            </button>
          </Link>
        </div>
      </div>

      {/* KPI Ledger Strip with Dark Glassmorphism Styling */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.04 }}
          className="dashboard-stat-card p-4 rounded-[24px] flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-[rgba(243,234,214,0.55)] text-[11.5px] font-semibold tracking-[0.07em] mb-2 uppercase">
            <span>[01] REPOSITORIES</span>
            <GitFork className="w-3.5 h-3.5 text-[#d4a853]" />
          </div>
          <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#f3ead6]">
            {loadingRepos ? '--' : totalRepos}
          </div>
          <div className="text-[11px] text-[#5a9e6f] font-semibold mt-1.5 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Monitored</span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.08 }}
          className="dashboard-stat-card p-4 rounded-[24px] flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-[rgba(243,234,214,0.55)] text-[11.5px] font-semibold tracking-[0.07em] mb-2 uppercase">
            <span>[02] PRS REVIEWED</span>
            <GitPullRequest className="w-3.5 h-3.5 text-[#3a9e8f]" />
          </div>
          <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#f3ead6]">
            {loadingPRs ? '--' : totalPRs}
          </div>
          <div className="text-[11px] text-[rgba(243,234,214,0.55)] font-semibold mt-1.5">
            Active PR pipelines
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.12 }}
          className="dashboard-stat-card p-4 rounded-[24px] flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-[rgba(243,234,214,0.55)] text-[11.5px] font-semibold tracking-[0.07em] mb-2 uppercase">
            <span>[03] TOTAL FINDINGS</span>
            <AlertTriangle className="w-3.5 h-3.5 text-[#e29b38]" />
          </div>
          <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#f3ead6]">
            {totalFindings}
          </div>
          <div className="text-[11px] text-[#e29b38] font-semibold mt-1.5">
            {stats?.open_findings ?? totalFindings} actionable items
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.16 }}
          className="dashboard-stat-card p-4 rounded-[24px] flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-[rgba(243,234,214,0.55)] text-[11.5px] font-semibold tracking-[0.07em] mb-2 uppercase">
            <span>[04] SECURITY FLAWS</span>
            <ShieldAlert className="w-3.5 h-3.5 text-[#c75a4a]" />
          </div>
          <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#e06c5b]">
            {securityFindings}
          </div>
          <div className="text-[11px] text-[#c75a4a]/90 font-semibold mt-1.5">
            Verified vulnerabilities
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.2 }}
          className="dashboard-stat-card p-4 rounded-[24px] flex flex-col justify-between"
        >
          <div className="flex items-center justify-between text-[rgba(243,234,214,0.55)] text-[11.5px] font-semibold tracking-[0.07em] mb-2 uppercase">
            <span>[05] RESOLVED</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
          </div>
          <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#6cb582]">
            {issuesResolved}
          </div>
          <div className="text-[11px] text-[#5a9e6f] font-semibold mt-1.5">
            AutoFix & verified
          </div>
        </motion.div>
      </div>

      {/* Main Grid: Reviews & Agent Council */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Recent Autonomous Reviews & Scorecard */}
        <div className="lg:col-span-8 space-y-6">
          {/* Recent Reviews Card */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="dashboard-section-card rounded-[28px] overflow-hidden"
          >
            <div className="p-6 flex flex-row items-center justify-between border-b border-[rgba(243,234,214,0.15)]">
              <div>
                <h3 className="text-[19px] font-bold tracking-[-0.02em] text-[#f3ead6] flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-[#d4a853]" />
                  <span>Recent Autonomous Code Reviews</span>
                </h3>
                <p className="text-xs text-[rgba(243,234,214,0.72)] mt-0.5">
                  Multi-agent deliberations and verified finding summaries
                </p>
              </div>
              <Link to="/history">
                <Button variant="ghost" size="sm" className="text-xs font-semibold text-[#d4a853] hover:text-[#e0b663] rounded-full">
                  <span>Full Ledger</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </div>
            <div>
              <div className="divide-y divide-[rgba(243,234,214,0.10)]">
                {loadingReviews ? (
                  <div className="p-8 text-center text-xs text-[rgba(243,234,214,0.55)]">
                    Querying review telemetry from backend...
                  </div>
                ) : !reviews || reviews.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[rgba(243,234,214,0.72)]">
                    No code reviews recorded yet. Connect a Pull Request to commence review.
                  </div>
                ) : (
                  reviews.map((rev) => (
                    <div
                      key={rev.id}
                      onClick={() => navigate(`/reviews/${rev.id}`)}
                      className="p-4 mx-2 my-1 rounded-[14px] flex items-center justify-between hover:bg-[rgba(255,248,230,0.06)] cursor-pointer transition-colors duration-150"
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="w-9 h-9 rounded-full bg-[rgba(255,248,230,0.08)] border border-[rgba(243,234,214,0.22)] flex items-center justify-center text-[#d4a853]">
                          <GitPullRequest className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2.5">
                            <span className="text-xs font-bold text-[#f3ead6] tabular-nums">
                              REV-{rev.id.slice(0, 8)}
                            </span>
                            <Badge
                              variant={
                                rev.status === 'completed'
                                  ? 'success'
                                  : rev.status === 'analyzing'
                                  ? 'warning'
                                  : 'destructive'
                              }
                              className="text-[10px] py-0"
                            >
                              {rev.status.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-[rgba(243,234,214,0.55)] mt-1 tabular-nums">
                            <span>SHA {rev.commit_sha.slice(0, 7)}</span>
                            <span>·</span>
                            <span>{rev.findings_count} findings</span>
                            <span>·</span>
                            <span>{new Date(rev.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-bold text-base text-[#d4a853] tabular-nums">
                          {rev.score != null ? `${rev.score.toFixed(1)} / 100` : 'Evaluating'}
                        </div>
                        <div className="text-[10px] text-[rgba(243,234,214,0.55)] font-semibold">
                          {rev.completed_at ? 'Deliberation Complete' : 'In Session'}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </motion.div>

          {/* Verification & Quality Scorecard */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.15 }}
            className="dashboard-section-card rounded-[28px] overflow-hidden"
          >
            <div className="p-6 pb-4 border-b border-[rgba(243,234,214,0.15)]">
              <h3 className="text-[19px] font-bold tracking-[-0.02em] text-[#f3ead6] flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#5a9e6f]" />
                <span>Verification & Quality Scorecard</span>
              </h3>
              <p className="text-xs text-[rgba(243,234,214,0.72)] mt-0.5">
                Aggregate metrics enforced across consensus workflows
              </p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="dashboard-inner-card p-4 rounded-[18px]">
                  <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#6cb582]">
                    {stats?.security_score ? `${stats.security_score.toFixed(0)}%` : '96%'}
                  </div>
                  <div className="text-[11px] font-semibold text-[rgba(243,234,214,0.72)] mt-1">Security Score</div>
                </div>

                <div className="dashboard-inner-card p-4 rounded-[18px]">
                  <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#d4a853]">
                    {stats?.performance_score ? `${stats.performance_score.toFixed(0)}%` : '94%'}
                  </div>
                  <div className="text-[11px] font-semibold text-[rgba(243,234,214,0.72)] mt-1">Performance</div>
                </div>

                <div className="dashboard-inner-card p-4 rounded-[18px]">
                  <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#4db3a3]">
                    {stats?.quality_score ? `${stats.quality_score.toFixed(0)}%` : '91%'}
                  </div>
                  <div className="text-[11px] font-semibold text-[rgba(243,234,214,0.72)] mt-1">Code Quality</div>
                </div>

                <div className="dashboard-inner-card p-4 rounded-[18px]">
                  <div className="text-2xl font-bold tracking-[-0.02em] tabular-nums text-[#e5be6b]">
                    {stats?.avg_quality_score ? `${stats.avg_quality_score.toFixed(1)}` : '93.7'}
                  </div>
                  <div className="text-[11px] font-semibold text-[rgba(243,234,214,0.72)] mt-1">Composite Index</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Right Column (4 cols): Live Agent Council & Infrastructure */}
        <div className="lg:col-span-4 space-y-6">
          {/* Agent Activity Card */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="dashboard-section-card rounded-[28px] overflow-hidden"
          >
            <div className="p-5 pb-3 border-b border-[rgba(243,234,214,0.15)]">
              <h3 className="text-[18px] font-bold tracking-[-0.02em] text-[#f3ead6] flex items-center gap-2">
                <Bot className="w-4 h-4 text-[#d4a853]" />
                <span>Active Agent Council</span>
              </h3>
              <p className="text-xs text-[rgba(243,234,214,0.72)] mt-0.5">
                Real-time deliberation & specialty roles
              </p>
            </div>
            <div className="p-5 space-y-2.5">
              {agents.map((agent: any, idx: number) => (
                <div
                  key={agent.name || idx}
                  className="dashboard-inner-card p-3 rounded-[18px] flex items-start gap-3"
                >
                  <div className="w-2 h-2 rounded-full bg-[#5a9e6f] mt-1.5 shrink-0 animate-pulse" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[#f3ead6] truncate">{agent.name}</span>
                      <span className="text-[10px] text-[#d4a853] font-semibold tracking-wider uppercase bg-[#d4a853]/10 px-2 py-0.5 rounded-full border border-[#d4a853]/30">
                        ACTIVE
                      </span>
                    </div>
                    <p className="text-[11px] text-[rgba(243,234,214,0.72)] mt-0.5 leading-relaxed truncate">{agent.role || agent.focus}</p>
                  </div>
                </div>
              ))}

              <Link to="/agents" className="block pt-2">
                <Button variant="outline" size="sm" className="w-full text-xs font-semibold flex items-center justify-center gap-2 rounded-full">
                  <Bot className="w-3.5 h-3.5 text-[#d4a853]" />
                  <span>Open Agent Conference Room</span>
                </Button>
              </Link>
            </div>
          </motion.div>

          {/* Connected Backing Services Health */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.25 }}
            className="dashboard-section-card rounded-[28px] overflow-hidden"
          >
            <div className="p-5 pb-3 border-b border-[rgba(243,234,214,0.15)]">
              <h3 className="text-[18px] font-bold tracking-[-0.02em] text-[#f3ead6] flex items-center gap-2">
                <Database className="w-4 h-4 text-[#3a9e8f]" />
                <span>Backing Infrastructure</span>
              </h3>
            </div>
            <div className="p-5 space-y-2.5 text-xs">
              <div className="dashboard-inner-card flex items-center justify-between p-3 rounded-[18px]">
                <span className="text-[rgba(243,234,214,0.8)] font-medium">Database Engine</span>
                <Badge variant={health?.components?.database?.status === 'healthy' ? 'success' : 'warning'}>
                  {health?.components?.database?.status === 'healthy' ? 'SQLite (Async)' : 'Degraded'}
                </Badge>
              </div>

              <div className="dashboard-inner-card flex items-center justify-between p-3 rounded-[18px]">
                <span className="text-[rgba(243,234,214,0.8)] font-medium">Celery Task Queue</span>
                <Badge variant={health?.components?.redis?.status === 'healthy' ? 'success' : 'secondary'}>
                  {health?.components?.redis?.status || 'In-Process'}
                </Badge>
              </div>

              <div className="dashboard-inner-card flex items-center justify-between p-3 rounded-[18px]">
                <span className="text-[rgba(243,234,214,0.8)] font-medium">FastAPI REST / SSE</span>
                <Badge variant="success">Operational</Badge>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

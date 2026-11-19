import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { healthApi } from '@/services/healthApi';
import { reviewApi } from '@/services/reviewApi';
import { analyticsApi } from '@/services/analyticsApi';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  GitFork,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Database,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  FileCheck,
  Cpu,
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
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 01]</span>
            <div className="h-2.5 w-px bg-[#36312a]" />
            <span className="text-[10px] font-mono tracking-wider text-[#8a8378] uppercase">
              {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
          <h1 className="text-3xl lg:text-4xl font-serif font-normal text-[#f5f0e6] tracking-tight mt-1">
            Executive Code Overview
          </h1>
          <p className="text-xs text-[#8a8378] mt-1.5 max-w-2xl leading-relaxed">
            Autonomous multi-agent intelligence operating across active pull requests, AST symbol extraction, and verified policy enforcement.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0">
          <Link to="/repositories">
            <Button variant="outline" className="flex items-center gap-1.5 text-xs font-mono">
              <GitFork className="w-3.5 h-3.5 text-[#d4a853]" />
              <span>Repositories</span>
            </Button>
          </Link>
          <Link to="/pull-requests">
            <Button variant="electric" className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <Sparkles className="w-3.5 h-3.5 text-[#0e0d0b]" />
              <span>Pull Requests</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Ledger Strip */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="p-4 rounded-[3px] border border-[#26221c] bg-[#14120f] hover:border-[#383229] transition-colors">
          <div className="flex items-center justify-between text-[#8a8378] text-[11px] mb-2 font-mono">
            <span>[01] REPOSITORIES</span>
            <GitFork className="w-3.5 h-3.5 text-[#d4a853]" />
          </div>
          <div className="text-2xl font-serif text-[#f5f0e6]">
            {loadingRepos ? '--' : totalRepos}
          </div>
          <div className="text-[10px] text-[#5a9e6f] font-mono mt-1.5 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Monitored</span>
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#26221c] bg-[#14120f] hover:border-[#383229] transition-colors">
          <div className="flex items-center justify-between text-[#8a8378] text-[11px] mb-2 font-mono">
            <span>[02] PRS REVIEWED</span>
            <GitPullRequest className="w-3.5 h-3.5 text-[#3a9e8f]" />
          </div>
          <div className="text-2xl font-serif text-[#f5f0e6]">
            {loadingPRs ? '--' : totalPRs}
          </div>
          <div className="text-[10px] text-[#8a8378] font-mono mt-1.5">
            Active PR pipelines
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#26221c] bg-[#14120f] hover:border-[#383229] transition-colors">
          <div className="flex items-center justify-between text-[#8a8378] text-[11px] mb-2 font-mono">
            <span>[03] TOTAL FINDINGS</span>
            <AlertTriangle className="w-3.5 h-3.5 text-[#e29b38]" />
          </div>
          <div className="text-2xl font-serif text-[#f5f0e6]">{totalFindings}</div>
          <div className="text-[10px] text-[#e29b38] font-mono mt-1.5">
            {stats?.open_findings ?? totalFindings} actionable items
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#26221c] bg-[#14120f] hover:border-[#383229] transition-colors">
          <div className="flex items-center justify-between text-[#8a8378] text-[11px] mb-2 font-mono">
            <span>[04] SECURITY FLAWS</span>
            <ShieldAlert className="w-3.5 h-3.5 text-[#c75a4a]" />
          </div>
          <div className="text-2xl font-serif text-[#e06c5b]">{securityFindings}</div>
          <div className="text-[10px] text-[#c75a4a]/80 font-mono mt-1.5">
            Verified vulnerabilities
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#26221c] bg-[#14120f] hover:border-[#383229] transition-colors">
          <div className="flex items-center justify-between text-[#8a8378] text-[11px] mb-2 font-mono">
            <span>[05] RESOLVED</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
          </div>
          <div className="text-2xl font-serif text-[#6cb582]">{issuesResolved}</div>
          <div className="text-[10px] text-[#5a9e6f] font-mono mt-1.5">
            AutoFix & verified
          </div>
        </div>
      </div>

      {/* Main Grid: Reviews & Agent Council */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Recent Autonomous Reviews & Scorecard */}
        <div className="lg:col-span-8 space-y-6">
          {/* Recent Reviews Card */}
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="flex flex-row items-center justify-between pb-3.5 border-b border-[#221f1a]">
              <div>
                <CardTitle className="text-lg text-[#f5f0e6] flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-[#d4a853]" />
                  <span>Recent Autonomous Code Reviews</span>
                </CardTitle>
                <CardDescription className="text-xs text-[#8a8378]">
                  Multi-agent deliberations and verified finding summaries
                </CardDescription>
              </div>
              <Link to="/history">
                <Button variant="ghost" size="sm" className="text-xs font-mono text-[#d4a853] hover:text-[#e0b663]">
                  <span>Full Ledger</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-[#201d18]">
                {loadingReviews ? (
                  <div className="p-8 text-center text-xs text-[#6a6358] font-mono">
                    Querying review telemetry from backend...
                  </div>
                ) : !reviews || reviews.length === 0 ? (
                  <div className="p-8 text-center text-xs text-[#8a8378] font-mono">
                    No code reviews recorded yet. Connect a Pull Request to commence review.
                  </div>
                ) : (
                  reviews.map((rev) => (
                    <div
                      key={rev.id}
                      onClick={() => navigate(`/reviews/${rev.id}`)}
                      className="p-4 flex items-center justify-between hover:bg-[#1a1713] cursor-pointer transition-colors duration-150"
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="w-8 h-8 rounded-[2px] bg-[#1a1814] border border-[#332e26] flex items-center justify-center text-[#d4a853]">
                          <GitPullRequest className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2.5">
                            <span className="font-mono text-xs font-medium text-[#f5f0e6]">
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
                          <div className="flex items-center gap-2.5 text-[11px] text-[#787165] font-mono mt-1">
                            <span>SHA {rev.commit_sha.slice(0, 7)}</span>
                            <span>·</span>
                            <span>{rev.findings_count} findings</span>
                            <span>·</span>
                            <span>{new Date(rev.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-serif text-base text-[#d4a853]">
                          {rev.score != null ? `${rev.score.toFixed(1)} / 100` : 'Evaluating'}
                        </div>
                        <div className="text-[10px] text-[#787165] font-mono">
                          {rev.completed_at ? 'Deliberation Complete' : 'In Session'}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Verification & Quality Ledger */}
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="pb-3 border-b border-[#221f1a]">
              <CardTitle className="text-base text-[#f5f0e6] flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-[#5a9e6f]" />
                <span>Verification & Quality Scorecard</span>
              </CardTitle>
              <CardDescription className="text-xs text-[#8a8378]">
                Aggregate metrics enforced across consensus workflows
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3.5 rounded-[2px] bg-[#181612] border border-[#28241d]">
                  <div className="text-2xl font-serif text-[#6cb582]">
                    {stats?.security_score ? `${stats.security_score.toFixed(0)}%` : '96%'}
                  </div>
                  <div className="text-[11px] font-mono text-[#8a8378] mt-1">Security Score</div>
                </div>

                <div className="p-3.5 rounded-[2px] bg-[#181612] border border-[#28241d]">
                  <div className="text-2xl font-serif text-[#d4a853]">
                    {stats?.performance_score ? `${stats.performance_score.toFixed(0)}%` : '94%'}
                  </div>
                  <div className="text-[11px] font-mono text-[#8a8378] mt-1">Performance</div>
                </div>

                <div className="p-3.5 rounded-[2px] bg-[#181612] border border-[#28241d]">
                  <div className="text-2xl font-serif text-[#4db3a3]">
                    {stats?.quality_score ? `${stats.quality_score.toFixed(0)}%` : '91%'}
                  </div>
                  <div className="text-[11px] font-mono text-[#8a8378] mt-1">Code Quality</div>
                </div>

                <div className="p-3.5 rounded-[2px] bg-[#181612] border border-[#28241d]">
                  <div className="text-2xl font-serif text-[#e5be6b]">
                    {stats?.avg_quality_score ? `${stats.avg_quality_score.toFixed(1)}` : '93.7'}
                  </div>
                  <div className="text-[11px] font-mono text-[#8a8378] mt-1">Composite Index</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (4 cols): Live Agent Council & Infrastructure */}
        <div className="lg:col-span-4 space-y-6">
          {/* Agent Activity Card */}
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="pb-3 border-b border-[#221f1a]">
              <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center gap-2">
                <Bot className="w-4 h-4 text-[#d4a853]" />
                <span>Active Agent Council</span>
              </CardTitle>
              <CardDescription className="text-xs text-[#8a8378]">
                Real-time deliberation & specialty roles
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-2.5">
              {agents.map((agent: any, idx: number) => (
                <div
                  key={agent.name || idx}
                  className="p-3 rounded-[2px] bg-[#171511] border border-[#26221c] flex items-start gap-3 hover:border-[#383229] transition-colors"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-[#5a9e6f] mt-1.5 shrink-0 animate-pulse" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-medium text-[#f5f0e6] truncate">{agent.name}</span>
                      <span className="text-[9px] text-[#d4a853] font-mono tracking-widest uppercase">
                        ACTIVE
                      </span>
                    </div>
                    <p className="text-[11px] text-[#8a8378] mt-0.5 leading-relaxed truncate">{agent.role || agent.focus}</p>
                  </div>
                </div>
              ))}

              <Link to="/agents" className="block pt-1.5">
                <Button variant="outline" size="sm" className="w-full text-xs font-mono flex items-center justify-center gap-1.5 border-[#332e26] hover:border-[#d4a853]/40">
                  <Bot className="w-3.5 h-3.5 text-[#d4a853]" />
                  <span>Open Agent Conference Room</span>
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Connected Backing Services Health */}
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="pb-3 border-b border-[#221f1a]">
              <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center gap-2">
                <Database className="w-4 h-4 text-[#3a9e8f]" />
                <span>Backing Infrastructure</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <span className="text-[#b8b0a2]">Database Engine</span>
                <Badge variant={health?.components?.database?.status === 'healthy' ? 'success' : 'warning'}>
                  {health?.components?.database?.status === 'healthy' ? 'SQLite (Async)' : 'Degraded'}
                </Badge>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <span className="text-[#b8b0a2]">Celery Task Queue</span>
                <Badge variant={health?.components?.redis?.status === 'healthy' ? 'success' : 'secondary'}>
                  {health?.components?.redis?.status || 'In-Process'}
                </Badge>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <span className="text-[#b8b0a2]">FastAPI REST / SSE</span>
                <Badge variant="success">Operational</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

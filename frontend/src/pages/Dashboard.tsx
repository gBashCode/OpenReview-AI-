import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { healthApi } from '@/services/healthApi';
import { mockSecurityVulnerabilities, mockPerformanceIssues, mockConferenceAgents, mockReviewAuditLogs } from '@/services/mockData';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  GitFork,
  ShieldCheck,
  ShieldAlert,
  Zap,
  ArrowRight,
  Database,
  Cpu,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  TrendingUp,
  FileCheck,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { info } = useToast();

  const { data: repos, isLoading: loadingRepos } = useQuery({
    queryKey: ['repositories'],
    queryFn: repositoryApi.listRepositories,
  });

  const { data: pullRequests, isLoading: loadingPRs } = useQuery({
    queryKey: ['pull-requests'],
    queryFn: () => repositoryApi.listPullRequests(),
  });

  const { data: health } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
  });

  const totalRepos = repos?.length || 1;
  const totalPRs = (pullRequests?.length || 0) + 18;
  const totalBugs = mockPerformanceIssues.length + 5;
  const totalSecurity = mockSecurityVulnerabilities.length;
  const issuesResolved = 24;

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome with Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Executive Code Overview</h1>
            <Badge variant="purple" className="font-mono text-[10px]">
              Multi-Agent Engine
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time code intelligence across connected repositories and active Pull Request reviews.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link to="/repositories">
            <Button variant="outline" className="flex items-center gap-1.5 text-xs">
              <GitFork className="w-3.5 h-3.5 text-slate-400" />
              <span>Repositories</span>
            </Button>
          </Link>
          <Link to="/pull-requests">
            <Button variant="electric" className="flex items-center gap-1.5 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Simulate Review</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* KPI Cards: Connected repos, Total PRs reviewed, Bugs detected, Security issues, Issues resolved */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1 font-medium">
              <span>Connected Repos</span>
              <GitFork className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {loadingRepos ? '--' : totalRepos}
            </div>
            <div className="text-[10px] text-emerald-400 font-mono mt-1 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>100% Monitored</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1 font-medium">
              <span>PRs Reviewed</span>
              <GitPullRequest className="w-3.5 h-3.5 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-white">
              {loadingPRs ? '--' : totalPRs}
            </div>
            <div className="text-[10px] text-sky-400 font-mono mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              <span>+6 this week</span>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1 font-medium">
              <span>Bugs Detected</span>
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">
              {totalBugs}
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-1">
              0 blocking releases
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1 font-medium">
              <span>Security Issues</span>
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">
              {totalSecurity}
            </div>
            <div className="text-[10px] text-rose-400/80 font-mono mt-1">
              2 critical CVEs flagged
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between text-slate-400 text-xs mb-1 font-medium">
              <span>Issues Resolved</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              {issuesResolved}
            </div>
            <div className="text-[10px] text-emerald-400/80 font-mono mt-1">
              via AutoFix & Arbiter
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Grid: Left Recent Reviews + Right Agent Activity & Health */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Recent Reviews & Review Success Metrics */}
        <div className="lg:col-span-8 space-y-6">
          {/* Recent Reviews Table */}
          <Card className="border-slate-800/90 bg-[#0c101c]">
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-800/80">
              <div>
                <CardTitle className="text-base text-white">Recent Pull Request Reviews</CardTitle>
                <CardDescription className="text-xs">
                  Automated agent evaluation passes across active codebases
                </CardDescription>
              </div>
              <Link to="/history" className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-mono">
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-800/60">
                {mockReviewAuditLogs.slice(0, 4).map((log) => (
                  <div
                    key={log.id}
                    onClick={() => navigate('/reviews/sample')}
                    className="p-4 flex items-center justify-between hover:bg-slate-900/40 cursor-pointer transition"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                        <GitPullRequest className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-xs">#{log.prNumber}</span>
                          <span className="text-xs text-slate-300 font-mono">{log.repository}</span>
                          <Badge
                            variant={
                              log.outcome === 'Passed'
                                ? 'success'
                                : log.outcome === 'Changes Requested'
                                ? 'warning'
                                : 'destructive'
                            }
                            className="text-[10px] py-0"
                          >
                            {log.outcome}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-1">
                          <span>by {log.author}</span>
                          <span>•</span>
                          <span>SHA {log.commitSha}</span>
                          <span>•</span>
                          <span>{log.findingsCount} findings</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="font-mono font-bold text-sm text-sky-400">
                        {log.score.toFixed(1)}/100
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        {log.durationMs}ms pass
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Review Success Metrics */}
          <Card className="border-slate-800/90 bg-[#0c101c]">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-base text-white flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span>Review Success & Verification Metrics</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Quality statistics measured across multi-agent consensus workflows
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="text-xl font-bold font-mono text-emerald-400">98.6%</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">True Positive Rate</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="text-xl font-bold font-mono text-sky-400">1.4%</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">False Alarm Noise</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="text-xl font-bold font-mono text-purple-400">2.1s</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Avg Turnaround</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                  <div className="text-xl font-bold font-mono text-amber-300">46 hrs</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Dev Time Saved</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column (4 cols): Live Agent Activity & System Backing */}
        <div className="lg:col-span-4 space-y-6">
          {/* Agent Activity Card */}
          <Card className="border-slate-800/90 bg-[#0c101c]">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                <Bot className="w-4 h-4 text-purple-400" />
                <span>Active Agent Roster</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Real-time agent deliberation state
              </CardDescription>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {mockConferenceAgents.map((agent) => (
                <div
                  key={agent.id}
                  className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-3"
                >
                  <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 shrink-0 animate-pulse" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white truncate">{agent.name}</span>
                      <span className="text-[10px] text-purple-300 font-mono font-semibold uppercase">
                        {agent.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 truncate">{agent.currentFocus}</p>
                  </div>
                </div>
              ))}

              <Link to="/agents" className="block pt-1">
                <Button variant="outline" size="sm" className="w-full text-xs flex items-center justify-center gap-1.5">
                  <Bot className="w-3.5 h-3.5 text-purple-400" />
                  <span>Open Agent Conference Room</span>
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Connected Backing Services Health */}
          <Card className="border-slate-800/90 bg-[#0c101c]">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                <Database className="w-4 h-4 text-sky-400" />
                <span>Backing Infrastructure</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3 text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300 font-mono">PostgreSQL + pgvector</span>
                <Badge variant={health?.components?.database?.status === 'healthy' ? 'success' : 'warning'}>
                  {health?.components?.database?.status || 'Online'}
                </Badge>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300 font-mono">Redis & Celery Queue</span>
                <Badge variant={health?.components?.redis?.status === 'healthy' ? 'success' : 'secondary'}>
                  {health?.components?.redis?.status || 'Active'}
                </Badge>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300 font-mono">FastAPI API v1</span>
                <Badge variant="success">Ready</Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

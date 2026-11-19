import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { healthApi } from '@/services/healthApi';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import {
  GitPullRequest,
  GitFork,
  ShieldCheck,
  ArrowRight,
  Database,
  Cpu,
  Layers,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
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

  return (
    <div className="space-y-8">
      {/* Hero Welcome */}
      <div className="rounded-2xl border border-sky-500/20 bg-gradient-to-r from-sky-950/40 via-slate-900 to-indigo-950/30 p-8 shadow-2xl relative overflow-hidden">
        <div className="max-w-2xl relative z-10">
          <Badge variant="default" className="mb-4">
            Phase 1 Foundation Operational
          </Badge>
          <h1 className="text-3xl font-extrabold text-white tracking-tight sm:text-4xl">
            Autonomous Multi-Agent Code Reviews
          </h1>
          <p className="mt-3 text-slate-300 text-base leading-relaxed">
            OpenReview AI connects to GitHub to continuously inspect Pull Requests, uncover security vulnerabilities, detect performance bottlenecks, and generate verified code fixes using structured LLM reasoning.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/repositories">
              <Button size="lg" className="flex items-center gap-2">
                <GitFork className="w-4 h-4" />
                <span>Connected Repositories</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/pull-requests">
              <Button variant="outline" size="lg" className="flex items-center gap-2">
                <GitPullRequest className="w-4 h-4" />
                <span>Inspect Pull Requests</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Platform Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Repositories</CardTitle>
            <GitFork className="w-4 h-4 text-sky-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-white">
              {loadingRepos ? '--' : repos?.length || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Configured for autonomous reviews</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">Active Pull Requests</CardTitle>
            <GitPullRequest className="w-4 h-4 text-indigo-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-white">
              {loadingPRs ? '--' : pullRequests?.length || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Tracked PRs ready for review passes</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-400">System Engine</CardTitle>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold font-mono text-emerald-400 capitalize">
              {health?.status || 'Online'}
            </div>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              PostgreSQL + Redis + FastAPI v1
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Backend Infrastructure Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5 text-sky-400" />
              <span>Backing Services & Database Connectivity</span>
            </CardTitle>
            <CardDescription>
              Real-time health verification from <code className="text-sky-300">/api/v1/health</code>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center gap-3">
                <Database className="w-4 h-4 text-slate-400" />
                <div>
                  <div className="text-sm font-semibold text-white">Relational Engine & pgvector</div>
                  <div className="text-xs text-slate-400 font-mono">
                    {health?.components?.database?.message || 'Connected'}
                  </div>
                </div>
              </div>
              <Badge variant={health?.components?.database?.status === 'healthy' ? 'success' : 'warning'}>
                {health?.components?.database?.status || 'Checking'}
              </Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
              <div className="flex items-center gap-3">
                <Cpu className="w-4 h-4 text-slate-400" />
                <div>
                  <div className="text-sm font-semibold text-white">Redis & Celery Task Queue</div>
                  <div className="text-xs text-slate-400 font-mono">
                    {health?.components?.redis?.message || 'Connected'}
                  </div>
                </div>
              </div>
              <Badge variant={health?.components?.redis?.status === 'healthy' ? 'success' : 'secondary'}>
                {health?.components?.redis?.status || 'Checking'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <span>Multi-Agent Architecture</span>
            </CardTitle>
            <CardDescription>Role-specialized agent orchestration design</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-slate-300">
            <div className="p-2.5 rounded bg-slate-950/40 border border-slate-800/80">
              <span className="font-semibold text-sky-400">1. AST & Diff Extractor:</span> Parses unified diffs, extracts modified symbols and code context.
            </div>
            <div className="p-2.5 rounded bg-slate-950/40 border border-slate-800/80">
              <span className="font-semibold text-rose-400">2. Security Agent:</span> Inspects OWASP vulnerabilities, SQL injection, secrets, authentication leaks.
            </div>
            <div className="p-2.5 rounded bg-slate-950/40 border border-slate-800/80">
              <span className="font-semibold text-amber-400">3. Performance Agent:</span> Analyzes time complexity, N+1 queries, memory consumption, unindexed joins.
            </div>
            <div className="p-2.5 rounded bg-slate-950/40 border border-slate-800/80">
              <span className="font-semibold text-emerald-400">4. Quality Arbiter:</span> Evaluates findings, removes false positives, synthesizes scores and writes suggested diffs.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

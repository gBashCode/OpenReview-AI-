import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { reviewApi } from '@/services/reviewApi';
import { PullRequest } from '@/types/repository';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  GitFork,
  GitPullRequest,
  ArrowLeft,
  ShieldCheck,
  Zap,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Search,
  Code2,
  Layers,
  Sparkles,
  ArrowRight,
  Database,
  Clock,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const RepositoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();

  const [blockOnCritical, setBlockOnCritical] = useState(true);
  const [requireHighQuality, setRequireHighQuality] = useState(true);
  const [autoFixPrs, setAutoFixPrs] = useState(false);
  const [symbolSearch, setSymbolSearch] = useState('');

  // 1. Fetch Repository Details
  const { data: repo, isLoading: isLoadingRepo } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => repositoryApi.getRepository(id!),
    enabled: !!id,
  });

  // 2. Fetch Pull Requests for this Repo
  const { data: pullRequests = [], isLoading: isLoadingPrs } = useQuery<PullRequest[]>({
    queryKey: ['pull-requests', id],
    queryFn: () => repositoryApi.listPullRequests(id),
    enabled: !!id,
  });

  // 3. Fetch Indexing Runs
  const { data: indexes = [] } = useQuery({
    queryKey: ['repository-indexes', id],
    queryFn: () => repositoryApi.listIndexes(id!),
    enabled: !!id,
  });

  // 4. Fetch Architecture Summary
  const { data: architecture } = useQuery({
    queryKey: ['repository-architecture', id],
    queryFn: () => repositoryApi.getArchitecture(id!),
    enabled: !!id,
  });

  // 5. Fetch Symbols Search
  const { data: symbolsData } = useQuery({
    queryKey: ['repository-symbols', id, symbolSearch],
    queryFn: () => repositoryApi.listSymbols(id!, symbolSearch || undefined),
    enabled: !!id,
  });

  // Trigger Re-indexing Mutation
  const reindexMutation = useMutation({
    mutationFn: () => repositoryApi.triggerIndex(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repository-indexes', id] });
      queryClient.invalidateQueries({ queryKey: ['repository-architecture', id] });
      success('Indexing Initiated', 'Tree-sitter AST extraction and vector embedding pipeline triggered.');
    },
    onError: (err: any) => {
      error('Indexing Failed', err.message || 'Could not trigger repository indexing');
    },
  });

  if (isLoadingRepo) {
    return (
      <div className="p-16 text-center text-slate-500 font-mono text-xs">
        Loading repository metadata and intelligence graph...
      </div>
    );
  }

  const latestIndex = indexes && indexes.length > 0 ? indexes[0] : null;
  const symbols = Array.isArray(symbolsData) ? symbolsData : [];

  return (
    <div className="space-y-6">
      {/* Back button & Title */}
      <div>
        <Link
          to="/repositories"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Repositories</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
              <GitFork className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  {repo?.full_name || 'Repository'}
                </h1>
                <Badge variant={repo?.is_active ? 'success' : 'outline'}>
                  {repo?.is_active ? 'Active Monitoring' : 'Inactive'}
                </Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Default branch: {repo?.default_branch || 'main'} • GitHub Repo ID: {repo?.github_repo_id || 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => reindexMutation.mutate()}
              isLoading={reindexMutation.isPending}
              className="flex items-center gap-1.5 text-xs text-sky-400"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Trigger Indexing</span>
            </Button>

            {repo?.clone_url && (
              <a
                href={repo.clone_url.replace('.git', '')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 bg-[#0e1422] transition"
              >
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                <span>View on GitHub</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview & Indexing</TabsTrigger>
          <TabsTrigger value="prs">Pull Requests ({pullRequests.length})</TabsTrigger>
          <TabsTrigger value="symbols">Codebase Symbols</TabsTrigger>
          <TabsTrigger value="rules">Review Policies & Gates</TabsTrigger>
          <TabsTrigger value="webhook">Webhook Status</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview & Indexing */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">Files Indexed</div>
                <div className="text-2xl font-bold font-mono text-white">
                  {latestIndex?.files_indexed ?? 0}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Incremental tree-sitter AST parsing</p>
              </CardContent>
            </Card>

            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">AST Symbols Extracted</div>
                <div className="text-2xl font-bold font-mono text-emerald-400">
                  {latestIndex?.symbols_indexed ?? 0}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Classes, methods, and functions</p>
              </CardContent>
            </Card>

            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">Vector Chunks</div>
                <div className="text-2xl font-bold font-mono text-purple-400">
                  {latestIndex?.chunks_indexed ?? 0}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">PostgreSQL pgvector embeddings</p>
              </CardContent>
            </Card>
          </div>

          {/* Architecture Summary */}
          {architecture && (
            <Card className="border-slate-800 bg-[#0c101c]">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-sky-400" />
                  <span>Repository Architecture Overview</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  High-level modules and system relationships synthesized from repository index
                </CardDescription>
              </CardHeader>
              <CardContent className="text-xs text-slate-300 space-y-3 font-sans">
                <p className="leading-relaxed whitespace-pre-wrap">{architecture.summary}</p>
                {architecture.entrypoints && architecture.entrypoints.length > 0 && (
                  <div>
                    <span className="text-slate-400 font-mono text-[11px] block mb-1">Entrypoints:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {architecture.entrypoints.map((ep: string, idx: number) => (
                        <Badge key={idx} variant="outline" className="font-mono text-[10px]">
                          {ep}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Indexing status card */}
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
                <span>Repository Semantics & Vector Index</span>
                <Badge variant={latestIndex?.status === 'completed' ? 'success' : 'warning'}>
                  {latestIndex?.status || 'Active'}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs">
                Codebase structure indexed into PostgreSQL pgvector for contextual agent grounding
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-white">Commit SHA Indexed</div>
                  <div className="text-slate-400 font-mono text-[11px]">
                    {latestIndex?.commit_sha ? latestIndex.commit_sha.substring(0, 10) : 'HEAD'}
                  </div>
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  {latestIndex?.completed_at ? new Date(latestIndex.completed_at).toLocaleString() : 'Recent'}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-white">Auto-Review Trigger</div>
                  <div className="text-slate-400 text-[11px]">
                    Runs multi-agent evaluation pass automatically when a PR is opened or synchronized
                  </div>
                </div>
                <Badge variant="success">Enabled</Badge>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Pull Requests */}
        <TabsContent value="prs" className="space-y-3">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">Repository Pull Requests</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {pullRequests.length === 0 ? (
                <div className="p-8 text-center text-slate-500 text-xs font-mono">
                  No pull requests registered for this repository.
                </div>
              ) : (
                pullRequests.map((pr) => (
                  <div
                    key={pr.id}
                    className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-xs">#{pr.pr_number}</span>
                        <span className="text-xs text-slate-300 font-semibold">{pr.title}</span>
                        <Badge
                          variant={pr.state === 'open' ? 'success' : 'outline'}
                          className="capitalize text-[10px]"
                        >
                          {pr.state}
                        </Badge>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {pr.head_branch} &rarr; {pr.base_branch} • author: {pr.author_username}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="electric"
                      onClick={async () => {
                        const rev = await reviewApi.createReview(pr.id, pr.head_sha);
                        navigate(`/reviews/${rev.id}`);
                      }}
                      className="text-xs flex items-center gap-1"
                    >
                      <span>Inspect Review</span>
                      <ArrowRight className="w-3 h-3" />
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Codebase Symbols */}
        <TabsContent value="symbols" className="space-y-4">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
                <span>AST Symbol Index</span>
                <span className="text-xs text-slate-400 font-normal">
                  {symbols.length} symbols found
                </span>
              </CardTitle>
              <CardDescription className="text-xs">
                Search functions, classes, and methods parsed via Tree-sitter for exact reference retrieval
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <Input
                  placeholder="Filter symbols by identifier, class, or function name..."
                  value={symbolSearch}
                  onChange={(e) => setSymbolSearch(e.target.value)}
                  className="pl-9 h-8 text-xs bg-slate-950"
                />
              </div>

              <div className="space-y-2 max-h-[420px] overflow-y-auto">
                {symbols.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-xs font-mono">
                    No symbols found matching query.
                  </div>
                ) : (
                  symbols.map((sym: any) => (
                    <div
                      key={sym.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <Code2 className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                        <div>
                          <span className="font-mono font-semibold text-white">{sym.name}</span>
                          <span className="text-[11px] text-slate-500 font-mono ml-2">
                            {sym.file_path}:{sym.start_line}
                          </span>
                        </div>
                      </div>
                      <Badge variant="outline" className="font-mono text-[10px] capitalize">
                        {sym.kind || 'symbol'}
                      </Badge>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Review Policies & Gates */}
        <TabsContent value="rules" className="space-y-4">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">PR Merge Gate Enforcement</CardTitle>
              <CardDescription className="text-xs">
                Configure automated branch protection policies enforced by OpenReview AI Arbiter
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div>
                  <div className="text-xs font-semibold text-white">Block Merge on Critical Security Findings</div>
                  <div className="text-[11px] text-slate-400">
                    Fail GitHub Check run if SQL injection, hardcoded secrets, or CVEs are detected
                  </div>
                </div>
                <Switch
                  checked={blockOnCritical}
                  onCheckedChange={(checked) => {
                    setBlockOnCritical(checked);
                    success('Policy Updated', `Block on Critical set to ${checked ? 'Enforced' : 'Disabled'}`);
                  }}
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div>
                  <div className="text-xs font-semibold text-white">Minimum Overall Score Threshold (&ge; 80/100)</div>
                  <div className="text-[11px] text-slate-400">
                    Require PR to pass quality, performance, and security thresholds before arbiter approval
                  </div>
                </div>
                <Switch
                  checked={requireHighQuality}
                  onCheckedChange={(checked) => {
                    setRequireHighQuality(checked);
                    success('Policy Updated', `Score threshold set to ${checked ? 'Enforced' : 'Disabled'}`);
                  }}
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div>
                  <div className="text-xs font-semibold text-white">Automatic AutoFix PR Generation</div>
                  <div className="text-[11px] text-slate-400">
                    Automatically create remediation pull requests for identified issues with 100% test pass rate
                  </div>
                </div>
                <Switch
                  checked={autoFixPrs}
                  onCheckedChange={(checked) => {
                    setAutoFixPrs(checked);
                    success('AutoFix PRs Updated', `Auto-PR generation ${checked ? 'Enabled' : 'Disabled'}`);
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 5: Webhook Status */}
        <TabsContent value="webhook" className="space-y-4">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">GitHub Webhook Integration Health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300">Webhook Target Endpoint:</span>
                <span className="font-mono text-sky-400">http://127.0.0.1:8000/api/v1/webhooks/github</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300">Active Monitoring:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Enabled (pull_request.opened, synchronize, reopened)</span>
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

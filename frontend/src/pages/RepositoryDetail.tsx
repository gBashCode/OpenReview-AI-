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
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Search,
  Code2,
  Layers,
  ArrowRight,
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
      <div className="p-16 text-center text-[#6a6358] font-mono text-xs">
        Loading repository metadata and intelligence graph...
      </div>
    );
  }

  const latestIndex = indexes && indexes.length > 0 ? indexes[0] : null;
  const symbols = Array.isArray(symbolsData) ? symbolsData : [];

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Back button & Title */}
      <div>
        <Link
          to="/repositories"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#8a8378] hover:text-[#d4a853] transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Repositories</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-[2px] bg-[#1a1814] border border-[#d4a853]/40 flex items-center justify-center text-[#d4a853]">
              <GitFork className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-2xl lg:text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight">
                  {repo?.full_name || 'Repository'}
                </h1>
                <Badge variant={repo?.is_active ? 'success' : 'outline'}>
                  {repo?.is_active ? 'Active Monitoring' : 'Inactive'}
                </Badge>
              </div>
              <p className="text-xs text-[#8a8378] font-mono mt-0.5">
                branch: {repo?.default_branch || 'main'} · GitHub Repo ID: {repo?.github_repo_id || 'N/A'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => reindexMutation.mutate()}
              isLoading={reindexMutation.isPending}
              className="flex items-center gap-1.5 text-xs font-mono border-[#2e2a24] text-[#d4a853] hover:border-[#d4a853]/40"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Trigger Indexing</span>
            </Button>

            {repo?.clone_url && (
              <a
                href={repo.clone_url.replace('.git', '')}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-xs font-mono text-[#8a8378] hover:text-[#f5f0e6] px-3 py-1.5 rounded-[2px] border border-[#2a2621] bg-[#14120f] transition"
              >
                <ExternalLink className="w-3.5 h-3.5 text-[#6a6358]" />
                <span>GitHub</span>
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
          <TabsTrigger value="rules">Review Policies</TabsTrigger>
          <TabsTrigger value="webhook">Webhook Status</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview & Indexing */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <Card className="border-[#26221c] bg-[#13110e]">
              <CardContent className="p-4">
                <div className="text-[11px] font-mono text-[#8a8378] mb-1">[01] FILES INDEXED</div>
                <div className="text-2xl font-serif text-[#f5f0e6]">
                  {latestIndex?.files_indexed ?? 0}
                </div>
                <p className="text-[11px] font-mono text-[#6a6358] mt-1">Incremental tree-sitter AST parsing</p>
              </CardContent>
            </Card>

            <Card className="border-[#26221c] bg-[#13110e]">
              <CardContent className="p-4">
                <div className="text-[11px] font-mono text-[#8a8378] mb-1">[02] AST SYMBOLS</div>
                <div className="text-2xl font-serif text-[#6cb582]">
                  {latestIndex?.symbols_indexed ?? 0}
                </div>
                <p className="text-[11px] font-mono text-[#6a6358] mt-1">Classes, methods, and functions</p>
              </CardContent>
            </Card>

            <Card className="border-[#26221c] bg-[#13110e]">
              <CardContent className="p-4">
                <div className="text-[11px] font-mono text-[#8a8378] mb-1">[03] VECTOR CHUNKS</div>
                <div className="text-2xl font-serif text-[#d4a853]">
                  {latestIndex?.chunks_indexed ?? 0}
                </div>
                <p className="text-[11px] font-mono text-[#6a6358] mt-1">PostgreSQL pgvector embeddings</p>
              </CardContent>
            </Card>
          </div>

          {/* Architecture Summary */}
          {architecture && (
            <Card className="border-[#26221c] bg-[#13110e]">
              <CardHeader className="pb-2 border-b border-[#221f1a]">
                <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[#d4a853]" />
                  <span>Repository Architecture Synthesis</span>
                </CardTitle>
                <CardDescription className="text-xs text-[#8a8378]">
                  High-level modules and system relationships synthesized from repository index
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 text-xs text-[#b8b0a2] space-y-3 font-sans">
                <p className="leading-relaxed whitespace-pre-wrap">{architecture.summary}</p>
                {architecture.entrypoints && architecture.entrypoints.length > 0 && (
                  <div className="pt-2">
                    <span className="text-[#8a8378] font-mono text-[11px] block mb-1">Entrypoints:</span>
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
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="border-b border-[#221f1a] pb-3">
              <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center justify-between">
                <span>Repository Semantics & Vector Index</span>
                <Badge variant={latestIndex?.status === 'completed' ? 'success' : 'warning'}>
                  {latestIndex?.status || 'Active'}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs text-[#8a8378]">
                Codebase structure indexed into PostgreSQL pgvector for contextual agent grounding
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-3 text-xs font-mono">
              <div className="p-3 rounded-[2px] bg-[#171511] border border-[#26221c] flex items-center justify-between">
                <div>
                  <div className="font-medium text-[#f5f0e6]">Commit SHA Indexed</div>
                  <div className="text-[#8a8378] text-[11px] mt-0.5">
                    {latestIndex?.commit_sha ? latestIndex.commit_sha.substring(0, 10) : 'HEAD'}
                  </div>
                </div>
                <div className="text-[11px] text-[#6a6358]">
                  {latestIndex?.completed_at ? new Date(latestIndex.completed_at).toLocaleString() : 'Recent'}
                </div>
              </div>

              <div className="p-3 rounded-[2px] bg-[#171511] border border-[#26221c] flex items-center justify-between">
                <div>
                  <div className="font-medium text-[#f5f0e6]">Auto-Review Trigger</div>
                  <div className="text-[#8a8378] text-[11px] mt-0.5">
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
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="border-b border-[#221f1a] pb-3">
              <CardTitle className="text-base font-serif text-[#f5f0e6]">Repository Pull Requests</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-2.5">
              {pullRequests.length === 0 ? (
                <div className="p-8 text-center text-[#6a6358] text-xs font-mono">
                  No pull requests registered for this repository.
                </div>
              ) : (
                pullRequests.map((pr) => (
                  <div
                    key={pr.id}
                    className="p-3.5 rounded-[2px] bg-[#171511] border border-[#26221c] flex items-center justify-between hover:border-[#383229] transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-[#d4a853]">#{pr.pr_number}</span>
                        <span className="font-serif text-base text-[#f5f0e6]">{pr.title}</span>
                        <Badge
                          variant={pr.state === 'open' ? 'success' : 'outline'}
                          className="capitalize text-[10px]"
                        >
                          {pr.state}
                        </Badge>
                      </div>
                      <div className="text-[11px] text-[#787165] font-mono mt-1">
                        {pr.head_branch} &rarr; {pr.base_branch} · author: {pr.author_username}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="electric"
                      onClick={async () => {
                        const rev = await reviewApi.createReview(pr.id, pr.head_sha);
                        navigate(`/reviews/${rev.id}`);
                      }}
                      className="text-xs font-mono flex items-center gap-1 font-medium"
                    >
                      <span>Inspect Review</span>
                      <ArrowRight className="w-3 h-3 text-[#0e0d0b]" />
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Codebase Symbols */}
        <TabsContent value="symbols" className="space-y-4">
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="pb-3 border-b border-[#221f1a]">
              <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center justify-between">
                <span>AST Symbol Index</span>
                <span className="text-xs text-[#8a8378] font-mono">
                  {symbols.length} symbols found
                </span>
              </CardTitle>
              <CardDescription className="text-xs text-[#8a8378]">
                Search functions, classes, and methods parsed via Tree-sitter for exact reference retrieval
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-3 font-mono">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#6a6358]" />
                <Input
                  placeholder="Filter symbols by identifier, class, or function name..."
                  value={symbolSearch}
                  onChange={(e) => setSymbolSearch(e.target.value)}
                  className="pl-9 h-8 text-xs font-mono bg-[#171511] border-[#26221c]"
                />
              </div>

              <div className="space-y-2 max-h-[420px] overflow-y-auto">
                {symbols.length === 0 ? (
                  <div className="p-8 text-center text-[#6a6358] text-xs font-mono">
                    No symbols found matching query.
                  </div>
                ) : (
                  symbols.map((sym: any) => (
                    <div
                      key={sym.id}
                      className="p-2.5 rounded-[2px] bg-[#171511] border border-[#26221c] flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <Code2 className="w-3.5 h-3.5 text-[#3a9e8f] shrink-0" />
                        <div>
                          <span className="font-mono font-medium text-[#f5f0e6]">{sym.name}</span>
                          <span className="text-[11px] text-[#6a6358] font-mono ml-2">
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
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="border-b border-[#221f1a] pb-3">
              <CardTitle className="text-base font-serif text-[#f5f0e6]">PR Merge Gate Enforcement</CardTitle>
              <CardDescription className="text-xs text-[#8a8378]">
                Configure automated branch protection policies enforced by OpenReview AI Arbiter
              </CardDescription>
            </CardHeader>
            <CardContent className="p-5 space-y-4">
              <div className="flex items-center justify-between p-3.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <div>
                  <div className="text-xs font-medium text-[#f5f0e6]">Block Merge on Critical Security Findings</div>
                  <div className="text-[11px] text-[#8a8378] mt-0.5">
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

              <div className="flex items-center justify-between p-3.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <div>
                  <div className="text-xs font-medium text-[#f5f0e6]">Minimum Overall Score Threshold (&ge; 80/100)</div>
                  <div className="text-[11px] text-[#8a8378] mt-0.5">
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

              <div className="flex items-center justify-between p-3.5 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <div>
                  <div className="text-xs font-medium text-[#f5f0e6]">Automatic AutoFix PR Generation</div>
                  <div className="text-[11px] text-[#8a8378] mt-0.5">
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
          <Card className="border-[#26221c] bg-[#13110e]">
            <CardHeader className="border-b border-[#221f1a] pb-3">
              <CardTitle className="text-base font-serif text-[#f5f0e6]">GitHub Webhook Integration Health</CardTitle>
            </CardHeader>
            <CardContent className="p-5 space-y-3 text-xs font-mono">
              <div className="flex items-center justify-between p-3 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <span className="text-[#8a8378]">Webhook Target:</span>
                <span className="text-[#d4a853]">http://127.0.0.1:8000/api/v1/webhooks/github</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-[2px] bg-[#171511] border border-[#26221c]">
                <span className="text-[#8a8378]">Active Monitoring:</span>
                <span className="text-[#5a9e6f] flex items-center gap-1.5">
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

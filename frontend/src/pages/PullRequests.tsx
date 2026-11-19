import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { reviewApi } from '@/services/reviewApi';
import { PullRequest, PullRequestCreateInput, Repository } from '@/types/repository';
import { Review } from '@/types/review';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  Plus,
  GitCommit,
  User,
  ArrowRight,
  Sparkles,
  Search,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const PullRequests: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'closed' | 'merged'>('all');
  const [repoFilter, setRepoFilter] = useState<string>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [analyzingPrId, setAnalyzingPrId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any | null>(null);
  const [selectedRepoId, setSelectedRepoId] = useState('');
  const [prNumber, setPrNumber] = useState(43);
  const [title, setTitle] = useState('feat: add async pgvector similarity search');
  const [author, setAuthor] = useState('octocat');

  const { data: repos } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: () => repositoryApi.listRepositories(),
  });

  const { data: pullRequests, isLoading } = useQuery<PullRequest[]>({
    queryKey: ['pull-requests', repoFilter],
    queryFn: () => repositoryApi.listPullRequests(repoFilter !== 'all' ? repoFilter : undefined),
  });

  const createPrMutation = useMutation({
    mutationFn: (input: PullRequestCreateInput) => repositoryApi.createPullRequest(input),
    onSuccess: (newPr: PullRequest) => {
      queryClient.invalidateQueries({ queryKey: ['pull-requests'] });
      setShowCreate(false);
      success('PR Simulated', `Pull Request #${newPr.pr_number} created.`);
      reviewApi.createReview(newPr.id, newPr.head_sha).then((rev: Review) => {
        navigate(`/reviews/${rev.id}`);
      });
    },
    onError: (err: any) => {
      error('Failed to create PR', err.message || 'Error communicating with backend');
    },
  });

  const handleCreatePR = (e: React.FormEvent) => {
    e.preventDefault();
    const repoId = selectedRepoId || (repos && repos.length > 0 ? repos[0].id : '');
    if (!repoId) {
      error('Repository required', 'Please select or connect a repository first.');
      return;
    }

    createPrMutation.mutate({
      repository_id: repoId,
      pr_number: Number(prNumber),
      title,
      head_branch: 'feature/vector-search',
      base_branch: 'main',
      head_sha: '7f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a',
      base_sha: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
      author_username: author,
      description: 'Adds cosine similarity lookup on embeddings via pgvector.',
    });
  };

  const handleAnalyzePR = async (prId: string) => {
    setAnalyzingPrId(prId);
    try {
      const res = await repositoryApi.analyzePullRequest(prId);
      setAnalysisResult(res);
      success('PR Impact Analysis Completed', `Risk Score: ${res.risk_score || 0}/100, Complexity: ${res.complexity_score || 0}/100`);
    } catch (err: any) {
      error('Analysis Failed', err.message || 'Could not analyze PR diff');
    } finally {
      setAnalyzingPrId(null);
    }
  };

  const filteredPRs = pullRequests?.filter((pr) => {
    const matchesSearch =
      pr.title.toLowerCase().includes(search.toLowerCase()) ||
      pr.author_username.toLowerCase().includes(search.toLowerCase()) ||
      String(pr.pr_number).includes(search);
    const matchesStatus = statusFilter === 'all' || pr.state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 03]</span>
            <div className="h-2.5 w-px bg-[#36312a]" />
            <span className="text-[10px] font-mono tracking-wider text-[#8a8378] uppercase">Review Queue</span>
          </div>
          <h1 className="text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight mt-1">
            Pull Request Reviews
          </h1>
          <p className="text-xs text-[#8a8378] mt-1.5 leading-relaxed">
            Active and historical pull requests evaluated across AST diffs, static rules, and multi-agent debates.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setShowCreate(true)}
            variant="electric"
            className="flex items-center gap-1.5 text-xs font-mono font-medium"
          >
            <Plus className="w-3.5 h-3.5 text-[#0e0d0b]" />
            <span>Simulate Pull Request</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 flex-1 max-w-lg">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#6a6358]" />
            <Input
              placeholder="Search by title, author, or #PR number..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-8 text-xs font-mono bg-[#14120f] border-[#26221c]"
            />
          </div>

          <select
            value={repoFilter}
            onChange={(e) => setRepoFilter(e.target.value)}
            className="h-8 rounded-[2px] border border-[#2a2621] bg-[#14120f] px-2.5 text-xs font-mono text-[#b8b0a2] focus:outline-none focus:border-[#d4a853]"
          >
            <option value="all">All Repositories</option>
            {repos?.map((r) => (
              <option key={r.id} value={r.id}>
                {r.full_name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1 bg-[#14120f] p-1 rounded-[2px] border border-[#26221c] text-xs font-mono">
          {(['all', 'open', 'merged', 'closed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1 rounded-[2px] capitalize text-[11px] transition-colors ${
                statusFilter === s
                  ? 'bg-[#221f1a] text-[#d4a853] font-medium border border-[#38332a]'
                  : 'text-[#8a8378] hover:text-[#d8d2c4]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* PR List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-12 text-center text-[#6a6358] font-mono text-xs">
            Querying pull request telemetry...
          </div>
        ) : !filteredPRs || filteredPRs.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-[#2e2a24] bg-[#14120f]">
            <GitPullRequest className="w-8 h-8 text-[#6a6358] mx-auto mb-3" />
            <h3 className="text-base font-serif text-[#f5f0e6]">No pull requests found</h3>
            <p className="text-xs text-[#8a8378] mt-1 max-w-sm mx-auto font-mono">
              Click &quot;Simulate Pull Request&quot; to test the multi-agent review pipeline.
            </p>
          </Card>
        ) : (
          filteredPRs.map((pr: PullRequest) => (
            <Card
              key={pr.id}
              className="border-[#26221c] bg-[#13110e] hover:border-[#383229] transition-colors"
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-[2px] bg-[#1b1915] border border-[#332e26] flex items-center justify-center text-[#3a9e8f]">
                    <GitPullRequest className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-[#d4a853]">#{pr.pr_number}</span>
                      <span className="font-serif text-base text-[#f5f0e6]">{pr.title}</span>
                      <Badge
                        variant={pr.state === 'open' ? 'success' : 'outline'}
                        className="text-[10px] py-0 capitalize font-mono"
                      >
                        {pr.state}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-[#787165] font-mono mt-1">
                      <span className="flex items-center gap-1 text-[#a69e90]">
                        <User className="w-3 h-3 text-[#6a6358]" />
                        {pr.author_username}
                      </span>
                      <span>·</span>
                      <span>{pr.head_branch} &rarr; {pr.base_branch}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <GitCommit className="w-3 h-3 text-[#6a6358]" />
                        {pr.head_sha.substring(0, 7)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleAnalyzePR(pr.id)}
                    isLoading={analyzingPrId === pr.id}
                    className="text-xs font-mono border-[#2e2a24]"
                  >
                    Analyze Impact
                  </Button>

                  <Button
                    size="sm"
                    variant="electric"
                    onClick={async () => {
                      const rev = await reviewApi.createReview(pr.id, pr.head_sha);
                      navigate(`/reviews/${rev.id}`);
                    }}
                    className="flex items-center gap-1.5 text-xs font-mono font-medium"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#0e0d0b]" />
                    <span>Inspect Review</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#0e0d0b]" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Analysis Result Dialog */}
      <Dialog open={!!analysisResult} onOpenChange={(open) => !open && setAnalysisResult(null)}>
        <DialogHeader>
          <DialogTitle>PR Impact & Risk Ledger</DialogTitle>
          <DialogDescription>
            Static diff analysis, algorithmic complexity profiling, and agent dispatch recommendations.
          </DialogDescription>
        </DialogHeader>

        {analysisResult && (
          <div className="space-y-4 text-xs font-mono">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-[2px] bg-[#181512] border border-[#2a2620]">
                <span className="text-[#8a8378] block text-[11px]">Explainable Risk Score</span>
                <span className="text-2xl font-serif text-[#f0af54]">
                  {analysisResult.risk_score ?? 0} / 100
                </span>
              </div>
              <div className="p-3.5 rounded-[2px] bg-[#181512] border border-[#2a2620]">
                <span className="text-[#8a8378] block text-[11px]">Complexity Score</span>
                <span className="text-2xl font-serif text-[#d4a853]">
                  {analysisResult.complexity_score ?? 0} / 100
                </span>
              </div>
            </div>

            <div>
              <span className="text-[#8a8378] block mb-1">Executive Summary</span>
              <p className="p-3 rounded-[2px] bg-[#161410] border border-[#26221c] text-[#d8d2c4] leading-relaxed font-sans text-xs">
                {analysisResult.pr_summary || 'No summary available.'}
              </p>
            </div>

            {analysisResult.risk_factors && analysisResult.risk_factors.length > 0 && (
              <div>
                <span className="text-[#8a8378] block mb-1">Risk Factors</span>
                <div className="flex flex-wrap gap-1.5">
                  {analysisResult.risk_factors.map((factor: string, idx: number) => (
                    <Badge key={idx} variant="warning" className="text-[10px]">
                      {factor}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {analysisResult.recommended_agents && analysisResult.recommended_agents.length > 0 && (
              <div>
                <span className="text-[#8a8378] block mb-1">Recommended Review Agents</span>
                <div className="flex flex-wrap gap-1.5">
                  {analysisResult.recommended_agents.map((agent: string, idx: number) => (
                    <Badge key={idx} variant="purple" className="text-[10px]">
                      {agent}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="ghost" onClick={() => setAnalysisResult(null)} className="font-mono text-xs">
                Close
              </Button>
            </DialogFooter>
          </div>
        )}
      </Dialog>

      {/* Modal Dialog for Simulating PR */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogHeader>
          <DialogTitle>Simulate Pull Request Event</DialogTitle>
          <DialogDescription>
            Simulates a pull_request.opened webhook event from GitHub to trigger the multi-agent code review workflow.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleCreatePR} className="space-y-4 font-mono text-xs">
          <div>
            <label className="block text-[11px] text-[#8a8378] mb-1">
              Connected Repository
            </label>
            <select
              value={selectedRepoId}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="w-full h-8 rounded-[2px] border border-[#2a2621] bg-[#161411] px-3 text-xs text-[#f5f0e6] focus:outline-none focus:border-[#d4a853]"
              required
            >
              <option value="">Select a repository...</option>
              {repos?.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.full_name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] text-[#8a8378] mb-1">
                PR Number
              </label>
              <Input
                type="number"
                value={prNumber}
                onChange={(e) => setPrNumber(Number(e.target.value))}
                required
              />
            </div>
            <div>
              <label className="block text-[11px] text-[#8a8378] mb-1">
                Author
              </label>
              <Input
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] text-[#8a8378] mb-1">
              Pull Request Title
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="electric" isLoading={createPrMutation.isPending}>
              Create & Trigger Review
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};

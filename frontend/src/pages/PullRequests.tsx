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
  CheckCircle2,
  AlertTriangle,
  Clock,
  Filter,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const PullRequests: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'closed' | 'merged'>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [selectedRepoId, setSelectedRepoId] = useState('');
  const [prNumber, setPrNumber] = useState(43);
  const [title, setTitle] = useState('feat: add async pgvector similarity search');
  const [author, setAuthor] = useState('octocat');

  const { data: repos } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: repositoryApi.listRepositories,
  });

  const { data: pullRequests, isLoading } = useQuery<PullRequest[]>({
    queryKey: ['pull-requests'],
    queryFn: () => repositoryApi.listPullRequests(),
  });

  const createPrMutation = useMutation({
    mutationFn: (input: PullRequestCreateInput) => repositoryApi.createPullRequest(input),
    onSuccess: (newPr: PullRequest) => {
      queryClient.invalidateQueries({ queryKey: ['pull-requests'] });
      setShowCreate(false);
      success('PR Simulated', `Pull Request #${newPr.pr_number} created.`);
      // Auto-trigger review pass
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

  const filteredPRs = pullRequests?.filter((pr) => {
    const matchesSearch =
      pr.title.toLowerCase().includes(search.toLowerCase()) ||
      pr.author_username.toLowerCase().includes(search.toLowerCase()) ||
      String(pr.pr_number).includes(search);
    const matchesStatus = statusFilter === 'all' || pr.state === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Pull Request Reviews</h1>
          <p className="text-xs text-slate-400 mt-1">
            Active and historical pull requests evaluated by OpenReview AI autonomous agents.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => setShowCreate(true)}
            variant="electric"
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Simulate Pull Request</span>
          </Button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <Input
            placeholder="Search by title, author, or #PR number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs bg-[#0b101c]"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-[#0e1422] p-1 rounded-lg border border-slate-800 text-xs">
          {(['all', 'open', 'merged', 'closed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-2.5 py-1 rounded capitalize text-[11px] transition ${
                statusFilter === s
                  ? 'bg-sky-500/20 text-sky-400 font-semibold'
                  : 'text-slate-400 hover:text-white'
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
          <div className="p-12 text-center text-slate-500 font-mono text-xs">
            Loading pull requests...
          </div>
        ) : !filteredPRs || filteredPRs.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-slate-800 bg-[#0c101c]">
            <GitPullRequest className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white">No pull requests found</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Click &quot;Simulate Pull Request&quot; above to simulate an incoming GitHub webhook review.
            </p>
          </Card>
        ) : (
          filteredPRs.map((pr: PullRequest) => (
            <Card
              key={pr.id}
              className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700/80 transition"
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <GitPullRequest className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-xs">#{pr.pr_number}</span>
                      <span className="font-semibold text-slate-200 text-sm">{pr.title}</span>
                      <Badge
                        variant={pr.state === 'open' ? 'success' : 'outline'}
                        className="text-[10px] py-0 capitalize"
                      >
                        {pr.state}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-1">
                      <span className="flex items-center gap-1 text-slate-400">
                        <User className="w-3 h-3 text-slate-500" />
                        {pr.author_username}
                      </span>
                      <span>•</span>
                      <span>{pr.head_branch} &rarr; {pr.base_branch}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <GitCommit className="w-3 h-3 text-slate-500" />
                        {pr.head_sha.substring(0, 7)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <Button
                    size="sm"
                    variant="electric"
                    onClick={async () => {
                      const rev = await reviewApi.createReview(pr.id, pr.head_sha);
                      navigate(`/reviews/${rev.id}`);
                    }}
                    className="flex items-center gap-1.5 text-xs font-semibold"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                    <span>Inspect Review</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Modal Dialog for Simulating PR */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogHeader>
          <DialogTitle>Simulate Pull Request Event</DialogTitle>
          <DialogDescription>
            Simulates an incoming pull_request.opened webhook event from GitHub to trigger the multi-agent code review workflow.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleCreatePR} className="space-y-4">
          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Connected Repository
            </label>
            <select
              value={selectedRepoId}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="w-full h-8 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
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
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
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
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
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
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
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

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
import { useNavigate } from 'react-router-dom';
import {
  GitPullRequest,
  Plus,
  GitCommit,
  User,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

export const PullRequests: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedRepoId, setSelectedRepoId] = useState('');
  const [prNumber, setPrNumber] = useState(42);
  const [title, setTitle] = useState('feat: add autonomous security analyzer');
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
      // Auto-trigger review pass
      reviewApi.createReview(newPr.id, newPr.head_sha).then((rev: Review) => {
        navigate(`/reviews/${rev.id}`);
      });
    },
  });

  const handleCreatePR = (e: React.FormEvent) => {
    e.preventDefault();
    const repoId = selectedRepoId || (repos && repos.length > 0 ? repos[0].id : '');
    if (!repoId) return;

    createPrMutation.mutate({
      repository_id: repoId,
      pr_number: Number(prNumber),
      title,
      head_branch: 'feature/security-agent',
      base_branch: 'main',
      head_sha: '7f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a',
      base_sha: '1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
      author_username: author,
      description: 'Adds AST-based deep vulnerability pattern scanning.',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Pull Requests</h1>
          <p className="text-sm text-slate-400 mt-1">
            Active and reviewed pull requests analyzed by OpenReview AI agents.
          </p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          <span>{showCreate ? 'Cancel' : 'Simulate Pull Request'}</span>
        </Button>
      </div>

      {showCreate && (
        <Card className="border-sky-500/40 bg-slate-900/90 shadow-xl">
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold text-white mb-2">Simulate New Pull Request</h3>
            <p className="text-xs text-slate-400 mb-4">
              Simulates a webhook event from GitHub to trigger the multi-agent code review workflow.
            </p>
            <form onSubmit={handleCreatePR} className="space-y-4 max-w-xl">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Target Repository</label>
                <select
                  value={selectedRepoId}
                  onChange={(e) => setSelectedRepoId(e.target.value)}
                  className="w-full h-9 rounded-md border border-slate-700 bg-slate-950 px-3 py-1 text-sm text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
                  required
                >
                  <option value="">Select a connected repository...</option>
                  {repos?.map((r: Repository) => (
                    <option key={r.id} value={r.id}>
                      {r.full_name}
                    </option>
                  ))}
                </select>
                {(!repos || repos.length === 0) && (
                  <p className="text-[11px] text-amber-400 mt-1">
                    * Please register a repository first in the Repositories tab.
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">PR Number</label>
                  <Input
                    type="number"
                    value={prNumber}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPrNumber(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Author</label>
                  <Input
                    value={author}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAuthor(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">PR Title</label>
                <Input
                  value={title}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTitle(e.target.value)}
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createPrMutation.isPending}>
                  Create & Launch Review
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* PR List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-slate-500 font-mono text-sm">
            Loading pull requests...
          </div>
        ) : !pullRequests || pullRequests.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-slate-800">
            <GitPullRequest className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No pull requests tracked</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
              Simulate or link a pull request to trigger autonomous agent analysis passes.
            </p>
          </Card>
        ) : (
          pullRequests.map((pr: PullRequest) => (
            <Card key={pr.id} className="hover:border-slate-700 transition">
              <CardContent className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <GitPullRequest className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-base">#{pr.pr_number}</span>
                      <span className="font-semibold text-slate-200">{pr.title}</span>
                      <Badge variant="outline" className="text-emerald-400 border-emerald-500/30">
                        {pr.state}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate-400 mt-1.5 font-mono">
                      <span className="flex items-center gap-1">
                        <User className="w-3.5 h-3.5 text-slate-500" />
                        {pr.author_username}
                      </span>
                      <span>
                        {pr.head_branch} &rarr; {pr.base_branch}
                      </span>
                      <span className="flex items-center gap-1">
                        <GitCommit className="w-3.5 h-3.5 text-slate-500" />
                        {pr.head_sha.substring(0, 7)}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <Button
                    size="sm"
                    onClick={async () => {
                      const rev = await reviewApi.createReview(pr.id, pr.head_sha);
                      navigate(`/reviews/${rev.id}`);
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Inspect Review</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

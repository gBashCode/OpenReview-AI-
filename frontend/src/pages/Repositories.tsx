import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { Repository, RepositoryCreateInput } from '@/types/repository';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Link, useNavigate } from 'react-router-dom';
import {
  GitFork,
  Plus,
  Trash2,
  ExternalLink,
  Search,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const Repositories: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();

  const [search, setSearch] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [owner, setOwner] = useState('');
  const [name, setName] = useState('');
  const [githubRepoId, setGithubRepoId] = useState(1001);
  const [description, setDescription] = useState('');

  const { data: repos, isLoading } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: () => repositoryApi.listRepositories(),
  });

  const createRepoMutation = useMutation({
    mutationFn: (input: RepositoryCreateInput) => repositoryApi.createRepository(input),
    onSuccess: (newRepo) => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      setShowDialog(false);
      setOwner('');
      setName('');
      setDescription('');
      success('Repository Connected', `Repository ${newRepo.full_name} is now active.`);
    },
    onError: (err: any) => {
      error('Failed to Connect Repository', err.message || 'Check owner/repo configuration');
    },
  });

  const deleteRepoMutation = useMutation({
    mutationFn: (id: string) => repositoryApi.deleteRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      info('Repository Removed', 'Autonomous review monitoring has been disabled.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner || !name) return;
    createRepoMutation.mutate({
      owner,
      name,
      github_repo_id: Number(githubRepoId),
      description: description || 'Primary codebase for multi-agent reviews',
      default_branch: 'main',
      is_active: true,
    });
  };

  const filteredRepos = repos?.filter((r) =>
    r.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (r.description && r.description.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Connected Repositories</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage codebases monitored for autonomous pull request inspection passes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => setShowDialog(true)}
            variant="electric"
            className="flex items-center gap-2 text-xs font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Connect Repository</span>
          </Button>
        </div>
      </div>

      {/* Search & Filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <Input
            placeholder="Filter repositories by name or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs bg-[#0b101c]"
          />
        </div>
        <div className="text-xs text-slate-500 font-mono">
          Showing {filteredRepos?.length || 0} repositories
        </div>
      </div>

      {/* Repositories List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 font-mono text-xs">
            Loading repositories from backend...
          </div>
        ) : !filteredRepos || filteredRepos.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-slate-800 bg-[#0c101c]">
            <GitFork className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-white">No repositories match your filter</h3>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Click &quot;Connect Repository&quot; to link your code repository via GitHub App.
            </p>
          </Card>
        ) : (
          filteredRepos.map((repo: Repository) => (
            <Card
              key={repo.id}
              className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700/80 transition"
            >
              <CardContent className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                    <GitFork className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/repositories/${repo.id}`}
                        className="font-bold text-white text-sm hover:text-sky-400 transition"
                      >
                        {repo.full_name}
                      </Link>
                      <Badge variant="success" className="text-[10px] py-0">
                        Active
                      </Badge>
                      <Badge variant="outline" className="font-mono text-[10px] py-0">
                        branch: {repo.default_branch}
                      </Badge>
                    </div>
                    {repo.description && (
                      <p className="text-xs text-slate-400 mt-0.5">{repo.description}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Link to={`/repositories/${repo.id}`}>
                    <Button variant="outline" size="sm" className="flex items-center gap-1.5 text-xs">
                      <span>Repository Details</span>
                      <ArrowRight className="w-3 h-3" />
                    </Button>
                  </Link>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteRepoMutation.mutate(repo.id)}
                    className="text-slate-500 hover:text-rose-400 hover:bg-rose-500/10"
                    title="Disconnect repository"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Connect Modal Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogHeader>
          <DialogTitle>Connect GitHub Repository</DialogTitle>
          <DialogDescription>
            Register an existing GitHub repository to enable autonomous multi-agent code reviews.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Owner / Organization
              </label>
              <Input
                placeholder="e.g. google-deepmind"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Repository Name
              </label>
              <Input
                placeholder="e.g. openreview-ai"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              GitHub Repo ID
            </label>
            <Input
              type="number"
              value={githubRepoId}
              onChange={(e) => setGithubRepoId(Number(e.target.value))}
              required
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Description (Optional)
            </label>
            <Input
              placeholder="Core backend platform services"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="electric" isLoading={createRepoMutation.isPending}>
              Save & Start Monitoring
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};

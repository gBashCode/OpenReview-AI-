import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { Repository, RepositoryCreateInput } from '@/types/repository';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { GitFork, Plus, Trash2 } from 'lucide-react';

export const Repositories: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [owner, setOwner] = useState('');
  const [name, setName] = useState('');
  const [githubRepoId, setGithubRepoId] = useState(1001);
  const [description, setDescription] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const { data: repos, isLoading } = useQuery<Repository[]>({
    queryKey: ['repositories'],
    queryFn: repositoryApi.listRepositories,
  });

  const createRepoMutation = useMutation({
    mutationFn: (input: RepositoryCreateInput) => repositoryApi.createRepository(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      setShowForm(false);
      setOwner('');
      setName('');
      setDescription('');
      setErrorMsg(null);
    },
    onError: (err: any) => {
      setErrorMsg(err.message || 'Failed to register repository');
    },
  });

  const deleteRepoMutation = useMutation({
    mutationFn: (id: string) => repositoryApi.deleteRepository(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!owner || !name) {
      setErrorMsg('Owner and Name are required');
      return;
    }
    createRepoMutation.mutate({
      owner,
      name,
      github_repo_id: Number(githubRepoId),
      description,
      default_branch: 'main',
      is_active: true,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Connected Repositories</h1>
          <p className="text-sm text-slate-400 mt-1">
            Repositories monitored for Pull Requests and automated agent review runs.
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          <span>{showForm ? 'Cancel' : 'Connect Repository'}</span>
        </Button>
      </div>

      {showForm && (
        <Card className="border-sky-500/40 bg-slate-900/90 shadow-xl">
          <CardHeader>
            <CardTitle>Connect New GitHub Repository</CardTitle>
            <CardDescription>
              Register a repository to enable autonomous code reviews via GitHub webhooks.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4 max-w-xl">
              {errorMsg && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                  {errorMsg}
                </div>
              )}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Owner / Org</label>
                  <Input
                    placeholder="e.g. google-deepmind"
                    value={owner}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOwner(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Repository Name</label>
                  <Input
                    placeholder="e.g. openreview-ai"
                    value={name}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">GitHub Repo ID</label>
                <Input
                  type="number"
                  value={githubRepoId}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setGithubRepoId(Number(e.target.value))}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
                <Input
                  placeholder="Primary core backend service"
                  value={description}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDescription(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="ghost" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createRepoMutation.isPending}>
                  Save Repository
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Repositories List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-slate-500 font-mono text-sm">
            Loading repositories...
          </div>
        ) : !repos || repos.length === 0 ? (
          <Card className="p-12 text-center border-dashed border-slate-800">
            <GitFork className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-white">No repositories linked yet</h3>
            <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
              Click &quot;Connect Repository&quot; above to link your first codebase for automated agent code reviews.
            </p>
          </Card>
        ) : (
          repos.map((repo: Repository) => (
            <Card key={repo.id} className="hover:border-slate-700 transition">
              <CardContent className="p-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                    <GitFork className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-base">{repo.full_name}</span>
                      <Badge variant="success">Active</Badge>
                      <Badge variant="outline" className="font-mono text-[10px]">
                        {repo.default_branch}
                      </Badge>
                    </div>
                    {repo.description && (
                      <p className="text-xs text-slate-400 mt-1">{repo.description}</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteRepoMutation.mutate(repo.id)}
                    title="Remove repository"
                    className="text-slate-400 hover:text-rose-400 hover:bg-rose-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
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

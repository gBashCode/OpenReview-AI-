import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { repositoryApi } from '@/services/repositoryApi';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  GitFork,
  GitPullRequest,
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Sliders,
  CheckCircle2,
  ExternalLink,
  Lock,
  GitBranch,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const RepositoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { success, info } = useToast();

  const [blockOnCritical, setBlockOnCritical] = useState(true);
  const [requireHighQuality, setRequireHighQuality] = useState(true);
  const [autoFixPrs, setAutoFixPrs] = useState(false);
  const [semanticIndexing, setSemanticIndexing] = useState(true);

  const { data: repo, isLoading } = useQuery({
    queryKey: ['repository', id],
    queryFn: () => repositoryApi.getRepository(id!),
    enabled: !!id,
  });

  const { data: pullRequests } = useQuery({
    queryKey: ['pull-requests', id],
    queryFn: () => repositoryApi.listPullRequests(id),
  });

  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono text-xs">
        Loading repository metadata...
      </div>
    );
  }

  const repoName = repo?.full_name || 'google-deepmind/openreview-ai';

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
                <h1 className="text-xl font-bold text-white tracking-tight">{repoName}</h1>
                <Badge variant="success">Active Monitoring</Badge>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Default branch: {repo?.default_branch || 'main'} • GitHub Repo ID: {repo?.github_repo_id || 1001}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={`https://github.com/${repoName}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 bg-[#0e1422] transition"
            >
              <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
              <span>View on GitHub</span>
            </a>
          </div>
        </div>
      </div>

      {/* Tabs navigation */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="rules">Review Policies & Gates</TabsTrigger>
          <TabsTrigger value="prs">Pull Requests ({pullRequests?.length || 2})</TabsTrigger>
          <TabsTrigger value="webhook">Webhook Status</TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">Total PRs Inspected</div>
                <div className="text-2xl font-bold font-mono text-white">42</div>
                <p className="text-[11px] text-slate-500 mt-1">100% automated coverage</p>
              </CardContent>
            </Card>

            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">Average Quality Score</div>
                <div className="text-2xl font-bold font-mono text-emerald-400">92.4/100</div>
                <p className="text-[11px] text-slate-500 mt-1">+4.2% since OpenReview AI installed</p>
              </CardContent>
            </Card>

            <Card className="border-slate-800 bg-[#0c101c]">
              <CardContent className="p-4">
                <div className="text-xs text-slate-400 font-medium mb-1">Vulnerabilities Blocked</div>
                <div className="text-2xl font-bold font-mono text-rose-400">7</div>
                <p className="text-[11px] text-slate-500 mt-1">0 criticals merged into production</p>
              </CardContent>
            </Card>
          </div>

          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">Repository Semantics & Vector Index</CardTitle>
              <CardDescription className="text-xs">
                Codebase structure indexed into PostgreSQL pgvector for contextual agent grounding
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                <div>
                  <div className="font-semibold text-white">pgvector Semantic Indexing</div>
                  <div className="text-slate-400 text-[11px]">
                    1,536-dimensional embeddings stored for architecture conventions and coding guidelines
                  </div>
                </div>
                <Badge variant="purple">Synchronized</Badge>
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

        {/* Tab 2: Review Policies & Gates */}
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

        {/* Tab 3: Pull Requests */}
        <TabsContent value="prs" className="space-y-3">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">Recent Pull Requests</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">#42</span>
                    <span className="text-xs text-slate-300 font-semibold">feat: add autonomous multi-agent reviewer</span>
                    <Badge variant="warning">Changes Requested</Badge>
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                    head: feature/security-agent • author: octocat
                  </div>
                </div>
                <Link to="/reviews/sample">
                  <Button size="sm" variant="electric">
                    Inspect Review
                  </Button>
                </Link>
              </div>

              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">#41</span>
                    <span className="text-xs text-slate-300 font-semibold">fix: database connection pool configuration</span>
                    <Badge variant="success">Passed</Badge>
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                    head: fix/pool-settings • author: alexrivera
                  </div>
                </div>
                <Link to="/reviews/sample">
                  <Button size="sm" variant="outline">
                    View Run
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Webhook Status */}
        <TabsContent value="webhook" className="space-y-4">
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader>
              <CardTitle className="text-sm font-semibold text-white">GitHub Webhook Integration Health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300">Webhook URL:</span>
                <span className="font-mono text-sky-400">https://api.openreview.ai/api/v1/webhooks/github</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-300">Last Ping Delivery:</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>200 OK (3 mins ago)</span>
                </span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

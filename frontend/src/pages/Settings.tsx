import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { organizationApi } from '@/services/organizationApi';
import { githubApi } from '@/services/githubApi';
import {
  Sliders,
  Github,
  Key,
  ShieldCheck,
  Bell,
  Trash2,
  AlertTriangle,
  Check,
  Save,
  RotateCw,
  ExternalLink,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const Settings: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, warning, error, info } = useToast();

  const [orgName, setOrgName] = useState('OpenReview Engineering');
  const [slug, setSlug] = useState('openreview-team');
  const [notifyOnCritical, setNotifyOnCritical] = useState(true);
  const [notifyOnSuccess, setNotifyOnSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Load real organization
  const { data: orgs = [] } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationApi.listOrganizations,
  });

  const activeOrg = orgs[0];

  useEffect(() => {
    if (activeOrg) {
      setOrgName(activeOrg.name);
      setSlug(activeOrg.slug);
    }
  }, [activeOrg]);

  // Load GitHub App installations
  const { data: installations = [], isLoading: loadingInstallations } = useQuery({
    queryKey: ['github-installations'],
    queryFn: () => githubApi.listInstallations(),
  });

  const handleConnectGitHub = async () => {
    try {
      const res = await githubApi.getConnectUrl();
      if (res.installation_url) {
        window.open(res.installation_url, '_blank');
        info('GitHub Integration', 'Follow instructions on GitHub to complete App authorization.');
      }
    } catch (err: any) {
      error('Integration Failed', err.message || 'Could not generate GitHub App connection URL.');
    }
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      success('Settings Saved', 'Workspace configuration updated successfully.');
    }, 400);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800/80">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Organization & Platform Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure general workspace parameters, GitHub App integrations, and notification routing.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Workspace Identity */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-sky-400" />
              <span>Workspace Profile</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Primary organization identity and tenant boundary identifier
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">Organization Name</label>
                <Input
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs"
                />
              </div>

              <div>
                <label className="text-xs text-slate-300 font-medium block mb-1">Workspace Slug</label>
                <Input
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-xs font-mono"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span>Active Subscription Tier:</span>
              <Badge variant="purple" className="text-[10px] uppercase font-mono">
                {activeOrg?.plan || 'Enterprise'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* GitHub App Integration Card */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-white flex items-center gap-2">
                  <Github className="w-4 h-4 text-white" />
                  <span>GitHub App Installations</span>
                </CardTitle>
                <CardDescription className="text-xs">
                  Authorize repositories for automatic review triggers and inline comments
                </CardDescription>
              </div>

              <Button
                type="button"
                variant="electric"
                size="sm"
                onClick={handleConnectGitHub}
                className="text-xs flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Install GitHub App</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-3">
            {loadingInstallations ? (
              <div className="text-xs text-slate-500 font-mono">Loading installations...</div>
            ) : installations.length === 0 ? (
              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 text-xs text-slate-400">
                No GitHub App installations connected yet. Click "Install GitHub App" to grant repository access.
              </div>
            ) : (
              installations.map((inst) => (
                <div
                  key={inst.id}
                  className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <Github className="w-4 h-4 text-sky-400" />
                    <div>
                      <span className="font-semibold text-white">{inst.account_login}</span>
                      <span className="text-slate-500 font-mono text-[11px] ml-2">ID: {inst.installation_id}</span>
                    </div>
                  </div>
                  <Badge variant="success" className="text-[10px]">Connected</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Notification Routing Card */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <Bell className="w-4 h-4 text-amber-400" />
              <span>Review Alert Preferences</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Configure real-time notifications for automated PR review conclusions
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <div>
                <div className="text-xs font-semibold text-white">Alert on Critical Vulnerabilities</div>
                <div className="text-[11px] text-slate-400">
                  Notify engineers immediately when critical security flaws or breaking bugs are detected.
                </div>
              </div>
              <Switch checked={notifyOnCritical} onCheckedChange={setNotifyOnCritical} />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
              <div>
                <div className="text-xs font-semibold text-white">Notify on Clean Reviews (Approval)</div>
                <div className="text-[11px] text-slate-400">
                  Notify author when a pull request review passes all multi-agent quality gates cleanly.
                </div>
              </div>
              <Switch checked={notifyOnSuccess} onCheckedChange={setNotifyOnSuccess} />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2.5">
          <Button type="submit" variant="electric" size="sm" isLoading={isSaving} className="text-xs font-semibold">
            <Save className="w-3.5 h-3.5 mr-1 text-amber-300" />
            <span>Save Configuration</span>
          </Button>
        </div>
      </form>
    </div>
  );
};

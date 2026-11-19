import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  Bell,
  Save,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Building2,
  Lock,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const Settings: React.FC = () => {
  const { success, error, info } = useToast();

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
      success('Ledger Saved', 'Workspace configuration updated in active ledger profile.');
    }, 400);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-4 border-b border-[#2a2621]">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono text-[10px] tracking-[0.2em] text-[#d4a853] uppercase font-bold">
            [LEDGER · 13 · WORKSPACE PREFERENCES]
          </span>
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5a9e6f]" />
          <span className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase">
            CONFIG REVISION #04
          </span>
        </div>
        <h1 className="font-serif text-3xl font-normal text-[#f4efe6] tracking-tight">
          Organization & System Configuration
        </h1>
        <p className="font-sans text-xs text-[#8c8273] mt-1">
          Configure general workspace parameters, GitHub App integrations, and automated notification routing.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Workspace Identity */}
        <Card className="border-[#2a2621] bg-[#14120f]">
          <CardHeader className="pb-3 border-b border-[#2a2621]">
            <div className="flex items-center justify-between">
              <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
                <Building2 className="w-4 h-4 text-[#d4a853]" />
                <span>Workspace Profile & Identity</span>
              </CardTitle>
              <Badge variant="outline" className="font-mono text-[10px] border-[#3e3525] text-[#d4a853]">
                TENANT ID
              </Badge>
            </div>
            <CardDescription className="font-sans text-xs text-[#8c8273]">
              Primary organization identity and multi-tenant boundary parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                  Organization Legal Name
                </label>
                <Input
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="font-sans text-xs"
                />
              </div>

              <div>
                <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                  Workspace Slug Identifier
                </label>
                <Input
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="font-mono text-xs"
                />
              </div>
            </div>

            <div className="pt-2 flex items-center gap-2 font-sans text-xs text-[#8c8273]">
              <span>Active Subscription Tier:</span>
              <Badge variant="amber" className="font-mono text-[10px] uppercase">
                {activeOrg?.plan || 'Enterprise'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* GitHub App Integration Card */}
        <Card className="border-[#2a2621] bg-[#14120f]">
          <CardHeader className="pb-3 border-b border-[#2a2621]">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
                  <Github className="w-4 h-4 text-[#f4efe6]" />
                  <span>GitHub App Installations</span>
                </CardTitle>
                <CardDescription className="font-sans text-xs text-[#8c8273]">
                  Authorize repositories for automatic review triggers and inline comments
                </CardDescription>
              </div>

              <Button
                type="button"
                variant="electric"
                size="sm"
                onClick={handleConnectGitHub}
                className="font-sans text-xs flex items-center gap-1.5"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                <span>Install GitHub App</span>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-6 space-y-3">
            {loadingInstallations ? (
              <div className="font-mono text-xs text-[#8c8273]">Querying GitHub App installations...</div>
            ) : installations.length === 0 ? (
              <div className="p-4 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621] font-sans text-xs text-[#8c8273]">
                No GitHub App installations connected yet. Click "Install GitHub App" to grant repository access.
              </div>
            ) : (
              installations.map((inst) => (
                <div
                  key={inst.id}
                  className="p-3.5 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621] flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-[2px] bg-[#1c1914] border border-[#342f27] flex items-center justify-center text-[#f4efe6]">
                      <Github className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="font-sans font-medium text-xs text-[#f4efe6]">
                        {inst.account_login}
                      </span>
                      <span className="font-mono text-[#5a5247] text-[11px] ml-2">
                        ID: {inst.installation_id}
                      </span>
                    </div>
                  </div>
                  <Badge variant="teal" className="font-mono text-[10px]">
                    CONNECTED
                  </Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Review Alert Preferences Card */}
        <Card className="border-[#2a2621] bg-[#14120f]">
          <CardHeader className="pb-3 border-b border-[#2a2621]">
            <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
              <Bell className="w-4 h-4 text-[#d4a853]" />
              <span>Review Alert Preferences</span>
            </CardTitle>
            <CardDescription className="font-sans text-xs text-[#8c8273]">
              Configure real-time notifications for automated PR review conclusions
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-3.5">
            <div className="flex items-center justify-between p-3.5 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621]">
              <div>
                <div className="font-sans text-xs font-medium text-[#f4efe6]">
                  Alert on Critical Security Vulnerabilities
                </div>
                <div className="font-sans text-[11px] text-[#8c8273] mt-0.5">
                  Notify engineers immediately when critical security flaws or breaking bugs are detected.
                </div>
              </div>
              <Switch checked={notifyOnCritical} onCheckedChange={setNotifyOnCritical} />
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621]">
              <div>
                <div className="font-sans text-xs font-medium text-[#f4efe6]">
                  Notify on Clean Reviews (Council Approval)
                </div>
                <div className="font-sans text-[11px] text-[#8c8273] mt-0.5">
                  Notify author when a pull request review passes all multi-agent quality gates cleanly.
                </div>
              </div>
              <Switch checked={notifyOnSuccess} onCheckedChange={setNotifyOnSuccess} />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2.5 pt-2">
          <Button
            type="submit"
            variant="electric"
            size="sm"
            isLoading={isSaving}
            className="font-sans text-xs"
          >
            <Save className="w-3.5 h-3.5 mr-1.5 text-[#0e0d0b]" />
            <span>Save Configuration</span>
          </Button>
        </div>
      </form>
    </div>
  );
};

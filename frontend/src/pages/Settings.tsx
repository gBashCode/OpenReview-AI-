import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
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
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const Settings: React.FC = () => {
  const { success, warning, info } = useToast();

  const [orgName, setOrgName] = useState('DeepMind Core Lab');
  const [slug, setSlug] = useState('deepmind-labs');
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/T00/B00/XXXXX');
  const [notifyOnCritical, setNotifyOnCritical] = useState(true);
  const [notifyOnSuccess, setNotifyOnSuccess] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      success('Settings Saved', 'Workspace configuration updated successfully.');
    }, 500);
  };

  const handleRotateWebhookSecret = () => {
    success('Webhook Secret Rotated', 'Updated GitHub App secret key.');
  };

  const handlePurgeVectorIndex = () => {
    warning('Vector Index Purged', 'Semantic pgvector cache cleared. It will rebuild on the next PR webhook.');
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800/80">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Organization Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure general workspace parameters, notification routing, and GitHub integrations.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Workspace Identity */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white">Workspace Identity</CardTitle>
            <CardDescription className="text-xs">
              Organization details shown on review comments and audit logs
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Organization Name
                </label>
                <Input
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="h-8 text-xs bg-[#0b101c]"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Workspace URL Slug
                </label>
                <Input
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="h-8 text-xs bg-[#0b101c] font-mono"
                  required
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* GitHub App Secrets & Webhook */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Github className="w-4 h-4 text-slate-300" />
                <span>GitHub App Connectivity</span>
              </span>
              <Badge variant="success">Connected</Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Credentials mapped from backend .env for webhook signature verification and PR comment posting
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs">
              <div>
                <div className="font-semibold text-white">GitHub Webhook Secret</div>
                <div className="text-slate-400 font-mono text-[11px]">••••••••••••••••••••••••••••••••</div>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleRotateWebhookSecret}
                className="text-xs"
              >
                <RotateCw className="w-3 h-3 mr-1 text-slate-400" />
                <span>Rotate Secret</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notifications & Slack Webhooks */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Bell className="w-4 h-4 text-purple-400" />
              <span>Slack & Webhook Notification Routing</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Slack Incoming Webhook URL
              </label>
              <Input
                value={slackWebhook}
                onChange={(e) => setSlackWebhook(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="h-8 text-xs bg-[#0b101c] font-mono"
              />
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between p-2.5 rounded bg-slate-950/60 border border-slate-800">
                <div>
                  <div className="text-xs font-semibold text-white">Alert on Critical Security CVEs</div>
                  <div className="text-[11px] text-slate-400">Dispatch immediate Slack message when Critical finding is confirmed</div>
                </div>
                <Switch
                  checked={notifyOnCritical}
                  onCheckedChange={setNotifyOnCritical}
                />
              </div>

              <div className="flex items-center justify-between p-2.5 rounded bg-slate-950/60 border border-slate-800">
                <div>
                  <div className="text-xs font-semibold text-white">Alert on Successful Review Approvals</div>
                  <div className="text-[11px] text-slate-400">Notify team channel when PR receives 100% clean check from Arbiter</div>
                </div>
                <Switch
                  checked={notifyOnSuccess}
                  onCheckedChange={setNotifyOnSuccess}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Save button */}
        <div className="flex justify-end">
          <Button type="submit" variant="electric" size="sm" isLoading={isSaving} className="text-xs font-semibold px-6">
            <Save className="w-3.5 h-3.5 mr-1.5" />
            <span>Save Settings</span>
          </Button>
        </div>

        {/* Danger Zone */}
        <Card className="border-rose-950/60 bg-rose-950/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-rose-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              <span>Danger Zone</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold text-white">Purge Vector Semantic Embeddings</div>
                <div className="text-slate-400 text-[11px]">Clear cached repository symbol vectors in PostgreSQL pgvector</div>
              </div>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={handlePurgeVectorIndex}
                className="text-xs"
              >
                Purge Vector Cache
              </Button>
            </div>
          </CardContent>
        </Card>
      </form>
    </div>
  );
};

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { mockTeamMembers, TeamMember } from '@/services/mockData';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Lock,
  Mail,
  KeyRound,
  CheckCircle2,
  Trash2,
  MoreVertical,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const TeamManagement: React.FC = () => {
  const { success, info } = useToast();
  const [members, setMembers] = useState<TeamMember[]>(mockTeamMembers);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'Admin' | 'Maintainer' | 'Reviewer' | 'Auditor'>('Reviewer');

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;

    const newMember: TeamMember = {
      id: `usr-${Date.now()}`,
      name: inviteEmail.split('@')[0],
      email: inviteEmail,
      role: inviteRole,
      avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100&h=100&fit=crop&crop=faces',
      lastActive: 'Invited (Pending)',
      twoFactorEnabled: false,
    };

    setMembers((prev) => [...prev, newMember]);
    setShowInviteModal(false);
    setInviteEmail('');
    success('Invitation Dispatched', `Invited ${inviteEmail} as ${inviteRole}.`);
  };

  const handleRemoveMember = (id: string, name: string) => {
    setMembers((prev) => prev.filter((m) => m.id !== id));
    info('Member Removed', `${name} has been removed from the organization.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Team & Role-Based Access Control</h1>
            <Badge variant="purple">RBAC Active</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage engineering team access, code review permissions, and enterprise single sign-on.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="electric"
            size="sm"
            onClick={() => setShowInviteModal(true)}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Invite Team Member</span>
          </Button>
        </div>
      </div>

      {/* SSO Status Banner */}
      <div className="p-4 rounded-xl border border-slate-800 bg-[#0c101c] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <KeyRound className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white flex items-center gap-2">
              <span>Enterprise Single Sign-On (Okta / SAML 2.0)</span>
              <Badge variant="success" className="text-[9px] py-0">Enforced</Badge>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              All team members must authenticate using company domain credentials and hardware 2FA.
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => info('SAML Configuration', 'Redirecting to Identity Provider management...')}
          className="text-xs"
        >
          Configure SAML
        </Button>
      </div>

      {/* Members Table */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardHeader className="pb-3 border-b border-slate-800/80">
          <CardTitle className="text-sm font-semibold text-white">Active Team Members ({members.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0e1422] border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
                <tr>
                  <th className="p-3.5 pl-4">Member</th>
                  <th className="p-3.5">Role</th>
                  <th className="p-3.5">2FA Authentication</th>
                  <th className="p-3.5">Activity</th>
                  <th className="p-3.5 pr-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-900/40 transition">
                    <td className="p-3.5 pl-4 flex items-center gap-3">
                      <img
                        src={m.avatar}
                        alt={m.name}
                        className="w-7 h-7 rounded-full object-cover border border-slate-700"
                      />
                      <div>
                        <div className="font-semibold text-white text-xs">{m.name}</div>
                        <div className="text-[11px] text-slate-500 font-mono">{m.email}</div>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <Badge
                        variant={m.role === 'Admin' ? 'purple' : m.role === 'Maintainer' ? 'default' : 'secondary'}
                        className="text-[10px] py-0"
                      >
                        {m.role}
                      </Badge>
                    </td>
                    <td className="p-3.5 font-mono text-[11px]">
                      {m.twoFactorEnabled ? (
                        <span className="text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Enabled</span>
                        </span>
                      ) : (
                        <span className="text-amber-400 flex items-center gap-1">
                          <Lock className="w-3 h-3" />
                          <span>Pending 2FA</span>
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 text-slate-400 text-[11px] font-mono">{m.lastActive}</td>
                    <td className="p-3.5 pr-4 text-right">
                      {m.role !== 'Admin' && (
                        <button
                          onClick={() => handleRemoveMember(m.id, m.name)}
                          className="text-slate-500 hover:text-rose-400 p-1 rounded transition"
                          title="Remove user"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Invite Member Dialog */}
      <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
        <DialogHeader>
          <DialogTitle>Invite Team Member</DialogTitle>
          <DialogDescription>
            Grant code review and policy management permissions to a colleague.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleInvite} className="space-y-4">
          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Work Email Address
            </label>
            <Input
              type="email"
              placeholder="colleague@company.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Permission Role
            </label>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as any)}
              className="w-full h-8 rounded-md border border-slate-700 bg-slate-950 px-3 text-xs text-white focus:outline-none focus:ring-1 focus:ring-sky-500"
            >
              <option value="Reviewer">Reviewer (Inspect findings, comment, approve)</option>
              <option value="Maintainer">Maintainer (Manage repos, branch rules, review gates)</option>
              <option value="Admin">Admin (Full administrative & billing control)</option>
              <option value="Auditor">Auditor (Read-only security & compliance export)</option>
            </select>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setShowInviteModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="electric">
              Send Invitation
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};

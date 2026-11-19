import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { organizationApi } from '@/services/organizationApi';
import { Organization, OrganizationMember } from '@/types/auth';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Lock,
  Mail,
  KeyRound,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const TeamManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'admin' | 'maintainer' | 'member'>('member');

  // Load organizations
  const { data: orgs = [] } = useQuery({
    queryKey: ['organizations'],
    queryFn: organizationApi.listOrganizations,
  });

  const activeOrg = orgs[0];
  const activeOrgId = activeOrg?.id;

  // Load members for organization
  const { data: members = [], isLoading } = useQuery({
    queryKey: ['org-members', activeOrgId],
    queryFn: () => (activeOrgId ? organizationApi.listMembers(activeOrgId) : Promise.resolve([])),
    enabled: !!activeOrgId,
  });

  const inviteMutation = useMutation({
    mutationFn: ({ email, role }: { email: string; role: string }) =>
      organizationApi.addMember(activeOrgId!, email, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['org-members', activeOrgId] });
      setShowInviteModal(false);
      setInviteEmail('');
      success('Invitation Dispatched', `Invited ${inviteEmail} as ${inviteRole}.`);
    },
    onError: (err: any) => {
      error('Invite Failed', err.message || 'Could not add member.');
    },
  });

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail || !activeOrgId) return;
    inviteMutation.mutate({ email: inviteEmail, role: inviteRole });
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
            Manage organization engineers, security auditors, and automated review authorizations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="electric"
            size="sm"
            onClick={() => setShowInviteModal(true)}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <UserPlus className="w-3.5 h-3.5 text-amber-300" />
            <span>Invite Team Member</span>
          </Button>
        </div>
      </div>

      {/* Organization Badge Card */}
      {activeOrg && (
        <div className="p-3 rounded-xl border border-slate-800 bg-[#0e1422] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-white">{activeOrg.name}</span>
            <Badge variant="outline" className="font-mono text-[10px]">
              Plan: {activeOrg.plan.toUpperCase()}
            </Badge>
          </div>
          <span className="text-slate-400 font-mono text-[11px]">{members.length} Active Member(s)</span>
        </div>
      )}

      {/* Team Roster Card */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardHeader className="pb-3 border-b border-slate-800/80">
          <CardTitle className="text-base text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-sky-400" />
            <span>Organization Members ({members.length})</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Assigned roles and permission bounds for {activeOrg?.name || 'OpenReview Engineering'}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-800/80">
            {isLoading ? (
              <div className="p-8 text-center text-xs text-slate-500 font-mono">Loading team members...</div>
            ) : members.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 font-mono">
                No members found in organization. Use the button above to invite members.
              </div>
            ) : (
              members.map((m: OrganizationMember) => (
                <div key={m.id} className="p-4 flex items-center justify-between hover:bg-slate-900/30 transition">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-sky-400 font-mono">
                      {(m.user?.full_name || m.user?.email || 'MB').slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-bold text-white text-xs">{m.user?.full_name || 'Team Member'}</div>
                      <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
                        <Mail className="w-3 h-3 text-slate-500" />
                        <span>{m.user?.email || m.user_id}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Badge variant={m.role === 'admin' ? 'purple' : 'outline'} className="text-[10px] uppercase font-mono">
                      {m.role}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Invite Modal */}
      <Dialog open={showInviteModal} onOpenChange={setShowInviteModal}>
        <form onSubmit={handleInvite} className="space-y-4">
          <DialogHeader>
            <DialogTitle>Invite Member to Organization</DialogTitle>
            <DialogDescription>
              Assign role and access permissions for code review operations.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">Email Address</label>
              <Input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="bg-slate-950 border-slate-800 text-xs"
              />
            </div>

            <div>
              <label className="text-xs text-slate-300 font-medium block mb-1">Role & Permissions</label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as any)}
                className="w-full h-9 rounded-md bg-slate-950 border border-slate-800 px-3 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="member">Member — Review code & view findings</option>
                <option value="maintainer">Maintainer — Trigger reviews & approve patches</option>
                <option value="admin">Admin — Manage integrations & organization settings</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" size="sm" onClick={() => setShowInviteModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="electric" size="sm" isLoading={inviteMutation.isPending}>
              Send Invitation
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};

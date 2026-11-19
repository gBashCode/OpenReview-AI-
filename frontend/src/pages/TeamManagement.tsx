import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Dialog, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { organizationApi } from '@/services/organizationApi';
import { OrganizationMember } from '@/types/auth';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Mail,
  KeyRound,
  CheckCircle2,
  Lock,
  Building2,
  Sparkles,
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
      success('Invitation Dispatched', `Granted credentials to ${inviteEmail} as [${inviteRole.toUpperCase()}].`);
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

  const getRoleBadge = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return <Badge variant="amber" className="font-mono text-[10px] tracking-wider uppercase">[ADMIN]</Badge>;
      case 'maintainer':
        return <Badge variant="teal" className="font-mono text-[10px] tracking-wider uppercase">[MAINTAINER]</Badge>;
      default:
        return <Badge variant="outline" className="font-mono text-[10px] tracking-wider uppercase">[MEMBER]</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#2a2621]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[#d4a853] uppercase font-bold">
              [LEDGER · 09 · ACCESS CONTROL]
            </span>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5a9e6f]" />
            <span className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase">
              RBAC v2.4 Active
            </span>
          </div>
          <h1 className="font-serif text-3xl font-normal text-[#f4efe6] tracking-tight">
            Team & Delegation Authority
          </h1>
          <p className="font-sans text-xs text-[#8c8273] mt-1 max-w-2xl">
            Manage organization engineers, security auditors, and multi-agent review authorizations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="electric"
            size="sm"
            onClick={() => setShowInviteModal(true)}
            className="flex items-center gap-1.5 font-sans text-xs"
          >
            <UserPlus className="w-3.5 h-3.5 text-[#0e0d0b]" />
            <span>Grant Member Access</span>
          </Button>
        </div>
      </div>

      {/* Organization Ledger Card */}
      {activeOrg && (
        <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-[0_2px_8px_rgba(0,0,0,0.3)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-[2px] bg-[#1c1914] border border-[#342f27] flex items-center justify-center text-[#d4a853]">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-serif text-lg font-normal text-[#f4efe6]">{activeOrg.name}</span>
                <Badge variant="outline" className="font-mono text-[10px] text-[#d4a853] border-[#3e3525]">
                  PLAN: {activeOrg.plan.toUpperCase()}
                </Badge>
              </div>
              <p className="font-sans text-[11px] text-[#8c8273] mt-0.5">
                Workspace Tenant Identifier: <code className="font-mono text-[10px] text-[#c9bfaf]">{activeOrg.slug || activeOrg.id}</code>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-[2px] border border-[#2a2621] bg-[#0e0d0b] font-mono text-[11px] text-[#c9bfaf] flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#5a9e6f]" />
              <span>{members.length} Authorized Seat(s)</span>
            </div>
          </div>
        </div>
      )}

      {/* Permissions Guide Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f]/60">
          <div className="flex items-center gap-2 mb-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#d4a853]" />
            <span className="font-serif text-sm font-normal text-[#f4efe6]">Admin</span>
          </div>
          <p className="font-sans text-[11px] text-[#8c8273] leading-relaxed">
            Full governance authority. Can configure API keys, edit webhooks, invite members, and override consensus decisions.
          </p>
        </div>

        <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f]/60">
          <div className="flex items-center gap-2 mb-1">
            <KeyRound className="w-3.5 h-3.5 text-[#3a9e8f]" />
            <span className="font-serif text-sm font-normal text-[#f4efe6]">Maintainer</span>
          </div>
          <p className="font-sans text-[11px] text-[#8c8273] leading-relaxed">
            Operational review authority. Can trigger multi-agent reviews, approve synthetic patches, and commit auto-fixes.
          </p>
        </div>

        <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f]/60">
          <div className="flex items-center gap-2 mb-1">
            <Users className="w-3.5 h-3.5 text-[#c9bfaf]" />
            <span className="font-serif text-sm font-normal text-[#f4efe6]">Member</span>
          </div>
          <p className="font-sans text-[11px] text-[#8c8273] leading-relaxed">
            Read and collaborate access. Can inspect pull request findings, agent conference deliberations, and diffs.
          </p>
        </div>
      </div>

      {/* Team Roster Card */}
      <Card className="border-[#2a2621] bg-[#14120f]">
        <CardHeader className="pb-3 border-b border-[#2a2621]">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
                <Users className="w-4 h-4 text-[#d4a853]" />
                <span>Authorized Personnel ({members.length})</span>
              </CardTitle>
              <CardDescription className="font-sans text-xs text-[#8c8273] mt-0.5">
                Cryptographically validated roles and permissions for {activeOrg?.name || 'OpenReview Engineering'}
              </CardDescription>
            </div>
            <span className="font-mono text-[10px] text-[#8c8273] uppercase tracking-wider">
              [CONFIDENTIAL LEDGER]
            </span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-[#2a2621]">
            {isLoading ? (
              <div className="p-8 text-center font-mono text-xs text-[#8c8273]">
                Querying authorization ledger...
              </div>
            ) : members.length === 0 ? (
              <div className="p-8 text-center font-sans text-xs text-[#8c8273]">
                No members found in organization. Use the button above to grant member access.
              </div>
            ) : (
              members.map((m: OrganizationMember, idx: number) => (
                <div
                  key={m.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[#1a1713]/50 transition"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-9 h-9 rounded-[2px] bg-[#1c1914] border border-[#342f27] flex items-center justify-center font-mono font-bold text-xs text-[#d4a853]">
                      {(m.user?.full_name || m.user?.email || 'MB').slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-sans font-medium text-xs text-[#f4efe6]">
                          {m.user?.full_name || 'Engineering Peer'}
                        </span>
                        <span className="font-mono text-[10px] text-[#8c8273]">
                          #{String(idx + 1).padStart(2, '0')}
                        </span>
                      </div>
                      <div className="font-mono text-[11px] text-[#8c8273] flex items-center gap-1.5 mt-0.5">
                        <Mail className="w-3 h-3 text-[#5a5247]" />
                        <span>{m.user?.email || m.user_id}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="font-mono text-[10px] text-[#5a5247] hidden md:block">
                      ROLE_AUTH_VERIFIED
                    </div>
                    {getRoleBadge(m.role)}
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
            <DialogTitle>Grant Access to Organization</DialogTitle>
            <DialogDescription>
              Assign role and access permissions for automated code review operations.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2">
            <div>
              <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                Engineer Email Address
              </label>
              <Input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="colleague@domain.com"
                className="font-mono text-xs"
              />
            </div>

            <div>
              <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                Assigned Role & Bound
              </label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value as any)}
                className="w-full h-9 rounded-[2px] bg-[#0e0d0b] border border-[#2a2621] px-3 font-sans text-xs text-[#f4efe6] focus:outline-none focus:border-[#d4a853] focus:ring-1 focus:ring-[#d4a853]/40"
              >
                <option value="member">Member — Review code & inspect findings</option>
                <option value="maintainer">Maintainer — Trigger council reviews & approve patches</option>
                <option value="admin">Admin — Manage integrations, models & org settings</option>
              </select>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowInviteModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="electric"
              size="sm"
              isLoading={inviteMutation.isPending}
            >
              Dispatch Invitation
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </div>
  );
};

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { findingApi } from '@/services/findingApi';
import { Finding } from '@/types/finding';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  ShieldCheck,
  Download,
  Search,
  ExternalLink,
  Wrench,
  CheckCircle2,
  FileCode,
  Sparkles,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const SecurityReports: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const { data: findings = [], isLoading } = useQuery({
    queryKey: ['security-findings', severityFilter, search],
    queryFn: () =>
      findingApi.listFindings({
        category: 'security',
        severity: severityFilter === 'all' ? undefined : severityFilter,
        search: search || undefined,
        limit: 100,
      }),
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, is_resolved }: { id: string; is_resolved: boolean }) =>
      findingApi.updateFinding(id, { is_resolved }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['security-findings'] });
      success('Finding Updated', 'Security issue status synchronized.');
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Could not update finding.');
    },
  });

  const criticalCount = findings.filter((f) => f.severity.toLowerCase() === 'critical').length;
  const highCount = findings.filter((f) => f.severity.toLowerCase() === 'high').length;
  const mediumCount = findings.filter((f) => f.severity.toLowerCase() === 'medium').length;
  const resolvedCount = findings.filter((f) => f.is_resolved).length;

  const handleExportSarif = () => {
    const sarifBlob = new Blob([JSON.stringify({ version: '2.1.0', runs: findings }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(sarifBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openreview-security-report.sarif.json';
    a.click();
    success('Report Exported', 'SARIF v2.1 format downloaded successfully.');
  };

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 07 · SECURITY]</span>
            <div className="h-2.5 w-px bg-[#36312a]" />
            <span className="text-[10px] font-mono tracking-wider text-[#8a8378] uppercase">Vulnerability Ledger</span>
          </div>
          <h1 className="text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight mt-1">
            Security Intelligence & CVEs
          </h1>
          <p className="text-xs text-[#8a8378] mt-1.5 leading-relaxed">
            Automated deep security analysis detecting injection flaws, secret leaks, and access control gaps.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportSarif}
            className="flex items-center gap-1.5 text-xs font-mono border-[#2e2a24] text-[#b8b0a2]"
          >
            <Download className="w-3.5 h-3.5 text-[#8a8378]" />
            <span>Export SARIF / JSON</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={() => navigate('/autofix')}
            className="flex items-center gap-1.5 text-xs font-mono font-medium"
          >
            <Wrench className="w-3.5 h-3.5 text-[#0e0d0b]" />
            <span>Remediate in AutoFix</span>
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] font-mono text-[#8a8378] mb-1 flex items-center justify-between">
            <span>[01] CRITICAL FLAWS</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#c75a4a]" />
          </div>
          <div className="text-2xl font-serif text-[#e06c5b]">{criticalCount}</div>
          <p className="text-[11px] font-mono text-[#6a6358] mt-1">High consequence vulnerabilities</p>
        </div>

        <div className="p-4 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] font-mono text-[#8a8378] mb-1 flex items-center justify-between">
            <span>[02] HIGH SEVERITY</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#e29b38]" />
          </div>
          <div className="text-2xl font-serif text-[#f0af54]">{highCount}</div>
          <p className="text-[11px] font-mono text-[#6a6358] mt-1">Requires reviewer triage</p>
        </div>

        <div className="p-4 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] font-mono text-[#8a8378] mb-1 flex items-center justify-between">
            <span>[03] MEDIUM RISK</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#d4a853]" />
          </div>
          <div className="text-2xl font-serif text-[#d4a853]">{mediumCount}</div>
          <p className="text-[11px] font-mono text-[#6a6358] mt-1">Hardening & best practices</p>
        </div>

        <div className="p-4 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] font-mono text-[#8a8378] mb-1 flex items-center justify-between">
            <span>[04] RESOLVED FLAWS</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
          </div>
          <div className="text-2xl font-serif text-[#6cb582]">{resolvedCount}</div>
          <p className="text-[11px] font-mono text-[#6a6358] mt-1">Patched or mitigated</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-2.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#6a6358]" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search security findings or file paths..."
            className="pl-9 h-8 text-xs font-mono bg-[#161411] border-[#2a2621]"
          />
        </div>

        <div className="flex items-center gap-1 w-full sm:w-auto font-mono text-xs">
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-[2px] text-xs font-mono capitalize transition-colors ${
                severityFilter === sev
                  ? 'bg-[#221f1a] text-[#d4a853] font-medium border border-[#38332a]'
                  : 'text-[#8a8378] hover:text-[#d8d2c4]'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-[#6a6358] font-mono">Loading security findings from backend...</div>
        ) : findings.length === 0 ? (
          <Card className="border-dashed border-[#26221c] bg-[#13110e]">
            <CardContent className="p-12 text-center space-y-2">
              <ShieldCheck className="w-8 h-8 text-[#5a9e6f] mx-auto" />
              <div className="text-base font-serif text-[#f5f0e6]">No Security Vulnerabilities Detected</div>
              <p className="text-xs text-[#8a8378] max-w-sm mx-auto font-mono">
                No active security findings match your criteria across analyzed pull requests.
              </p>
            </CardContent>
          </Card>
        ) : (
          findings.map((f: Finding) => (
            <Card key={f.id} className="border-[#26221c] bg-[#13110e] hover:border-[#383229] transition-colors">
              <CardContent className="p-5 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-[2px] flex items-center justify-center shrink-0 mt-0.5 ${
                        f.severity.toLowerCase() === 'critical'
                          ? 'bg-[#221614] text-[#e06c5b] border border-[#c75a4a]/30'
                          : f.severity.toLowerCase() === 'high'
                          ? 'bg-[#221b12] text-[#f0af54] border border-[#e29b38]/30'
                          : 'bg-[#1e1b16] text-[#d4a853] border border-[#d4a853]/30'
                      }`}
                    >
                      <ShieldAlert className="w-4 h-4" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-serif text-base text-[#f5f0e6]">{f.title}</span>
                        <Badge
                          variant={
                            f.severity.toLowerCase() === 'critical'
                              ? 'destructive'
                              : f.severity.toLowerCase() === 'high'
                              ? 'warning'
                              : 'secondary'
                          }
                          className="text-[10px] py-0 font-mono"
                        >
                          {f.severity.toUpperCase()}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] font-mono py-0 text-[#8a8378] border-[#2e2a24]">
                          {f.verification_status}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-[#787165] font-mono">
                        <FileCode className="w-3.5 h-3.5 text-[#6a6358]" />
                        <span>
                          {f.file_path}:{f.line_number || '—'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant={f.is_resolved ? 'outline' : 'secondary'}
                      size="sm"
                      onClick={() => resolveMutation.mutate({ id: f.id, is_resolved: !f.is_resolved })}
                      className="text-xs font-mono h-7 border-[#2e2a24]"
                    >
                      {f.is_resolved ? 'Reopen' : 'Mark Resolved'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/reviews/${f.review_id}`)}
                      className="text-xs font-mono h-7 text-[#d4a853] hover:text-[#f5f0e6]"
                    >
                      <span>Review Details</span>
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </div>

                <p className="text-xs text-[#b8b0a2] leading-relaxed font-sans">{f.message}</p>

                {f.evidence && (
                  <div className="p-3 rounded-[2px] bg-[#0c0a09] border border-[#24201a] font-mono text-[11px] text-[#b8b0a2] overflow-x-auto">
                    <div className="text-[9px] uppercase font-mono text-[#6a6358] mb-1">Source Evidence</div>
                    <pre>{f.evidence}</pre>
                  </div>
                )}

                {f.suggested_patch && (
                  <div className="p-3 rounded-[2px] bg-[#142017] border border-[#5a9e6f]/30 font-mono text-[11px] text-[#6cb582] overflow-x-auto">
                    <div className="text-[9px] uppercase font-mono text-[#5a9e6f] font-medium mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-[#d4a853]" />
                      <span>Suggested Remediation</span>
                    </div>
                    <pre>{f.suggested_patch}</pre>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

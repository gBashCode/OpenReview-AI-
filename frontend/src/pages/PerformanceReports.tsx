import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { findingApi } from '@/services/findingApi';
import { Finding } from '@/types/finding';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  TrendingDown,
  Clock,
  Database,
  Cpu,
  ArrowRight,
  Wrench,
  FileCode,
  Flame,
  Search,
  CheckCircle2,
  ExternalLink,
  Sparkles,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const PerformanceReports: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error } = useToast();
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const { data: findings = [], isLoading } = useQuery({
    queryKey: ['performance-findings', severityFilter, search],
    queryFn: () =>
      findingApi.listFindings({
        category: 'performance',
        severity: severityFilter === 'all' ? undefined : severityFilter,
        search: search || undefined,
        limit: 100,
      }),
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, is_resolved }: { id: string; is_resolved: boolean }) =>
      findingApi.updateFinding(id, { is_resolved }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['performance-findings'] });
      success('Finding Updated', 'Performance issue status synchronized.');
    },
    onError: (err: any) => {
      error('Update Failed', err.message || 'Could not update finding.');
    },
  });

  const criticalCount = findings.filter((f) => f.severity.toLowerCase() === 'critical').length;
  const highCount = findings.filter((f) => f.severity.toLowerCase() === 'high').length;
  const mediumCount = findings.filter((f) => f.severity.toLowerCase() === 'medium').length;
  const resolvedCount = findings.filter((f) => f.is_resolved).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Performance & Complexity Reports</h1>
            <Badge variant="warning">Latency & Big-O Profiling</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Algorithmic efficiency, N+1 ORM query detection, and async event loop blocking analysis.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="electric"
            size="sm"
            onClick={() => navigate('/autofix')}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Wrench className="w-3.5 h-3.5 text-amber-300" />
            <span>Apply Optimizations</span>
          </Button>
        </div>
      </div>

      {/* High-level performance KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Critical Bottlenecks</span>
              <Database className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">{criticalCount}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">High latency regressions</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Algorithmic Inefficiencies</span>
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">{highCount}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Sub-optimal loops & scans</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Minor Warnings</span>
              <Flame className="w-3.5 h-3.5 text-yellow-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-yellow-400">{mediumCount}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Memory & resource tuning</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Optimizations Applied</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">{resolvedCount}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Resolved in active PRs</p>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-xl border border-slate-800 bg-[#0e1422]">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search performance findings or file paths..."
            className="pl-9 h-8 text-xs bg-slate-950/60 border-slate-800"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto">
          {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-md text-xs font-semibold capitalize transition ${
                severityFilter === sev
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Performance Findings List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-500 font-mono">Loading performance findings from backend...</div>
        ) : findings.length === 0 ? (
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardContent className="p-12 text-center space-y-2">
              <Zap className="w-8 h-8 text-emerald-400 mx-auto" />
              <div className="text-sm font-semibold text-white">All Clear — No Performance Regressions</div>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                No active performance bottlenecks detected in analyzed pull requests.
              </p>
            </CardContent>
          </Card>
        ) : (
          findings.map((f: Finding) => (
            <Card key={f.id} className="border-slate-800 bg-[#0c101c] hover:border-slate-700/80 transition">
              <CardContent className="p-5 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                        f.severity.toLowerCase() === 'critical'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      <Zap className="w-4 h-4" />
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-white text-sm">{f.title}</span>
                        <Badge
                          variant={
                            f.severity.toLowerCase() === 'critical'
                              ? 'destructive'
                              : f.severity.toLowerCase() === 'high'
                              ? 'warning'
                              : 'secondary'
                          }
                          className="text-[10px] py-0"
                        >
                          {f.severity.toUpperCase()}
                        </Badge>
                        <Badge variant="outline" className="text-[10px] font-mono py-0 text-slate-400">
                          {f.verification_status}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                        <FileCode className="w-3.5 h-3.5 text-slate-500" />
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
                      className="text-xs h-7"
                    >
                      {f.is_resolved ? 'Reopen' : 'Mark Resolved'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/reviews/${f.review_id}`)}
                      className="text-xs h-7 text-sky-400 hover:text-sky-300"
                    >
                      <span>Review Details</span>
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{f.message}</p>

                {f.evidence && (
                  <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-900 font-mono text-[11px] text-slate-300 overflow-x-auto">
                    <div className="text-[10px] uppercase text-slate-500 mb-1">Source Evidence</div>
                    <pre>{f.evidence}</pre>
                  </div>
                )}

                {f.suggested_patch && (
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/20 font-mono text-[11px] text-emerald-300 overflow-x-auto">
                    <div className="text-[10px] uppercase text-emerald-400 font-semibold mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-amber-300" />
                      <span>Suggested Optimization</span>
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

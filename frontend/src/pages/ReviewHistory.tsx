import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { mockReviewAuditLogs, ReviewAuditLog } from '@/services/mockData';
import { useNavigate } from 'react-router-dom';
import {
  History,
  Search,
  Download,
  GitPullRequest,
  GitCommit,
  User,
  Clock,
  ArrowRight,
  Filter,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const ReviewHistory: React.FC = () => {
  const navigate = useNavigate();
  const { success } = useToast();
  const [search, setSearch] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState('all');

  const filteredLogs = mockReviewAuditLogs.filter((log) => {
    const matchesSearch =
      log.repository.toLowerCase().includes(search.toLowerCase()) ||
      log.author.toLowerCase().includes(search.toLowerCase()) ||
      String(log.prNumber).includes(search);
    const matchesOutcome = outcomeFilter === 'all' || log.outcome === outcomeFilter;
    return matchesSearch && matchesOutcome;
  });

  const handleExportCsv = () => {
    const header = 'ID,Timestamp,Repository,PR,Commit,Author,Outcome,Score,Findings,DurationMs,Model\n';
    const rows = filteredLogs.map((l) =>
      `${l.id},${l.timestamp},${l.repository},${l.prNumber},${l.commitSha},${l.author},${l.outcome},${l.score},${l.findingsCount},${l.durationMs},${l.agentModel}`
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openreview-audit-logs.csv';
    a.click();
    success('Audit Log Exported', 'CSV report downloaded.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Review History & Compliance Audit</h1>
          <p className="text-xs text-slate-400 mt-1">
            Complete cryptographic audit trail of all automated multi-agent code reviews and checks.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export Audit CSV</span>
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <Input
            placeholder="Search by repo, author, or #PR..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs bg-[#0b101c]"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-[#0e1422] p-1 rounded-lg border border-slate-800 text-xs">
          {['all', 'Passed', 'Changes Requested'].map((o) => (
            <button
              key={o}
              onClick={() => setOutcomeFilter(o)}
              className={`px-2.5 py-1 rounded text-[11px] transition ${
                outcomeFilter === o
                  ? 'bg-sky-500/20 text-sky-400 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {o}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Table */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0e1422] border-b border-slate-800 text-[11px] font-mono text-slate-400 uppercase">
                <tr>
                  <th className="p-3.5 pl-4">Timestamp</th>
                  <th className="p-3.5">Repository & PR</th>
                  <th className="p-3.5">Commit</th>
                  <th className="p-3.5">Author</th>
                  <th className="p-3.5">Outcome</th>
                  <th className="p-3.5">Score</th>
                  <th className="p-3.5">Latency</th>
                  <th className="p-3.5 pr-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredLogs.map((log: ReviewAuditLog) => (
                  <tr key={log.id} className="hover:bg-slate-900/40 transition">
                    <td className="p-3.5 pl-4 text-slate-400 text-[11px]">{log.timestamp}</td>
                    <td className="p-3.5">
                      <div className="font-semibold text-white font-sans">{log.repository}</div>
                      <div className="text-[10px] text-sky-400">PR #{log.prNumber}</div>
                    </td>
                    <td className="p-3.5 text-slate-300">
                      <span className="flex items-center gap-1">
                        <GitCommit className="w-3 h-3 text-slate-500" />
                        {log.commitSha}
                      </span>
                    </td>
                    <td className="p-3.5 text-slate-400 font-sans">{log.author}</td>
                    <td className="p-3.5">
                      <Badge
                        variant={log.outcome === 'Passed' ? 'success' : 'warning'}
                        className="text-[10px] py-0"
                      >
                        {log.outcome}
                      </Badge>
                    </td>
                    <td className="p-3.5 font-bold text-slate-200">
                      {log.score.toFixed(1)}/100
                    </td>
                    <td className="p-3.5 text-slate-500 text-[11px]">
                      {log.durationMs}ms
                    </td>
                    <td className="p-3.5 pr-4 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate('/reviews/sample')}
                        className="h-7 text-xs text-sky-400 hover:text-sky-300"
                      >
                        <span>Inspect</span>
                        <ArrowRight className="w-3 h-3 ml-1" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

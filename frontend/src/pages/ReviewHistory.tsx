import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { reviewApi } from '@/services/reviewApi';
import { Review } from '@/types/review';
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
  CheckCircle2,
  FileCheck,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const ReviewHistory: React.FC = () => {
  const navigate = useNavigate();
  const { success } = useToast();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: reviews = [], isLoading } = useQuery({
    queryKey: ['reviews-history', statusFilter],
    queryFn: () =>
      reviewApi.listReviews({
        status: statusFilter === 'all' ? undefined : statusFilter,
        limit: 100,
      }),
  });

  const filteredReviews = reviews.filter((rev) => {
    const matchesSearch =
      rev.id.toLowerCase().includes(search.toLowerCase()) ||
      rev.commit_sha.toLowerCase().includes(search.toLowerCase()) ||
      (rev.summary && rev.summary.toLowerCase().includes(search.toLowerCase()));
    return matchesSearch;
  });

  const handleExportCsv = () => {
    const header = 'Review ID,Status,Score,Security,Performance,Quality,Findings,Commit,Created At\n';
    const rows = filteredReviews
      .map(
        (r) =>
          `"${r.id}","${r.status}",${r.score || 0},${r.security_score || 0},${r.performance_score || 0},${r.quality_score || 0},${r.findings_count},"${r.commit_sha}","${r.created_at}"`
      )
      .join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openreview-review-history.csv';
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
            placeholder="Search by review ID, commit SHA, or summary..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs bg-[#0b101c]"
          />
        </div>

        <div className="flex items-center gap-1.5 bg-[#0e1422] p-1 rounded-lg border border-slate-800 text-xs">
          {['all', 'completed', 'analyzing', 'failed'].map((o) => (
            <button
              key={o}
              onClick={() => setStatusFilter(o)}
              className={`px-2.5 py-1 rounded text-[11px] capitalize transition ${
                statusFilter === o
                  ? 'bg-sky-500/20 text-sky-400 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {o}
            </button>
          ))}
        </div>
      </div>

      {/* Reviews Table / List */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardContent className="p-0">
          <div className="divide-y divide-slate-800/80">
            {isLoading ? (
              <div className="p-12 text-center text-xs text-slate-500 font-mono">
                Loading review history from backend...
              </div>
            ) : filteredReviews.length === 0 ? (
              <div className="p-12 text-center space-y-2">
                <FileCheck className="w-8 h-8 text-slate-600 mx-auto" />
                <div className="text-sm font-semibold text-white">No Review Records Found</div>
                <p className="text-xs text-slate-400">
                  Trigger an automated code review on any pull request to record an audit entry.
                </p>
              </div>
            ) : (
              filteredReviews.map((rev: Review) => (
                <div
                  key={rev.id}
                  onClick={() => navigate(`/reviews/${rev.id}`)}
                  className="p-4 flex items-center justify-between hover:bg-slate-900/50 cursor-pointer transition"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                      <GitPullRequest className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white text-xs">Review {rev.id.slice(0, 8)}</span>
                        <Badge
                          variant={
                            rev.status === 'completed'
                              ? 'success'
                              : rev.status === 'analyzing'
                              ? 'warning'
                              : 'destructive'
                          }
                          className="text-[10px] py-0"
                        >
                          {rev.status.toUpperCase()}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-slate-500 font-mono mt-1">
                        <span className="flex items-center gap-1">
                          <GitCommit className="w-3 h-3 text-slate-600" />
                          <span>{rev.commit_sha.slice(0, 7)}</span>
                        </span>
                        <span>•</span>
                        <span>{rev.findings_count} findings</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-slate-600" />
                          <span>{new Date(rev.created_at).toLocaleString()}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="font-mono font-bold text-sm text-sky-400">
                        {rev.score != null ? `${rev.score.toFixed(1)}/100` : '--'}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Security: {rev.security_score != null ? `${rev.security_score.toFixed(0)}%` : '--'}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-slate-500" />
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

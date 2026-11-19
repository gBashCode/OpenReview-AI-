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
  Search,
  Download,
  GitPullRequest,
  GitCommit,
  Clock,
  ArrowRight,
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
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 09 · AUDIT]</span>
            <div className="h-2.5 w-px bg-[#36312a]" />
            <span className="text-[10px] font-mono tracking-wider text-[#8a8378] uppercase">Review Audit Trail</span>
          </div>
          <h1 className="text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight mt-1">
            Review History & Compliance Audit
          </h1>
          <p className="text-xs text-[#8a8378] mt-1.5 leading-relaxed">
            Cryptographic audit trail of all automated multi-agent code reviews, static checks, and arbiter verdicts.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportCsv}
            className="flex items-center gap-1.5 text-xs font-mono border-[#2e2a24] text-[#b8b0a2]"
          >
            <Download className="w-3.5 h-3.5 text-[#8a8378]" />
            <span>Export Audit CSV</span>
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#6a6358]" />
          <Input
            placeholder="Search by review ID, commit SHA, or summary..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-8 text-xs font-mono bg-[#14120f] border-[#26221c]"
          />
        </div>

        <div className="flex items-center gap-1 bg-[#14120f] p-1 rounded-[2px] border border-[#26221c] text-xs font-mono">
          {['all', 'completed', 'analyzing', 'failed'].map((o) => (
            <button
              key={o}
              onClick={() => setStatusFilter(o)}
              className={`px-3 py-1 rounded-[2px] text-[11px] capitalize transition-colors ${
                statusFilter === o
                  ? 'bg-[#221f1a] text-[#d4a853] font-medium border border-[#38332a]'
                  : 'text-[#8a8378] hover:text-[#d8d2c4]'
              }`}
            >
              {o}
            </button>
          ))}
        </div>
      </div>

      {/* Reviews Table / List */}
      <Card className="border-[#26221c] bg-[#13110e]">
        <CardContent className="p-0">
          <div className="divide-y divide-[#201d18]">
            {isLoading ? (
              <div className="p-12 text-center text-xs text-[#6a6358] font-mono">
                Querying review history from backend...
              </div>
            ) : filteredReviews.length === 0 ? (
              <div className="p-12 text-center space-y-2">
                <FileCheck className="w-8 h-8 text-[#6a6358] mx-auto mb-2" />
                <div className="text-base font-serif text-[#f5f0e6]">No Review Records Found</div>
                <p className="text-xs text-[#8a8378] font-mono">
                  Trigger an automated code review on any pull request to record an audit entry.
                </p>
              </div>
            ) : (
              filteredReviews.map((rev: Review) => (
                <div
                  key={rev.id}
                  onClick={() => navigate(`/reviews/${rev.id}`)}
                  className="p-4 flex items-center justify-between hover:bg-[#1a1713] cursor-pointer transition-colors"
                >
                  <div className="flex items-center gap-3.5">
                    <div className="w-9 h-9 rounded-[2px] bg-[#1b1915] border border-[#332e26] flex items-center justify-center text-[#d4a853]">
                      <GitPullRequest className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-medium text-[#f5f0e6]">REV-{rev.id.slice(0, 8)}</span>
                        <Badge
                          variant={
                            rev.status === 'completed'
                              ? 'success'
                              : rev.status === 'analyzing'
                              ? 'warning'
                              : 'destructive'
                          }
                          className="text-[10px] py-0 font-mono"
                        >
                          {rev.status.toUpperCase()}
                        </Badge>
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-[#787165] font-mono mt-1">
                        <span className="flex items-center gap-1">
                          <GitCommit className="w-3 h-3 text-[#6a6358]" />
                          <span>{rev.commit_sha.slice(0, 7)}</span>
                        </span>
                        <span>·</span>
                        <span>{rev.findings_count} findings</span>
                        <span>·</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-[#6a6358]" />
                          <span>{new Date(rev.created_at).toLocaleString()}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="font-serif text-base text-[#d4a853]">
                        {rev.score != null ? `${rev.score.toFixed(1)} / 100` : '--'}
                      </div>
                      <div className="text-[10px] text-[#787165] font-mono">
                        Security: {rev.security_score != null ? `${rev.security_score.toFixed(0)}%` : '--'}
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[#6a6358]" />
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

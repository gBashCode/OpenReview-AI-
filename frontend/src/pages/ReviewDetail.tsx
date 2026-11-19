import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi } from '@/services/reviewApi';
import { autofixApi } from '@/services/autofixApi';
import { Review, ReviewComment } from '@/types/review';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ReviewSummaryScore } from '@/components/reviews/ReviewSummaryScore';
import { FindingCard } from '@/components/reviews/FindingCard';
import { MonacoDiffViewer } from '@/components/code/MonacoDiffViewer';
import {
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  Clock,
  FileCode,
  Shield,
  FileText,
  Send,
  Wrench,
  Bot,
  AlertTriangle,
  FolderTree,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

interface ReviewFile {
  name: string;
  path: string;
  findingsCount: number;
  comments: ReviewComment[];
  suggestedPatch?: string | null;
}

export const ReviewDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, error, info } = useToast();

  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  // Fetch real review data
  const { data: review, isLoading } = useQuery<Review>({
    queryKey: ['review', id],
    queryFn: () => reviewApi.getReview(id!),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'pending' || query.state.data?.status === 'analyzing' ? 3000 : false),
  });

  // Subscribe to real-time Server-Sent Events (SSE) updates
  useEffect(() => {
    if (!id) return;
    const unsubscribe = reviewApi.streamEvents(id, (eventType: string, data: any) => {
      if (eventType === 'status_update') {
        queryClient.invalidateQueries({ queryKey: ['review', id] });
      } else if (eventType === 'completed') {
        queryClient.invalidateQueries({ queryKey: ['review', id] });
        info('Review Completed', `Autonomous agents finished evaluation with status: ${data?.status || 'completed'}`);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [id, queryClient, info]);

  // Orchestrate / Run real multi-agent review pass
  const orchestrateMutation = useMutation({
    mutationFn: () => reviewApi.orchestrateReview(id!),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['review', id] });
      success(
        'Review Orchestration Started',
        `Autonomous agent conference analyzing PR changes (Status: ${updated.status}).`
      );
    },
    onError: (err: any) => {
      error('Review Failed', err.message || 'Could not orchestrate multi-agent review');
    },
  });

  // Publish verified review directly to GitHub PR
  const publishMutation = useMutation({
    mutationFn: () => reviewApi.publishReview(id!),
    onSuccess: (res) => {
      success(
        'Published to GitHub',
        `Posted review comments and commit status to GitHub PR (${res.published_comments_count ?? 0} comments).`
      );
    },
    onError: (err: any) => {
      error('Publishing Failed', err.message || 'Error publishing review to GitHub API');
    },
  });

  // Group comments into files dynamically
  const changedFiles: ReviewFile[] = useMemo(() => {
    if (!review?.comments || review.comments.length === 0) return [];
    const map = new Map<string, ReviewFile>();
    for (const c of review.comments) {
      const p = c.file_path || 'source_code.py';
      const name = p.split('/').pop() || p;
      if (!map.has(p)) {
        map.set(p, {
          path: p,
          name,
          findingsCount: 0,
          comments: [],
          suggestedPatch: c.suggested_patch,
        });
      }
      const item = map.get(p)!;
      item.findingsCount += 1;
      item.comments.push(c);
      if (!item.suggestedPatch && c.suggested_patch) {
        item.suggestedPatch = c.suggested_patch;
      }
    }
    return Array.from(map.values());
  }, [review?.comments]);

  const currentFile = changedFiles[selectedFileIndex] || changedFiles[0];
  const fileComments = currentFile ? currentFile.comments : review?.comments || [];

  if (isLoading) {
    return (
      <div className="p-16 text-center text-slate-500 font-mono text-xs">
        Loading review intelligence and agent verdicts...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <Link
            to="/pull-requests"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Pull Requests</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">
              PR Review #{review?.id ? review.id.substring(0, 8) : 'Pass'}
            </h1>
            <Badge
              variant={
                review?.status === 'completed'
                  ? 'success'
                  : review?.status === 'analyzing'
                  ? 'purple'
                  : 'warning'
              }
              className="capitalize text-xs flex items-center gap-1"
            >
              {review?.status === 'analyzing' && <Activity className="w-3 h-3 animate-spin" />}
              <span>{review?.status || 'Pending'}</span>
            </Badge>
            <span className="text-xs text-slate-500 font-mono">
              SHA: {review?.commit_sha ? review.commit_sha.substring(0, 7) : 'HEAD'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => publishMutation.mutate()}
            isLoading={publishMutation.isPending}
            className="flex items-center gap-1.5 text-xs"
          >
            <Send className="w-3.5 h-3.5 text-sky-400" />
            <span>Publish to GitHub</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={() => orchestrateMutation.mutate()}
            isLoading={orchestrateMutation.isPending || review?.status === 'analyzing'}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>{review?.status === 'completed' ? 'Re-run Review' : 'Run Multi-Agent Review'}</span>
          </Button>
        </div>
      </div>

      {/* Summary Score Indicators */}
      <ReviewSummaryScore
        score={review?.score}
        securityScore={review?.security_score}
        performanceScore={review?.performance_score}
        qualityScore={review?.quality_score}
      />

      {/* Arbiter Executive Summary Card */}
      {review?.summary && (
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Arbiter Consensus Summary</span>
              </span>
              <span className="text-[11px] font-mono text-purple-400 font-normal">
                Multi-Agent Deliberated
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
            {review.summary}
          </CardContent>
        </Card>
      )}

      {/* Code Review Workspace: File Tree + Diff Viewer + Inline Finding Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (3 cols): Changed File Explorer */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <span className="flex items-center gap-1.5">
              <FolderTree className="w-3.5 h-3.5 text-sky-400" />
              <span>Affected Files ({changedFiles.length})</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">
              {review?.findings_count || 0} findings
            </span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#0c101c] p-2 space-y-1">
            {changedFiles.length === 0 ? (
              <div className="p-4 text-center text-slate-500 text-xs">
                No affected files detected yet.
              </div>
            ) : (
              changedFiles.map((file, idx) => (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => setSelectedFileIndex(idx)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition flex items-center justify-between ${
                    selectedFileIndex === idx
                      ? 'bg-sky-500/10 border border-sky-500/30 text-sky-300 font-semibold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] shrink-0">
                    {file.findingsCount > 0 && (
                      <span className="w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 text-center leading-4 font-bold">
                        {file.findingsCount}
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-950/10 text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 text-purple-300 font-semibold text-[11px]">
              <Bot className="w-3.5 h-3.5" />
              <span>Conference Navigation</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Explore cross-examination and adversarial challenges between Bug Hunter, Security Sentinel and Reviewer 2 in the conference room.
            </p>
            <Link
              to="/conference"
              className="inline-flex items-center gap-1 text-[11px] text-purple-400 hover:underline pt-1"
            >
              <span>Open Agent Conference</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Middle Column (6 cols): Monaco Diff Viewer */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-sky-400" />
              <span className="font-mono text-xs">{currentFile?.path || 'Source Diff'}</span>
            </div>
            <Badge variant="outline" className="font-mono text-[10px]">
              Diff Inspection
            </Badge>
          </div>

          <MonacoDiffViewer
            fileName={currentFile?.name || 'file.py'}
            language="python"
            originalCode={
              currentFile?.comments?.[0]?.message
                ? `# Original Context from ${currentFile.path}\n# Line ${currentFile.comments[0].line_number || 1}\n\n# Code under inspection:\n` +
                  (currentFile.comments[0].message || '')
                : '# Source code before review'
            }
            code={
              currentFile?.suggestedPatch ||
              (currentFile?.comments?.[0]?.suggested_patch
                ? currentFile.comments[0].suggested_patch
                : '# No automated patch suggested for this file.')
            }
            isDiffMode={true}
            height="480px"
          />
        </div>

        {/* Right Column (3 cols): Inline AI Findings & AutoFix action */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-rose-400" />
              <span>Findings ({fileComments.length})</span>
            </span>
            <Link to="/autofix" className="text-[10px] text-sky-400 hover:underline flex items-center gap-0.5">
              <span>AutoFix Studio</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-0.5">
            {fileComments.length === 0 ? (
              <Card className="p-6 text-center border-dashed border-slate-800 bg-[#0c101c]">
                <Clock className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400">
                  No verified findings on this file.
                </p>
              </Card>
            ) : (
              fileComments.map((finding) => (
                <FindingCard
                  key={finding.id}
                  comment={finding}
                  isSelected={selectedFindingId === finding.id}
                  onSelect={() => setSelectedFindingId(finding.id)}
                />
              ))
            )}

            <Button
              variant="electric"
              size="sm"
              onClick={() => navigate('/autofix')}
              className="w-full text-xs flex items-center justify-center gap-2 mt-2"
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>Open in AutoFix Studio</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

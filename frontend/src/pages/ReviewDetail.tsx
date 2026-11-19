import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi } from '@/services/reviewApi';
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
  FileCode,
  Shield,
  FileText,
  Send,
  Wrench,
  Bot,
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
      <div className="p-16 text-center text-[#6a6358] font-mono text-xs">
        Loading review intelligence and agent verdicts...
      </div>
    );
  }

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Top Header */}
      <div>
        <Link
          to="/pull-requests"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-[#8a8378] hover:text-[#d4a853] transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Pull Requests</span>
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 04]</span>
              <div className="h-2.5 w-px bg-[#36312a]" />
              <span className="text-xs text-[#8a8378] font-mono">
                SHA: {review?.commit_sha ? review.commit_sha.substring(0, 7) : 'HEAD'}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1">
              <h1 className="text-2xl lg:text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight">
                Review #{review?.id ? review.id.substring(0, 8) : 'Pass'}
              </h1>
              <Badge
                variant={
                  review?.status === 'completed'
                    ? 'success'
                    : review?.status === 'analyzing'
                    ? 'purple'
                    : 'warning'
                }
                className="capitalize text-xs flex items-center gap-1 font-mono"
              >
                {review?.status === 'analyzing' && <Activity className="w-3 h-3 animate-spin" />}
                <span>{review?.status || 'Pending'}</span>
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => publishMutation.mutate()}
              isLoading={publishMutation.isPending}
              className="flex items-center gap-1.5 text-xs font-mono border-[#2e2a24] text-[#b8b0a2] hover:border-[#d4a853]/40"
            >
              <Send className="w-3.5 h-3.5 text-[#3a9e8f]" />
              <span>Publish to GitHub</span>
            </Button>

            <Button
              variant="electric"
              size="sm"
              onClick={() => orchestrateMutation.mutate()}
              isLoading={orchestrateMutation.isPending || review?.status === 'analyzing'}
              className="flex items-center gap-1.5 text-xs font-mono font-medium"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#0e0d0b]" />
              <span>{review?.status === 'completed' ? 'Re-run Review' : 'Run Multi-Agent Review'}</span>
            </Button>
          </div>
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
        <Card className="border-[#26221c] bg-[#13110e]">
          <CardHeader className="pb-2 border-b border-[#221f1a]">
            <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#5a9e6f]" />
                <span>Arbiter Consensus Summary</span>
              </span>
              <span className="text-[10px] font-mono text-[#d4a853] font-normal tracking-wider uppercase">
                Multi-Agent Deliberated
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-5 text-xs text-[#d8d2c4] font-sans whitespace-pre-wrap leading-relaxed">
            {review.summary}
          </CardContent>
        </Card>
      )}

      {/* Code Review Workspace: File Tree + Diff Viewer + Inline Finding Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (3 cols): Changed File Explorer */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-[#8a8378] px-1">
            <span className="flex items-center gap-1.5">
              <FolderTree className="w-3.5 h-3.5 text-[#d4a853]" />
              <span>Affected Files ({changedFiles.length})</span>
            </span>
            <span className="text-[10px] text-[#6a6358]">
              {review?.findings_count || 0} findings
            </span>
          </div>

          <div className="rounded-[2px] border border-[#26221c] bg-[#13110e] p-2 space-y-1">
            {changedFiles.length === 0 ? (
              <div className="p-4 text-center text-[#6a6358] text-xs font-mono">
                No affected files detected yet.
              </div>
            ) : (
              changedFiles.map((file, idx) => (
                <button
                  key={file.path}
                  type="button"
                  onClick={() => setSelectedFileIndex(idx)}
                  className={`w-full text-left p-2.5 rounded-[2px] text-xs font-mono transition-colors flex items-center justify-between ${
                    selectedFileIndex === idx
                      ? 'bg-[#1e1b16] border border-[#38332a] text-[#d4a853] font-medium'
                      : 'text-[#8a8378] hover:text-[#d8d2c4] hover:bg-[#171511]'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode className="w-3.5 h-3.5 shrink-0 text-[#6a6358]" />
                    <span className="truncate">{file.name}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] shrink-0">
                    {file.findingsCount > 0 && (
                      <span className="px-1.5 py-0.2 rounded-[2px] bg-[#221614] border border-[#c75a4a]/40 text-[#e06c5b] font-mono">
                        {file.findingsCount}
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>

          <div className="p-3.5 rounded-[2px] border border-[#2e2a23] bg-[#161410] text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 text-[#d4a853] font-mono text-[11px] font-medium">
              <Bot className="w-3.5 h-3.5" />
              <span>Conference Navigation</span>
            </div>
            <p className="text-[11px] text-[#8a8378] leading-relaxed">
              Explore cross-examination and adversarial challenges between Bug Hunter, Security Sentinel and Reviewer 2 in the conference room.
            </p>
            <Link
              to="/agents"
              className="inline-flex items-center gap-1 text-[11px] font-mono text-[#d4a853] hover:underline pt-1"
            >
              <span>Open Agent Conference</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Middle Column (6 cols): Monaco Diff Viewer */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-[#8a8378] px-1">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-[#3a9e8f]" />
              <span className="text-[#f5f0e6]">{currentFile?.path || 'Source Diff'}</span>
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
          <div className="flex items-center justify-between text-xs font-mono text-[#8a8378] px-1">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-[#e06c5b]" />
              <span>Findings ({fileComments.length})</span>
            </span>
            <Link to="/autofix" className="text-[10px] text-[#d4a853] hover:underline flex items-center gap-0.5">
              <span>AutoFix Studio</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-0.5">
            {fileComments.length === 0 ? (
              <Card className="p-6 text-center border-dashed border-[#26221c] bg-[#13110e]">
                <p className="text-xs text-[#8a8378] font-mono">
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
              className="w-full text-xs font-mono flex items-center justify-center gap-2 mt-2 font-medium"
            >
              <Wrench className="w-3.5 h-3.5 text-[#0e0d0b]" />
              <span>Open in AutoFix Studio</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

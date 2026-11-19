import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MonacoDiffViewer } from '@/components/code/MonacoDiffViewer';
import { mockAutoFixProposals, AutoFixItem } from '@/services/mockData';
import {
  Wrench,
  CheckCircle2,
  XCircle,
  GitCommit,
  GitPullRequest,
  Check,
  Play,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const AutoFix: React.FC = () => {
  const { success, error, info } = useToast();
  const [proposals, setProposals] = useState<AutoFixItem[]>(mockAutoFixProposals);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isEditable, setIsEditable] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const selectedProposal = proposals[selectedIndex] || proposals[0];

  const handleApprove = () => {
    setIsApplying(true);
    setTimeout(() => {
      setIsApplying(false);
      success(
        'AutoFix Patch Approved & Committed',
        `Committed patch for "${selectedProposal.title}" to branch for PR #${selectedProposal.prNumber}.`
      );
    }, 800);
  };

  const handleCreatePr = () => {
    success(
      'Automated Fix PR Created',
      `Opened pull request "autofix/${selectedProposal.id}" on GitHub.`
    );
  };

  const handleReject = () => {
    info(
      'Proposal Rejected',
      `AutoFix recommendation for ${selectedProposal.filePath} was dismissed.`
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">AutoFix Remediation Studio</h1>
            <Badge variant="purple">Verified Code Fixes</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Review side-by-side proposed code fixes synthesized by the Quality Arbiter and verified with automated test checks.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReject}
            className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300"
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Reject Proposal</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleCreatePr}
            className="flex items-center gap-1.5 text-xs text-sky-400"
          >
            <GitPullRequest className="w-3.5 h-3.5" />
            <span>Create Fix PR</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={handleApprove}
            isLoading={isApplying}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve & Commit Patch</span>
          </Button>
        </div>
      </div>

      {/* Main Studio Layout: Left Proposals List + Right Side-by-side Diff & Test Results */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (4 cols): Proposals Selection */}
        <div className="lg:col-span-4 space-y-3">
          <div className="text-xs font-semibold text-white px-1 flex items-center justify-between">
            <span>Pending AutoFix Proposals ({proposals.length})</span>
            <span className="text-[10px] text-slate-500 font-mono">Arbiter Verified</span>
          </div>

          <div className="space-y-2.5">
            {proposals.map((item, idx) => (
              <div
                key={item.id}
                onClick={() => setSelectedIndex(idx)}
                className={`p-3.5 rounded-xl border cursor-pointer transition ${
                  selectedIndex === idx
                    ? 'border-sky-500/60 bg-[#0e1526] ring-1 ring-sky-500/30'
                    : 'border-slate-800/80 bg-[#0c101c] hover:border-slate-700 hover:bg-slate-900/50'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <Badge
                      variant={
                        item.severity === 'critical'
                          ? 'destructive'
                          : item.severity === 'high'
                          ? 'warning'
                          : 'secondary'
                      }
                      className="text-[9px] py-0 uppercase"
                    >
                      {item.severity}
                    </Badge>
                    <span className="text-[10px] font-mono text-purple-400 capitalize">
                      {item.category}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">PR #{item.prNumber}</span>
                </div>

                <h3 className="text-xs font-bold text-white mb-1 leading-snug">{item.title}</h3>
                <p className="text-[11px] text-slate-400 line-clamp-2">{item.explanation}</p>

                <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-500 truncate max-w-[180px]">{item.filePath}</span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Tests Pass</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column (8 cols): Side-by-Side Monaco Diff & Test Suite Verification */}
        <div className="lg:col-span-8 space-y-4">
          {/* Header Info */}
          <div className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800 bg-[#0c101c]">
            <div>
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-mono font-semibold text-white">
                  {selectedProposal.filePath}
                </span>
                <Badge variant="outline" className="font-mono text-[10px]">
                  Side-by-Side Unified Diff
                </Badge>
              </div>
              <p className="text-xs text-slate-400 mt-1">{selectedProposal.explanation}</p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsEditable(!isEditable);
                info('Editor Mode', isEditable ? 'Set to Read-Only' : 'Set to Interactive Edit Mode');
              }}
              className="text-xs text-slate-300"
            >
              <span>{isEditable ? 'Lock Editor' : 'Edit Patch in Monaco'}</span>
            </Button>
          </div>

          {/* Monaco Diff Viewer */}
          <MonacoDiffViewer
            fileName={selectedProposal.filePath}
            language="python"
            originalCode={selectedProposal.originalCode}
            code={selectedProposal.proposedCode}
            isDiffMode={true}
            readOnly={!isEditable}
            height="420px"
          />

          {/* Test Execution & Safety Verification Results */}
          <Card className="border-slate-800 bg-[#0c101c]">
            <CardHeader className="pb-3 border-b border-slate-800/80">
              <CardTitle className="text-xs font-semibold text-white flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Sandbox Test & Verification Results</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  Status: All Passing
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-mono">Unit Test Pass Rate</div>
                <div className="font-semibold text-emerald-400 font-mono mt-0.5">
                  {selectedProposal.testsSummary}
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-mono">AST Syntax Verification</div>
                <div className="font-semibold text-white font-mono mt-0.5">
                  Valid Python 3.12+ AST
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase font-mono">Regression Risk Index</div>
                <div className="font-semibold text-emerald-400 font-mono mt-0.5">
                  Minimal (&lt; 0.05%)
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

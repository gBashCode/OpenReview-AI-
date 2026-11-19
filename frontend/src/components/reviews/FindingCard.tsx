import React, { useState } from 'react';
import { ReviewComment } from '../../types/review';
import { Badge } from '../ui/badge';
import {
  ShieldAlert,
  Zap,
  Bug,
  Code2,
  ChevronDown,
  ChevronUp,
  FileCode2,
} from 'lucide-react';

interface FindingCardProps {
  comment: ReviewComment;
  onSelect?: () => void;
  isSelected?: boolean;
}

export const FindingCard: React.FC<FindingCardProps> = ({
  comment,
  onSelect,
  isSelected = false,
}) => {
  const [expanded, setExpanded] = useState(false);

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'security':
        return <ShieldAlert className="w-4 h-4 text-rose-400" />;
      case 'performance':
        return <Zap className="w-4 h-4 text-amber-400" />;
      case 'bug':
        return <Bug className="w-4 h-4 text-orange-400" />;
      default:
        return <Code2 className="w-4 h-4 text-sky-400" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <Badge variant="destructive">Critical</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      case 'warning':
        return <Badge variant="warning">Warning</Badge>;
      default:
        return <Badge variant="secondary">Info</Badge>;
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`rounded-xl border transition cursor-pointer p-5 ${
        isSelected
          ? 'border-sky-500/60 bg-slate-900/90 ring-1 ring-sky-500/30'
          : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-900/70'
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {getCategoryIcon(comment.category)}
          <span className="text-xs uppercase font-mono tracking-wider font-semibold text-slate-300">
            {comment.category}
          </span>
          {getSeverityBadge(comment.severity)}
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
          <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
          <span>{comment.file_path}</span>
          {comment.line_number && <span className="text-sky-400">#L{comment.line_number}</span>}
        </div>
      </div>

      <h4 className="font-semibold text-white text-base mb-1.5">{comment.title}</h4>
      <p className="text-sm text-slate-300 leading-relaxed mb-3">{comment.message}</p>

      {comment.suggested_patch && (
        <div className="mt-3">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 font-medium transition"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{expanded ? 'Hide Suggested Fix' : 'View Suggested Fix'}</span>
          </button>

          {expanded && (
            <div className="mt-2 rounded-lg bg-black/60 border border-slate-800 p-3 font-mono text-xs text-emerald-400 overflow-x-auto">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">
                Suggested Replacement / Diff
              </div>
              <pre className="whitespace-pre-wrap">{comment.suggested_patch}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

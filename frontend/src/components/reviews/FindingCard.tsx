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
        return <ShieldAlert className="w-3.5 h-3.5 text-[#c75a4a]" />;
      case 'performance':
        return <Zap className="w-3.5 h-3.5 text-[#e29b38]" />;
      case 'bug':
        return <Bug className="w-3.5 h-3.5 text-[#e06c5b]" />;
      default:
        return <Code2 className="w-3.5 h-3.5 text-[#d4a853]" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'error':
        return <Badge variant="destructive" className="font-mono text-[9px] uppercase">Critical</Badge>;
      case 'warning':
        return <Badge variant="warning" className="font-mono text-[9px] uppercase">Warning</Badge>;
      default:
        return <Badge variant="secondary" className="font-mono text-[9px] uppercase">Info</Badge>;
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`rounded-[2px] border transition-colors cursor-pointer p-4 ${
        isSelected
          ? 'border-[#d4a853] bg-[#1a1713] ring-1 ring-[#d4a853]/30'
          : 'border-[#26221c] bg-[#14120f] hover:border-[#383229]'
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {getCategoryIcon(comment.category)}
          <span className="text-[10px] uppercase font-mono tracking-wider font-medium text-[#d8d2c4]">
            {comment.category}
          </span>
          {getSeverityBadge(comment.severity)}
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-[#787165] font-mono">
          <FileCode2 className="w-3 h-3 text-[#6a6358]" />
          <span>{comment.file_path.split('/').pop()}</span>
          {comment.line_number && <span className="text-[#d4a853]">#L{comment.line_number}</span>}
        </div>
      </div>

      <h4 className="font-serif text-base text-[#f5f0e6] mb-1 leading-snug">{comment.title}</h4>
      <p className="text-xs text-[#8a8378] leading-relaxed mb-2.5 font-sans">{comment.message}</p>

      {comment.suggested_patch && (
        <div className="mt-2.5 pt-2 border-t border-[#221f1a]">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="flex items-center gap-1 text-[11px] font-mono text-[#d4a853] hover:text-[#e0b663] transition"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            <span>{expanded ? 'Hide Unified Patch' : 'View Unified Patch'}</span>
          </button>

          {expanded && (
            <div className="mt-2 rounded-[2px] bg-[#0c0a09] border border-[#2a2620] p-3 font-mono text-[11px] text-[#6cb582] overflow-x-auto">
              <div className="text-[9px] text-[#6a6358] uppercase tracking-wider mb-1 font-mono">
                Unified Patch Ledger
              </div>
              <pre className="whitespace-pre-wrap leading-relaxed">{comment.suggested_patch}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

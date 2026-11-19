import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Shield, Zap, Sparkles, Award } from 'lucide-react';

interface ReviewSummaryScoreProps {
  score?: number | null;
  securityScore?: number | null;
  performanceScore?: number | null;
  qualityScore?: number | null;
}

export const ReviewSummaryScore: React.FC<ReviewSummaryScoreProps> = ({
  score = 0,
  securityScore = 0,
  performanceScore = 0,
  qualityScore = 0,
}) => {
  const getScoreColor = (val: number | null | undefined) => {
    if (!val) return 'text-[#8a8378]';
    if (val >= 90) return 'text-[#6cb582]';
    if (val >= 75) return 'text-[#d4a853]';
    if (val >= 60) return 'text-[#f0af54]';
    return 'text-[#e06c5b]';
  };

  const metrics = [
    {
      label: '[01] OVERALL SCORE',
      val: score,
      icon: Award,
      color: getScoreColor(score),
    },
    {
      label: '[02] SECURITY INDEX',
      val: securityScore,
      icon: Shield,
      color: getScoreColor(securityScore),
    },
    {
      label: '[03] PERFORMANCE',
      val: performanceScore,
      icon: Zap,
      color: getScoreColor(performanceScore),
    },
    {
      label: '[04] CODE QUALITY',
      val: qualityScore,
      icon: Sparkles,
      color: getScoreColor(qualityScore),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {metrics.map((m) => {
        const Icon = m.icon;
        return (
          <Card key={m.label} className="border-[#26221c] bg-[#13110e]">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-mono text-[#8a8378] tracking-wider mb-1">{m.label}</p>
                <div className="text-2xl font-serif tracking-tight flex items-baseline gap-1">
                  <span className={m.color}>{m.val ? m.val.toFixed(1) : '--'}</span>
                  <span className="text-xs font-mono text-[#6a6358] font-normal">/100</span>
                </div>
              </div>
              <div className="w-9 h-9 rounded-[2px] bg-[#1b1915] border border-[#2e2a24] flex items-center justify-center text-[#8a8378]">
                <Icon className="w-4 h-4" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

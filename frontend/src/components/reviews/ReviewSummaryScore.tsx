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
    if (!val) return 'text-slate-400';
    if (val >= 90) return 'text-emerald-400';
    if (val >= 75) return 'text-sky-400';
    if (val >= 60) return 'text-amber-400';
    return 'text-rose-400';
  };

  const metrics = [
    {
      label: 'Overall Score',
      val: score,
      icon: Award,
      color: getScoreColor(score),
    },
    {
      label: 'Security Index',
      val: securityScore,
      icon: Shield,
      color: getScoreColor(securityScore),
    },
    {
      label: 'Performance',
      val: performanceScore,
      icon: Zap,
      color: getScoreColor(performanceScore),
    },
    {
      label: 'Code Quality',
      val: qualityScore,
      icon: Sparkles,
      color: getScoreColor(qualityScore),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metrics.map((m) => {
        const Icon = m.icon;
        return (
          <Card key={m.label} className="border-slate-800 bg-slate-900/60">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 font-medium mb-1">{m.label}</p>
                <div className="text-2xl font-bold font-mono tracking-tight flex items-baseline gap-1">
                  <span className={m.color}>{m.val ? m.val.toFixed(1) : '--'}</span>
                  <span className="text-xs text-slate-500 font-normal">/100</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-slate-800/80 flex items-center justify-center text-slate-400">
                <Icon className="w-5 h-5" />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

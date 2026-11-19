import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { mockPerformanceIssues, PerformanceIssue } from '@/services/mockData';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  TrendingDown,
  Clock,
  Database,
  Cpu,
  ArrowRight,
  Wrench,
  FileCode,
  Flame,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const PerformanceReports: React.FC = () => {
  const navigate = useNavigate();
  const { info } = useToast();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Performance & Complexity Reports</h1>
            <Badge variant="warning">Latency & Big-O Profiling</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Algorithmic efficiency, N+1 ORM query detection, and async event loop blocking analysis.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="electric"
            size="sm"
            onClick={() => navigate('/autofix')}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Wrench className="w-3.5 h-3.5 text-amber-300" />
            <span>Apply Optimizations</span>
          </Button>
        </div>
      </div>

      {/* High-level performance KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>N+1 Queries Detected</span>
              <Database className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">1</div>
            <p className="text-[11px] text-slate-500 mt-0.5">340ms roundtrip penalty</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Big-O Regressions</span>
              <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-rose-400">1</div>
            <p className="text-[11px] text-slate-500 mt-0.5">O(N^2) nested loop in diff reconciliation</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Avg Latency Gain</span>
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">-45%</div>
            <p className="text-[11px] text-slate-500 mt-0.5">on endpoints adopting AutoFix</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Async Loop Blocks</span>
              <Cpu className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-sky-400">1</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Synchronous file read in async def</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Findings List */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-white">Flagged Performance Bottlenecks</h2>
        {mockPerformanceIssues.map((issue: PerformanceIssue) => (
          <Card key={issue.id} className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700/80 transition">
            <CardContent className="p-5">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <Badge variant={issue.severity === 'high' ? 'warning' : 'secondary'} className="uppercase text-[10px]">
                    {issue.type}
                  </Badge>
                  <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                    {issue.estimatedLatencyPenalty}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
                  <FileCode className="w-3.5 h-3.5 text-slate-500" />
                  <span>{issue.filePath}#L{issue.lineNumber}</span>
                </div>
              </div>

              <h3 className="font-semibold text-white text-sm mb-1">{issue.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-3">{issue.impact}</p>

              <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs font-mono text-emerald-400 mb-3">
                <div className="text-[10px] uppercase text-slate-500 mb-1">Recommended Optimization</div>
                <code>{issue.suggestedOptimization}</code>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                <span className="text-slate-500 font-mono text-[11px]">Repository: {issue.repository}</span>
                <Button
                  size="sm"
                  variant="electric"
                  onClick={() => navigate('/autofix')}
                  className="flex items-center gap-1.5 text-xs font-semibold"
                >
                  <Wrench className="w-3 h-3 text-amber-300" />
                  <span>View in AutoFix</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

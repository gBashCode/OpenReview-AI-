import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../services/healthApi';
import { Badge } from '../ui/badge';
import { Activity, ShieldCheck, Github, Zap } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { data: health, isLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
    refetchInterval: 15000,
  });

  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <Badge variant="outline" className="animate-pulse flex items-center gap-1.5">
          <Activity className="w-3 h-3 text-slate-400" />
          <span>Connecting...</span>
        </Badge>
      );
    }
    if (health?.status === 'healthy') {
      return (
        <Badge variant="success" className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>All Systems Operational</span>
        </Badge>
      );
    }
    if (health?.status === 'degraded') {
      return (
        <Badge variant="warning" className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400" />
          <span>Degraded Mode</span>
        </Badge>
      );
    }
    return (
      <Badge variant="destructive" className="flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-rose-400" />
        <span>Offline</span>
      </Badge>
    );
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg text-white tracking-tight">OpenReview</span>
            <span className="text-xs px-1.5 py-0.5 rounded font-mono font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30">
              AI
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">Autonomous Multi-Agent Reviewer</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {getStatusBadge()}

        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-400 hover:text-white transition flex items-center gap-1 px-3 py-1.5 rounded-md hover:bg-slate-800"
        >
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>API Docs</span>
        </a>

        <div className="h-4 w-px bg-slate-800" />

        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Github className="w-4 h-4 text-slate-300" />
          <span className="font-mono">GitHub App v0.1</span>
        </div>
      </div>
    </header>
  );
};

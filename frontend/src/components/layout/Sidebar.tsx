import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  GitFork,
  GitPullRequest,
  Sliders,
  Terminal,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/repositories', label: 'Repositories', icon: GitFork },
  { to: '/pull-requests', label: 'Pull Requests', icon: GitPullRequest },
  { to: '/settings', label: 'Engine Settings', icon: Sliders },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/40 p-4 flex flex-col justify-between min-h-[calc(100vh-57px)]">
      <div className="space-y-6">
        <div>
          <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 font-mono">
            Navigation
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div>
          <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500 font-mono">
            Agent Pipelines
          </div>
          <div className="space-y-2 px-3 text-xs text-slate-400">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Security Agent
              </span>
              <span className="font-mono text-[10px] text-slate-500">Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Performance Agent
              </span>
              <span className="font-mono text-[10px] text-slate-500">Active</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Quality Arbiter
              </span>
              <span className="font-mono text-[10px] text-slate-500">Active</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-3 rounded-lg border border-slate-800/80 bg-slate-900/40 text-xs">
        <div className="flex items-center gap-2 text-slate-300 font-mono font-semibold mb-1">
          <Terminal className="w-3.5 h-3.5 text-sky-400" />
          <span>Local Stack</span>
        </div>
        <p className="text-slate-500 text-[11px] leading-relaxed">
          PostgreSQL (pgvector), Redis, Celery & FastAPI v1 API
        </p>
      </div>
    </aside>
  );
};

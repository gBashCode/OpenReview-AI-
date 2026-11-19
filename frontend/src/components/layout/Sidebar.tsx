import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  GitFork,
  GitPullRequest,
  Wrench,
  Bot,
  ShieldAlert,
  Zap,
  History,
  Users,
  BarChart3,
  Sliders,
  Cpu,
  Flame,
  CheckCircle2,
} from 'lucide-react';

interface NavSection {
  title: string;
  items: {
    to: string;
    label: string;
    icon: React.ElementType;
    badge?: string;
  }[];
}

const navSections: NavSection[] = [
  {
    title: 'Core Platform',
    items: [
      { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/pull-requests', label: 'Pull Requests', icon: GitPullRequest, badge: 'Live' },
      { to: '/repositories', label: 'Repositories', icon: GitFork },
      { to: '/autofix', label: 'AutoFix Studio', icon: Wrench, badge: '3' },
    ],
  },
  {
    title: 'Multi-Agent Intelligence',
    items: [
      { to: '/agents', label: 'Agent Conference', icon: Bot, badge: '5 Agents' },
      { to: '/security', label: 'Security Reports', icon: ShieldAlert },
      { to: '/performance', label: 'Performance Reports', icon: Zap },
      { to: '/history', label: 'Review Audit Log', icon: History },
    ],
  },
  {
    title: 'Administration',
    items: [
      { to: '/team', label: 'Team & RBAC', icon: Users },
      { to: '/analytics', label: 'Usage & Analytics', icon: BarChart3 },
      { to: '/models', label: 'AI Model Config', icon: Cpu },
      { to: '/settings', label: 'Engine Settings', icon: Sliders },
    ],
  },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-60 border-r border-slate-800/80 bg-[#070b12] p-3 flex flex-col justify-between shrink-0 min-h-[calc(100vh-53px)] select-none">
      <div className="space-y-6">
        {navSections.map((section) => (
          <div key={section.title}>
            <div className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500 font-mono">
              {section.title}
            </div>
            <nav className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-sky-500/10 text-sky-400 font-semibold border border-sky-500/20'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700/60">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Autonomous Agent Live Status Widget */}
      <div className="pt-4 border-t border-slate-800/80 space-y-2">
        <div className="p-2.5 rounded-lg border border-purple-500/20 bg-gradient-to-b from-purple-950/20 to-slate-900/40 text-[11px]">
          <div className="flex items-center justify-between text-purple-300 font-mono font-semibold mb-1">
            <span className="flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-purple-400" />
              <span>Multi-Agent Engine</span>
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Security, Performance, Bug & Arbiter agents running consensus.
          </p>
        </div>

        <div className="text-[10px] text-slate-500 font-mono text-center">
          OpenReview AI v0.1.0-alpha
        </div>
      </div>
    </aside>
  );
};

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
    <aside className="w-60 border-r border-[#26221c] bg-[#110f0d] p-3.5 flex flex-col justify-between shrink-0 min-h-[calc(100vh-53px)] select-none">
      <div className="space-y-6">
        {navSections.map((section) => (
          <div key={section.title}>
            <div className="px-3 mb-2 text-[10px] font-mono uppercase tracking-widest text-[#787165]">
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
                      `flex items-center justify-between px-3 py-1.5 rounded-[2px] text-xs transition-colors duration-150 ${
                        isActive
                          ? 'bg-[#1e1b16] text-[#d4a853] font-medium border-l-2 border-[#d4a853]'
                          : 'text-[#8a8378] hover:text-[#d8d2c4] hover:bg-[#171512]'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded-[2px] font-mono bg-[#1c1a16] text-[#d4a853] border border-[#2f2a22]">
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
      <div className="pt-4 border-t border-[#26221c] space-y-2">
        <div className="p-3 rounded-[2px] border border-[#2e2a23] bg-[#161410] text-[11px]">
          <div className="flex items-center justify-between text-[#d4a853] font-mono font-medium mb-1">
            <span className="flex items-center gap-1.5">
              <Bot className="w-3.5 h-3.5 text-[#d4a853]" />
              <span>Council Deliberation</span>
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#5a9e6f] animate-pulse" />
          </div>
          <p className="text-[#8a8378] text-[10px] leading-relaxed">
            Bug, Security, Perf & Arbiter running AST consensus passes.
          </p>
        </div>

        <div className="text-[10px] text-[#6a6358] font-mono text-center tracking-wider">
          OPENREVIEW AI · v0.1.0-alpha
        </div>
      </div>
    </aside>
  );
};

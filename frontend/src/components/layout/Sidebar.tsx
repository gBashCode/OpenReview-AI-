import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
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
  const shouldReduceMotion = useReducedMotion();
  let itemCounter = 0;

  return (
    <aside
      className="sidebar-container w-64 px-3.5 pb-6 flex flex-col justify-between shrink-0 min-h-screen select-none overflow-y-auto"
      style={{ paddingTop: 'var(--header-h, 96px)' }}
    >
      <div className="space-y-4">
        {navSections.map((section, sectionIndex) => (
          <div
            key={section.title}
            className="sidebar-card-animate sidebar-section-card p-[14px] relative"
            style={{ animationDelay: `${sectionIndex * 0.12}s` }}
          >
            {/* Section label: #9a927f */}
            <div className="px-3 pb-2 text-[12px] font-semibold uppercase tracking-[0.07em] text-[#9a927f] select-none relative z-10">
              {section.title}
            </div>
            <nav className="space-y-1 relative z-10">
              {section.items.map((item) => {
                const Icon = item.icon;
                const currentItemIndex = itemCounter++;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `sidebar-nav-item sidebar-item-animate group relative flex items-center justify-between h-[42px] px-3.5 rounded-full text-[13px] outline-none focus-gold ${
                        isActive
                          ? 'text-[#e0b04a] font-semibold'
                          : 'text-[#9a927f] font-medium hover:text-[#ece6d8]'
                      }`
                    }
                    style={{ animationDelay: `${0.18 + currentItemIndex * 0.045}s` }}
                  >
                    {({ isActive }) => (
                      <>
                        {/* Active item: gold text #e0b04a, background rgba(224,176,74,.14), inset border rgba(224,176,74,.4) */}
                        {isActive && (
                          <motion.div
                            layoutId="sidebar-active-indicator"
                            transition={{
                              duration: shouldReduceMotion ? 0 : 0.5,
                              ease: [0.22, 1, 0.36, 1],
                            }}
                            className="sidebar-active-pill absolute inset-0 rounded-full bg-[rgba(224,176,74,0.14)] border border-[rgba(224,176,74,0.4)] shadow-[inset_0_0_0_1px_rgba(224,176,74,0.25)] pointer-events-none z-0"
                          />
                        )}

                        <div className="flex items-center gap-2.5 relative z-10 min-w-0">
                          <Icon className="sidebar-nav-icon w-4 h-4 shrink-0 text-current" />
                          <span className="truncate">{item.label}</span>
                        </div>

                        {item.badge && (
                          <span className="relative z-10 text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-[rgba(255,255,255,0.05)] text-[#e0b04a] border border-[#2c261c] shadow-[inset_0_0_0_1px_#2c261c] flex items-center gap-1.5 shrink-0">
                            {item.badge === 'Live' && (
                              <span className="relative flex h-1.5 w-1.5 shrink-0">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#e0b04a] opacity-75" />
                                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#e0b04a]" />
                              </span>
                            )}
                            <span>{item.badge}</span>
                          </span>
                        )}
                      </>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Autonomous Agent Live Status Widget */}
      <div className="space-y-2 mt-4 relative z-10">
        <div className="sidebar-card-animate sidebar-section-card p-3.5 rounded-[24px] text-[11.5px]">
          <div className="flex items-center justify-between text-[#ece6d8] font-semibold mb-1">
            <span className="flex items-center gap-1.5">
              <Bot className="w-4 h-4 text-[#e0b04a]" />
              <span>Council Deliberation</span>
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#e0b04a] animate-pulse" />
          </div>
          <p className="text-[#9a927f] text-[11px] leading-relaxed">
            Bug, Security, Perf & Arbiter running AST consensus passes.
          </p>
        </div>

        <div className="text-[11px] text-[#9a927f] font-semibold text-center tracking-wider py-1 select-none">
          OPENREVIEW AI · v0.1.0-alpha
        </div>
      </div>
    </aside>
  );
};

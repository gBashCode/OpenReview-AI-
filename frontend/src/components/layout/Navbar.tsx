import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../services/healthApi';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  Zap,
  Bell,
  Search,
  ExternalLink,
  User,
  LogOut,
  ChevronDown,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { useToast } from '../ui/toast';
import { useAuth } from '../../context/AuthContext';
import { OpenReviewLogo } from './OpenReviewLogo';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { info, success } = useToast();
  const { user, logout, isDemoMode } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const headerRef = useRef<HTMLElement>(null);

  const { data: health, isLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
    refetchInterval: 15000,
  });

  // Dynamically measure header and set --header-h on :root via ResizeObserver
  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    const updateHeaderHeight = () => {
      const topOffset = header.offsetTop || 20;
      const totalHeight = header.offsetHeight + topOffset + 16;
      document.documentElement.style.setProperty('--header-h', `${totalHeight}px`);
    };

    updateHeaderHeight();

    const observer = new ResizeObserver(() => {
      updateHeaderHeight();
    });

    observer.observe(header);
    window.addEventListener('resize', updateHeaderHeight);

    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateHeaderHeight);
    };
  }, []);

  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <div className="header-pill flex items-center gap-2 h-[40px] px-3.5 rounded-full border border-[rgba(224,176,74,0.45)] bg-[rgba(224,176,74,0.06)] text-[#e0b04a] text-[12.5px] font-semibold animate-pulse whitespace-nowrap shrink-0">
          <Activity className="w-3.5 h-3.5 text-[#e0b04a]" />
          <span>Syncing...</span>
        </div>
      );
    }
    if (health?.status === 'healthy') {
      return (
        <div className="header-pill flex items-center gap-2 h-[40px] px-3.5 rounded-full border border-[rgba(224,176,74,0.45)] bg-[rgba(224,176,74,0.06)] text-[#e0b04a] text-[12.5px] font-semibold whitespace-nowrap shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#e0b04a] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#e0b04a]" />
          </span>
          <span>Engine Online</span>
        </div>
      );
    }
    if (health?.status === 'degraded') {
      return (
        <div className="header-pill flex items-center gap-2 h-[40px] px-3.5 rounded-full border border-[rgba(224,176,74,0.45)] bg-[rgba(224,176,74,0.06)] text-[#e0b04a] text-[12.5px] font-semibold whitespace-nowrap shrink-0">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#e0b04a] opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#e0b04a]" />
          </span>
          <span>Local Engine (SQLite)</span>
        </div>
      );
    }
    return (
      <div className="header-pill flex items-center gap-2 h-[40px] px-3.5 rounded-full border border-[#c75a4a]/45 bg-[rgba(199,90,74,0.08)] text-[#e06c5b] text-[12.5px] font-semibold whitespace-nowrap shrink-0">
        <span className="w-2 h-2 rounded-full bg-[#c75a4a] animate-pulse" />
        <span>Offline</span>
      </div>
    );
  };

  return (
    <header
      ref={headerRef}
      className="header-container header-brown-container sticky top-5 z-40 mx-auto w-[calc(100%-40px)] max-w-[1500px] rounded-[999px] max-[760px]:rounded-[32px] px-6 py-2.5 max-[760px]:px-4 max-[760px]:py-3.5 flex items-center justify-between max-[760px]:flex-wrap max-[760px]:gap-3 relative"
    >
      {/* Travelling Gold Light (#e0b04a) on Header Curved Border */}
      <div className="header-border-track" aria-hidden="true">
        <div className="header-border-beam" />
      </div>

      {/* Left: Brand Logo & Brown Search Bar */}
      <div className="flex items-center gap-3 md:gap-4 relative z-10 shrink min-w-0 max-[760px]:w-full max-[760px]:justify-between">
        <div className="header-item-animate shrink-0" style={{ animationDelay: '0.06s' }}>
          <Link
            to="/dashboard"
            className="flex items-center gap-2.5 group outline-none focus-gold rounded-full"
            aria-label="OpenReview AI Dashboard"
          >
            {/* Animated OpenReview AI Geometric Emblem */}
            <OpenReviewLogo size={36} />
            <div className="flex items-baseline gap-1.5">
              <span className="text-[20px] font-bold tracking-[-0.02em] text-[#ece6d8] group-hover:text-[#e0b04a] transition-colors whitespace-nowrap">
                OpenReview
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold tracking-widest bg-[rgba(224,176,74,0.14)] text-[#e0b04a] border border-[#e0b04a]/30">
                AI
              </span>
            </div>
          </Link>
        </div>

        {/* Search Bar: background rgba(255,255,255,.04), inset 1px #2c261c, placeholder #9a927f */}
        <div
          role="button"
          tabIndex={0}
          onClick={() => info('Command Palette', 'Type ⌘K anytime to jump between repositories, PRs, and review rules.')}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              info('Command Palette', 'Type ⌘K anytime to jump between repositories, PRs, and review rules.');
            }
          }}
          className="header-search-bar group hidden md:flex items-center justify-between px-3.5 text-[#9a927f] cursor-pointer outline-none header-item-animate focus-gold shrink min-w-0"
          style={{ animationDelay: '0.12s' }}
          aria-label="Search PRs, repos, AST rules (⌘K)"
        >
          <div className="flex items-center gap-2 min-w-0 overflow-hidden">
            <Search className="w-3.5 h-3.5 text-[#9a927f] group-focus:text-[#e0b04a] transition-colors shrink-0" />
            <span className="text-[13px] text-[#9a927f] group-hover:text-[#ece6d8] transition-colors truncate">
              Search PRs, repos, AST rules...
            </span>
          </div>
          <kbd className="ml-2 text-[10px] px-2 py-0.5 rounded-full bg-[rgba(255,255,255,0.06)] text-[#9a927f] border border-[#2c261c] shadow-sm shrink-0 hidden min-[1180px]:inline-flex">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right Action Icons & Status */}
      <div className="flex items-center gap-2 lg:gap-3 relative z-10 shrink-0 max-[760px]:w-full max-[760px]:justify-between max-[760px]:flex-wrap">
        {/* Item 3: Local Engine / Status Chip */}
        <div className="header-item-animate whitespace-nowrap shrink-0" style={{ animationDelay: '0.18s' }}>
          {getStatusBadge()}
        </div>

        {/* Item 4: Public Landing / Product Tour */}
        <div className="header-item-animate whitespace-nowrap shrink-0" style={{ animationDelay: '0.24s' }}>
          <Link
            to="/landing"
            className="header-pill hidden sm:flex items-center gap-2 h-[40px] px-3.5 rounded-full text-[13px] font-semibold text-[#ece6d8] hover:text-[#e0b04a] hover:bg-[rgba(224,176,74,0.14)] transition group whitespace-nowrap shrink-0 focus-gold"
            title="Product Tour"
          >
            <ExternalLink className="w-3.5 h-3.5 text-[#9a927f] group-hover:text-[#e0b04a] transition-colors shrink-0" />
            <span className="hidden min-[1180px]:inline">Product Tour</span>
          </Link>
        </div>

        {/* Item 5: API Docs link */}
        <div className="header-item-animate whitespace-nowrap shrink-0" style={{ animationDelay: '0.30s' }}>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="header-pill hidden sm:flex items-center gap-2 h-[40px] px-3.5 rounded-full text-[13px] font-semibold text-[#ece6d8] hover:text-[#e0b04a] hover:bg-[rgba(224,176,74,0.14)] transition group whitespace-nowrap shrink-0 focus-gold"
            title="API Documentation"
          >
            <Zap className="w-3.5 h-3.5 text-[#3a9e8f] group-hover:text-[#e0b04a] transition-colors shrink-0" />
            <span className="hidden min-[1180px]:inline">API Docs</span>
          </a>
        </div>

        {/* Demo Mode Indicator (when active) */}
        {isDemoMode && (
          <div className="header-item-animate whitespace-nowrap shrink-0" style={{ animationDelay: '0.36s' }}>
            <div
              className="header-pill hidden sm:flex items-center gap-2 h-[40px] px-3.5 rounded-full border border-[#e0b04a] bg-[rgba(224,176,74,0.14)] text-[#e0b04a] text-[13px] font-semibold shadow-sm whitespace-nowrap shrink-0"
              title="Active Sandbox Demo Session with Read-Only Capabilities"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#e0b04a] animate-pulse shrink-0" />
              <span>Demo Mode</span>
            </div>
          </div>
        )}

        {/* Item 7: Notification Bell (background rgba(255,255,255,.04), inset 1px #2c261c, gold notification dot) */}
        <div className="header-item-animate relative shrink-0" style={{ animationDelay: '0.42s' }}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-[42px] h-[42px] rounded-full flex items-center justify-center border border-[#2c261c] bg-[rgba(255,255,255,0.04)] text-[#9a927f] hover:text-[#ece6d8] hover:border-[#e0b04a]/50 hover:bg-[rgba(255,255,255,0.08)] transition relative cursor-pointer active:scale-[0.97] shrink-0 focus-gold"
            title="Notifications"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4 shrink-0" />
            <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 rounded-full bg-[#e0b04a] ring-2 ring-[#14110d]" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-3 w-80 rounded-[18px] border border-[#2c261c] bg-[#14110d] p-4 shadow-2xl shadow-black/80 z-50 text-xs animate-in fade-in duration-100">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#2c261c]">
                <span className="text-sm text-[#ece6d8] font-semibold">Review Alerts</span>
                <span className="text-[10px] text-[#e0b04a] font-semibold bg-[rgba(224,176,74,0.14)] px-2 py-0.5 rounded-full border border-[#e0b04a]/30">2 unread</span>
              </div>
              <div className="space-y-2.5">
                <div
                  onClick={() => {
                    navigate('/autofix');
                    setShowNotifications(false);
                  }}
                  className="p-2.5 rounded-[16px] bg-[#1c1813] border border-[#2c261c] hover:border-[#e0b04a]/40 cursor-pointer transition shadow-sm"
                >
                  <div className="flex items-center gap-1.5 text-[#e06c5b] font-semibold text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Critical CVE-89 Detected</span>
                  </div>
                  <p className="text-[#9a927f] mt-1 text-[11px] leading-relaxed">
                    PR #42 in openreview-ai has an automated patch verified by sandbox.
                  </p>
                </div>

                <div
                  onClick={() => {
                    navigate('/agents');
                    setShowNotifications(false);
                  }}
                  className="p-2.5 rounded-[16px] bg-[#1c1813] border border-[#2c261c] hover:border-[#e0b04a]/40 cursor-pointer transition shadow-sm"
                >
                  <div className="flex items-center gap-1.5 text-[#5a9e6f] font-semibold text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Agent Consensus Reached</span>
                  </div>
                  <p className="text-[#9a927f] mt-1 text-[11px] leading-relaxed">
                    Arbiter approved findings on commit 7f9a1b2 across 5 agents.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="h-5 w-px bg-[#2c261c] shrink-0" />

        {/* Item 8: Profile Pill (background rgba(255,255,255,.04), inset 1px #2c261c, gold hover border) */}
        <div className="header-item-animate relative shrink-0" style={{ animationDelay: '0.48s' }}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2.5 h-[42px] p-1.5 pr-3.5 rounded-full border border-[#2c261c] bg-[rgba(255,255,255,0.04)] hover:border-[#e0b04a] hover:bg-[rgba(255,255,255,0.08)] transition cursor-pointer active:scale-[0.97] max-w-[260px] focus-gold"
            aria-label="User Account Menu"
          >
            {/* Avatar gold #e0b04a on rgba(224,176,74,.14) */}
            <div className="w-7 h-7 rounded-full bg-[rgba(224,176,74,0.14)] border border-[#e0b04a]/40 flex items-center justify-center text-[11px] font-bold text-[#e0b04a] shadow-sm shrink-0">
              {(user?.full_name || user?.email || 'OR').slice(0, 2).toUpperCase()}
            </div>
            <span className="text-[13px] font-semibold text-[#ece6d8] hidden sm:inline whitespace-nowrap overflow-hidden text-ellipsis max-w-[200px]">
              {user?.full_name || 'Lead Architect'}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-[#9a927f] shrink-0" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-3 w-48 rounded-[18px] border border-[#2c261c] bg-[#14110d] p-2 shadow-2xl shadow-black/80 z-50 text-xs animate-in fade-in duration-100">
              <div className="px-3 py-2 border-b border-[#2c261c] mb-1">
                <div className="font-semibold text-[#ece6d8]">{user?.full_name || 'Lead Architect'}</div>
                <div className="text-[10px] text-[#9a927f] truncate">{user?.email || 'architect@openreview.ai'}</div>
              </div>
              <button
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-3 py-2 rounded-full hover:bg-[rgba(255,255,255,0.05)] text-[#9a927f] hover:text-[#ece6d8] flex items-center gap-2 transition"
              >
                <User className="w-3.5 h-3.5 text-[#9a927f]" />
                <span>Account Profile</span>
              </button>
              <button
                onClick={() => {
                  logout();
                  setShowUserMenu(false);
                  success('Logged Out', 'Returned to sign-in portal.');
                  navigate('/login');
                }}
                className="w-full text-left px-3 py-2 rounded-full hover:bg-[#c75a4a]/10 text-[#e06c5b] flex items-center gap-2 transition"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

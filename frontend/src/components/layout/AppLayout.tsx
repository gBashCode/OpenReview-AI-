import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

export const AppLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f0e0c] flex flex-col justify-center items-center text-[#8a8378]">
        <div className="w-10 h-10 rounded-[2px] bg-[#1c1a17] border border-[#d4a853]/30 flex items-center justify-center shadow-lg shadow-[#d4a853]/5 mb-4 animate-pulse">
          <ShieldCheck className="w-5 h-5 text-[#d4a853]" />
        </div>
        <p className="text-xs font-mono tracking-wider uppercase text-[#b8b0a2]">Verifying Review Session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#0f0e0c] flex flex-col selection:bg-[#d4a853]/25 selection:text-[#f5f0e6]">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

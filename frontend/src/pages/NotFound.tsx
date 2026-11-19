import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ArrowLeft, Compass } from 'lucide-react';

export const NotFound: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[65vh] text-center px-4">
      <div className="max-w-md w-full p-8 rounded-[3px] border border-[#2a2621] bg-[#14120f] shadow-[0_8px_32px_rgba(0,0,0,0.5)] relative overflow-hidden">
        <div className="inline-flex items-center gap-2 mb-4 font-mono text-[10px] tracking-[0.2em] text-[#d4a853] uppercase font-bold">
          [LEDGER · 404 · ENTRY UNLOCATED]
        </div>

        <h1 className="font-serif text-7xl font-normal text-[#f4efe6] tracking-tight mb-2">
          404
        </h1>

        <h2 className="font-serif text-xl font-normal text-[#c9bfaf] mb-3">
          Document Not Found in Repository Ledger
        </h2>

        <p className="font-sans text-xs text-[#8c8273] leading-relaxed mb-6">
          The requested coordinate or review dossier does not exist, has been archived, or was referenced under a revoked cryptographic hash.
        </p>

        <Link to="/">
          <Button variant="electric" size="sm" className="font-sans text-xs inline-flex items-center gap-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Review Ledger</span>
          </Button>
        </Link>
      </div>
    </div>
  );
};

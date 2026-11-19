import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';

export const NotFound: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-6xl font-extrabold text-sky-400 font-mono">404</h1>
      <h2 className="text-xl font-bold text-white mt-4">Page Not Found</h2>
      <p className="text-sm text-slate-400 mt-2 max-w-sm">
        The requested page does not exist or has been moved.
      </p>
      <Link to="/" className="mt-6">
        <Button>Return to Dashboard</Button>
      </Link>
    </div>
  );
};

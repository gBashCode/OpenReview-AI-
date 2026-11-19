import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  title: string;
  description?: string;
  type?: ToastType;
  duration?: number;
}

interface ToastContextType {
  toast: (options: Omit<Toast, 'id'>) => void;
  success: (title: string, description?: string) => void;
  error: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    ({ title, description, type = 'info', duration = 4000 }: Omit<Toast, 'id'>) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, title, description, type, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = (title: string, description?: string) => addToast({ title, description, type: 'success' });
  const error = (title: string, description?: string) => addToast({ title, description, type: 'error' });
  const warning = (title: string, description?: string) => addToast({ title, description, type: 'warning' });
  const info = (title: string, description?: string) => addToast({ title, description, type: 'info' });

  const getIcon = (type?: ToastType) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-[#5a9e6f] shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-[#c75a4a] shrink-0" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-[#e29b38] shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-[#d4a853] shrink-0" />;
    }
  };

  return (
    <ToastContext.Provider value={{ toast: addToast, success, error, warning, info }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto flex items-start gap-3 p-3.5 rounded-[18px] border border-[rgba(243,234,214,0.22)] bg-[#14120f]/95 backdrop-blur-xl text-[#f3ead6] shadow-xl shadow-black/80 transition-all duration-200 animate-in fade-in slide-in-from-bottom-2"
          >
            <div className="mt-0.5">{getIcon(t.type)}</div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-semibold text-[#f3ead6] tracking-tight">{t.title}</div>
              {t.description && (
                <div className="text-[11px] text-[rgba(243,234,214,0.72)] mt-0.5 leading-relaxed">{t.description}</div>
              )}
            </div>
            <button
              onClick={() => removeToast(t.id)}
              className="text-[rgba(243,234,214,0.55)] hover:text-[#f3ead6] p-0.5 rounded-full transition"
              aria-label="Dismiss toast"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

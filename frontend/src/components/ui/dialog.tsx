import * as React from "react";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

export const Dialog: React.FC<DialogProps> = ({ open, onOpenChange, children }) => {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
        onClick={() => onOpenChange(false)}
      />
      <div className="relative z-50 w-full max-w-lg rounded-[28px] border border-[rgba(243,234,214,0.22)] bg-[#12100d]/95 backdrop-blur-2xl p-6 shadow-2xl shadow-black/90 animate-in fade-in zoom-in-95 duration-150">
        <button
          onClick={() => onOpenChange(false)}
          className="absolute right-5 top-5 text-[rgba(243,234,214,0.72)] hover:text-[#f3ead6] p-1.5 rounded-full hover:bg-white/10 transition"
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>
        {children}
      </div>
    </div>
  );
};

export const DialogHeader: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => <div className={cn("flex flex-col space-y-1.5 text-left mb-4", className)}>{children}</div>;

export const DialogContent: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => <div className={cn("space-y-4", className)}>{children}</div>;

export const DialogTitle: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <h2 className={cn("text-[20px] font-bold tracking-[-0.02em] text-[#f3ead6]", className)}>
    {children}
  </h2>
);

export const DialogDescription: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <p className={cn("text-xs text-[rgba(243,234,214,0.72)] leading-relaxed", className)}>
    {children}
  </p>
);

export const DialogFooter: React.FC<{ className?: string; children: React.ReactNode }> = ({
  className,
  children,
}) => (
  <div className={cn("flex items-center justify-end gap-2 pt-4 border-t border-[rgba(243,234,214,0.15)] mt-4", className)}>
    {children}
  </div>
);

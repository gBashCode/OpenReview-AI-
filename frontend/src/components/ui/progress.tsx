import * as React from "react";
import { cn } from "../../lib/utils";

interface ProgressProps {
  value: number; // 0 to 100
  max?: number;
  className?: string;
  indicatorClassName?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  className,
  indicatorClassName,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-slate-800/80",
        className
      )}
    >
      <div
        className={cn(
          "h-full bg-gradient-to-r from-sky-500 to-indigo-500 transition-all duration-300",
          indicatorClassName
        )}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

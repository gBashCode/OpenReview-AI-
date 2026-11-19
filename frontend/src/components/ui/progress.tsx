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
        "relative h-1.5 w-full overflow-hidden rounded-[1px] bg-[#221f1a]",
        className
      )}
    >
      <div
        className={cn(
          "h-full bg-gradient-to-r from-[#d4a853] via-[#e29b38] to-[#c7882c] transition-all duration-300",
          indicatorClassName
        )}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

import * as React from "react";
import { cn } from "../../lib/utils";

interface SwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onCheckedChange,
  disabled = false,
  className,
  id,
}) => {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      id={id}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border border-[#36312a] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#d4a853] disabled:cursor-not-allowed disabled:opacity-40",
        checked ? "bg-[#d4a853]" : "bg-[#1c1a17]",
        className
      )}
    >
      <span
        className={cn(
          "pointer-events-none block h-3.5 w-3.5 rounded-full shadow transition-transform",
          checked ? "translate-x-4 bg-[#0e0d0b]" : "translate-x-0.5 bg-[#8a8378]"
        )}
      />
    </button>
  );
};

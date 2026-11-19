import * as React from "react";
import { cn } from "../../lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-8 w-full rounded-[2px] border border-[#2e2a24] bg-[#161411] px-3 py-1 text-xs text-[#f5f0e6] shadow-sm transition-colors placeholder:text-[#6a6358] focus-visible:outline-none focus-visible:border-[#d4a853] focus-visible:ring-1 focus-visible:ring-[#d4a853]/40 disabled:cursor-not-allowed disabled:opacity-40 font-mono",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };

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
          "flex h-9 w-full rounded-full border border-[rgba(243,234,214,0.22)] bg-[rgba(255,248,230,0.06)] px-4 py-1.5 text-xs text-[#f3ead6] shadow-sm transition-colors placeholder:text-[rgba(243,234,214,0.5)] focus-visible:outline-none focus-visible:border-[#d4a853] focus-visible:ring-2 focus-visible:ring-[#d4a853]/40 disabled:cursor-not-allowed disabled:opacity-40",
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

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-[3px] text-xs font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#d4a853] disabled:pointer-events-none disabled:opacity-40 select-none cursor-pointer tracking-tight",
  {
    variants: {
      variant: {
        default:
          "bg-[#d4a853] text-[#0e0d0b] font-semibold hover:bg-[#e0b663] active:translate-y-[1px] shadow-sm",
        electric:
          "bg-gradient-to-r from-[#d4a853] via-[#e29b38] to-[#c7882c] text-[#0e0d0b] font-semibold hover:brightness-110 active:translate-y-[1px] shadow-sm shadow-[#d4a853]/10",
        purple:
          "bg-[#3a9e8f] text-[#0e0d0b] font-semibold hover:bg-[#47b2a2] active:translate-y-[1px]",
        destructive:
          "bg-[#c75a4a] text-[#f7e8e6] font-semibold hover:bg-[#d96555] active:translate-y-[1px]",
        outline:
          "border border-[#36312a] bg-[#161411]/80 text-[#d8d2c4] hover:bg-[#201d19] hover:text-[#f5f0e6] hover:border-[#4a433a]",
        secondary:
          "bg-[#201d19] text-[#d8d2c4] hover:bg-[#2a2621] hover:text-white border border-[#2a2621]",
        ghost:
          "hover:bg-[#201d19] hover:text-[#f5f0e6] text-[#9e9689]",
        link:
          "text-[#d4a853] underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-8 px-3.5 py-1.5",
        sm: "h-7 rounded-[2px] px-2.5 text-[11px]",
        lg: "h-9 rounded-[3px] px-5 text-sm",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, isLoading, children, disabled, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-0.5 mr-2 h-3.5 w-3.5 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-full text-xs font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#e0b04a] disabled:pointer-events-none disabled:opacity-40 select-none cursor-pointer tracking-tight active:scale-[0.97]",
  {
    variants: {
      variant: {
        default:
          "bg-[#d4a853] text-[#0e0d0b] hover:bg-[#e0b663] shadow-sm",
        electric:
          "bg-gradient-to-r from-[#d4a853] via-[#e29b38] to-[#c7882c] text-[#0e0d0b] hover:brightness-110 shadow-sm shadow-[#d4a853]/20",
        purple:
          "bg-[#3a9e8f] text-[#0e0d0b] hover:bg-[#47b2a2]",
        destructive:
          "bg-[#c75a4a] text-[#f7e8e6] hover:bg-[#d96555]",
        outline:
          "border border-[rgba(243,234,214,0.22)] bg-[rgba(255,248,230,0.06)] text-[#f3ead6] hover:bg-[rgba(255,248,230,0.12)] hover:border-[rgba(243,234,214,0.45)]",
        secondary:
          "bg-[rgba(255,248,230,0.08)] text-[#f3ead6] hover:bg-[rgba(255,248,230,0.15)] border border-[rgba(243,234,214,0.18)]",
        ghost:
          "hover:bg-[rgba(255,248,230,0.08)] hover:text-[#f5f0e6] text-[rgba(243,234,214,0.72)]",
        link:
          "text-[#d4a853] underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-9 px-4 py-1.5",
        sm: "h-7 px-3 text-[11px]",
        lg: "h-11 px-6 text-sm",
        icon: "h-9 w-9",
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
        className={cn(buttonVariants({ variant, size, className }), className)}
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

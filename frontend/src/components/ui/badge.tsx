import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-[2px] border px-2 py-0.5 text-[11px] font-mono tracking-tight font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "border-[#d4a853]/40 bg-[#d4a853]/10 text-[#e5be6b]",
        secondary:
          "border-[#2a2621] bg-[#1a1815] text-[#b8b0a2]",
        purple:
          "border-[#3a9e8f]/40 bg-[#3a9e8f]/10 text-[#4db3a3]",
        teal:
          "border-[#3a9e8f]/40 bg-[#3a9e8f]/10 text-[#4db3a3]",
        amber:
          "border-[#d4a853]/40 bg-[#d4a853]/10 text-[#e5be6b]",
        electric:
          "border-[#d4a853]/50 bg-[#241f16] text-[#f2cb7c]",
        destructive:
          "border-[#c75a4a]/40 bg-[#c75a4a]/10 text-[#e06c5b]",
        warning:
          "border-[#e29b38]/40 bg-[#e29b38]/10 text-[#f0af54]",
        success:
          "border-[#5a9e6f]/40 bg-[#5a9e6f]/10 text-[#6cb582]",
        outline:
          "border-[#36312a] bg-transparent text-[#9e9689]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };

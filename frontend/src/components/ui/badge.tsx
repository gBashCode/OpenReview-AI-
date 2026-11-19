import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-semibold tracking-wide transition-colors select-none",
  {
    variants: {
      variant: {
        default:
          "border-[#d4a853]/40 bg-[#d4a853]/15 text-[#f2cb7c]",
        secondary:
          "border-[rgba(243,234,214,0.22)] bg-[rgba(255,248,230,0.08)] text-[#f3ead6]",
        purple:
          "border-[#3a9e8f]/40 bg-[#3a9e8f]/15 text-[#4db3a3]",
        teal:
          "border-[#3a9e8f]/40 bg-[#3a9e8f]/15 text-[#4db3a3]",
        amber:
          "border-[#d4a853]/40 bg-[#d4a853]/15 text-[#f2cb7c]",
        electric:
          "border-[#d4a853]/50 bg-[#241f16] text-[#f2cb7c]",
        destructive:
          "border-[#c75a4a]/40 bg-[#c75a4a]/15 text-[#e06c5b]",
        warning:
          "border-[#e29b38]/40 bg-[#e29b38]/15 text-[#f0af54]",
        success:
          "border-[#5a9e6f]/40 bg-[#5a9e6f]/15 text-[#6cb582]",
        outline:
          "border-[rgba(243,234,214,0.25)] bg-transparent text-[rgba(243,234,214,0.72)]",
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

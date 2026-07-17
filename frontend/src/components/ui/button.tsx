import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        secondary:
          "bg-panel-elevated text-foreground hover:bg-panel-elevated/80 border border-border",
        ghost: "hover:bg-panel-elevated text-muted hover:text-foreground",
        outline:
          "border border-border bg-transparent hover:bg-panel-elevated text-foreground",
        ai: "bg-ai/15 text-ai border border-ai/30 hover:bg-ai/25",
        bullish: "bg-bullish/15 text-bullish border border-bullish/30 hover:bg-bullish/25",
        bearish: "bg-bearish/15 text-bearish border border-bearish/30 hover:bg-bearish/25",
        danger: "bg-bearish text-white hover:bg-bearish/90",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-sm px-3 text-xs",
        lg: "h-11 rounded-sm px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

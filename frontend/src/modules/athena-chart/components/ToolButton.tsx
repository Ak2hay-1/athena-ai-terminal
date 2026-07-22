"use client";

import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ToolButtonProps {
  label: string;
  active?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

export function ToolButton({
  label,
  active,
  onClick,
  children,
  className,
}: ToolButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={label}
          onClick={onClick}
          className={cn(
            "flex h-8 w-8 items-center justify-center rounded-sm border text-muted transition-colors",
            active
              ? "border-primary/50 bg-primary/15 text-primary"
              : "border-transparent hover:border-border hover:bg-panel-elevated hover:text-foreground",
            className,
          )}
        >
          {children}
        </button>
      </TooltipTrigger>
      <TooltipContent side="right">{label}</TooltipContent>
    </Tooltip>
  );
}

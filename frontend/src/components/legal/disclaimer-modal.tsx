"use client";

import { useId, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DISCLAIMER_CHECKBOX_LABEL,
  DISCLAIMER_TEXT,
  DISCLAIMER_TITLE,
  DISCLAIMER_VERSION,
} from "@/constants/disclaimer";
import { cn } from "@/lib/utils";

export interface DisclaimerModalProps {
  open: boolean;
  accepting?: boolean;
  error?: string | null;
  onAccept: () => void;
  onDecline: () => void;
}

export function DisclaimerModal({
  open,
  accepting = false,
  error = null,
  onAccept,
  onDecline,
}: DisclaimerModalProps) {
  const [checked, setChecked] = useState(false);
  const checkboxId = useId();
  const errorId = useId();

  const canAccept = checked && !accepting;

  return (
    <Dialog open={open}>
      <DialogContent
        showClose={false}
        role="alertdialog"
        aria-modal="true"
        aria-describedby="risk-disclaimer-body"
        className="flex max-h-[min(90vh,720px)] w-full max-w-xl flex-col gap-0 overflow-hidden border-warning/30 p-0 sm:max-w-xl"
        onEscapeKeyDown={(event) => event.preventDefault()}
        onPointerDownOutside={(event) => event.preventDefault()}
        onInteractOutside={(event) => event.preventDefault()}
      >
        <DialogHeader className="border-b border-border px-5 py-4 sm:px-6">
          <div className="flex items-start gap-3">
            <span
              className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-sm border border-warning/35 bg-warning/10 text-warning"
              aria-hidden="true"
            >
              <AlertTriangle className="h-4 w-4" />
            </span>
            <div className="min-w-0 space-y-1">
              <DialogTitle className="text-base text-foreground sm:text-lg">
                {DISCLAIMER_TITLE}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted">
                Disclaimer v{DISCLAIMER_VERSION} · Required before terminal access
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div
          id="risk-disclaimer-body"
          tabIndex={0}
          className="min-h-0 flex-1 overflow-y-auto px-5 py-4 text-sm leading-relaxed text-foreground/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-warning/40 sm:px-6"
        >
          {DISCLAIMER_TEXT.split("\n\n").map((paragraph, index) => (
            <p
              key={index}
              className={cn(
                "whitespace-pre-line",
                index > 0 && "mt-3",
                paragraph.startsWith("Athena DOES NOT") && "font-medium text-warning/90",
              )}
            >
              {paragraph}
            </p>
          ))}
        </div>

        <div className="space-y-4 border-t border-border bg-panel-elevated/40 px-5 py-4 sm:px-6">
          <label
            htmlFor={checkboxId}
            className="flex cursor-pointer items-start gap-3 text-sm text-foreground"
          >
            <input
              id={checkboxId}
              type="checkbox"
              checked={checked}
              onChange={(event) => setChecked(event.target.checked)}
              disabled={accepting}
              className="mt-0.5 h-4 w-4 shrink-0 rounded-sm border-border accent-warning focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-warning/50"
              aria-describedby={error ? errorId : undefined}
            />
            <span>{DISCLAIMER_CHECKBOX_LABEL}</span>
          </label>

          {error ? (
            <p id={errorId} role="alert" className="text-sm text-bearish">
              {error}
            </p>
          ) : null}

          <DialogFooter className="gap-2 sm:gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={onDecline}
              disabled={accepting}
              className="w-full sm:w-auto"
            >
              Decline
            </Button>
            <Button
              type="button"
              onClick={onAccept}
              disabled={!canAccept}
              aria-disabled={!canAccept}
              className="w-full bg-warning text-primary-foreground hover:bg-warning/90 sm:w-auto"
            >
              {accepting ? "Saving…" : "I Agree & Continue"}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

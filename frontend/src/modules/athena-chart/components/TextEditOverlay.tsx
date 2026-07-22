"use client";

import { useDrawingStore } from "../store/drawing-store";
import type { ChartController } from "../engine/controller";

interface Props {
  engineRef: React.MutableRefObject<ChartController | null>;
}

export function TextEditOverlay({ engineRef }: Props) {
  const textEdit = useDrawingStore((s) => s.textEdit);
  const setTextEdit = useDrawingStore((s) => s.setTextEdit);
  if (!textEdit) return null;

  return (
    <input
      autoFocus
      defaultValue={textEdit.text}
      className="absolute z-30 rounded-sm border border-primary bg-panel px-2 py-1 text-xs text-foreground"
      style={{ left: textEdit.x, top: textEdit.y }}
      onBlur={(e) => {
        engineRef.current?.drawingEngine.manager.update(textEdit.id, {
          meta: { text: e.target.value },
        });
        setTextEdit(null);
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        if (e.key === "Escape") setTextEdit(null);
      }}
    />
  );
}

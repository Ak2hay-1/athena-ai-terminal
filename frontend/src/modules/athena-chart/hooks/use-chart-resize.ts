"use client";

import { useEffect } from "react";

/** Observe element size changes (for layout shells around the canvas). */
export function useChartResize(
  ref: React.RefObject<HTMLElement | null>,
  onResize: (width: number, height: number) => void,
) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      onResize(width, height);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, onResize]);
}

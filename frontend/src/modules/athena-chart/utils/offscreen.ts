/** Feature-detect OffscreenCanvas for future worker rendering. */
export function supportsOffscreenCanvas(): boolean {
  return typeof OffscreenCanvas !== "undefined";
}

export function tryTransferToOffscreen(
  canvas: HTMLCanvasElement,
): OffscreenCanvas | null {
  if (!supportsOffscreenCanvas()) return null;
  if (!("transferControlToOffscreen" in canvas)) return null;
  try {
    return canvas.transferControlToOffscreen();
  } catch {
    return null;
  }
}

import { create } from "zustand";
import type {
  DrawingObject,
  DrawingTool,
  MagnetMode,
} from "../types";

interface DrawingState {
  tool: DrawingTool;
  magnetMode: MagnetMode;
  objects: DrawingObject[];
  selectedIds: string[];
  canUndo: boolean;
  canRedo: boolean;
  contextMenu: { x: number; y: number; drawingId: string | null } | null;
  textEdit: { id: string; text: string; x: number; y: number } | null;
  setTool: (tool: DrawingTool) => void;
  cycleMagnet: () => void;
  setMagnetMode: (mode: MagnetMode) => void;
  setObjects: (objects: DrawingObject[]) => void;
  setSelectedIds: (ids: string[]) => void;
  setHistoryFlags: (canUndo: boolean, canRedo: boolean) => void;
  setContextMenu: (menu: DrawingState["contextMenu"]) => void;
  setTextEdit: (edit: DrawingState["textEdit"]) => void;
  clearDrawings: () => void;
}

const MAGNET_CYCLE: MagnetMode[] = ["strong", "weak", "off"];

export const useDrawingStore = create<DrawingState>((set, get) => ({
  tool: "crosshair",
  magnetMode: "strong",
  objects: [],
  selectedIds: [],
  canUndo: false,
  canRedo: false,
  contextMenu: null,
  textEdit: null,
  setTool: (tool) => {
    if (tool === "magnet") {
      get().cycleMagnet();
      return;
    }
    set({ tool });
  },
  cycleMagnet: () =>
    set((s) => {
      const i = MAGNET_CYCLE.indexOf(s.magnetMode);
      return { magnetMode: MAGNET_CYCLE[(i + 1) % MAGNET_CYCLE.length] };
    }),
  setMagnetMode: (magnetMode) => set({ magnetMode }),
  setObjects: (objects) => {
    const prev = get().objects;
    if (Object.is(prev, objects)) return;
    if (
      prev.length === objects.length &&
      prev.every(
        (o, i) =>
          o.id === objects[i]?.id &&
          o.updatedAt === objects[i]?.updatedAt &&
          o.selected === objects[i]?.selected,
      )
    ) {
      return;
    }
    set({ objects });
  },
  setSelectedIds: (selectedIds) => set({ selectedIds }),
  setHistoryFlags: (canUndo, canRedo) => set({ canUndo, canRedo }),
  setContextMenu: (contextMenu) => set({ contextMenu }),
  setTextEdit: (textEdit) => set({ textEdit }),
  clearDrawings: () => set({ objects: [], selectedIds: [] }),
}));

/** @deprecated use magnetMode */
export function useLegacyMagnet(): boolean {
  return useDrawingStore.getState().magnetMode !== "off";
}

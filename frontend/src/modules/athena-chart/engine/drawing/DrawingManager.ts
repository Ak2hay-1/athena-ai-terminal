import type { DrawingObject } from "../../types";
import { cloneObject } from "./factory";
import { HistoryManager } from "./HistoryManager";

export class DrawingManager {
  private objects: DrawingObject[] = [];
  private clipboard: DrawingObject[] = [];
  readonly history = new HistoryManager();
  private onChange?: (objects: DrawingObject[]) => void;
  private onHistory?: (canUndo: boolean, canRedo: boolean) => void;

  setCallbacks(opts: {
    onChange?: (objects: DrawingObject[]) => void;
    onHistory?: (canUndo: boolean, canRedo: boolean) => void;
  }): void {
    this.onChange = opts.onChange;
    this.onHistory = opts.onHistory;
  }

  getAll(): DrawingObject[] {
    return this.objects;
  }

  getVisibleSorted(): DrawingObject[] {
    return this.objects
      .filter((o) => o.visible)
      .slice()
      .sort((a, b) => a.zIndex - b.zIndex);
  }

  setAll(objects: DrawingObject[], recordHistory = false): void {
    const equivalent =
      objects.length === this.objects.length &&
      objects.every(
        (o, i) =>
          o.id === this.objects[i]?.id &&
          o.updatedAt === this.objects[i]?.updatedAt &&
          o.selected === this.objects[i]?.selected,
      );
    // Skip clone+emit when React is echoing the same drawings back (breaks update-depth loop)
    if (equivalent && !recordHistory) return;
    if (recordHistory) {
      this.history.push({
        kind: "replaceAll",
        before: this.objects.map(cloneObject),
        after: objects.map(cloneObject),
      });
    }
    this.objects = objects.map(cloneObject);
    this.emit();
  }

  add(obj: DrawingObject, record = true): void {
    if (record) this.history.push({ kind: "add", objects: [cloneObject(obj)] });
    this.objects = [...this.objects, cloneObject(obj)];
    this.emit();
  }

  addMany(objs: DrawingObject[], record = true): void {
    if (!objs.length) return;
    if (record) this.history.push({ kind: "add", objects: objs.map(cloneObject) });
    this.objects = [...this.objects, ...objs.map(cloneObject)];
    this.emit();
  }

  remove(ids: string[], record = true): void {
    const removed = this.objects.filter((o) => ids.includes(o.id));
    if (!removed.length) return;
    if (record) this.history.push({ kind: "remove", objects: removed.map(cloneObject) });
    const idSet = new Set(ids);
    this.objects = this.objects.filter((o) => !idSet.has(o.id));
    this.emit();
  }

  update(id: string, patch: Partial<DrawingObject>, record = true): void {
    const idx = this.objects.findIndex((o) => o.id === id);
    if (idx < 0) return;
    const before = cloneObject(this.objects[idx]);
    const after: DrawingObject = {
      ...before,
      ...patch,
      points: patch.points ? patch.points.map((p) => ({ ...p })) : before.points,
      style: patch.style ? { ...before.style, ...patch.style } : before.style,
      meta: patch.meta ? { ...before.meta, ...patch.meta } : before.meta,
      updatedAt: Date.now(),
    };
    if (record) this.history.push({ kind: "update", before: [before], after: [cloneObject(after)] });
    const next = this.objects.slice();
    next[idx] = after;
    this.objects = next;
    this.emit();
  }

  updateMany(updates: DrawingObject[], record = true): void {
    if (!updates.length) return;
    const before: DrawingObject[] = [];
    const after: DrawingObject[] = [];
    const map = new Map(updates.map((u) => [u.id, u]));
    this.objects = this.objects.map((o) => {
      const u = map.get(o.id);
      if (!u) return o;
      before.push(cloneObject(o));
      const n = { ...cloneObject(u), updatedAt: Date.now() };
      after.push(n);
      return n;
    });
    if (record) this.history.push({ kind: "update", before, after });
    this.emit();
  }

  select(ids: string[], additive = false): void {
    const idSet = new Set(ids);
    this.objects = this.objects.map((o) => ({
      ...o,
      selected: additive ? o.selected || idSet.has(o.id) : idSet.has(o.id),
    }));
    this.emit(false);
  }

  clearSelection(): void {
    if (!this.objects.some((o) => o.selected)) return;
    this.objects = this.objects.map((o) => ({ ...o, selected: false }));
    this.emit(false);
  }

  getSelected(): DrawingObject[] {
    return this.objects.filter((o) => o.selected);
  }

  duplicateSelected(): void {
    const selected = this.getSelected();
    if (!selected.length) return;
    const copies = selected.map((o) => {
      const c = cloneObject(o);
      c.id = `${o.id}-copy-${Date.now()}`;
      c.selected = true;
      c.zIndex = Date.now();
      c.points = c.points.map((p) => ({ t: p.t, p: p.p * 1.0001 }));
      c.createdAt = Date.now();
      c.updatedAt = Date.now();
      return c;
    });
    this.objects = this.objects.map((o) => ({ ...o, selected: false }));
    this.addMany(copies, true);
  }

  copySelected(): void {
    this.clipboard = this.getSelected().map(cloneObject);
  }

  paste(): void {
    if (!this.clipboard.length) return;
    const copies = this.clipboard.map((o) => {
      const c = cloneObject(o);
      c.id = `${o.id}-paste-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      c.selected = true;
      c.zIndex = Date.now();
      c.createdAt = Date.now();
      c.updatedAt = Date.now();
      return c;
    });
    this.objects = this.objects.map((o) => ({ ...o, selected: false }));
    this.addMany(copies, true);
  }

  bringForward(): void {
    const selected = this.getSelected();
    if (!selected.length) return;
    const maxZ = Math.max(...this.objects.map((o) => o.zIndex), 0);
    this.updateMany(
      selected.map((o) => ({ ...o, zIndex: maxZ + 1, updatedAt: Date.now() })),
      true,
    );
  }

  sendBackward(): void {
    const selected = this.getSelected();
    if (!selected.length) return;
    const minZ = Math.min(...this.objects.map((o) => o.zIndex), 0);
    this.updateMany(
      selected.map((o) => ({ ...o, zIndex: minZ - 1, updatedAt: Date.now() })),
      true,
    );
  }

  setLocked(locked: boolean): void {
    const selected = this.getSelected();
    this.updateMany(
      selected.map((o) => ({ ...o, locked, updatedAt: Date.now() })),
      true,
    );
  }

  setVisible(visible: boolean): void {
    const selected = this.getSelected();
    this.updateMany(
      selected.map((o) => ({ ...o, visible, updatedAt: Date.now() })),
      true,
    );
  }

  setColor(color: string): void {
    const selected = this.getSelected();
    this.updateMany(
      selected.map((o) => ({
        ...o,
        style: { ...o.style, color },
        updatedAt: Date.now(),
      })),
      true,
    );
  }

  undo(): void {
    this.history.undo((objs) => {
      this.objects = objs;
      this.emit();
    }, this.objects);
  }

  redo(): void {
    this.history.redo((objs) => {
      this.objects = objs;
      this.emit();
    }, this.objects);
  }

  private emit(history = true): void {
    this.onChange?.(this.objects.map(cloneObject));
    if (history) {
      this.onHistory?.(this.history.canUndo, this.history.canRedo);
    }
  }
}

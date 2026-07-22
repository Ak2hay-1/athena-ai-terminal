import type { DrawingObject } from "../../types";
import { cloneObject } from "./factory";

export type HistoryCommand =
  | { kind: "add"; objects: DrawingObject[] }
  | { kind: "remove"; objects: DrawingObject[] }
  | { kind: "update"; before: DrawingObject[]; after: DrawingObject[] }
  | { kind: "replaceAll"; before: DrawingObject[]; after: DrawingObject[] };

export class HistoryManager {
  private undoStack: HistoryCommand[] = [];
  private redoStack: HistoryCommand[] = [];

  get canUndo(): boolean {
    return this.undoStack.length > 0;
  }

  get canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  push(cmd: HistoryCommand): void {
    this.undoStack.push(cmd);
    this.redoStack = [];
  }

  undo(apply: (objects: DrawingObject[]) => void, current: DrawingObject[]): DrawingObject[] {
    const cmd = this.undoStack.pop();
    if (!cmd) return current;
    this.redoStack.push(cmd);
    const next = this.applyInverse(cmd, current);
    apply(next);
    return next;
  }

  redo(apply: (objects: DrawingObject[]) => void, current: DrawingObject[]): DrawingObject[] {
    const cmd = this.redoStack.pop();
    if (!cmd) return current;
    this.undoStack.push(cmd);
    const next = this.applyForward(cmd, current);
    apply(next);
    return next;
  }

  clear(): void {
    this.undoStack = [];
    this.redoStack = [];
  }

  private applyInverse(cmd: HistoryCommand, current: DrawingObject[]): DrawingObject[] {
    switch (cmd.kind) {
      case "add": {
        const ids = new Set(cmd.objects.map((o) => o.id));
        return current.filter((o) => !ids.has(o.id));
      }
      case "remove":
        return [...current, ...cmd.objects.map(cloneObject)];
      case "update": {
        const map = new Map(cmd.before.map((o) => [o.id, cloneObject(o)]));
        return current.map((o) => map.get(o.id) ?? o);
      }
      case "replaceAll":
        return cmd.before.map(cloneObject);
    }
  }

  private applyForward(cmd: HistoryCommand, current: DrawingObject[]): DrawingObject[] {
    switch (cmd.kind) {
      case "add":
        return [...current, ...cmd.objects.map(cloneObject)];
      case "remove": {
        const ids = new Set(cmd.objects.map((o) => o.id));
        return current.filter((o) => !ids.has(o.id));
      }
      case "update": {
        const map = new Map(cmd.after.map((o) => [o.id, cloneObject(o)]));
        return current.map((o) => map.get(o.id) ?? o);
      }
      case "replaceAll":
        return cmd.after.map(cloneObject);
    }
  }
}

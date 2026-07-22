import type { DecisionInput, DecisionSnapshot } from "../types";
import type { DecisionMemoryRecord } from "../types";
import { runDecisionPipeline, hashCandlesLight } from "../core/pipeline";
import type { DecisionWorkerRequest, DecisionWorkerResponse } from "../workers/protocol";

/**
 * Decision engine service — worker when available, main-thread fallback.
 * Incremental: skips when analysis hash + settings unchanged.
 */
export class DecisionService {
  private worker: Worker | null = null;
  private lastHash = "";
  private pendingId: string | null = null;
  private onResult?: (snap: DecisionSnapshot, memory: DecisionMemoryRecord[]) => void;
  private onError?: (msg: string) => void;

  constructor() {
    if (typeof window !== "undefined" && typeof Worker !== "undefined") {
      try {
        this.worker = new Worker(
          new URL("../workers/decision.worker.ts", import.meta.url),
          { type: "module" },
        );
        this.worker.onmessage = (e: MessageEvent<DecisionWorkerResponse>) => {
          const msg = e.data;
          if (msg.type === "result" && msg.id === this.pendingId) {
            this.onResult?.(msg.snapshot, msg.memory);
          }
          if (msg.type === "error" && msg.id === this.pendingId) {
            this.onError?.(msg.message);
          }
        };
      } catch {
        this.worker = null;
      }
    }
  }

  setHandlers(opts: {
    onResult: (snap: DecisionSnapshot, memory: DecisionMemoryRecord[]) => void;
    onError?: (msg: string) => void;
  }): void {
    this.onResult = opts.onResult;
    this.onError = opts.onError;
  }

  decide(input: DecisionInput, force = false): void {
    const hash = [
      hashCandlesLight(input.candles),
      input.analysis.analyzedAt,
      Math.round(input.analysis.confluence.overallConfidence),
      input.timeframe,
      JSON.stringify(input.settings),
      input.previousOpportunity?.id ?? "",
      input.previousOpportunity?.updatedAt ?? 0,
    ].join(":");
    if (!force && hash === this.lastHash) return;
    this.lastHash = hash;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    this.pendingId = id;

    if (this.worker) {
      const req: DecisionWorkerRequest = { type: "decide", id, input };
      this.worker.postMessage(req);
      return;
    }

    try {
      const { snapshot, memory } = runDecisionPipeline(input);
      this.onResult?.(snapshot, memory);
    } catch (err) {
      this.onError?.(err instanceof Error ? err.message : "Decision failed");
    }
  }

  destroy(): void {
    this.worker?.terminate();
    this.worker = null;
  }
}

let singleton: DecisionService | null = null;

export function getDecisionService(): DecisionService {
  if (!singleton) singleton = new DecisionService();
  return singleton;
}

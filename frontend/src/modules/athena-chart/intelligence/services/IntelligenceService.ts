import type { AnalysisInput, AnalysisSnapshot } from "../types";
import { runAnalysisPipeline, hashCandles } from "../analysis/pipeline";
import type { IntelWorkerRequest, IntelWorkerResponse } from "../workers/protocol";
import { generateMockCandles } from "../../services/marketDataService";

/**
 * Runs analysis in a Web Worker when available; falls back to main thread.
 * Incremental: skips if candle hash unchanged.
 */
export class IntelligenceService {
  private worker: Worker | null = null;
  private lastHash = "";
  private pendingId: string | null = null;
  private onResult?: (snap: AnalysisSnapshot) => void;
  private onError?: (msg: string) => void;

  constructor() {
    if (typeof window !== "undefined" && typeof Worker !== "undefined") {
      try {
        this.worker = new Worker(
          new URL("../workers/analysis.worker.ts", import.meta.url),
          { type: "module" },
        );
        this.worker.onmessage = (e: MessageEvent<IntelWorkerResponse>) => {
          const msg = e.data;
          if (msg.type === "result" && msg.id === this.pendingId) {
            this.onResult?.(msg.snapshot);
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
    onResult: (snap: AnalysisSnapshot) => void;
    onError?: (msg: string) => void;
  }): void {
    this.onResult = opts.onResult;
    this.onError = opts.onError;
  }

  analyze(input: AnalysisInput, force = false): void {
    const hash = `${hashCandles(input.candles)}:${JSON.stringify(input.settings)}:${input.timeframe}`;
    if (!force && hash === this.lastHash) return;
    this.lastHash = hash;
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    this.pendingId = id;

    // Attach MTF series via mock aggregation if not provided
    if (!input.multiTimeframe?.length) {
      const frames = ["1M", "5M", "15M", "1H", "4H", "D1"];
      input = {
        ...input,
        multiTimeframe: frames.map((tf) => ({
          timeframe: tf,
          candles: generateMockCandles({
            symbol: input.symbol,
            timeframe: tf,
            count: tf === "D1" ? 120 : 200,
          }),
        })),
      };
    }

    if (this.worker) {
      const req: IntelWorkerRequest = { type: "analyze", id, input };
      this.worker.postMessage(req);
      return;
    }

    try {
      const snap = runAnalysisPipeline(input);
      this.onResult?.(snap);
    } catch (err) {
      this.onError?.(err instanceof Error ? err.message : "Analysis failed");
    }
  }

  destroy(): void {
    this.worker?.terminate();
    this.worker = null;
  }
}

let singleton: IntelligenceService | null = null;

export function getIntelligenceService(): IntelligenceService {
  if (!singleton) singleton = new IntelligenceService();
  return singleton;
}

/**
 * Worker message protocol for future off-main-thread indicator computation.
 */
export type IndicatorWorkerRequest =
  | { type: "ping"; id: string }
  | {
      type: "compute";
      id: string;
      indicator: "sma" | "ema" | "rsi" | "macd";
      values: number[];
      period?: number;
    };

export type IndicatorWorkerResponse =
  | { type: "pong"; id: string }
  | {
      type: "result";
      id: string;
      values: Array<number | null>;
    }
  | { type: "error"; id: string; message: string };

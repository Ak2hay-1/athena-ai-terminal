/// <reference lib="webworker" />
import { runAnalysisPipeline } from "../analysis/pipeline";
import type { IntelWorkerRequest, IntelWorkerResponse } from "./protocol";

/**
 * Intelligence analysis worker — never blocks UI.
 * Runs deterministic rule engines only (no GPT).
 */
self.onmessage = (event: MessageEvent<IntelWorkerRequest>) => {
  const msg = event.data;
  try {
    if (msg.type === "ping") {
      const res: IntelWorkerResponse = { type: "pong", id: msg.id };
      self.postMessage(res);
      return;
    }
    if (msg.type === "analyze") {
      const snapshot = runAnalysisPipeline(msg.input);
      const res: IntelWorkerResponse = { type: "result", id: msg.id, snapshot };
      self.postMessage(res);
    }
  } catch (err) {
    const res: IntelWorkerResponse = {
      type: "error",
      id: msg.id,
      message: err instanceof Error ? err.message : "Analysis failed",
    };
    self.postMessage(res);
  }
};

export {};

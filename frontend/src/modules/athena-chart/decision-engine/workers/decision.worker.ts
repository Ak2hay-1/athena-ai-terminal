/// <reference lib="webworker" />
import { runDecisionPipeline } from "../core/pipeline";
import type { DecisionWorkerRequest, DecisionWorkerResponse } from "./protocol";

/**
 * Decision engine worker — deterministic trade intelligence only (no GPT).
 */
self.onmessage = (event: MessageEvent<DecisionWorkerRequest>) => {
  const msg = event.data;
  try {
    if (msg.type === "ping") {
      const res: DecisionWorkerResponse = { type: "pong", id: msg.id };
      self.postMessage(res);
      return;
    }
    if (msg.type === "decide") {
      const { snapshot, memory } = runDecisionPipeline(msg.input);
      const res: DecisionWorkerResponse = {
        type: "result",
        id: msg.id,
        snapshot,
        memory,
      };
      self.postMessage(res);
    }
  } catch (err) {
    const res: DecisionWorkerResponse = {
      type: "error",
      id: msg.id,
      message: err instanceof Error ? err.message : "Decision failed",
    };
    self.postMessage(res);
  }
};

export {};

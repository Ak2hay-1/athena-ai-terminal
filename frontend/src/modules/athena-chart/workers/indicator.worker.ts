/// <reference lib="webworker" />
import type { IndicatorWorkerRequest, IndicatorWorkerResponse } from "./protocol";

/**
 * Stub indicator worker — echoes ping; compute path reserved for Phase 2.
 * Controllers currently compute indicators synchronously on the main thread.
 */
self.onmessage = (event: MessageEvent<IndicatorWorkerRequest>) => {
  const msg = event.data;
  if (msg.type === "ping") {
    const res: IndicatorWorkerResponse = { type: "pong", id: msg.id };
    self.postMessage(res);
    return;
  }
  if (msg.type === "compute") {
    const res: IndicatorWorkerResponse = {
      type: "error",
      id: msg.id,
      message: "Worker compute not wired yet — use sync indicators.",
    };
    self.postMessage(res);
  }
};

export {};

/// <reference lib="webworker" />
/**
 * Copilot worker stub — prompt packing can move off-main later.
 * GPT calls stay on main (network); this validates cost-gate triggers only.
 */
import type { CopilotTrigger } from "../utils/costGate";
import { mayCallGpt } from "../utils/costGate";

export type CopilotWorkerRequest = {
  type: "may_call";
  id: string;
  trigger: CopilotTrigger;
};

export type CopilotWorkerResponse = {
  type: "may_call_result";
  id: string;
  allowed: boolean;
};

self.onmessage = (event: MessageEvent<CopilotWorkerRequest>) => {
  const msg = event.data;
  if (msg.type === "may_call") {
    const res: CopilotWorkerResponse = {
      type: "may_call_result",
      id: msg.id,
      allowed: mayCallGpt(msg.trigger),
    };
    self.postMessage(res);
  }
};

export {};

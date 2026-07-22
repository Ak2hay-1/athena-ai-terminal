import type { DecisionInput, DecisionMemoryRecord, DecisionSnapshot } from "../types";

export type DecisionWorkerRequest =
  | { type: "decide"; id: string; input: DecisionInput }
  | { type: "ping"; id: string };

export type DecisionWorkerResponse =
  | {
      type: "result";
      id: string;
      snapshot: DecisionSnapshot;
      memory: DecisionMemoryRecord[];
    }
  | { type: "pong"; id: string }
  | { type: "error"; id: string; message: string };

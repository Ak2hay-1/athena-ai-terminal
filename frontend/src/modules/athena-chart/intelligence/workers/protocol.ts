import type { AnalysisInput, AnalysisSnapshot } from "../types";

export type IntelWorkerRequest =
  | { type: "analyze"; id: string; input: AnalysisInput }
  | { type: "ping"; id: string };

export type IntelWorkerResponse =
  | { type: "result"; id: string; snapshot: AnalysisSnapshot }
  | { type: "pong"; id: string }
  | { type: "error"; id: string; message: string };

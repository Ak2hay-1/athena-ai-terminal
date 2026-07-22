/**
 * Abstract input layer — voice/mic ready, text-only for now.
 */
export type CopilotInputModality = "text" | "voice" | "speech_out";

export interface CopilotUserInput {
  modality: CopilotInputModality;
  text: string;
  audioBlob?: Blob;
}

export function normalizeUserInput(raw: string | CopilotUserInput): CopilotUserInput {
  if (typeof raw === "string") {
    return { modality: "text", text: raw.trim() };
  }
  return { ...raw, text: raw.text.trim() };
}

/** Future: wire Web Speech API / mic here without changing CopilotService. */
export function isVoiceEnabled(): boolean {
  return false;
}

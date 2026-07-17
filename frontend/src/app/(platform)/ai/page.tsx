import type { Metadata } from "next";
import { AiChatView } from "@/features/ai/components/ai-chat-view";

export const metadata: Metadata = { title: "Athena AI" };

export default function AiChatPage() {
  return <AiChatView />;
}

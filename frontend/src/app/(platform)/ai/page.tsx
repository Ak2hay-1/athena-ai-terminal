import type { Metadata } from "next";
import { Suspense } from "react";
import { AiChatView } from "@/features/ai/components/ai-chat-view";

export const metadata: Metadata = { title: "Athena AI" };

export default function AiChatPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto flex h-[min(720px,calc(100dvh-7.5rem))] max-w-[960px] items-center justify-center text-sm text-muted">
          Loading assistant…
        </div>
      }
    >
      <AiChatView />
    </Suspense>
  );
}

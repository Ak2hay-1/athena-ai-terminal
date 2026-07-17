import type { Metadata } from "next";
import { JournalView } from "@/features/journal/components/journal-view";

export const metadata: Metadata = { title: "Journal" };

export default function JournalPage() {
  return <JournalView />;
}

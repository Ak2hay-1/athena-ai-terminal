import type { Metadata } from "next";
import { MarketsListView } from "@/features/markets/components/markets-list-view";

export const metadata: Metadata = { title: "Markets" };

export default function MarketsPage() {
  return <MarketsListView />;
}

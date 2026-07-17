import type { Metadata } from "next";
import { MarketDetailView } from "@/features/markets/components/market-detail-view";

type Props = { params: Promise<{ symbol: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { symbol } = await params;
  return { title: symbol.toUpperCase() };
}

export default async function MarketDetailPage({ params }: Props) {
  const { symbol } = await params;
  return <MarketDetailView symbol={symbol} />;
}

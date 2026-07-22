import type { Metadata } from "next";
import { Suspense } from "react";
import { AdvancedChartView } from "@/features/markets/components/advanced-chart-view";

type Props = { params: Promise<{ symbol: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { symbol } = await params;
  return { title: `${symbol.toUpperCase()} Chart` };
}

export default async function AdvancedChartPage({ params }: Props) {
  const { symbol } = await params;
  return (
    <Suspense
      fallback={
        <div className="flex h-[60vh] items-center justify-center text-sm text-muted">
          Loading chart…
        </div>
      }
    >
      <AdvancedChartView symbol={symbol} />
    </Suspense>
  );
}

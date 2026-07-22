import type { Metadata } from "next";
import { AthenaChartPage } from "@/modules/athena-chart/pages/AthenaChartPage";

export const metadata: Metadata = {
  title: "Athena Chart",
  description: "Professional charting terminal",
};

export default function ChartPage() {
  return <AthenaChartPage />;
}

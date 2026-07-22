import type { Metadata } from "next";
import { LearningDashboard } from "@/features/learning/components/learning-dashboard";

export const metadata: Metadata = { title: "Learning" };

export default function LearningPage() {
  return <LearningDashboard />;
}

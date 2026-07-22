import type { Metadata } from "next";
import { CoachDashboard } from "@/features/coach/components/coach-dashboard";

export const metadata: Metadata = {
  title: "Athena Coach",
  description: "Self-learning intelligence, goals, and personal coaching",
};

export default function CoachPage() {
  return <CoachDashboard />;
}

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Recommendation } from "@/types";

function institutionalRating(grade: string, score: number): string {
  if (grade === "Institutional" || score >= 95) return "Institutional";
  if (score >= 85) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 60) return "Average";
  return "Below Average";
}

export function TradeQualityCard({
  recommendation,
}: {
  recommendation: Recommendation;
}) {
  const score = recommendation.tradeQuality ?? 0;
  const grade = recommendation.qualityGrade || "—";
  if (score <= 0 && !recommendation.qualityGrade) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade Quality</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-sm border border-primary/30 bg-primary/5 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Overall Grade
          </p>
          <p className="mt-1 text-2xl font-semibold tracking-tight text-zinc-100">
            {grade || "—"}
          </p>
        </div>
        <div className="rounded-sm border border-border/60 bg-background/30 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Quality Score
          </p>
          <p className="mt-1 font-mono text-2xl text-zinc-100">{score}</p>
        </div>
        <div className="rounded-sm border border-border/60 bg-background/30 px-3 py-3">
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
            Institutional Rating
          </p>
          <p className="mt-1 text-lg text-zinc-100">
            {institutionalRating(grade, score)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

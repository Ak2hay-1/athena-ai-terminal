"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LearningCalibrationBucket } from "@/services/learning";

export function ConfidenceCalibration({
  items,
}: {
  items: LearningCalibrationBucket[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence calibration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.length === 0 ? (
          <p className="text-sm text-muted">No calibration data yet.</p>
        ) : (
          items.map((item) => (
            <div
              key={item.bucket}
              className="flex flex-wrap items-center justify-between gap-2 rounded-sm border border-border/60 px-3 py-2 text-sm"
            >
              <span className="font-mono">{item.bucket}%</span>
              <span className="text-muted">
                Predicted mid {item.predicted_mid.toFixed(0)}%
              </span>
              <span>
                Actual WR{" "}
                <span className="font-medium text-foreground">
                  {item.actual_win_rate.toFixed(1)}%
                </span>
              </span>
              <span className="text-muted">n={item.sample_size}</span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

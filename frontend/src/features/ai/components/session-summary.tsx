"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { summarizeSession } from "@/services/ai";
import { useAuthStore } from "@/store/auth-store";

type Props = {
  stats: Record<string, unknown>;
  title?: string;
};

export function SessionSummary({ stats, title = "Session summary" }: Props) {
  const user = useAuthStore((s) => s.user);
  const query = useQuery({
    queryKey: ["ai", "session-summary", stats],
    queryFn: () => summarizeSession(stats),
    enabled: Boolean(user && stats),
  });

  if (query.isLoading) {
    return (
      <Card>
        <CardContent className="py-4 text-sm text-muted">
          Summarizing session…
        </CardContent>
      </Card>
    );
  }

  if (!query.data?.success) {
    return null;
  }

  const { summary, highlights, risk_notes, lessons } = query.data;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p className="text-zinc-200">{summary}</p>
        {highlights.length > 0 ? (
          <Section label="Highlights" items={highlights} />
        ) : null}
        {risk_notes.length > 0 ? (
          <Section label="Risk notes" items={risk_notes} />
        ) : null}
        {lessons.length > 0 ? <Section label="Lessons" items={lessons} /> : null}
      </CardContent>
    </Card>
  );
}

function Section({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="mb-1 text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <ul className="list-disc space-y-1 pl-4 text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

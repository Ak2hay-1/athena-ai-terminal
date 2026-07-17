import Link from "next/link";
import { Button } from "@/components/ui/button";

interface PagePlaceholderProps {
  title: string;
  description: string;
  ctaHref?: string;
  ctaLabel?: string;
}

export function PagePlaceholder({
  title,
  description,
  ctaHref = "/",
  ctaLabel = "Back to Dashboard",
}: PagePlaceholderProps) {
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-start gap-4 py-16">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
        Coming next
      </p>
      <h2 className="text-3xl font-semibold tracking-tight">{title}</h2>
      <p className="text-sm leading-relaxed text-muted">{description}</p>
      <Button variant="secondary" asChild>
        <Link href={ctaHref}>{ctaLabel}</Link>
      </Button>
    </div>
  );
}

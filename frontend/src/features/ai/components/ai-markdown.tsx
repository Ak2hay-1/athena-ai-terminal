"use client";

/** Lightweight markdown-ish renderer (no extra dependency). */
export function AiMarkdown({ content }: { content: string }) {
  const blocks = content.split(/\n{2,}/);

  return (
    <div className="space-y-2 text-sm leading-relaxed text-zinc-200">
      {blocks.map((block, index) => {
        const lines = block.split("\n");
        const isList = lines.every((line) => /^[-*•]\s+/.test(line.trim()) || !line.trim());
        if (isList && lines.some((line) => line.trim())) {
          return (
            <ul key={index} className="list-disc space-y-1 pl-4">
              {lines
                .filter((line) => line.trim())
                .map((line, i) => (
                  <li key={i}>{renderInline(line.replace(/^[-*•]\s+/, ""))}</li>
                ))}
            </ul>
          );
        }
        return (
          <p key={index} className="whitespace-pre-wrap">
            {lines.map((line, i) => (
              <span key={i}>
                {i > 0 ? <br /> : null}
                {renderInline(line)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}

function renderInline(text: string) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={index}
          className="rounded-sm bg-background/50 px-1 py-0.5 font-mono text-[12px] text-primary"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

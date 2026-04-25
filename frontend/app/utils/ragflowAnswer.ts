import { renderPaperMarkdown } from "./markdown";

export function normalizeRagflowAnswer(
  answer: string | null | undefined,
): string {
  if (!answer) return "";

  const normalized = answer.replace(/\r\n?/g, "\n").trim();
  const lines = normalized.split("\n");
  const out: string[] = [];

  const isListLine = (line: string) => /^(\s*)([-*+]|\d+\.)\s+/.test(line);

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i] ?? "";
    out.push(line);

    const next = lines[i + 1] ?? "";
    if (isListLine(line) && isListLine(next)) {
      out.push("");
    }
  }

  return out.join("\n").trim();
}

export async function renderRagflowAnswer(
  answer: string | null | undefined,
): Promise<string> {
  const normalized = normalizeRagflowAnswer(answer);

  if (!normalized) return "";

  const rendered = await renderPaperMarkdown(normalized, {
    sections: [],
    includeHeadings: false,
  });
  return rendered.html;
}

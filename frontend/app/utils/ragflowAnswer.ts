import { renderPaperMarkdown } from "./markdown";

export function normalizeRagflowAnswer(
  answer: string | null | undefined,
): string {
  if (!answer) return "";

  return answer.replace(/\r\n?/g, "\n").trim();
}

export async function renderRagflowAnswer(
  answer: string | null | undefined,
): Promise<string> {
  const normalized = normalizeRagflowAnswer(answer);

  if (!normalized) return "";

  const rendered = await renderPaperMarkdown(normalized, { sections: [] });
  return rendered.html;
}

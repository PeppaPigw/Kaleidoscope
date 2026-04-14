import { describe, expect, it } from "vitest";

import { normalizeRagflowAnswer, renderRagflowAnswer } from "./ragflowAnswer";

describe("ragflowAnswer", () => {
  it("normalizes line endings without stripping paragraph breaks", () => {
    const answer = "First line.\r\nSecond line.\r\n\r\nThird line.";

    expect(normalizeRagflowAnswer(answer)).toBe(
      "First line.\nSecond line.\n\nThird line.",
    );
  });

  it("renders single line breaks as prose instead of forced breaks", async () => {
    const rendered = await renderRagflowAnswer(
      [
        "Existing narrative extraction methods face a trade-off.",
        "9.9%",
        "higher alignment than keyword matching on semantic agendas",
        "(p = 0.017)",
        "",
        "A second paragraph remains separate.",
      ].join("\n"),
    );

    expect(rendered).toContain("<p>");
    expect(rendered).not.toContain("<br");
    expect(rendered.match(/<p>/g)?.length).toBe(2);
    expect(rendered).toContain("9.9%");
    expect(rendered).toContain("A second paragraph remains separate.");
  });

  it("preserves markdown list formatting when present", async () => {
    const rendered = await renderRagflowAnswer(
      ["Key points:", "", "- First item", "- Second item"].join("\n"),
    );

    expect(rendered).toContain("<ul>");
    expect(rendered).toContain("<li>");
    expect(rendered).toContain("First item");
    expect(rendered).toContain("Second item");
  });
});

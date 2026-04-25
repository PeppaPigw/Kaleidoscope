import { afterEach, describe, expect, it, vi } from "vitest";

const markdownRuntimeMockState = vi.hoisted(() => ({
  failFirstMathjaxExecution: false,
  mathjaxExecutionCount: 0,
}));

vi.mock("rehype-mathjax", async (importOriginal) => {
  const actual = await importOriginal<typeof import("rehype-mathjax")>();

  return {
    ...actual,
    default(...args: Parameters<typeof actual.default>) {
      markdownRuntimeMockState.mathjaxExecutionCount += 1;

      if (
        markdownRuntimeMockState.failFirstMathjaxExecution &&
        markdownRuntimeMockState.mathjaxExecutionCount === 1
      ) {
        throw new Error("Transient rehype-mathjax execution failure");
      }

      return actual.default(...args);
    },
  };
});

import { renderPaperMarkdown } from "./markdown";

function normalizeNbsp(html: string): string {
  return html.replace(/&nbsp;/g, "\u00a0").replace(/&#xa0;/gi, "\u00a0");
}

afterEach(() => {
  markdownRuntimeMockState.failFirstMathjaxExecution = false;
  markdownRuntimeMockState.mathjaxExecutionCount = 0;
  vi.resetModules();
});

describe("renderPaperMarkdown", () => {
  it("renders math, html tables, and extracts headings from full markdown", async () => {
    const markdown = `
# Sample Paper

Inline math $E = mc^2$ appears here.

$$
\\int_0^1 x^2 \\, dx
$$

<table><tr><td>A</td><td>B</td></tr></table>
`;

    const rendered = await renderPaperMarkdown(markdown, {
      title: "Sample Paper",
      sections: [],
    });

    expect(rendered.headings).toEqual([
      {
        id: "user-content-sample-paper",
        title: "Sample Paper",
        level: 1,
      },
    ]);
    expect(rendered.html).toContain("<mjx-container");
    expect(rendered.html).toContain("<table>");
    expect(rendered.html).toContain("<td>A</td>");
  });

  it("sanitizes unsafe inline event handlers from embedded html", async () => {
    const markdown =
      '<img src="https://example.com/figure.png" onerror="alert(1)" />';

    const rendered = await renderPaperMarkdown(markdown, {
      title: "Unsafe HTML",
      sections: [],
    });

    expect(rendered.html).toContain("<img");
    expect(rendered.html).not.toContain("onerror=");
  });

  it("uses full markdown as the source of truth even when sections are present", async () => {
    const rendered = await renderPaperMarkdown(
      "# Sample Paper\n\n<table><tr><td>Rendered from markdown</td></tr></table>",
      {
        title: "Sample Paper",
        sections: [
          {
            title: "Intro",
            level: 1,
            paragraphs: ["Only a paragraph fallback"],
          },
        ],
      },
    );

    expect(rendered.html).toContain("Rendered from markdown");
    expect(rendered.html).not.toContain("Only a paragraph fallback");
  });

  it("collapses blank-line-separated author metadata into one line per author", async () => {
    const markdown = `
# Drift-Aware Continual Tokenization for Generative Recommendation

Yuebo Feng

Fudan University

Shanghai, China

ybfeng25@m.fudan.edu.cn

Jiahao Liu

Fudan University

Shanghai, China

jiahaoliu21@m.fudan.edu.cn

# Abstract

Test abstract.
`;

    const rendered = await renderPaperMarkdown(markdown, {
      title: "Drift-Aware Continual Tokenization for Generative Recommendation",
      sections: [],
    });

    const normalizedHtml = normalizeNbsp(rendered.html);

    expect(normalizedHtml).toContain(
      '<p>Yuebo Feng\u00a0\u00a0\u00a0\u00a0Fudan University\u00a0\u00a0\u00a0\u00a0<a href="mailto:ybfeng25@m.fudan.edu.cn">ybfeng25@m.fudan.edu.cn</a></p>',
    );
    expect(normalizedHtml).toContain(
      '<p>Jiahao Liu\u00a0\u00a0\u00a0\u00a0Fudan University\u00a0\u00a0\u00a0\u00a0<a href="mailto:jiahaoliu21@m.fudan.edu.cn">jiahaoliu21@m.fudan.edu.cn</a></p>',
    );
    expect(normalizedHtml).not.toContain("Shanghai, China");
  });

  it("retries markdown rendering after a transient pipeline failure", async () => {
    const markdown = "# Retry Title\n\nInline math $E = mc^2$.";
    markdownRuntimeMockState.failFirstMathjaxExecution = true;

    await expect(
      renderPaperMarkdown(markdown, {
        sections: [],
      }),
    ).rejects.toThrow("Transient rehype-mathjax execution failure");

    const rendered = await renderPaperMarkdown(markdown, {
      sections: [],
    });

    expect(markdownRuntimeMockState.mathjaxExecutionCount).toBe(2);
    expect(rendered.html).toContain("Retry Title");
    expect(rendered.html).toContain("<mjx-container");
    expect(rendered.headings).toEqual([
      {
        id: "user-content-retry-title",
        title: "Retry Title",
        level: 1,
      },
    ]);
  });
});

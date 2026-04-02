import type { Schema } from 'hast-util-sanitize'
import GithubSlugger from 'github-slugger'
import { toString } from 'mdast-util-to-string'
import rehypeMathjax from 'rehype-mathjax'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
import rehypeStringify from 'rehype-stringify'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import remarkParse from 'remark-parse'
import remarkRehype from 'remark-rehype'
import { unified } from 'unified'
import { visit } from 'unist-util-visit'

const CLOBBER_PREFIX = 'user-content-'
const CACHE_LIMIT = 12

type PaperSection = {
  title?: string;
  level?: number;
  paragraphs?: string[];
}

export interface RenderedMarkdownHeading {
  id: string;
  title: string;
  level: number;
}

export interface RenderedMarkdownResult {
  html: string;
  headings: RenderedMarkdownHeading[];
}

const renderCache = new Map<string, Promise<RenderedMarkdownResult>>()
const defaultAttributes = defaultSchema.attributes || {}

const sanitizeSchema: Schema = {
  ...defaultSchema,
  attributes: {
    ...defaultAttributes,
    code: [
      ...(defaultAttributes.code || []),
      ['className', 'language-math', 'math-inline', 'math-display'],
    ],
    div: [
      ...(defaultAttributes.div || []),
      ['className', 'math', 'math-inline', 'math-display'],
    ],
    pre: [
      ...(defaultAttributes.pre || []),
      ['className', 'language-math', 'math-inline', 'math-display'],
    ],
    span: [
      ...(defaultAttributes.span || []),
      ['className', 'math', 'math-inline', 'math-display'],
    ],
  },
}

function rebuildMarkdownFromSections(sections: PaperSection[]): string {
  return sections
    .map((section) => {
      const title = section.title?.trim() || "Untitled";
      const level = Math.min(Math.max(section.level || 1, 1), 6);
      const paragraphs = (section.paragraphs || [])
        .map((paragraph) => paragraph.trim())
        .filter(Boolean);

      return [`${"#".repeat(level)} ${title}`, ...paragraphs].join("\n\n");
    })
    .filter(Boolean)
    .join("\n\n");
}

function buildSourceMarkdown(
  markdown: string,
  sections: PaperSection[],
): string {
  const trimmed = markdown.trim();
  if (trimmed) return trimmed;

  return rebuildMarkdownFromSections(sections);
}

function buildHeadingId(title: string, slugger: GithubSlugger): string {
  return `${CLOBBER_PREFIX}${slugger.slug(title)}`
}

function extractHeadings(markdown: string): RenderedMarkdownHeading[] {
  const slugger = new GithubSlugger();
  const tree = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkMath)
    .parse(markdown);

  const headings: RenderedMarkdownHeading[] = [];

  visit(tree, "heading", (node) => {
    const title = toString(node).trim();
    if (!title) return;

    headings.push({
      id: buildHeadingId(title, slugger),
      title,
      level: node.depth,
    });
  });

  return headings;
}

function fallbackHeadingsFromSections(
  sections: PaperSection[],
): RenderedMarkdownHeading[] {
  const slugger = new GithubSlugger();

  return sections
    .map((section) => {
      const title = section.title?.trim() || "";
      if (!title) return null;

      return {
        id: buildHeadingId(title, slugger),
        title,
        level: Math.min(Math.max(section.level || 1, 1), 6),
      };
    })
    .filter((section): section is RenderedMarkdownHeading => Boolean(section));
}

function rememberResult(
  cacheKey: string,
  promise: Promise<RenderedMarkdownResult>,
): Promise<RenderedMarkdownResult> {
  renderCache.set(cacheKey, promise);

  if (renderCache.size > CACHE_LIMIT) {
    const oldestKey = renderCache.keys().next().value;
    if (oldestKey) renderCache.delete(oldestKey);
  }

  return promise;
}

export async function renderPaperMarkdown(
  markdown: string,
  options: {
    title?: string | null;
    sections?: PaperSection[] | null;
  } = {},
): Promise<RenderedMarkdownResult> {
  const sections = options.sections || [];
  const source = buildSourceMarkdown(markdown, sections);
  const cacheKey = JSON.stringify([source]);
  const cached = renderCache.get(cacheKey);

  if (cached) return cached;

  const renderPromise = (async () => {
    if (!source) {
      return {
        html: "<p><em>No content available.</em></p>",
        headings: fallbackHeadingsFromSections(sections),
      };
    }

    const headings = extractHeadings(source);
    const file = await unified()
      .use(remarkParse)
      .use(remarkGfm)
      .use(remarkMath)
      .use(remarkRehype, {
        allowDangerousHtml: true,
        clobberPrefix: CLOBBER_PREFIX,
      })
      .use(rehypeRaw)
      .use(rehypeSlug)
      .use(rehypeSanitize, sanitizeSchema)
      .use(rehypeMathjax)
      .use(rehypeStringify)
      .process(source);

    return {
      html: String(file),
      headings:
        headings.length > 0 ? headings : fallbackHeadingsFromSections(sections),
    };
  })();

  return rememberResult(cacheKey, renderPromise);
}

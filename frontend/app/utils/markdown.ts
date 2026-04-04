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

const EMAIL_RE = /@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/
const AUTHOR_FIELD_SEPARATOR = '\u00a0\u00a0\u00a0\u00a0'

function splitBlocks(lines: string[]): string[][] {
  const blocks: string[][] = []
  let currentBlock: string[] = []

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      if (currentBlock.length > 0) {
        blocks.push(currentBlock)
        currentBlock = []
      }
      continue
    }

    currentBlock.push(trimmed)
  }

  if (currentBlock.length > 0)
    blocks.push(currentBlock)

  return blocks
}

function formatAuthorEntry(fields: string[]): string | null {
  const normalizedFields = fields
    .map(field => field.trim())
    .filter(Boolean)

  if (normalizedFields.length < 3)
    return null

  const name = normalizedFields[0]
  const email = normalizedFields.find(field => EMAIL_RE.test(field))
  const affiliation = normalizedFields
    .slice(1)
    .find(field => !EMAIL_RE.test(field))

  if (!name || !affiliation || !email)
    return null

  return [name, affiliation, email].join(AUTHOR_FIELD_SEPARATOR)
}

function normalizeAuthorHeader(lines: string[]): string[] {
  const blocks = splitBlocks(lines)
  const paragraphs: string[] = []
  let pendingFields: string[] = []

  const flushPendingFields = () => {
    if (pendingFields.length === 0)
      return

    const mergedAuthorEntry = formatAuthorEntry(pendingFields)
    if (mergedAuthorEntry)
      paragraphs.push(mergedAuthorEntry)
    else
      paragraphs.push(...pendingFields)

    pendingFields = []
  }

  for (const block of blocks) {
    const blockText = block.join(' ').trim()
    if (!blockText)
      continue

    pendingFields.push(blockText)
    if (EMAIL_RE.test(blockText))
      flushPendingFields()
  }

  flushPendingFields()
  return paragraphs
}

/**
 * Collapses author name/institution/email lines in the paper header into
 * a single line per person, separated by 4 non-breaking spaces.
 *
 * Only operates on the region before the first non-title heading or "Abstract".
 */
function preprocessAuthorBlock(markdown: string): string {
  const lines = markdown.split('\n')
  const limit = Math.min(lines.length, 80)
  let titleEnd = 0

  // Find header region end: after the title heading, stop at the next heading or "Abstract"
  let sawFirstHeading = false
  let headerEnd = limit
  for (let i = 0; i < limit; i++) {
    const currentLine = lines[i] ?? ''

    if (/^#{1,6}\s/.test(currentLine)) {
      if (!sawFirstHeading) {
        sawFirstHeading = true
        titleEnd = i + 1
        continue
      }
      headerEnd = i
      break
    }
    if (/^abstract\s*$/i.test(currentLine.trim())) {
      headerEnd = i
      break
    }
  }

  const prefix = lines.slice(0, titleEnd).join('\n').trimEnd()
  const normalizedHeader = normalizeAuthorHeader(lines.slice(titleEnd, headerEnd)).join('\n\n')
  const suffix = lines.slice(headerEnd).join('\n').trimStart()

  return [prefix, normalizedHeader, suffix]
    .filter(Boolean)
    .join('\n\n')
}

function buildSourceMarkdown(
  markdown: string,
  sections: PaperSection[],
): string {
  const trimmed = markdown.trim();
  if (trimmed) return preprocessAuthorBlock(trimmed);

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

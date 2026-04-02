function normalizeMarkdownText(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '$1')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/[*_~>#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function countMarkdownWords(markdown: string): number {
  const normalized = normalizeMarkdownText(markdown)
  if (!normalized)
    return 0

  return normalized
    .split(/\s+/)
    .filter(Boolean)
    .length
}

export function buildWritingExcerpt(markdown: string, maxLength = 140): string {
  const normalized = normalizeMarkdownText(markdown)
  if (!normalized || normalized.length <= maxLength)
    return normalized

  const words = normalized.split(/\s+/).filter(Boolean)
  const limit = Math.max(0, maxLength - 3)
  let excerpt = ''

  for (const word of words) {
    const candidate = excerpt ? `${excerpt} ${word}` : word
    if (candidate.length > limit)
      break
    excerpt = candidate
  }

  if (!excerpt)
    return `${normalized.slice(0, limit).trim()}...`

  return `${excerpt}...`
}

export function sortWritingDocumentsByUpdatedAt<T extends { updated_at?: string | null }>(
  documents: T[],
): T[] {
  return [...documents].sort((left, right) => {
    const leftTs = left.updated_at ? Date.parse(left.updated_at) : Number.NEGATIVE_INFINITY
    const rightTs = right.updated_at ? Date.parse(right.updated_at) : Number.NEGATIVE_INFINITY
    return rightTs - leftTs
  })
}

import { describe, expect, it } from 'vitest'

import {
  buildWritingExcerpt,
  countMarkdownWords,
  sortWritingDocumentsByUpdatedAt,
} from './writing'

describe('writing utils', () => {
  it('counts visible words while ignoring markdown formatting markers', () => {
    expect(countMarkdownWords('# Heading\n\nText with **bold** and $E = mc^2$.')).toBe(8)
  })

  it('builds a trimmed excerpt from markdown content', () => {
    expect(
      buildWritingExcerpt('## Intro\n\nThis is a draft paragraph with [a link](https://example.com).', 28),
    ).toBe('Intro This is a draft...')
  })

  it('sorts documents by most recently updated first', () => {
    const sorted = sortWritingDocumentsByUpdatedAt([
      { id: 'older', updated_at: '2026-04-01T10:00:00Z' },
      { id: 'newer', updated_at: '2026-04-02T10:00:00Z' },
      { id: 'missing' },
    ])

    expect(sorted.map(item => item.id)).toEqual(['newer', 'older', 'missing'])
  })
})

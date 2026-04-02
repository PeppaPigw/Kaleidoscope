import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  useApi,
  type Collection,
  type PaperListResponse,
  type SearchResponse,
} from './useApi'

describe('useApi.searchPapers', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiUrl: 'http://127.0.0.1:8000' },
    }))
    vi.stubGlobal('$fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('sends mode, page, and per_page to the backend search endpoint', async () => {
    const response: SearchResponse = {
      hits: [],
      total: 0,
      page: 2,
      per_page: 40,
      query: 'graph neural nets',
      mode: 'hybrid',
      processing_time_ms: 12,
    }
    fetchMock.mockResolvedValue(response)

    const api = useApi()
    const result = await api.searchPapers('graph neural nets', {
      mode: 'hybrid',
      page: 2,
      per_page: 40,
    })

    const [url, options] = fetchMock.mock.calls[0] ?? []

    expect(url).toBeTypeOf('string')
    const requestUrl = new URL(url as string)
    expect(requestUrl.pathname).toBe('/api/v1/search')
    expect(requestUrl.searchParams.get('q')).toBe('graph neural nets')
    expect(requestUrl.searchParams.get('mode')).toBe('hybrid')
    expect(requestUrl.searchParams.get('page')).toBe('2')
    expect(requestUrl.searchParams.get('per_page')).toBe('40')
    expect(options).toEqual(expect.objectContaining({
      headers: { 'Content-Type': 'application/json' },
    }))
    expect(result).toEqual(response)
  })
})

describe('useApi.listRecentPapers', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiUrl: 'http://127.0.0.1:8000' },
    }))
    vi.stubGlobal('$fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('fetches the latest papers and maps them for the dashboard queue', async () => {
    const response: PaperListResponse = {
      items: [
        {
          id: 'paper-1',
          title: 'Latest Paper',
        },
      ],
      total: 1,
      page: 1,
      per_page: 5,
    }
    fetchMock.mockResolvedValue(response)

    const api = useApi()
    const result = await api.listRecentPapers()

    const [url, options] = fetchMock.mock.calls[0] ?? []

    expect(url).toBeTypeOf('string')
    const requestUrl = new URL(url as string)
    expect(requestUrl.pathname).toBe('/api/v1/papers')
    expect(requestUrl.searchParams.get('page')).toBe('1')
    expect(requestUrl.searchParams.get('per_page')).toBe('5')
    expect(requestUrl.searchParams.get('sort_by')).toBe('created_at')
    expect(requestUrl.searchParams.get('order')).toBe('desc')
    expect(options).toEqual(expect.objectContaining({
      headers: { 'Content-Type': 'application/json' },
    }))
    expect(result).toEqual([
      { id: 'paper-1', title: 'Latest Paper', time: '~10 min', mode: 'read' },
    ])
  })
})

describe('useApi.collections', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiUrl: 'http://127.0.0.1:8000' },
    }))
    vi.stubGlobal('$fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('returns the backend collection array directly', async () => {
    const response: Collection[] = [
      {
        id: 'collection-1',
        name: 'Workspace A',
        description: 'Mapped from backend collection',
        paper_count: 7,
        updated_at: '2026-03-30T12:00:00Z',
      },
    ]
    fetchMock.mockResolvedValue(response)

    const api = useApi()
    const result = await api.listCollections()

    const [url, options] = fetchMock.mock.calls[0] ?? []

    expect(url).toBeTypeOf('string')
    expect(new URL(url as string).pathname).toBe('/api/v1/collections')
    expect(options).toEqual(expect.objectContaining({
      headers: { 'Content-Type': 'application/json' },
    }))
    expect(result).toEqual(response)
  })

  it('creates a collection with name and description payload', async () => {
    const response: Collection = {
      id: 'collection-2',
      name: 'New Workspace',
      description: 'Created from modal',
    }
    fetchMock.mockResolvedValue(response)

    const api = useApi()
    const result = await api.createCollection({
      name: 'New Workspace',
      description: 'Created from modal',
    })

    const [url, options] = fetchMock.mock.calls[0] ?? []

    expect(url).toBeTypeOf('string')
    expect(new URL(url as string).pathname).toBe('/api/v1/collections')
    expect(options).toEqual(expect.objectContaining({
      method: 'POST',
      body: {
        name: 'New Workspace',
        description: 'Created from modal',
      },
      headers: { 'Content-Type': 'application/json' },
    }))
    expect(result).toEqual(response)
  })

  it('fetches collection detail, collection papers, and researcher profile endpoints', async () => {
    fetchMock
      .mockResolvedValueOnce({ id: 'collection-3', name: 'Detail' })
      .mockResolvedValueOnce([{ paper_id: 'paper-9', title: 'Mapped Paper' }])
      .mockResolvedValueOnce({ id: 'author-1', display_name: 'Ada Researcher' })

    const api = useApi()
    const collection = await api.getCollection('collection-3')
    const papers = await api.getCollectionPapers('collection-3')
    const profile = await api.getResearcherProfile('author-1')

    expect(new URL(fetchMock.mock.calls[0]?.[0] as string).pathname)
      .toBe('/api/v1/collections/collection-3')
    expect(new URL(fetchMock.mock.calls[1]?.[0] as string).pathname)
      .toBe('/api/v1/collections/collection-3/papers')
    expect(new URL(fetchMock.mock.calls[2]?.[0] as string).pathname)
      .toBe('/api/v1/researchers/author-1/profile')
    expect(collection).toEqual({ id: 'collection-3', name: 'Detail' })
    expect(papers).toEqual({
      papers: [{ paper_id: 'paper-9', title: 'Mapped Paper', id: 'paper-9' }],
    })
    expect(profile).toEqual({ id: 'author-1', display_name: 'Ada Researcher' })
  })
})

describe('useApi.writing', () => {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiUrl: 'http://127.0.0.1:8000' },
    }))
    vi.stubGlobal('$fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('lists, creates, updates, and deletes writing documents through the writing endpoints', async () => {
    fetchMock
      .mockResolvedValueOnce({
        items: [
          {
            id: 'doc-1',
            user_id: 'user-1',
            title: 'Draft One',
            markdown_content: '# Draft One',
            plain_text_excerpt: 'Draft One',
            word_count: 2,
            cover_image_url: null,
            created_at: '2026-04-02T12:00:00Z',
            updated_at: '2026-04-02T12:00:00Z',
            last_opened_at: '2026-04-02T12:00:00Z',
          },
        ],
        total: 1,
      })
      .mockResolvedValueOnce({
        id: 'doc-2',
        user_id: 'user-1',
        title: 'Untitled',
        markdown_content: '',
        plain_text_excerpt: '',
        word_count: 0,
        cover_image_url: null,
        created_at: '2026-04-02T12:00:00Z',
        updated_at: '2026-04-02T12:00:00Z',
        last_opened_at: '2026-04-02T12:00:00Z',
      })
      .mockResolvedValueOnce({
        id: 'doc-1',
        user_id: 'user-1',
        title: 'Draft One',
        markdown_content: '# Draft One',
        plain_text_excerpt: 'Draft One',
        word_count: 2,
        cover_image_url: null,
        created_at: '2026-04-02T12:00:00Z',
        updated_at: '2026-04-02T12:00:00Z',
        last_opened_at: '2026-04-02T12:00:00Z',
      })

    const api = useApi()
    const list = await api.listWritingDocuments()
    const created = await api.createWritingDocument()
    const updated = await api.updateWritingDocument('doc-1', {
      title: 'Draft One',
      markdown_content: '# Draft One',
    })
    await api.deleteWritingDocument('doc-1')

    expect(new URL(fetchMock.mock.calls[0]?.[0] as string).pathname)
      .toBe('/api/v1/writing/documents')
    expect(fetchMock.mock.calls[0]?.[1]).toEqual(expect.objectContaining({
      headers: { 'Content-Type': 'application/json' },
    }))

    expect(new URL(fetchMock.mock.calls[1]?.[0] as string).pathname)
      .toBe('/api/v1/writing/documents')
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }))

    expect(new URL(fetchMock.mock.calls[2]?.[0] as string).pathname)
      .toBe('/api/v1/writing/documents/doc-1')
    expect(fetchMock.mock.calls[2]?.[1]).toEqual(expect.objectContaining({
      method: 'PATCH',
      body: {
        title: 'Draft One',
        markdown_content: '# Draft One',
      },
      headers: { 'Content-Type': 'application/json' },
    }))

    expect(new URL(fetchMock.mock.calls[3]?.[0] as string).pathname)
      .toBe('/api/v1/writing/documents/doc-1')
    expect(fetchMock.mock.calls[3]?.[1]).toEqual(expect.objectContaining({
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    }))

    expect(list.total).toBe(1)
    expect(created.id).toBe('doc-2')
    expect(updated.title).toBe('Draft One')
  })

  it('uploads writing images as multipart form data without forcing a JSON content type', async () => {
    fetchMock.mockResolvedValue({
      url: 'https://img.example.com/writing/user-1/figure.png',
    })

    const api = useApi()
    const file = new File(['png-bytes'], 'figure.png', { type: 'image/png' })
    const result = await api.uploadWritingImage(file)

    const [url, options] = fetchMock.mock.calls[0] ?? []

    expect(new URL(url as string).pathname).toBe('/api/v1/writing/images')
    expect(options).toEqual(expect.objectContaining({
      method: 'POST',
    }))
    expect(options?.body).toBeInstanceOf(FormData)
    expect(options?.headers).toEqual({})
    expect(result.url).toBe('https://img.example.com/writing/user-1/figure.png')
  })
})

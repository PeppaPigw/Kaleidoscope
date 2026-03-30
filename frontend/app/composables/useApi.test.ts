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
      public: { apiUrl: 'http://localhost:8000' },
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
      public: { apiUrl: 'http://localhost:8000' },
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
      public: { apiUrl: 'http://localhost:8000' },
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
})

import { nextTick, ref, watch, watchEffect } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usePaperQA } from './usePaperQA'

describe('usePaperQA', () => {
  const apiFetch = vi.fn()
  const fetchMock = vi.fn()

  function makeStreamResponse(events: Array<Record<string, unknown>>) {
    const encoder = new TextEncoder()
    const payload = `${events.map(event => `data: ${JSON.stringify(event)}\n\n`).join('')}data: [DONE]\n\n`
    return {
      ok: true,
      status: 200,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(payload))
          controller.close()
        },
      }),
    }
  }

  beforeEach(() => {
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('computed', (getter: () => unknown) => ({
      get value() {
        return getter()
      },
    }))
    vi.stubGlobal('watch', watch)
    vi.stubGlobal('watchEffect', watchEffect)
    vi.stubGlobal('onUnmounted', () => {})
    vi.stubGlobal('useApi', () => ({ apiFetch }))
    vi.stubGlobal('useRuntimeConfig', () => ({
      public: { apiUrl: 'http://127.0.0.1:8000' },
    }))
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    apiFetch.mockReset()
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('reactively transitions a QA item from loading to answered', async () => {
    apiFetch
      .mockResolvedValueOnce({
        status: 'completed',
        chunk_count: 12,
        error_message: null,
      })

    fetchMock.mockResolvedValue(
      makeStreamResponse([
        { type: 'chunk', content: 'Agenda-based narrative extraction.' },
        { type: 'sources', sources: [] },
      ]),
    )

    const historySnapshots: Array<{ loading: boolean, answer: string | null } | null> = []
    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    watchEffect(() => {
      const item = qa.history.value[0]
      historySnapshots.push(
        item
          ? { loading: item.loading, answer: item.answer }
          : null,
      )
    })

    await qa.ask('What is the main contribution?')
    await nextTick()

    expect(historySnapshots).toContainEqual({
      loading: true,
      answer: null,
    })
    expect(historySnapshots).toContainEqual({
      loading: false,
      answer: 'Agenda-based narrative extraction.',
    })
    expect(qa.history.value[0]).toMatchObject({
      loading: false,
      answer: 'Agenda-based narrative extraction.',
      error: null,
    })
  })

  it('sends prior turns with follow-up questions and keeps messages in chronological order', async () => {
    apiFetch
      .mockResolvedValueOnce({
        status: 'completed',
        chunk_count: 12,
        error_message: null,
      })

    fetchMock
      .mockResolvedValueOnce(
        makeStreamResponse([
          { type: 'chunk', content: 'First answer.' },
          { type: 'sources', sources: [] },
        ]),
      )
      .mockResolvedValueOnce(
        makeStreamResponse([
          { type: 'chunk', content: 'Second answer.' },
          { type: 'sources', sources: [] },
        ]),
      )

    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    await qa.ask('First question?')
    await qa.ask('Follow up?')
    await nextTick()

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/api/v1/paper-qa/paper-1/ask/stream',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          question: 'First question?',
          history: [],
        }),
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/api/v1/paper-qa/paper-1/ask/stream',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          question: 'Follow up?',
          history: [
            {
              question: 'First question?',
              answer: 'First answer.',
            },
          ],
        }),
      }),
    )
    expect(qa.history.value.map(item => item.question)).toEqual([
      'First question?',
      'Follow up?',
    ])
  })

  it('clears the current conversation when starting a new chat', async () => {
    apiFetch
      .mockResolvedValueOnce({
        status: 'completed',
        chunk_count: 12,
        error_message: null,
      })

    fetchMock.mockResolvedValue(
      makeStreamResponse([
        { type: 'chunk', content: 'First answer.' },
        { type: 'sources', sources: [] },
      ]),
    )

    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    await qa.ask('First question?')
    expect(qa.history.value).toHaveLength(1)

    qa.newChat()

    expect(qa.history.value).toEqual([])
  })

  it('stores a fresh copy of sources for each answer', async () => {
    const sharedSources = [
      {
        section_title: '1. Introduction',
        normalized_section: 'introduction',
        text_snippet: 'Intro snippet',
      },
    ]

    apiFetch
      .mockResolvedValueOnce({
        status: 'completed',
        chunk_count: 12,
        error_message: null,
      })

    fetchMock.mockResolvedValue(
      makeStreamResponse([
        { type: 'chunk', content: 'First answer.' },
        { type: 'sources', sources: sharedSources },
      ]),
    )

    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    await qa.ask('First question?')

    const firstSharedSource = sharedSources[0]
    if (firstSharedSource) {
      firstSharedSource.section_title = 'Mutated source'
    }

    expect(qa.history.value[0]?.sources[0]).toMatchObject({
      section_title: '1. Introduction',
      normalized_section: 'introduction',
      text_snippet: 'Intro snippet',
    })
  })
})

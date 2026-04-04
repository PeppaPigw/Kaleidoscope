import { nextTick, ref, watch, watchEffect } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usePaperQA } from './usePaperQA'

describe('usePaperQA', () => {
  const apiFetch = vi.fn()

  beforeEach(() => {
    vi.stubGlobal('ref', ref)
    vi.stubGlobal('computed', (getter: () => unknown) => ({
      get value() {
        return getter()
      },
    }))
    vi.stubGlobal('watch', watch)
    vi.stubGlobal('onUnmounted', () => {})
    vi.stubGlobal('useApi', () => ({ apiFetch }))
  })

  afterEach(() => {
    apiFetch.mockReset()
    vi.unstubAllGlobals()
  })

  it('reactively transitions a QA item from loading to answered', async () => {
    apiFetch
      .mockResolvedValueOnce({
        status: 'completed',
        chunk_count: 12,
        error_message: null,
      })
      .mockResolvedValueOnce({
        answer: 'Agenda-based narrative extraction.',
        sources: [],
        latency_ms: 7140,
      })

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
      .mockResolvedValueOnce({
        answer: 'First answer.',
        sources: [],
        latency_ms: 1200,
      })
      .mockResolvedValueOnce({
        answer: 'Second answer.',
        sources: [],
        latency_ms: 1800,
      })

    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    await qa.ask('First question?')
    await qa.ask('Follow up?')
    await nextTick()

    expect(apiFetch).toHaveBeenNthCalledWith(2, '/paper-qa/paper-1/ask', {
      method: 'POST',
      body: {
        question: 'First question?',
        history: [],
      },
    })
    expect(apiFetch).toHaveBeenNthCalledWith(3, '/paper-qa/paper-1/ask', {
      method: 'POST',
      body: {
        question: 'Follow up?',
        history: [
          {
            question: 'First question?',
            answer: 'First answer.',
          },
        ],
      },
    })
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
      .mockResolvedValueOnce({
        answer: 'First answer.',
        sources: [],
        latency_ms: 1200,
      })

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
      .mockResolvedValueOnce({
        answer: 'First answer.',
        sources: sharedSources,
        latency_ms: 1200,
      })

    const paperId = ref('paper-1')
    const qa = usePaperQA(paperId)

    await qa.ask('First question?')

    sharedSources[0].section_title = 'Mutated source'

    expect(qa.history.value[0]?.sources[0]).toMatchObject({
      section_title: '1. Introduction',
      normalized_section: 'introduction',
      text_snippet: 'Intro snippet',
    })
  })
})

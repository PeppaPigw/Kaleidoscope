import { expect, test } from '@playwright/test'

const runtimeProcess = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process
const runtimeBuffer = (globalThis as unknown as {
  Buffer: {
    from: (value: string, encoding: string) => any
  }
}).Buffer
const baseUrl = runtimeProcess?.env?.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:3000'
const tinyPngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9VE7s2kAAAAASUVORK5CYII='

test.describe('Frontend smoke', () => {
  test('dashboard renders hero content and a monitor ribbon', async ({ page }) => {
    await page.goto(`${baseUrl}/dashboard`)

    await expect(page).toHaveURL(/\/dashboard$/)
    await expect(
      page.getByText('Clinical Multimodal Reasoning Enters the Verification Era'),
    ).toBeVisible()
    await expect(page.locator('.ks-monitor-ribbon__item').first()).toBeVisible()
    await expect(page.locator('.ks-monitor-ribbon')).toContainText(/API Server|API/)
  })

  test('admin console renders the registry and runner from mocked backend probes', async ({ page }) => {
    await page.route('http://127.0.0.1:8000/api/openapi.json', async route => {
      await route.fulfill({
        json: {
          openapi: '3.1.0',
          paths: {
            '/health': {
              get: { summary: 'Health Check' },
            },
            '/api/v1/admin/reprocess': {
              post: {
                tags: ['admin'],
                summary: 'Reprocess Papers',
                operationId: 'reprocess_papers',
              },
            },
            '/api/v1/ragflow/sync/status': {
              get: {
                tags: ['ragflow'],
                summary: 'Get Sync Status',
                operationId: 'get_sync_status',
              },
            },
            '/api/v1/papers': {
              get: {
                tags: ['papers'],
                summary: 'List Papers',
                operationId: 'list_papers',
              },
            },
          },
        },
      })
    })

    await page.route('http://127.0.0.1:8000/health', async route => {
      await route.fulfill({ json: { status: 'ok', version: '1.0.0' } })
    })

    await page.route('http://127.0.0.1:8000/health/services', async route => {
      await route.fulfill({
        json: {
          services: {
            postgresql: 'ok',
            redis: 'ok',
            grobid: 'ok',
          },
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/auth/me', async route => {
      await route.fulfill({ json: { user_id: 'user-1', mode: 'single_user' } })
    })

    await page.route('http://127.0.0.1:8000/api/v1/search/health', async route => {
      await route.fulfill({ json: { keyword: 'ok', semantic: 'ok', degraded_mode: false } })
    })

    await page.route('http://127.0.0.1:8000/api/v1/ragflow/sync/status', async route => {
      await route.fulfill({
        json: {
          enabled: true,
          freshness_minutes: 30,
          health: { status: 'ok' },
          counts: {
            total_mappings: 12,
            paper_mappings: 10,
            collection_mappings: 2,
            stale_mappings: 1,
          },
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/analytics/data-coverage', async route => {
      await route.fulfill({
        json: {
          total_papers: 42,
          institution_coverage_note: 'Good (61.9% papers have institution). Institution analytics are reliable.',
          fields: [
            { field: 'published_at', pct: 100 },
            { field: 'keywords', pct: 93 },
            { field: 'abstract', pct: 97 },
          ],
        },
      })
    })

    await page.route(/http:\/\/127\.0\.0\.1:8000\/api\/v1\/papers\?page=1&per_page=1/, async route => {
      await route.fulfill({
        json: {
          items: [{ id: 'paper-1', title: 'Sample Paper' }],
          total: 1,
          page: 1,
          per_page: 1,
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/collections', async route => {
      await route.fulfill({
        json: [{ id: 'collection-1', name: 'Sample Collection' }],
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/papers', async route => {
      await route.fulfill({
        json: {
          items: [{ id: 'paper-1', title: 'Sample Paper' }],
          total: 1,
          page: 1,
          per_page: 20,
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/researchers/emerging?top_k=1', async route => {
      await route.fulfill({
        json: {
          authors: [{ author_id: 'author-1', display_name: 'Sample Author' }],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/trends/topics?limit=1', async route => {
      await route.fulfill({
        json: {
          topics: [{ id: 'topic-1', label: 'Transformers' }],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/tags', async route => {
      await route.fulfill({
        json: [{ id: 'tag-1', name: 'NLP' }],
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/experiments?limit=1', async route => {
      await route.fulfill({
        json: [{ id: 'experiment-1', name: 'Sample Experiment' }],
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/feeds', async route => {
      await route.fulfill({
        json: { items: [{ id: 'feed-1', name: 'Feed' }], total: 1 },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/alerts/rules', async route => {
      await route.fulfill({
        json: { rules: [{ id: 'rule-1', name: 'Rule' }] },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/governance/searches', async route => {
      await route.fulfill({
        json: [{ id: 'search-1', name: 'Search' }],
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/governance/webhooks', async route => {
      await route.fulfill({
        json: [{ id: 'webhook-1', url: 'https://example.com' }],
      })
    })

    await page.goto(`${baseUrl}/admin`)

    await expect(page.getByRole('heading', { name: 'Admin Console' }).first()).toBeVisible()
    await expect(page.getByText('API Registry')).toBeVisible()
    await expect(page.getByText('/api/v1/admin/reprocess')).toBeVisible()
    await expect(page.getByText('Endpoint Runner')).toBeVisible()
    await expect(page.getByText('Auto probe queue')).toBeVisible()
    await expect(page.getByText('healthy')).toBeVisible()
    await expect(page.getByText('Registered routes')).toBeVisible()

    await page.getByText('/api/v1/papers').click()
    await page.getByRole('button', { name: 'Run Request' }).click()

    await page.getByText('/api/v1/ragflow/sync/status').click()
    await page.getByRole('button', { name: 'Run Request' }).click()

    await expect(page.getByText('Cross-endpoint restore')).toBeVisible()

    await page.locator('.admin-runner__history').filter({ hasText: 'Cross-endpoint restore' }).getByText('List Papers').click()
    await expect(page.locator('.admin-runner__endpoint-path')).toContainText('/api/v1/papers')
  })

  test('reader renders scientific markdown with math and html tables', async ({ page }) => {
    await page.route('http://127.0.0.1:8000/api/v1/papers/paper-1/content', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-1',
          title: 'Sample Scientific Paper',
          abstract: 'Abstract',
          has_full_text: true,
          format: 'markdown',
          markdown: '# Sample Scientific Paper\n\nInline math $E = mc^2$.\n\n$$\n\\\\int_0^1 x^2 \\\\, dx\n$$\n\n<table><tr><td>Metric</td><td>Value</td></tr><tr><td>Accuracy</td><td>91%</td></tr></table>',
          remote_urls: [],
          markdown_provenance: { source: 'test' },
          sections: [
            { title: 'Fallback Section', level: 1, paragraphs: ['This should not replace the markdown body.'] },
          ],
          figures: [],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/intelligence/papers/paper-1/highlights', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-1',
          highlights: ['Important result'],
          contributions: ['A contribution'],
          limitations: ['A limitation'],
          has_analysis: true,
        },
      })
    })

    await page.goto(`${baseUrl}/reader/paper-1`)

    await expect(page.getByRole('heading', { name: 'Sample Scientific Paper' }).first()).toBeVisible()
    await expect(page.locator('table')).toBeVisible()
    await expect(page.locator('td').filter({ hasText: '91%' })).toBeVisible()
    await expect(page.locator('mjx-container').first()).toBeVisible()
    await expect(page.getByText('This should not replace the markdown body.')).toHaveCount(0)

    const inlineMath = page.locator('p mjx-container:not([display="true"])').first()
    const displayMath = page.locator('mjx-container[display="true"]').first()

    const inlineMathStyles = await inlineMath.evaluate((element) => {
      const styles = window.getComputedStyle(element)
      return {
        display: styles.display,
        marginTop: styles.marginTop,
        marginBottom: styles.marginBottom,
        overflowX: styles.overflowX,
        whiteSpace: styles.whiteSpace,
      }
    })

    const displayMathStyles = await displayMath.evaluate((element) => {
      const styles = window.getComputedStyle(element)
      return {
        display: styles.display,
        overflowX: styles.overflowX,
      }
    })

    expect(inlineMathStyles).toMatchObject({
      display: 'inline-block',
      marginTop: '0px',
      marginBottom: '0px',
      overflowX: 'visible',
      whiteSpace: 'nowrap',
    })
    expect(displayMathStyles).toMatchObject({
      display: 'block',
      overflowX: 'auto',
    })
  })

  test('reader outline tracks the section currently in view', async ({ page }) => {
    const longParagraph = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. '.repeat(60)

    await page.route('http://127.0.0.1:8000/api/v1/papers/paper-scroll/content', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-scroll',
          title: 'Scrollable Paper',
          abstract: 'Abstract',
          has_full_text: true,
          format: 'markdown',
          markdown: [
            '# Scrollable Paper',
            '## First Section',
            longParagraph,
            longParagraph,
            '## Second Section',
            longParagraph,
            longParagraph,
            '## Third Section',
            longParagraph,
            longParagraph,
          ].join('\n\n'),
          remote_urls: [],
          markdown_provenance: { source: 'test' },
          sections: [],
          figures: [],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/intelligence/papers/paper-scroll/highlights', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-scroll',
          highlights: [],
          contributions: [],
          limitations: [],
          has_analysis: true,
        },
      })
    })

    await page.goto(`${baseUrl}/reader/paper-scroll`)

    const activeOutlineItem = page.locator('.ks-outline-spine__item--active .ks-outline-spine__title')

    await expect(activeOutlineItem).toHaveText('Scrollable Paper')

    await page.locator('.ks-mc__rendered h2', { hasText: 'Third Section' }).evaluate((element: Element) => {
      element.scrollIntoView({ block: 'start' })
    })

    await expect(activeOutlineItem).toHaveText('Third Section')
  })

  test('reader constrains oversized inline figures for comfortable reading', async ({ page }) => {
    const tallFigure = `data:image/svg+xml;utf8,${encodeURIComponent(`
      <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="3200" viewBox="0 0 1200 3200">
        <rect width="1200" height="3200" fill="#dbeafe" />
        <text x="120" y="1600" font-size="120" fill="#1e3a8a">Tall Figure</text>
      </svg>
    `)}`

    await page.route('http://127.0.0.1:8000/api/v1/papers/paper-image/content', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-image',
          title: 'Image Heavy Paper',
          abstract: 'Abstract',
          has_full_text: true,
          format: 'markdown',
          markdown: [
            '# Image Heavy Paper',
            '## Visual Result',
            `![Tall figure](${tallFigure})`,
          ].join('\n\n'),
          remote_urls: [],
          markdown_provenance: { source: 'test' },
          sections: [],
          figures: [],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/intelligence/papers/paper-image/highlights', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-image',
          highlights: [],
          contributions: [],
          limitations: [],
          has_analysis: true,
        },
      })
    })

    await page.goto(`${baseUrl}/reader/paper-image`)

    const image = page.getByAltText('Tall figure')
    await expect(image).toBeVisible()

    const imageMetrics = await image.evaluate(async (element: HTMLImageElement) => {
      if (!element.complete) {
        await new Promise<void>((resolve) => {
          element.addEventListener('load', () => resolve(), { once: true })
        })
      }

      const rect = element.getBoundingClientRect()
      const styles = window.getComputedStyle(element)
      return {
        height: rect.height,
        width: rect.width,
        maxHeight: styles.maxHeight,
        objectFit: styles.objectFit,
      }
    })

    expect(imageMetrics.height).toBeLessThanOrEqual(560)
    expect(imageMetrics.objectFit).toBe('contain')
    expect(imageMetrics.maxHeight).not.toBe('none')
  })

  test('paper profile surfaces extracted code, dataset, and weight links', async ({ page }) => {
    await page.route('http://127.0.0.1:8000/api/v1/papers/paper-supplements', async route => {
      await route.fulfill({
        json: {
          id: 'paper-supplements',
          title: 'Supplement-rich Paper',
          abstract: 'Abstract',
          arxiv_id: '2603.29651',
          citation_count: 7,
          published_at: '2026-03-31',
          has_full_text: true,
          authors: [
            {
              id: 'author-1',
              display_name: 'Sample Author',
              position: 0,
            },
          ],
          raw_metadata: null,
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/papers/paper-supplements/content', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-supplements',
          title: 'Supplement-rich Paper',
          abstract: 'Abstract',
          has_full_text: true,
          format: 'markdown',
          markdown: [
            '# Supplement-rich Paper',
            '## Data and Code Availability',
            'Source code: https://github.com/acme/narrative-maps.',
            'Dataset release: https://doi.org/10.5281/zenodo. 18930804.',
            'Model checkpoints: https://huggingface.co/acme/narrative-map-large',
          ].join('\n\n'),
          remote_urls: [
            { url: 'https://arxiv.org/pdf/2603.29651.pdf', source: 'arxiv', type: 'pdf' },
          ],
          markdown_provenance: { source: 'test' },
          sections: [],
          figures: [],
        },
      })
    })

    await page.route('http://127.0.0.1:8000/api/v1/claims/papers/paper-supplements', async route => {
      await route.fulfill({ json: { claims: [] } })
    })

    await page.route('http://127.0.0.1:8000/api/v1/intelligence/papers/paper-supplements/similar?top_k=5', async route => {
      await route.fulfill({ json: { similar_papers: [] } })
    })

    await page.route('http://127.0.0.1:8000/api/v1/intelligence/papers/paper-supplements/highlights', async route => {
      await route.fulfill({
        json: {
          paper_id: 'paper-supplements',
          highlights: [],
          contributions: [],
          limitations: [],
          has_analysis: true,
        },
      })
    })

    await page.goto(`${baseUrl}/papers/paper-supplements`)

    const supplementRail = page.locator('.ks-supplement-rail')
    await expect(supplementRail).toBeVisible()
    await expect(supplementRail).toContainText('GitHub Repository')
    await expect(supplementRail).toContainText('Zenodo Dataset')
    await expect(supplementRail).toContainText('Hugging Face Weights')
    await expect(supplementRail).toContainText('PDF')
    await expect(supplementRail).toContainText('arXiv')
  })

  test('writing studio loads a document, autosaves markdown, and inserts uploaded images', async ({ page }) => {
    let savedPayload: { title?: string, markdown_content?: string } | null = null
    let uploadCount = 0

    await page.route('http://127.0.0.1:8000/api/v1/writing/documents', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            items: [
              {
                id: 'doc-1',
                user_id: 'user-1',
                title: 'Draft One',
                markdown_content: '# Draft One\n\nA starting paragraph.',
                plain_text_excerpt: 'Draft One A starting paragraph.',
                word_count: 5,
                cover_image_url: null,
                created_at: '2026-04-02T12:00:00Z',
                updated_at: '2026-04-02T12:00:00Z',
                last_opened_at: '2026-04-02T12:00:00Z',
              },
            ],
            total: 1,
          },
        })
        return
      }

      await route.fallback()
    })

    await page.route('http://127.0.0.1:8000/api/v1/writing/documents/doc-1', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          json: {
            id: 'doc-1',
            user_id: 'user-1',
            title: 'Draft One',
            markdown_content: '# Draft One\n\nA starting paragraph.',
            plain_text_excerpt: 'Draft One A starting paragraph.',
            word_count: 5,
            cover_image_url: null,
            created_at: '2026-04-02T12:00:00Z',
            updated_at: '2026-04-02T12:00:00Z',
            last_opened_at: '2026-04-02T12:00:00Z',
          },
        })
        return
      }

      if (route.request().method() === 'PATCH') {
        savedPayload = route.request().postDataJSON() as { title?: string, markdown_content?: string }
        await route.fulfill({
          json: {
            id: 'doc-1',
            user_id: 'user-1',
            title: savedPayload.title ?? 'Draft One',
            markdown_content: savedPayload.markdown_content ?? '',
            plain_text_excerpt: 'Updated excerpt',
            word_count: 8,
            cover_image_url: null,
            created_at: '2026-04-02T12:00:00Z',
            updated_at: '2026-04-02T12:00:05Z',
            last_opened_at: '2026-04-02T12:00:05Z',
          },
        })
        return
      }

      await route.fallback()
    })

    await page.route('http://127.0.0.1:8000/api/v1/writing/images', async route => {
      uploadCount += 1
      await route.fulfill({
        status: 201,
        json: {
          url: `data:image/png;base64,${tinyPngBase64}`,
          alt: 'figure',
        },
      })
    })

    await page.goto(`${baseUrl}/writing`)

    await expect(page.getByRole('heading', { name: 'Writing Studio' })).toBeVisible()
    await expect(page.getByTestId('writing-document-item-doc-1')).toHaveText('Draft One')
    await expect(page.getByLabel('Document title')).toHaveValue('Draft One')
    await expect(page.getByTestId('writing-sidepanel-outline')).toHaveAttribute('aria-selected', 'true')
    await expect(page.getByTestId('writing-outline')).toContainText('Draft One')
    const leftRailSpacing = await page.evaluate(() => {
      const head = document.querySelector('.ks-writing-studio__rail-head')
      const firstItem = document.querySelector('.ks-writing-studio__document-item')
      if (!head || !firstItem)
        return null

      return firstItem.getBoundingClientRect().top - head.getBoundingClientRect().bottom
    })
    expect(leftRailSpacing).not.toBeNull()
    expect(leftRailSpacing!).toBeGreaterThan(12)
    await page.getByTestId('writing-sidepanel-preview').click()
    await expect(page.getByTestId('writing-preview')).toContainText('A starting paragraph.')
    await page.getByTestId('writing-sidepanel-outline').click()

    await page.getByLabel('Document title').fill('Draft One Revised')
    await expect.poll(() => savedPayload?.title ?? null).toBe('Draft One Revised')
    await expect(page.locator('.ks-writing-studio__status-pill.is-saved')).toBeVisible()

    await page.setInputFiles('[data-testid="writing-image-input"]', {
      name: 'figure.png',
      mimeType: 'image/png',
      buffer: runtimeBuffer.from(tinyPngBase64, 'base64'),
    })

    await expect.poll(() => uploadCount).toBe(1)
    await expect(page.locator('.tiptap img[src^="data:image/png;base64,"]')).toBeVisible()
    await page.getByTestId('writing-sidepanel-preview').click()
    await expect(page.getByTestId('writing-preview').locator('img[alt="figure"]')).toBeVisible()
  })
})

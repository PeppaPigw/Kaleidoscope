import { expect, test } from '@playwright/test'

const baseUrl = 'http://127.0.0.1:3000'

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
})

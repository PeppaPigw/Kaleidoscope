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
})

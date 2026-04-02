import { describe, expect, it } from 'vitest'

import sidebarSource from './AppSidebar.vue?raw'

describe('AppSidebar branding', () => {
  it('renders the rounded icon before the Kaleidoscope wordmark', () => {
    expect(sidebarSource).toContain('src="/brand/kaleidoscope-icon-rounded.png"')
    expect(sidebarSource).toMatch(
      /<div class="ks-sidebar__logo">[\s\S]*ks-sidebar__logo-mark[\s\S]*ks-sidebar__logo-text/,
    )
  })
})

import { describe, expect, it } from 'vitest'

import nuxtConfigSource from './nuxt.config.ts?raw'

describe('nuxt favicon config', () => {
  it('uses the rounded PNG as the browser tab icon', () => {
    expect(nuxtConfigSource).toContain("{ rel: 'icon', type: 'image/png', href: '/brand/kaleidoscope-icon-rounded.png' }")
    expect(nuxtConfigSource).toContain("{ rel: 'shortcut icon', href: '/brand/kaleidoscope-icon-rounded.png' }")
    expect(nuxtConfigSource).not.toContain("type: 'image/svg+xml'")
  })
})

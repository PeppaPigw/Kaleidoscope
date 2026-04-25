import { describe, expect, it } from "vitest";

import nuxtConfigSource from "./nuxt.config.ts?raw";

describe("nuxt favicon config", () => {
  it("uses the rounded PNG as the browser tab icon", () => {
    expect(nuxtConfigSource).toMatch(
      /rel:\s*"icon",\s*type:\s*"image\/png",\s*href:\s*"\/brand\/kaleidoscope-icon-rounded\.png"/,
    );
    expect(nuxtConfigSource).toMatch(
      /rel:\s*"shortcut icon",\s*href:\s*"\/brand\/kaleidoscope-icon-rounded\.png"/,
    );
    expect(nuxtConfigSource).not.toMatch(/type:\s*"image\/svg\+xml"/);
  });
});

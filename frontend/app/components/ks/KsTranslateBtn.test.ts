import { describe, expect, it } from "vitest";

import translateButtonSource from "./KsTranslateBtn.vue?raw";

describe("KsTranslateBtn translation labels", () => {
  it("binds the translation helper before using localized button copy in the template", () => {
    expect(translateButtonSource).toMatch(
      /const\s*\{\s*t,\s*translate,\s*getCached,\s*setCached,\s*isPending\s*\}\s*=\s*useTranslation\(\)/,
    );
    expect(translateButtonSource).toContain("t('translateAbstract')");
    expect(translateButtonSource).toContain("t('hideTranslation')");
    expect(translateButtonSource).toContain("t('showTranslation')");
  });
});

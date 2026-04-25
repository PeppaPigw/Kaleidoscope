import { describe, expect, it } from "vitest";

import facetWallSource from "./FacetWall.vue?raw";

describe("FacetWall alignment", () => {
  it("keeps facet option content left-aligned", () => {
    expect(facetWallSource).toContain(
      '<span class="ks-facet-wall__option-label">{{ opt.label }}</span>',
    );
    expect(facetWallSource).toContain(
      '<span class="ks-facet-wall__option-count ks-type-data">{{ opt.count }}</span>',
    );
    expect(facetWallSource).toContain("justify-content: flex-start;");
    expect(facetWallSource).toContain("align-items: flex-start;");
    expect(facetWallSource).toContain("text-align: left;");
  });
});

import { describe, expect, it } from "vitest";

import dashboardPageSource from "./dashboard.vue?raw";
import subscriptionsPageSource from "./settings/subscriptions.vue?raw";

describe("subscriptions personalization wiring", () => {
  it("loads the shared taxonomy and persists research facets with subscriptions", () => {
    expect(subscriptionsPageSource).toContain('"/labels.json"');
    expect(subscriptionsPageSource).toContain("Research Facets");
    expect(subscriptionsPageSource).toContain(
      "research_facets: selectedResearchFacets.value",
    );
    expect(subscriptionsPageSource).toContain("getResearchFacetSelectionCount");
    expect(subscriptionsPageSource).toContain("getResearchFacetSummary");
  });
});

describe("dashboard personalization wiring", () => {
  it("injects research facet terms into the For You request and renders facet guidance", () => {
    expect(dashboardPageSource).toContain("getResearchFacetTerms");
    expect(dashboardPageSource).toContain("getResearchFacetSummary");
    expect(dashboardPageSource).toContain(
      "const facetTerms = getResearchFacetTerms(",
    );
    expect(dashboardPageSource).toContain(
      'return `FOR YOU — ${category} + ${facetSummary.join(" · ")}`;',
    );
    expect(dashboardPageSource).toContain(
      'Guided by {{ forYouFacetSummary.join(" · ") }}',
    );
  });
});

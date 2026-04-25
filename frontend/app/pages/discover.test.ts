import { describe, expect, it } from "vitest";

import discoverPageSource from "./discover.vue?raw";

describe("discover page search wiring", () => {
  it("submits suggestion chips through the same search handler as the composer CTA", () => {
    expect(discoverPageSource).toContain(
      '@suggestion-click="handleQuerySubmit"',
    );
    expect(discoverPageSource).toContain('@submit="handleQuerySubmit"');
  });

  it("hydrates topbar-driven searches from the discover route query", () => {
    expect(discoverPageSource).toContain(
      "const routeQueryText = computed(() =>",
    );
    expect(discoverPageSource).toContain("route.query.q");
    expect(discoverPageSource).toContain("async function syncSearchFromRoute");
    expect(discoverPageSource).toContain('activeTab.value = "search"');
    expect(discoverPageSource).toContain("q: trimmed");
  });

  it("loads 50 results per page and removes the secondary reading obstacles", () => {
    expect(discoverPageSource).toContain("const PAGE_SIZE = 50;");
    expect(discoverPageSource).not.toContain("<DiscoverVenueShelf");
    expect(discoverPageSource).not.toContain("<DiscoverGraphTeaser");
    expect(discoverPageSource).not.toContain("<DiscoverSavedExplorations");
    expect(discoverPageSource).not.toContain("<DiscoverNextActionsBar");
  });
});

import { describe, expect, it } from "vitest";

import topbarSource from "./AppTopbar.vue?raw";
import queryRibbonSource from "../search/QueryRibbon.vue?raw";

function extractZIndex(source: string, selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = source.match(
    new RegExp(`${escapedSelector}\\s*\\{[^}]*z-index:\\s*(\\d+)`, "s"),
  );

  const value = match?.[1];
  if (!value) {
    throw new Error(`Unable to find z-index for selector: ${selector}`);
  }

  return Number.parseInt(value, 10);
}

describe("AppTopbar sticky layering", () => {
  it("stays above search sticky surfaces so dropdowns are not clipped", () => {
    const topbarZIndex = extractZIndex(topbarSource, ".ks-topbar");
    const queryRibbonZIndex = extractZIndex(
      queryRibbonSource,
      ".ks-query-ribbon",
    );

    expect(topbarZIndex).toBeGreaterThan(queryRibbonZIndex);
  });

  it("routes quick search submissions into Discover instead of the legacy search page", () => {
    expect(topbarSource).toContain('path: "/discover"');
    expect(topbarSource).toContain('tab: "search"');
    expect(topbarSource).toContain("q: query");
    expect(topbarSource).not.toContain("navigateTo(`/search?q=");
  });
});

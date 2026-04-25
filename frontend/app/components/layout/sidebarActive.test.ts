import { describe, expect, it } from "vitest";

import { getActiveSidebarPath, isSidebarItemActive } from "./sidebarActive";

const navPaths = [
  "/dashboard",
  "/discover",
  "/search",
  "/insights/landscape",
  "/workspaces",
  "/analysis/evidence",
  "/analysis",
  "/synthesis",
  "/writing",
  "/knowledge",
];

describe("isSidebarItemActive", () => {
  it("matches the exact route", () => {
    expect(isSidebarItemActive("/analysis", "/analysis", navPaths)).toBe(true);
  });

  it("matches child routes that stay within the same section", () => {
    expect(
      isSidebarItemActive("/workspaces/ws-1", "/workspaces", navPaths),
    ).toBe(true);
  });

  it("does not match a sibling item that only shares a prefix", () => {
    expect(
      isSidebarItemActive("/analysis/evidence", "/analysis", navPaths),
    ).toBe(false);
  });
});

describe("getActiveSidebarPath", () => {
  it("prefers the longest matching navigation path", () => {
    expect(getActiveSidebarPath("/analysis/evidence", navPaths)).toBe(
      "/analysis/evidence",
    );
  });
});

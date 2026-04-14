import { describe, expect, it } from "vitest";

import sidebarSource from "./AppSidebar.vue?raw";

describe("AppSidebar branding", () => {
  it("renders the rounded icon before the Kaleidoscope wordmark", () => {
    expect(sidebarSource).toContain(
      'src="/brand/kaleidoscope-icon-rounded.png"',
    );
    expect(sidebarSource).toMatch(
      /<div class="ks-sidebar__logo">[\s\S]*ks-sidebar__logo-mark[\s\S]*ks-sidebar__logo-text/,
    );
  });

  it("uses the shared app shell state so collapsing the rail changes the layout", () => {
    expect(sidebarSource).toContain("} = useAppShell();");
    expect(sidebarSource).toContain("'ks-sidebar--collapsed': collapsed");
    expect(sidebarSource).toContain("'ks-sidebar--mobile-open': mobileOpen");
    expect(sidebarSource).toContain('@click="toggleSidebar()"');
  });
});

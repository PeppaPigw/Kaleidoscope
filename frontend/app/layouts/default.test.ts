import { describe, expect, it } from "vitest";

import layoutSource from "./default.vue?raw";

describe("default layout shell", () => {
  it("binds the app shell to the shared sidebar width instead of a fixed offset", () => {
    expect(layoutSource).toContain("const {");
    expect(layoutSource).toContain("} = useAppShell();");
    expect(layoutSource).toContain(
      "grid-template-columns: var(--sidebar-width) minmax(0, 1fr);",
    );
    expect(layoutSource).not.toContain("margin-left: var(--sidebar-width);");
  });

  it("gates the scrim with top-level refs so desktop pages do not stay blurred", () => {
    expect(layoutSource).toContain('v-if="isMobile && mobileOpen"');
    expect(layoutSource).not.toContain(
      'v-if="shell.isMobile && shell.mobileOpen"',
    );
  });
});

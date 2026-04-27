import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  withKaleidoscopeApiKeyHeaders,
  withKaleidoscopeApiKeyQuery,
  withKaleidoscopeAuthHeaders,
} from "./apiKey";

describe("Kaleidoscope API key helpers", () => {
  beforeEach(() => {
    vi.stubGlobal("useRuntimeConfig", () => ({
      public: { apiKey: "sk-kaleidoscope" },
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("adds the default API key to protected direct fetch headers", () => {
    expect(withKaleidoscopeApiKeyHeaders({ Accept: "application/json" })).toEqual({
      "X-API-Key": "sk-kaleidoscope",
      Accept: "application/json",
    });
  });

  it("keeps bearer auth and API key headers together", () => {
    expect(withKaleidoscopeAuthHeaders({ Authorization: "Bearer jwt" })).toEqual({
      "X-API-Key": "sk-kaleidoscope",
      Authorization: "Bearer jwt",
    });
  });

  it("adds the API key query parameter for browser-only streams and links", () => {
    expect(
      withKaleidoscopeApiKeyQuery("http://127.0.0.1:8000/api/openapi.json"),
    ).toBe("http://127.0.0.1:8000/api/openapi.json?api_key=sk-kaleidoscope");
    expect(withKaleidoscopeApiKeyQuery("/api/v1/sse?topic=rag")).toBe(
      "/api/v1/sse?topic=rag&api_key=sk-kaleidoscope",
    );
  });
});

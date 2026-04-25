import { describe, expect, it } from "vitest";

import {
  appendApiQuery,
  buildApiHeaders,
  buildApiRequestPath,
  buildCurlCommand,
  createJsonExample,
  maskApiKeyForDisplay,
  parseJsonObjectInput,
  replaceApiPathParams,
} from "./apiDocs";

describe("api docs request helpers", () => {
  it("adds the top-level API key header to JSON requests", () => {
    expect(buildApiHeaders(" sk-test ", true)).toEqual({
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-API-Key": "sk-test",
    });
  });

  it("resolves path params and query params for a runnable endpoint", () => {
    const path = buildApiRequestPath("/api/v1/papers/{paper_id}/content", {
      pathParams: { paper_id: "paper 123" },
      query: {
        include: ["figures", "claims"],
        filters: { min_confidence: 0.8 },
        empty: "",
      },
    });

    const requestUrl = new URL(path, "http://placeholder.local");
    expect(requestUrl.pathname).toBe("/api/v1/papers/paper%20123/content");
    expect(requestUrl.searchParams.getAll("include")).toEqual([
      "figures",
      "claims",
    ]);
    expect(requestUrl.searchParams.get("filters")).toBe(
      JSON.stringify({ min_confidence: 0.8 }),
    );
    expect(requestUrl.searchParams.has("empty")).toBe(false);
  });

  it("masks API keys for documentation previews", () => {
    expect(maskApiKeyForDisplay("sk-kaleidoscope")).toBe("sk-**");
    expect(maskApiKeyForDisplay("custom-secret")).toBe("**");
    expect(maskApiKeyForDisplay("   ")).toBe("");
  });

  it("builds a cURL snippet that mirrors the debugger request", () => {
    const command = buildCurlCommand({
      baseUrl: "http://127.0.0.1:8000/",
      method: "POST",
      path: "/api/v1/ragflow/sync/trigger",
      apiKey: maskApiKeyForDisplay("sk-kaleidoscope"),
      body: { collection_id: "collection-1" },
    });

    expect(command).toContain(
      "curl 'http://127.0.0.1:8000/api/v1/ragflow/sync/trigger'",
    );
    expect(command).toContain("-X POST");
    expect(command).toContain("-H 'X-API-Key: sk-**'");
    expect(command).toContain("--data '{");
    expect(command).toContain('"collection_id": "collection-1"');
  });

  it("rejects non-object path and query JSON inputs", () => {
    expect(() => parseJsonObjectInput("[]", "Query params")).toThrow(
      "Query params must be a JSON object",
    );
  });

  it("creates useful request body examples from OpenAPI schemas", () => {
    expect(
      createJsonExample({
        type: "object",
        properties: {
          query: { type: "string" },
          limit: { type: "integer", default: 20 },
          include_figures: { type: "boolean" },
          tags: { type: "array", items: { type: "string" } },
        },
      }),
    ).toEqual({
      query: "string",
      limit: 20,
      include_figures: true,
      tags: ["string"],
    });
  });

  it("exposes focused low-level helpers for page previews", () => {
    expect(
      replaceApiPathParams("/papers/{paper_id}", { paper_id: "a/b" }),
    ).toBe("/papers/a%2Fb");
    expect(appendApiQuery("/papers", { page: 2 })).toBe("/papers?page=2");
  });
});

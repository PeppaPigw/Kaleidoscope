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
import { getApiExampleProfile } from "./apiExampleRegistry";
import { API_RUNTIME_EXAMPLE_REGISTRY } from "./apiRuntimeExamples";

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

  it("builds a safe cURL preview that mirrors the debugger request", () => {
    const command = buildCurlCommand({
      baseUrl: "http://127.0.0.1:8000/",
      method: "POST",
      path: "/api/v1/ragflow/sync/trigger",
      apiKey: "sk-kaleidoscope",
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

  it("copies a runnable cURL command with the local default API key", () => {
    const command = buildCurlCommand({
      baseUrl: "http://127.0.0.1:8000",
      method: "GET",
      path: "/api/v1/agent/capabilities",
      apiKey: "sk-kaleidoscope",
      mode: "copy",
    });

    expect(command).toContain("-H 'X-API-Key: sk-kaleidoscope'");
    expect(command).not.toContain("KS_API_KEY=");
    expect(command).not.toContain("sk-**");
  });

  it("copies custom API keys through an environment variable", () => {
    const command = buildCurlCommand({
      baseUrl: "http://127.0.0.1:8000",
      method: "GET",
      path: "/api/v1/agent/capabilities",
      apiKey: "custom-secret",
      mode: "copy",
    });

    expect(command).toContain("KS_API_KEY='custom-secret' curl");
    expect(command).toContain('-H "X-API-Key: $KS_API_KEY"');
    expect(command).not.toContain("-H 'X-API-Key: custom-secret'");
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

  it("provides runnable agent examples with live corpus scope and budgets", () => {
    const profile = getApiExampleProfile(
      "POST /api/v1/agent/context/task-pack",
    );

    expect(profile?.body).toEqual(
      expect.objectContaining({
        scope: expect.objectContaining({
          paper_ids: ["31a1d910-a440-4a71-8614-93bc570f7a5d"],
          topic: "Dual-View Training for Instruction-Following Information Retrieval",
        }),
        token_budget: 2048,
        include_provenance: true,
        include_confidence: true,
        input: expect.objectContaining({
          task: "write a grounded literature review",
          query: "Dual-View Training for Instruction-Following Information Retrieval",
        }),
      }),
    );
    expect(profile?.responseShape).toEqual(
      expect.objectContaining({
        data: expect.objectContaining({
          context_blocks: expect.arrayContaining([
            expect.objectContaining({
              paper_id: "31a1d910-a440-4a71-8614-93bc570f7a5d",
              paper_title:
                "Dual-View Training for Instruction-Following Information Retrieval",
              content: expect.stringContaining(
                "Instruction-following information retrieval",
              ),
            }),
          ]),
          tool_suggestions: expect.arrayContaining([
            expect.objectContaining({
              path: "/api/v1/agent/context/task-pack",
            }),
          ]),
        }),
        meta: expect.objectContaining({
          implementation_status: "production",
        }),
      }),
    );
  });

  it("uses non-empty live evidence in right-panel API examples", () => {
    const profile = getApiExampleProfile("POST /api/v1/agent/evidence/search");

    expect(profile?.body).toEqual(
      expect.objectContaining({
        query: "Dual-View Training for Instruction-Following Information Retrieval",
        paper_ids: ["31a1d910-a440-4a71-8614-93bc570f7a5d"],
        include_paper_fallback: true,
      }),
    );
    expect(profile?.responseShape).toEqual(
      expect.objectContaining({
        total: 5,
        evidence: expect.arrayContaining([
          expect.objectContaining({
            anchor: "E1",
            paper_title:
              "Dual-View Training for Instruction-Following Information Retrieval",
            section_title: "Abstract",
            content: expect.stringContaining(
              "explicit user constraints",
            ),
          }),
        ]),
      }),
    );
  });

  it("prefers verifier-generated examples over manual schema examples", () => {
    const profile = getApiExampleProfile(
      "GET /api/v1/agent/papers/{paper_id}/section-map",
    );

    expect(profile?.pathParams).toEqual({
      paper_id: "31a1d910-a440-4a71-8614-93bc570f7a5d",
    });
    expect(profile?.responseShape).toEqual(
      expect.objectContaining({
        data: expect.objectContaining({
          sections: expect.arrayContaining([
            expect.objectContaining({
              title: "Abstract",
              paragraphs: expect.arrayContaining([
                expect.stringContaining("explicit user constraints"),
              ]),
            }),
          ]),
        }),
      }),
    );
  });

  it("keeps contract aliases and endpoint ids backed by runtime examples", () => {
    const endpointProfile = getApiExampleProfile(
      "POST /api/v1/agent/context/task-pack",
    );
    const contractProfile = API_RUNTIME_EXAMPLE_REGISTRY["agent-context-task-pack"];

    expect(contractProfile?.responseShape).toEqual(endpointProfile?.responseShape);
    expect(endpointProfile?.responseShape).toEqual(
      expect.objectContaining({
        data: expect.objectContaining({
          context_blocks: expect.arrayContaining([
            expect.objectContaining({
              section_title: "Abstract",
              content: expect.stringContaining(
                "Instruction-following information retrieval",
              ),
            }),
          ]),
        }),
      }),
    );
  });

  it("does not expose old placeholder examples in API docs registries", () => {
    const serializedRuntimeExamples = JSON.stringify(API_RUNTIME_EXAMPLE_REGISTRY);

    expect(serializedRuntimeExamples).not.toContain(
      "00000000-0000-0000-0000-000000000001",
    );
    expect(serializedRuntimeExamples).not.toContain("10.1000/smoke-test");
    expect(serializedRuntimeExamples).not.toContain("Evidence snippet");
    expect(serializedRuntimeExamples).not.toContain("Section text");
  });
});

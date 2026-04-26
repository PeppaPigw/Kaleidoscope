import { describe, expect, it } from "vitest";

import {
  createHistoryRestoreSeed,
  createRunnerSeed,
  normalizeOpenApiCatalog,
  resolveAutoProbePath,
  sliceAutoProbeBatch,
} from "./useAdminConsole";

describe("normalizeOpenApiCatalog", () => {
  it("normalizes live OpenAPI paths into grouped endpoints", () => {
    const endpoints = normalizeOpenApiCatalog({
      paths: {
        "/docs": {
          get: {
            summary: "Swagger UI",
          },
        },
        "/health": {
          get: {
            summary: "Health Check",
          },
        },
        "/api/v1/admin/reprocess": {
          post: {
            tags: ["admin"],
            summary: "Reprocess Papers",
            operationId: "reprocess_papers",
            parameters: [
              {
                name: "limit",
                in: "query",
                required: false,
                schema: { type: "integer", default: 50 },
              },
            ],
          },
        },
        "/api/v1/papers/{paper_id}": {
          get: {
            tags: ["papers"],
            summary: "Get Paper",
            operationId: "get_paper",
            parameters: [
              {
                name: "paper_id",
                in: "path",
                required: true,
                schema: { type: "string" },
              },
            ],
          },
        },
        "/api/v1/sse": {
          get: {
            tags: ["sse"],
            summary: "Event Stream",
            operationId: "event_stream",
          },
        },
        "/api/v1/agent/ingest/source": {
          post: {
            tags: ["agent-acquisition"],
            summary: "Import one paper from arXiv URL.",
            operationId: "agent_a01_post_api_v1_agent_ingest_source",
            requestBody: {
              content: {
                "application/json": {
                  schema: { type: "object" },
                },
              },
            },
          },
        },
      },
    });

    expect(endpoints.map((endpoint) => endpoint.id)).toEqual([
      "POST /api/v1/admin/reprocess",
      "POST /api/v1/agent/ingest/source",
      "GET /api/v1/papers/{paper_id}",
      "GET /api/v1/sse",
      "GET /health",
    ]);

    expect(endpoints[0]).toMatchObject({
      domain: "admin",
      tag: "admin",
      probeMode: "mutating",
      parameters: [
        expect.objectContaining({
          name: "limit",
          location: "query",
          defaultValue: 50,
        }),
      ],
    });

    expect(endpoints[1]).toMatchObject({
      domain: "agent-acquisition",
      tag: "agent-acquisition",
      probeMode: "mutating",
    });

    expect(endpoints[2]).toMatchObject({
      domain: "papers",
      probeMode: "safe",
      autoProbeEligible: true,
      parameters: [
        expect.objectContaining({
          name: "paper_id",
          location: "path",
          required: true,
        }),
      ],
    });

    expect(endpoints[3]).toMatchObject({
      isStream: true,
      probeMode: "stream",
    });

    expect(endpoints[4]).toMatchObject({
      domain: "system",
      probeMode: "safe",
    });
  });
});

describe("createRunnerSeed", () => {
  it("creates a runnable seed from endpoint parameters and body metadata", () => {
    const [endpoint] = normalizeOpenApiCatalog({
      paths: {
        "/api/v1/ragflow/sync/trigger": {
          post: {
            tags: ["ragflow"],
            summary: "Trigger Sync",
            operationId: "trigger_sync",
            requestBody: {
              required: true,
              content: {
                "application/json": {
                  example: { collection_id: "abc-123" },
                },
              },
            },
            parameters: [
              {
                name: "paper_id",
                in: "query",
                required: false,
                schema: { type: "string" },
              },
            ],
          },
        },
      },
    });

    const seed = createRunnerSeed(endpoint!);

    expect(seed.pathParamsText).toBe("{}");
    expect(seed.queryText).toBe("{}");
    expect(seed.bodyText).toContain('"collection_id": "abc-123"');
  });
});

describe("resolveAutoProbePath", () => {
  it("resolves path parameters with sampled ids for automatic probing", () => {
    const endpoints = normalizeOpenApiCatalog({
      paths: {
        "/api/v1/papers/{paper_id}/content": {
          get: {
            tags: ["papers"],
            summary: "Paper Content",
            operationId: "get_paper_content",
            parameters: [
              {
                name: "paper_id",
                in: "path",
                required: true,
                schema: { type: "string" },
              },
            ],
          },
        },
        "/api/v1/trends/keywords/timeseries": {
          get: {
            tags: ["trends"],
            summary: "Keyword Timeseries",
            operationId: "keyword_timeseries",
            parameters: [
              {
                name: "keywords",
                in: "query",
                required: true,
                schema: { type: "string" },
              },
            ],
          },
        },
      },
    });

    const contentEndpoint = endpoints.find((endpoint) =>
      endpoint.path.includes("/content"),
    );
    const timeseriesEndpoint = endpoints.find((endpoint) =>
      endpoint.path.includes("/timeseries"),
    );

    expect(
      resolveAutoProbePath(contentEndpoint!, {
        paperId: "paper-123",
        collectionId: null,
        authorId: null,
        topicId: null,
        tagId: null,
        experimentId: null,
        feedId: null,
        alertRuleId: null,
        searchId: null,
        webhookId: null,
      }),
    ).toEqual({
      path: "/api/v1/papers/paper-123/content",
      detail: "Auto probe uses sampled identifiers",
    });

    expect(
      resolveAutoProbePath(timeseriesEndpoint!, {
        paperId: "paper-123",
        collectionId: null,
        authorId: null,
        topicId: null,
        tagId: null,
        experimentId: null,
        feedId: null,
        alertRuleId: null,
        searchId: null,
        webhookId: null,
      }),
    ).toEqual({
      path: null,
      detail: "Missing sample values for keywords",
    });
  });
});

describe("sliceAutoProbeBatch", () => {
  it("returns the next probe page without overshooting", () => {
    expect(sliceAutoProbeBatch(["a", "b", "c", "d"], 1, "next", 2)).toEqual({
      items: ["b", "c"],
      nextCursor: 3,
    });

    expect(sliceAutoProbeBatch(["a", "b", "c", "d"], 3, "next", 2)).toEqual({
      items: ["d"],
      nextCursor: 4,
    });
  });

  it("can drain all remaining probes in a single pass", () => {
    expect(sliceAutoProbeBatch(["a", "b", "c", "d"], 1, "all", 2)).toEqual({
      items: ["b", "c", "d"],
      nextCursor: 4,
    });
  });
});

describe("createHistoryRestoreSeed", () => {
  it("serializes saved request history back into editor-friendly JSON", () => {
    expect(
      createHistoryRestoreSeed({
        pathParams: { paper_id: "paper-1" },
        query: { limit: 10 },
        body: { refresh: true },
      }),
    ).toEqual({
      pathParamsText: '{\n  "paper_id": "paper-1"\n}',
      queryText: '{\n  "limit": 10\n}',
      bodyText: '{\n  "refresh": true\n}',
    });
  });

  it("keeps empty bodies blank so GET-style restores stay clean", () => {
    expect(
      createHistoryRestoreSeed({
        pathParams: {},
        query: {},
        body: null,
      }),
    ).toEqual({
      pathParamsText: "{}",
      queryText: "{}",
      bodyText: "",
    });
  });
});

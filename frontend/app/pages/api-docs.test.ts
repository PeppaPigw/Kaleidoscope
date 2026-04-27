import { describe, expect, it } from "vitest";

import source from "./api-docs.vue?raw";
import {
  applyApiExampleProfileToRunnerSeed,
  buildCurlCommand,
} from "../utils/apiDocs";
import { getApiExampleProfile } from "../utils/apiExampleRegistry";

describe("api docs page workflow integration", () => {
  it("loads workflow contracts and endpoint profiles from OpenAPI", () => {
    expect(source).toContain("normalizeOpenApiWorkflows");
    expect(source).toContain("workflows.value = normalizeOpenApiWorkflows(document)");
    expect(source).toContain("endpoint.agentProfile");
    expect(source).toContain("endpointAgentUseCases(endpoint)");
  });

  it("keeps the debugger backed by real runtime examples and API-key headers", () => {
    expect(source).toContain("getApiExampleProfile(endpoint.id)");
    expect(source).toContain("expectedShapeHint");
    expect(source).toContain("headers: buildApiHeaders(apiKey.value)");
    expect(source).toContain("headers: buildApiHeaders(apiKey.value, payload.body !== undefined)");
    expect(source).toContain("applyApiExampleProfileToRunnerSeed");
    expect(source).toContain("selectedExampleProfile.value?.responseShape");
  });

  it("selects workflow steps as runnable endpoints", () => {
    expect(source).toContain("function selectWorkflowStep(step: AgentWorkflowStep)");
    expect(source).toContain("selectedEndpointId.value = endpoint.id");
    expect(source).toContain("@click=\"selectWorkflowStep(step)\"");
    expect(source).toContain("Workflow Library");
  });

  it("provides a runnable right-panel request for production agent evidence search", () => {
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
            section_title: "Abstract",
            content: expect.stringContaining("explicit user constraints"),
          }),
        ]),
      }),
    );
  });

  it("applies runtime examples to the executable runner seed", () => {
    const profile = getApiExampleProfile("POST /api/v1/agent/evidence/search");
    const seed = applyApiExampleProfileToRunnerSeed({
      seed: {
        pathParams: {},
        query: {},
        body: {},
        pathParamsText: "{}",
        queryText: "{}",
        bodyText: "{}",
      },
      profile,
      generatedBody: { query: "string" },
      hasRequestBody: true,
    });

    expect(seed.pathParamsText).toBe("{}");
    expect(seed.queryText).toBe("{}");
    expect(seed.bodyText).toContain(
      '"query": "Dual-View Training for Instruction-Following Information Retrieval"',
    );
    expect(seed.bodyText).toContain('"include_paper_fallback": true');
    expect(seed.bodyText).not.toBe("{}");
    expect(seed.body).toEqual(profile?.body);
  });

  it("copies the same live debugger request with a real API key header", () => {
    const profile = getApiExampleProfile("POST /api/v1/agent/evidence/search");
    const command = buildCurlCommand({
      baseUrl: "http://127.0.0.1:8000",
      method: "POST",
      path: "/api/v1/agent/evidence/search",
      apiKey: "sk-kaleidoscope",
      mode: "copy",
      body: profile?.body,
    });

    expect(command).toContain(
      "curl 'http://127.0.0.1:8000/api/v1/agent/evidence/search'",
    );
    expect(command).toContain("-X POST");
    expect(command).toContain("-H 'X-API-Key: sk-kaleidoscope'");
    expect(command).toContain('"include_paper_fallback": true');
    expect(command).toContain(
      '"query": "Dual-View Training for Instruction-Following Information Retrieval"',
    );
    expect(command).not.toContain("sk-**");
    expect(command).not.toContain("{}");
  });
});

import { describe, expect, it } from "vitest";

import source from "./api-docs.vue?raw";

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
  });

  it("selects workflow steps as runnable endpoints", () => {
    expect(source).toContain("function selectWorkflowStep(step: AgentWorkflowStep)");
    expect(source).toContain("selectedEndpointId.value = endpoint.id");
    expect(source).toContain("@click=\"selectWorkflowStep(step)\"");
    expect(source).toContain("Workflow Library");
  });
});

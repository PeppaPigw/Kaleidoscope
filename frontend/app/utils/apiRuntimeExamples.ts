import runtimeExampleDocument from "../../../docs/memo/agent-api-runtime-examples.json";

import type { ApiExampleProfile } from "./apiExampleRegistry";

interface RuntimeExampleDocument {
  examples?: RuntimeExample[];
}

interface RuntimeExample {
  id?: string;
  method?: string;
  path?: string;
  request?: {
    path?: string;
    query?: unknown;
    body?: unknown;
  };
  response?: {
    status?: number;
    category?: string;
    body?: unknown;
    preview?: string;
  };
}

interface RankedRuntimeProfile {
  profile: ApiExampleProfile;
  score: number;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizePathname(value: string): string {
  if (value.startsWith("/")) {
    return value.split("?")[0] || value;
  }

  try {
    return new URL(value, "http://placeholder.local").pathname;
  } catch {
    return value.split("?")[0] || value;
  }
}

function decodePathPart(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function routeIdFor(example: RuntimeExample): string | null {
  const method = example.method?.toUpperCase();
  const path = example.path;
  return method && path ? `${method} ${path}` : null;
}

function extractPathParams(
  templatePath: string | undefined,
  requestPath: string | undefined,
): Record<string, unknown> {
  if (!templatePath || !requestPath || !templatePath.includes("{")) {
    return {};
  }

  const templateParts = normalizePathname(templatePath)
    .split("/")
    .filter(Boolean)
    .map(decodePathPart);
  const requestParts = normalizePathname(requestPath)
    .split("/")
    .filter(Boolean)
    .map(decodePathPart);

  if (templateParts.length !== requestParts.length) {
    return {};
  }

  const pathParams: Record<string, unknown> = {};

  templateParts.forEach((part, index) => {
    const match = /^\{([^}]+)\}$/.exec(part);
    if (!match) {
      return;
    }

    const key = match[1];
    if (!key) {
      return;
    }

    pathParams[key] = requestParts[index] ?? "";
  });

  return pathParams;
}

function readRuntimeStatus(responseBody: unknown): string | null {
  if (!isRecord(responseBody)) {
    return null;
  }

  const meta = responseBody.meta;
  if (isRecord(meta)) {
    const readiness = meta.readiness;
    if (isRecord(readiness) && typeof readiness.status === "string") {
      return readiness.status;
    }
    if (typeof meta.implementation_status === "string") {
      return meta.implementation_status;
    }
  }

  const data = responseBody.data;
  if (isRecord(data) && typeof data.implementation_status === "string") {
    return data.implementation_status;
  }

  return null;
}

function hasMeaningfulValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === "string") {
    return value.trim().length > 0;
  }

  if (Array.isArray(value)) {
    return value.some(hasMeaningfulValue);
  }

  if (isRecord(value)) {
    return Object.values(value).some(hasMeaningfulValue);
  }

  return true;
}

function scoreRuntimeExample(
  example: RuntimeExample,
  profile: ApiExampleProfile,
): number {
  let score = 0;

  if (example.response?.category === "agent_contract_json") {
    score += 100;
  }

  if (hasMeaningfulValue(profile.responseShape)) {
    score += 20;
  }

  const runtimeStatus = readRuntimeStatus(profile.responseShape);
  if (runtimeStatus === "production") {
    score += 10;
  } else if (runtimeStatus === "beta") {
    score += 5;
  } else if (runtimeStatus === "planned") {
    score -= 5;
  }

  if (example.response?.status === 200) {
    score += 2;
  }

  return score;
}

function profileFromRuntimeExample(example: RuntimeExample): ApiExampleProfile {
  const profile: ApiExampleProfile = {};
  const pathParams = extractPathParams(example.path, example.request?.path);

  if (Object.keys(pathParams).length > 0) {
    profile.pathParams = pathParams;
  }

  if (
    isRecord(example.request?.query) &&
    Object.keys(example.request.query).length > 0
  ) {
    profile.query = example.request.query;
  }

  if (
    example.request &&
    "body" in example.request &&
    example.request.body !== null
  ) {
    profile.body = example.request.body;
  }

  if (example.response && "body" in example.response) {
    profile.responseShape = example.response.body;
  } else if (example.response?.preview) {
    profile.responseShape = example.response.preview;
  }

  return profile;
}

function addProfileForKey(
  registry: Map<string, RankedRuntimeProfile>,
  key: string | null | undefined,
  rankedProfile: RankedRuntimeProfile,
) {
  if (!key) {
    return;
  }

  const current = registry.get(key);
  if (!current || rankedProfile.score >= current.score) {
    registry.set(key, rankedProfile);
  }
}

function buildRuntimeExampleRegistry(): Record<string, ApiExampleProfile> {
  const document = runtimeExampleDocument as RuntimeExampleDocument;
  const registry = new Map<string, RankedRuntimeProfile>();

  for (const example of document.examples ?? []) {
    const profile = profileFromRuntimeExample(example);
    const rankedProfile = {
      profile,
      score: scoreRuntimeExample(example, profile),
    };

    addProfileForKey(registry, example.id, rankedProfile);
    addProfileForKey(registry, routeIdFor(example), rankedProfile);
  }

  return Object.fromEntries(
    Array.from(registry.entries()).map(([key, value]) => [key, value.profile]),
  );
}

export const API_RUNTIME_EXAMPLE_REGISTRY = buildRuntimeExampleRegistry();

export function getRuntimeApiExampleProfile(
  endpointId: string,
): ApiExampleProfile | null {
  return API_RUNTIME_EXAMPLE_REGISTRY[endpointId] ?? null;
}

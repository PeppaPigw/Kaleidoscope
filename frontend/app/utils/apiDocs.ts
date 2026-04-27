export interface ApiRequestPathInput {
  pathParams?: Record<string, unknown>;
  query?: Record<string, unknown>;
}

export interface CurlCommandInput extends ApiRequestPathInput {
  baseUrl: string;
  path: string;
  method: string;
  apiKey?: string;
  mode?: "display" | "copy";
  body?: unknown;
}

export interface ApiRunnerSeed extends ApiRequestPathInput {
  body?: unknown;
  pathParamsText: string;
  queryText: string;
  bodyText: string;
}

export interface ApiExampleRunnerProfile extends ApiRequestPathInput {
  body?: unknown;
}

export interface ApiRunnerSeedInput {
  seed: ApiRunnerSeed;
  profile?: ApiExampleRunnerProfile | null;
  generatedBody?: unknown;
  hasRequestBody: boolean;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function quoteShellValue(value: string): string {
  return `'${value.replace(/'/g, `'\\''`)}'`;
}

function normalizePath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}

export function normalizeApiBaseUrl(baseUrl: string): string {
  return baseUrl.trim().replace(/\/+$/, "");
}

export function resolveApiRequestUrl(baseUrl: string, path: string): string {
  const normalizedBaseUrl = normalizeApiBaseUrl(baseUrl);
  return `${normalizedBaseUrl}${normalizePath(path)}`;
}

export function maskApiKeyForDisplay(apiKey: string): string {
  const trimmedApiKey = apiKey.trim();
  if (!trimmedApiKey) {
    return "";
  }

  if (trimmedApiKey.startsWith("sk-")) {
    return "sk-**";
  }

  return "**";
}

export function buildApiHeaders(
  apiKey: string,
  includeJson = false,
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (includeJson) {
    headers["Content-Type"] = "application/json";
  }

  const trimmedApiKey = apiKey.trim();
  if (trimmedApiKey) {
    headers["X-API-Key"] = trimmedApiKey;
  }

  return headers;
}

export function replaceApiPathParams(
  path: string,
  params: Record<string, unknown> = {},
): string {
  return path.replace(/\{([^}]+)\}/g, (_, key: string) => {
    const value = params[key];
    return encodeURIComponent(
      value === undefined || value === null ? "" : String(value),
    );
  });
}

export function appendApiQuery(
  path: string,
  query: Record<string, unknown> = {},
): string {
  const url = new URL(path, "http://placeholder.local");

  for (const [key, rawValue] of Object.entries(query)) {
    if (rawValue === "" || rawValue === null || rawValue === undefined) {
      continue;
    }

    if (Array.isArray(rawValue)) {
      for (const item of rawValue) {
        url.searchParams.append(key, String(item));
      }
      continue;
    }

    if (typeof rawValue === "object") {
      url.searchParams.set(key, JSON.stringify(rawValue));
      continue;
    }

    url.searchParams.set(key, String(rawValue));
  }

  return `${url.pathname}${url.search}`;
}

export function buildApiRequestPath(
  path: string,
  input: ApiRequestPathInput = {},
): string {
  return appendApiQuery(
    replaceApiPathParams(path, input.pathParams ?? {}),
    input.query ?? {},
  );
}

export function parseJsonObjectInput(
  input: string,
  label: string,
): Record<string, unknown> {
  const trimmedInput = input.trim();
  if (!trimmedInput) {
    return {};
  }

  const parsed = JSON.parse(trimmedInput) as unknown;
  if (!isRecord(parsed)) {
    throw new Error(`${label} must be a JSON object`);
  }

  return parsed;
}

export function parseJsonBodyInput(input: string): unknown | null {
  const trimmedInput = input.trim();
  if (!trimmedInput) {
    return null;
  }

  return JSON.parse(trimmedInput) as unknown;
}

export function formatJsonPreview(value: unknown, fallback = ""): string {
  if (value === undefined) {
    return fallback;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return fallback;
  }
}

export function applyApiExampleProfileToRunnerSeed(
  input: ApiRunnerSeedInput,
): ApiRunnerSeed {
  const { seed, profile, generatedBody, hasRequestBody } = input;
  const seedBody =
    seed.bodyText && seed.bodyText !== "{}" ? seed.body : generatedBody;

  return {
    pathParams: profile?.pathParams ?? seed.pathParams ?? {},
    query: profile?.query ?? seed.query ?? {},
    body: hasRequestBody ? (profile?.body ?? seedBody) : null,
    pathParamsText: formatJsonPreview(
      profile?.pathParams ?? seed.pathParams,
      seed.pathParamsText,
    ),
    queryText: formatJsonPreview(profile?.query ?? seed.query, seed.queryText),
    bodyText: hasRequestBody
      ? formatJsonPreview(profile?.body ?? seedBody, "{}")
      : "",
  };
}

function firstSchemaVariant(value: unknown): Record<string, unknown> | null {
  if (!Array.isArray(value)) {
    return null;
  }

  return value.find(isRecord) ?? null;
}

function createExampleFromSchema(
  schema: Record<string, unknown>,
  depth: number,
): unknown {
  if ("example" in schema) {
    return schema.example;
  }

  if ("default" in schema) {
    return schema.default;
  }

  const enumValues = Array.isArray(schema.enum) ? schema.enum : null;
  if (enumValues && enumValues.length > 0) {
    return enumValues[0];
  }

  const nestedSchema =
    firstSchemaVariant(schema.oneOf) ??
    firstSchemaVariant(schema.anyOf) ??
    firstSchemaVariant(schema.allOf);
  if (nestedSchema) {
    return createExampleFromSchema(nestedSchema, depth + 1);
  }

  const schemaType = typeof schema.type === "string" ? schema.type : null;
  const schemaFormat = typeof schema.format === "string" ? schema.format : null;

  if (depth > 4) {
    return schemaType === "array" ? [] : schemaType === "object" ? {} : null;
  }

  if (schemaType === "string") {
    if (schemaFormat === "date-time") {
      return "2026-04-26T00:00:00Z";
    }
    if (schemaFormat === "date") {
      return "2026-04-26";
    }
    return "string";
  }

  if (schemaType === "integer") {
    return 1;
  }

  if (schemaType === "number") {
    return 1.0;
  }

  if (schemaType === "boolean") {
    return true;
  }

  if (schemaType === "array") {
    const itemSchema = isRecord(schema.items) ? schema.items : null;
    return itemSchema ? [createExampleFromSchema(itemSchema, depth + 1)] : [];
  }

  const properties = isRecord(schema.properties) ? schema.properties : null;
  if (schemaType === "object" || properties) {
    if (!properties) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(properties)
        .slice(0, 16)
        .filter(([, propertySchema]) => isRecord(propertySchema))
        .map(([key, propertySchema]) => [
          key,
          createExampleFromSchema(
            propertySchema as Record<string, unknown>,
            depth + 1,
          ),
        ]),
    );
  }

  return {};
}

export function createJsonExample(
  schema: Record<string, unknown> | null,
): unknown {
  if (!schema) {
    return {};
  }

  return createExampleFromSchema(schema, 0);
}

export function buildCurlCommand(input: CurlCommandInput): string {
  const path = buildApiRequestPath(input.path, input);
  const url = resolveApiRequestUrl(input.baseUrl, path);
  const hasBody = input.body !== undefined && input.body !== null;
  const mode = input.mode ?? "display";
  const rawApiKey = (input.apiKey ?? "").trim();
  const trimmedApiKey =
    mode === "display" ? maskApiKeyForDisplay(rawApiKey) : rawApiKey;
  const useApiKeyEnv =
    mode === "copy" &&
    Boolean(trimmedApiKey) &&
    trimmedApiKey !== "sk-kaleidoscope";
  const headers = buildApiHeaders(
    useApiKeyEnv ? "$KS_API_KEY" : trimmedApiKey,
    hasBody,
  );
  const prefix = useApiKeyEnv
    ? `KS_API_KEY=${quoteShellValue(trimmedApiKey)} `
    : "";
  const parts = [`${prefix}curl ${quoteShellValue(url)}`, `-X ${input.method}`];

  for (const [header, value] of Object.entries(headers)) {
    if (useApiKeyEnv && header === "X-API-Key") {
      parts.push(`-H "X-API-Key: $KS_API_KEY"`);
      continue;
    }
    parts.push(`-H ${quoteShellValue(`${header}: ${value}`)}`);
  }

  if (hasBody) {
    parts.push(
      `--data ${quoteShellValue(formatJsonPreview(input.body, "null"))}`,
    );
  }

  const continuation = ` ${String.fromCharCode(92)}`;

  return parts
    .map((part, index) => {
      const suffix = index === parts.length - 1 ? "" : continuation;
      return index === 0 ? `${part}${suffix}` : `  ${part}${suffix}`;
    })
    .join("\n");
}

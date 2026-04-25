const DEFAULT_KALEIDOSCOPE_API_KEY = "sk-kaleidoscope";

export function getKaleidoscopeApiKey(): string {
  const configured = useRuntimeConfig().public.apiKey;
  if (typeof configured === "string" && configured.trim()) {
    return configured.trim();
  }
  return DEFAULT_KALEIDOSCOPE_API_KEY;
}

export function withKaleidoscopeApiKeyHeaders(
  headers: Record<string, string> = {},
): Record<string, string> {
  const apiKey = getKaleidoscopeApiKey();
  if (!apiKey) return { ...headers };
  return { "X-API-Key": apiKey, ...headers };
}

export function withKaleidoscopeApiKeyQuery(url: string): string {
  const apiKey = getKaleidoscopeApiKey();
  if (!apiKey) return url;

  const isAbsolute = /^https?:\/\//i.test(url);
  const parsed = new URL(
    url,
    isAbsolute ? undefined : "http://placeholder.local",
  );
  if (!parsed.searchParams.has("api_key")) {
    parsed.searchParams.set("api_key", apiKey);
  }
  return isAbsolute ? parsed.toString() : `${parsed.pathname}${parsed.search}`;
}

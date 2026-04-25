/**
 * useAuth — lightweight auth composable for Kaleidoscope.
 *
 * Manages JWT token storage and login/logout.
 * When KALEIDOSCOPE_JWT_SECRET is not set on the server,
 * the returned token is "single-user-mode" and this composable
 * is essentially a no-op (app works without login).
 */

const TOKEN_KEY = "ks_access_token";

export function useAuth() {
  const { rawFetch } = useApi();
  const token = ref<string | null>(null);
  const userId = ref<string | null>(null);
  const isSingleUserMode = ref(true);

  function loadToken() {
    if (import.meta.client) {
      token.value = localStorage.getItem(TOKEN_KEY);
    }
  }

  async function login(username: string, password: string): Promise<boolean> {
    try {
      const res = await rawFetch<{
        access_token: string;
        user_id: string;
        mode: string;
      }>("/api/v1/auth/login", {
        method: "POST",
        body: { username, password },
      });
      token.value = res.access_token;
      userId.value = res.user_id;
      isSingleUserMode.value = res.mode === "single_user";
      if (import.meta.client && res.access_token !== "single-user-mode") {
        localStorage.setItem(TOKEN_KEY, res.access_token);
      }
      return true;
    } catch {
      return false;
    }
  }

  async function logout() {
    await rawFetch("/api/v1/auth/logout", { method: "POST" }).catch(() => {});
    token.value = null;
    userId.value = null;
    if (import.meta.client) {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  async function fetchMe() {
    try {
      const res = await rawFetch<{ user_id: string; mode: string }>(
        "/api/v1/auth/me",
      );
      userId.value = res.user_id;
      isSingleUserMode.value = res.mode === "single_user";
    } catch {
      // Ignore, single-user mode
    }
  }

  onMounted(() => {
    loadToken();
    fetchMe();
  });

  return { token, userId, isSingleUserMode, login, logout, fetchMe };
}

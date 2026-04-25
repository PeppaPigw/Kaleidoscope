/**
 * Global auth middleware — redirects to /login when no token is present.
 * Only runs on the client side; SSR always passes through.
 */
export default defineNuxtRouteMiddleware((to) => {
  // Skip server-side rendering
  if (import.meta.server) return;

  const publicRoutes = ["/login"];
  const isPublic = publicRoutes.some((r) => to.path === r);

  const token = localStorage.getItem("ks_access_token");
  const hasToken = Boolean(token);

  if (!hasToken && !isPublic) {
    return navigateTo("/login");
  }

  if (hasToken && to.path === "/login") {
    return navigateTo("/dashboard");
  }
});

<script setup lang="ts">
import { withKaleidoscopeApiKeyHeaders } from "~/utils/apiKey";

definePageMeta({ layout: "auth" });

useHead({
  title: "Sign In — Kaleidoscope",
  link: [
    { rel: "preconnect", href: "https://fonts.googleapis.com" },
    { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
    {
      rel: "stylesheet",
      href: "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&display=swap",
    },
  ],
});

const config = useRuntimeConfig();
const apiBase = config.public.apiUrl as string;

const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");
const showPassword = ref(false);

async function handleSubmit() {
  if (!username.value.trim() || !password.value) return;
  loading.value = true;
  error.value = "";
  try {
    const res = await $fetch<{
      access_token: string;
      user_id: string;
      mode: string;
    }>(`${apiBase}/api/v1/auth/login`, {
      method: "POST",
      body: { username: username.value.trim(), password: password.value },
      headers: withKaleidoscopeApiKeyHeaders(),
    });
    if (import.meta.client) {
      localStorage.setItem(
        "ks_access_token",
        res.access_token || "single-user-mode",
      );
      localStorage.setItem("ks_user_id", res.user_id);
    }
    await navigateTo("/dashboard");
  } catch (e: unknown) {
    const err = e as { data?: { detail?: string }; status?: number };
    if (err?.status === 401) {
      error.value = "Invalid username or password.";
    } else {
      error.value = "Something went wrong. Please try again.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="ks-login">
    <!-- ── Left editorial panel ──────────────────────── -->
    <div class="ks-login__panel" aria-hidden="true">
      <div class="ks-login__panel-grid" />

      <div class="ks-login__panel-content">
        <div class="ks-login__brand">
          <img
            src="/brand/kaleidoscope-icon-rounded.png"
            alt=""
            class="ks-login__brand-icon"
          />
          <span class="ks-login__brand-name">Kaleidoscope</span>
        </div>

        <div class="ks-login__headline">
          <p class="ks-login__headline-line ks-login__headline-line--light">
            Where
          </p>
          <p class="ks-login__headline-line">discovery</p>
          <p class="ks-login__headline-line ks-login__headline-line--italic">
            begins.
          </p>
        </div>

        <div class="ks-login__panel-footer">
          <div class="ks-login__stat">
            <span class="ks-login__stat-num">∞</span>
            <span class="ks-login__stat-label">Papers indexed</span>
          </div>
          <div class="ks-login__stat">
            <span class="ks-login__stat-num">AI</span>
            <span class="ks-login__stat-label">Powered analysis</span>
          </div>
          <div class="ks-login__stat">
            <span class="ks-login__stat-num">24h</span>
            <span class="ks-login__stat-label">Live updates</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Right form panel ──────────────────────────── -->
    <div class="ks-login__form-side">
      <form class="ks-login__form" @submit.prevent="handleSubmit">
        <div class="ks-login__form-header">
          <h1 class="ks-login__form-title">Sign in</h1>
          <p class="ks-login__form-subtitle">Access your research workspace</p>
        </div>

        <div class="ks-login__fields">
          <div class="ks-login__field">
            <label class="ks-login__label" for="username">Username</label>
            <input
              id="username"
              v-model="username"
              type="text"
              class="ks-login__input"
              autocomplete="username"
              :disabled="loading"
              placeholder="Enter your username"
              @keydown.enter="handleSubmit"
            />
          </div>

          <div class="ks-login__field">
            <label class="ks-login__label" for="password">Password</label>
            <div class="ks-login__password-wrap">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="ks-login__input"
                autocomplete="current-password"
                :disabled="loading"
                placeholder="Enter your password"
                @keydown.enter="handleSubmit"
              />
              <button
                type="button"
                class="ks-login__password-toggle"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? "⊘" : "◎" }}
              </button>
            </div>
          </div>
        </div>

        <Transition name="ks-fade">
          <p v-if="error" class="ks-login__error" role="alert">
            {{ error }}
          </p>
        </Transition>

        <button
          type="submit"
          class="ks-login__submit"
          :disabled="loading || !username.trim() || !password"
        >
          <span v-if="!loading">Sign In</span>
          <span v-else class="ks-login__spinner" />
        </button>
      </form>

      <p class="ks-login__footer-note">
        Kaleidoscope Research Platform · Single-tenant mode
      </p>
    </div>
  </div>
</template>

<style scoped>
/* ─── Layout ────────────────────────────────────────────── */
.ks-login {
  display: flex;
  min-height: 100dvh;
  width: 100%;
}

/* ─── Left panel ────────────────────────────────────────── */
.ks-login__panel {
  position: relative;
  flex: 0 0 58%;
  background: #0d0d0d;
  overflow: hidden;
  display: flex;
  align-items: stretch;
}

.ks-login__panel-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(
    ellipse 80% 80% at 30% 40%,
    black 20%,
    transparent 100%
  );
}

/* Prismatic accent blob */
.ks-login__panel::before {
  content: "";
  position: absolute;
  width: 600px;
  height: 600px;
  top: -80px;
  left: -120px;
  background: radial-gradient(
    ellipse at center,
    rgba(13, 115, 119, 0.22) 0%,
    rgba(13, 115, 119, 0.08) 40%,
    transparent 70%
  );
  pointer-events: none;
}

.ks-login__panel::after {
  content: "";
  position: absolute;
  width: 400px;
  height: 400px;
  bottom: 60px;
  right: -80px;
  background: radial-gradient(
    ellipse at center,
    rgba(13, 115, 119, 0.12) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.ks-login__panel-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  padding: 48px 56px;
}

/* Brand */
.ks-login__brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ks-login__brand-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
}

.ks-login__brand-name {
  font: 600 1rem / 1 var(--font-display, "Cormorant Garamond", Georgia, serif);
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.04em;
}

/* Headline */
.ks-login__headline {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
}

.ks-login__headline-line {
  font-family: "Cormorant Garamond", Georgia, serif;
  font-weight: 300;
  font-size: clamp(3.5rem, 6vw, 6rem);
  line-height: 1;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  letter-spacing: -0.02em;
}

.ks-login__headline-line--light {
  color: rgba(255, 255, 255, 0.35);
  font-size: clamp(2rem, 3.5vw, 3.5rem);
  margin-bottom: 0.15em;
}

.ks-login__headline-line--italic {
  font-style: italic;
  color: rgba(13, 200, 209, 0.85);
  font-weight: 300;
}

/* Footer stats */
.ks-login__panel-footer {
  display: flex;
  gap: 40px;
}

.ks-login__stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ks-login__stat-num {
  font: 600 1.5rem / 1 var(--font-display, monospace);
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: -0.02em;
}

.ks-login__stat-label {
  font: 400 0.6875rem / 1 var(--font-sans, sans-serif);
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* ─── Right form side ───────────────────────────────────── */
.ks-login__form-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
  background: var(--color-surface, #fafaf7);
}

.ks-login__form {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.ks-login__form-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-login__form-title {
  font: 700 1.875rem / 1.1 var(--font-display, Georgia, serif);
  color: var(--color-text, #1a1a1a);
  margin: 0;
  letter-spacing: -0.03em;
}

.ks-login__form-subtitle {
  font: 400 0.875rem / 1.4 var(--font-sans, sans-serif);
  color: var(--color-secondary, #6b7280);
  margin: 0;
}

/* Fields */
.ks-login__fields {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.ks-login__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ks-login__label {
  font: 600 0.75rem / 1 var(--font-sans, sans-serif);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-secondary, #6b7280);
}

.ks-login__input {
  width: 100%;
  padding: 11px 14px;
  background: var(--color-bg, #f5f5f2);
  border: 1.5px solid var(--color-border, #e5e5e0);
  border-radius: 6px;
  font: 400 0.9375rem / 1.4 var(--font-sans, sans-serif);
  color: var(--color-text, #1a1a1a);
  outline: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
  -webkit-appearance: none;
}

.ks-login__input::placeholder {
  color: var(--color-secondary, #9ca3af);
  font-weight: 400;
}

.ks-login__input:focus {
  border-color: var(--color-primary, #0d7377);
  box-shadow: 0 0 0 3px rgba(13, 115, 119, 0.12);
}

.ks-login__input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.ks-login__password-wrap {
  position: relative;
}

.ks-login__password-wrap .ks-login__input {
  padding-right: 48px;
}

.ks-login__password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 1rem;
  color: var(--color-secondary, #9ca3af);
  cursor: pointer;
  line-height: 1;
  padding: 4px;
  transition: color 0.15s ease;
}

.ks-login__password-toggle:hover {
  color: var(--color-text, #1a1a1a);
}

/* Error */
.ks-login__error {
  padding: 10px 14px;
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.2);
  border-radius: 6px;
  font: 500 0.8125rem / 1.4 var(--font-sans, sans-serif);
  color: #dc2626;
  margin: -8px 0;
}

/* Submit */
.ks-login__submit {
  width: 100%;
  padding: 13px 24px;
  background: var(--color-primary, #0d7377);
  border: none;
  border-radius: 6px;
  font: 600 0.9375rem / 1 var(--font-sans, sans-serif);
  letter-spacing: 0.02em;
  color: #fff;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    transform 0.1s ease,
    opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
}

.ks-login__submit:hover:not(:disabled) {
  background: var(--color-primary-dark, #0a5f63);
}

.ks-login__submit:active:not(:disabled) {
  transform: scale(0.99);
}

.ks-login__submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Spinner */
.ks-login__spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ks-spin 0.7s linear infinite;
}

@keyframes ks-spin {
  to {
    transform: rotate(360deg);
  }
}

/* Footer note */
.ks-login__footer-note {
  margin-top: 40px;
  font: 400 0.6875rem / 1 var(--font-sans, sans-serif);
  color: var(--color-secondary, #9ca3af);
  letter-spacing: 0.04em;
  text-align: center;
}

/* ─── Responsive ─────────────────────────────────────────── */
@media (max-width: 900px) {
  .ks-login__panel {
    display: none;
  }
  .ks-login__form-side {
    flex: none;
    width: 100%;
  }
}
</style>

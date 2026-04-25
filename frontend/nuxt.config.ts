// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

declare const process: { env: Record<string, string | undefined> };

export default defineNuxtConfig({
  compatibilityDate: "2025-05-15",

  // SPA mode — no SSR needed, avoids locale hydration mismatch
  ssr: false,

  future: {
    compatibilityVersion: 4,
  },

  devtools: { enabled: true },

  // ─── Modules ───────────────────────────────────────────────
  modules: ["@pinia/nuxt", "@nuxt/eslint", "@vueuse/motion/nuxt"],

  // ─── CSS ───────────────────────────────────────────────────
  css: [
    "@fontsource/playfair-display/400.css",
    "@fontsource/playfair-display/600.css",
    "@fontsource/playfair-display/700.css",
    "@fontsource/source-serif-pro/400.css",
    "@fontsource/source-serif-pro/600.css",
    "@fontsource-variable/inter",
    "@fontsource/jetbrains-mono/400.css",
    "@fontsource/jetbrains-mono/500.css",
    "katex/dist/katex.min.css",
    "~/assets/css/tokens.css",
    "~/assets/css/typography.css",
    "~/assets/css/editorial.css",
    "~/assets/css/motion.css",
  ],

  // ─── Tailwind v4 via Vite plugin ──────────────────────────
  vite: {
    plugins: [tailwindcss()],
  },

  // ─── Runtime Config ────────────────────────────────────────
  runtimeConfig: {
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
      apiKey: process.env.NUXT_PUBLIC_API_KEY || "sk-kaleidoscope",
    },
  },

  // ─── App Config ────────────────────────────────────────────
  app: {
    head: {
      title: "Kaleidoscope — Research Reimagined",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Literature dataset analysis and management platform for researchers.",
        },
      ],
      link: [
        {
          rel: "icon",
          type: "image/png",
          href: "/brand/kaleidoscope-icon-rounded.png",
        },
        { rel: "shortcut icon", href: "/brand/kaleidoscope-icon-rounded.png" },
        {
          rel: "apple-touch-icon",
          href: "/brand/kaleidoscope-icon-rounded.png",
        },
      ],
      htmlAttrs: { lang: "en" },
    },
    pageTransition: {
      name: "page-handoff",
    },
  },

  // ─── TypeScript ────────────────────────────────────────────
  typescript: {
    strict: true,
    typeCheck: false, // enable via `pnpm type-check`
  },
});

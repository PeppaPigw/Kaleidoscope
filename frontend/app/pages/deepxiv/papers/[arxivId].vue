<script setup lang="ts">
/**
 * DeepXiv Paper Reader — progressive paper reading with three-column layout.
 *
 * Left:   metadata card + section navigation
 * Center: content area (abstract, sections, preview, full text)
 * Right:  social impact, external links, import action
 */
import {
  Loader2,
  ExternalLink,
  Download,
  BookOpen,
  FileText,
} from "lucide-vue-next";
import type {
  DeepXivHeadResponse,
  DeepXivBriefResponse,
  DeepXivSocialImpact,
} from "~/composables/useDeepXiv";

definePageMeta({ layout: "default", title: "Paper Reader" });
useHead({ title: "Paper Reader -- DeepXiv" });

const route = useRoute();
const {
  getPaperHead,
  getPaperBrief,
  getPaperSection,
  getPaperPreview,
  getPaperRaw,
  getSocialImpact,
} = useDeepXiv();

const arxivId = computed(() => route.params.arxivId as string);

// ── Data state ──────────────────────────────────────────
const headData = ref<DeepXivHeadResponse | null>(null);
const briefData = ref<DeepXivBriefResponse | null>(null);
const socialImpact = ref<DeepXivSocialImpact | null>(null);
const sectionContent = ref<string | null>(null);
const activeSection = ref<string | null>(null);

// ── Loading state ───────────────────────────────────────
const headLoading = ref(true);
const briefLoading = ref(true);
const socialLoading = ref(false);
const sectionLoading = ref(false);
const contentLoading = ref(false);

// ── Content mode ────────────────────────────────────────
type ContentMode = "abstract" | "section" | "preview" | "raw";
const contentMode = ref<ContentMode>("abstract");
const contentText = ref<string | null>(null);

// ── Derived ─────────────────────────────────────────────
const paperTitle = computed(
  () => headData.value?.title ?? briefData.value?.title ?? "Loading...",
);

const paperAuthors = computed(() => {
  if (!headData.value?.authors) return [];
  return headData.value.authors.map((a) =>
    typeof a === "string" ? a : a.name,
  );
});

const paperSections = computed(() =>
  (headData.value?.sections ?? []).map((section) => ({
    ...section,
    tldr: section.tldr ?? "",
  })),
);

const paperAbstract = computed(() => headData.value?.abstract ?? "");

// ── Load data on mount ──────────────────────────────────
async function loadPaperData() {
  headLoading.value = true;
  briefLoading.value = true;

  const [headResult, briefResult] = await Promise.allSettled([
    getPaperHead(arxivId.value),
    getPaperBrief(arxivId.value),
  ]);

  if (headResult.status === "fulfilled") {
    headData.value = headResult.value;
  }
  headLoading.value = false;

  if (briefResult.status === "fulfilled") {
    briefData.value = briefResult.value;
  }
  briefLoading.value = false;

  // Load social impact lazily
  socialLoading.value = true;
  try {
    socialImpact.value = await getSocialImpact(arxivId.value);
  } catch {
    socialImpact.value = null;
  } finally {
    socialLoading.value = false;
  }
}

// ── Section loading ─────────────────────────────────────
async function handleSectionSelect(sectionName: string) {
  activeSection.value = sectionName;
  contentMode.value = "section";
  sectionLoading.value = true;
  sectionContent.value = null;

  try {
    const res = await getPaperSection(arxivId.value, sectionName);
    sectionContent.value = res.content;
  } catch {
    sectionContent.value = "Failed to load section.";
  } finally {
    sectionLoading.value = false;
  }
}

// ── Preview / Raw loading ───────────────────────────────
async function loadPreview() {
  contentMode.value = "preview";
  contentLoading.value = true;
  contentText.value = null;
  activeSection.value = null;

  try {
    const res = await getPaperPreview(arxivId.value);
    contentText.value = res.text;
  } catch {
    contentText.value = "Failed to load preview.";
  } finally {
    contentLoading.value = false;
  }
}

async function loadRaw() {
  contentMode.value = "raw";
  contentLoading.value = true;
  contentText.value = null;
  activeSection.value = null;

  try {
    const res = await getPaperRaw(arxivId.value);
    contentText.value = res.content;
  } catch {
    contentText.value = "Failed to load full text.";
  } finally {
    contentLoading.value = false;
  }
}

function showAbstract() {
  contentMode.value = "abstract";
  activeSection.value = null;
  sectionContent.value = null;
  contentText.value = null;
}

// ── Display content ─────────────────────────────────────
const displayContent = computed(() => {
  switch (contentMode.value) {
    case "abstract":
      return paperAbstract.value || "No abstract available.";
    case "section":
      return sectionContent.value;
    case "preview":
    case "raw":
      return contentText.value;
    default:
      return null;
  }
});

const contentLabel = computed(() => {
  switch (contentMode.value) {
    case "abstract":
      return "Abstract";
    case "section":
      return activeSection.value ?? "Section";
    case "preview":
      return "Preview";
    case "raw":
      return "Full Text";
    default:
      return "";
  }
});

const isContentLoading = computed(
  () => sectionLoading.value || contentLoading.value,
);

const shouldRenderPreviewMarkdown = computed(
  () =>
    contentMode.value === "preview" &&
    Boolean(displayContent.value) &&
    !isContentLoading.value,
);

// ── Lifecycle ───────────────────────────────────────────
onMounted(() => {
  void loadPaperData();
});

watch(arxivId, () => {
  headData.value = null;
  briefData.value = null;
  socialImpact.value = null;
  sectionContent.value = null;
  contentText.value = null;
  activeSection.value = null;
  contentMode.value = "abstract";
  void loadPaperData();
});
</script>

<template>
  <div class="ks-dxreader">
    <!-- Loading skeleton -->
    <div v-if="headLoading && briefLoading" class="ks-dxreader__loading-page">
      <Loader2 :size="28" class="ks-dxreader__spinner" />
      <span>Loading paper...</span>
    </div>

    <!-- Three-column layout -->
    <div v-else class="ks-dxreader__layout">
      <!-- LEFT: Metadata + Section nav -->
      <aside class="ks-dxreader__left">
        <!-- Paper metadata card -->
        <div class="ks-dxreader__meta-card">
          <h1 class="ks-dxreader__paper-title">{{ paperTitle }}</h1>

          <!-- Authors -->
          <div v-if="paperAuthors.length" class="ks-dxreader__authors">
            <span class="ks-dxreader__label">Authors</span>
            <div class="ks-dxreader__author-list">
              <span
                v-for="(author, i) in paperAuthors"
                :key="i"
                class="ks-dxreader__author"
                >{{ author }}</span
              >
            </div>
          </div>

          <!-- Keywords -->
          <div v-if="headData?.keywords?.length" class="ks-dxreader__field">
            <span class="ks-dxreader__label">Keywords</span>
            <div class="ks-dxreader__tags">
              <span
                v-for="kw in headData.keywords"
                :key="kw"
                class="ks-dxreader__tag"
                >{{ kw }}</span
              >
            </div>
          </div>

          <!-- Citations -->
          <div class="ks-dxreader__field">
            <span class="ks-dxreader__label">Citations</span>
            <span class="ks-dxreader__value">{{
              headData?.citations ?? briefData?.citations ?? 0
            }}</span>
          </div>

          <!-- Categories -->
          <div v-if="headData?.categories?.length" class="ks-dxreader__field">
            <span class="ks-dxreader__label">Categories</span>
            <div class="ks-dxreader__tags">
              <span
                v-for="cat in headData.categories"
                :key="cat"
                class="ks-dxreader__tag ks-dxreader__tag--cat"
                >{{ cat }}</span
              >
            </div>
          </div>

          <!-- GitHub link -->
          <a
            v-if="headData?.github_url"
            :href="headData.github_url"
            target="_blank"
            rel="noopener"
            class="ks-dxreader__ext-link"
          >
            GitHub Repository
            <ExternalLink :size="12" />
          </a>

          <!-- arXiv link -->
          <a
            :href="`https://arxiv.org/abs/${arxivId}`"
            target="_blank"
            rel="noopener"
            class="ks-dxreader__ext-link"
          >
            arXiv Page
            <ExternalLink :size="12" />
          </a>
        </div>

        <!-- Section navigation -->
        <div v-if="paperSections.length" class="ks-dxreader__sections">
          <span class="ks-dxreader__label">Sections</span>
          <DeepxivSectionNav
            :sections="paperSections"
            :active-section="activeSection"
            @select="handleSectionSelect"
          />
        </div>
      </aside>

      <!-- CENTER: Content area -->
      <main class="ks-dxreader__center">
        <!-- Content mode tabs -->
        <div class="ks-dxreader__content-tabs">
          <button
            :class="[
              'ks-dxreader__tab',
              contentMode === 'abstract' && 'ks-dxreader__tab--active',
            ]"
            @click="showAbstract"
          >
            <BookOpen :size="14" />
            Abstract
          </button>
          <button
            :class="[
              'ks-dxreader__tab',
              contentMode === 'preview' && 'ks-dxreader__tab--active',
            ]"
            @click="loadPreview"
          >
            <FileText :size="14" />
            Preview
          </button>
          <button
            :class="[
              'ks-dxreader__tab',
              contentMode === 'raw' && 'ks-dxreader__tab--active',
            ]"
            @click="loadRaw"
          >
            <Download :size="14" />
            Full Text
          </button>
        </div>

        <!-- Content label -->
        <div class="ks-dxreader__content-header">
          <span class="ks-dxreader__content-label">{{ contentLabel }}</span>
        </div>

        <!-- Content -->
        <div class="ks-dxreader__content">
          <div v-if="isContentLoading" class="ks-dxreader__content-loading">
            <Loader2 :size="20" class="ks-dxreader__spinner" />
            <span>Loading...</span>
          </div>
          <PaperDeepAnalysis
            v-else-if="shouldRenderPreviewMarkdown"
            :analysis="displayContent!"
            :show-header="false"
          />
          <div v-else-if="displayContent" class="ks-dxreader__content-text">
            {{ displayContent }}
          </div>
          <div v-else class="ks-dxreader__content-empty">
            No content available.
          </div>
        </div>
      </main>

      <!-- RIGHT: Social impact + Links + Actions -->
      <aside class="ks-dxreader__right">
        <!-- Social impact -->
        <div class="ks-dxreader__social-section">
          <span class="ks-dxreader__label">Social Impact</span>
          <div v-if="socialLoading" class="ks-dxreader__right-loading">
            <Loader2 :size="14" class="ks-dxreader__spinner" />
            <span>Loading...</span>
          </div>
          <DeepxivSocialImpactBadge
            v-else-if="socialImpact"
            :impact="socialImpact"
          />
          <p v-else class="ks-dxreader__right-muted">
            No social data available
          </p>
        </div>

        <!-- External links -->
        <div class="ks-dxreader__links-section">
          <span class="ks-dxreader__label">Links</span>
          <div class="ks-dxreader__link-list">
            <a
              :href="`https://arxiv.org/html/${arxivId}`"
              target="_blank"
              rel="noopener"
              class="ks-dxreader__link-item"
            >
              arXiv HTML
              <ExternalLink :size="12" />
            </a>
            <a
              v-if="headData?.src_url || briefData?.src_url"
              :href="headData?.src_url ?? briefData?.src_url ?? ''"
              target="_blank"
              rel="noopener"
              class="ks-dxreader__link-item"
            >
              PDF Source
              <ExternalLink :size="12" />
            </a>
          </div>
        </div>

        <!-- Import action -->
        <div class="ks-dxreader__action-section">
          <button class="ks-dxreader__import-btn">
            Import to Kaleidoscope
          </button>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.ks-dxreader {
  min-height: 100vh;
  padding: 24px;
}

/* ── Page loading ────────────────────────────────────── */
.ks-dxreader__loading-page {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 60vh;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-dxreader__spinner {
  animation: ks-dxr-spin 0.8s linear infinite;
}

@keyframes ks-dxr-spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Three-column layout ─────────────────────────────── */
.ks-dxreader__layout {
  display: grid;
  grid-template-columns: 260px 1fr 280px;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ── Shared ──────────────────────────────────────────── */
.ks-dxreader__label {
  display: block;
  font: 600 0.625rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-secondary);
  margin-bottom: 6px;
}

.ks-dxreader__value {
  font: 500 0.875rem / 1 var(--font-mono);
  color: var(--color-text);
}

/* ── LEFT panel ──────────────────────────────────────── */
.ks-dxreader__left {
  position: sticky;
  top: 80px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  max-height: calc(100vh - 120px);
}

.ks-dxreader__meta-card {
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ks-dxreader__paper-title {
  font: 700 1rem / 1.3 var(--font-display, serif);
  color: var(--color-text);
  margin: 0;
}

.ks-dxreader__authors {
  display: flex;
  flex-direction: column;
}

.ks-dxreader__author-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-dxreader__author {
  font: 400 0.75rem / 1.3 var(--font-sans);
  color: var(--color-primary);
}

.ks-dxreader__author + .ks-dxreader__author::before {
  content: ", ";
  color: var(--color-secondary);
}

.ks-dxreader__field {
  display: flex;
  flex-direction: column;
}

.ks-dxreader__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-dxreader__tag {
  padding: 2px 8px;
  font: 400 0.6875rem / 1.4 var(--font-sans);
  border-radius: 3px;
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
}

.ks-dxreader__tag--cat {
  background: color-mix(in srgb, var(--color-secondary) 12%, transparent);
  color: var(--color-secondary);
}

.ks-dxreader__ext-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-primary);
  text-decoration: none;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-dxreader__ext-link:hover {
  opacity: 0.7;
}

/* Section nav */
.ks-dxreader__sections {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

/* ── CENTER panel ────────────────────────────────────── */
.ks-dxreader__center {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.ks-dxreader__content-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
}

.ks-dxreader__tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: none;
  border-radius: 4px;
  font: 500 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
  cursor: pointer;
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth),
    background var(--duration-fast) var(--ease-smooth);
}

.ks-dxreader__tab:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-dxreader__tab--active {
  border-color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}

.ks-dxreader__content-header {
  margin-bottom: 12px;
}

.ks-dxreader__content-label {
  font: 600 0.75rem / 1 var(--font-mono);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
}

.ks-dxreader__content {
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  min-height: 400px;
}

.ks-dxreader__content-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 40px 0;
  justify-content: center;
  font: 400 0.875rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-dxreader__content-text {
  font: 400 0.9375rem / 1.8 var(--font-sans);
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}

.ks-dxreader__content-empty {
  padding: 40px 0;
  text-align: center;
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
}

/* ── RIGHT panel ─────────────────────────────────────── */
.ks-dxreader__right {
  position: sticky;
  top: 80px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ks-dxreader__social-section,
.ks-dxreader__links-section,
.ks-dxreader__action-section {
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.ks-dxreader__right-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font: 400 0.75rem / 1 var(--font-sans);
  color: var(--color-secondary);
}

.ks-dxreader__right-muted {
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 4px 0 0;
}

/* Links */
.ks-dxreader__link-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-dxreader__link-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  text-decoration: none;
  transition:
    border-color var(--duration-fast) var(--ease-smooth),
    color var(--duration-fast) var(--ease-smooth);
}

.ks-dxreader__link-item:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Import button */
.ks-dxreader__import-btn {
  width: 100%;
  padding: 12px 16px;
  background: var(--color-primary);
  color: var(--color-bg);
  border: none;
  border-radius: 6px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity var(--duration-fast) var(--ease-smooth);
}

.ks-dxreader__import-btn:hover {
  opacity: 0.85;
}

/* ── Responsive ──────────────────────────────────────── */
@media (max-width: 1024px) {
  .ks-dxreader__layout {
    grid-template-columns: 1fr;
  }

  .ks-dxreader__left,
  .ks-dxreader__right {
    position: static;
    max-height: none;
  }
}
</style>

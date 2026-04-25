<script setup lang="ts">
/**
 * InterestsModal — onboarding modal to set user research interests.
 * Shown automatically on first visit (preferences.interests_set !== true).
 * Also accessible from the profile menu.
 */
import { X, Check } from "lucide-vue-next";

const emit = defineEmits<{ close: [] }>();

const { preferences, savePreferences, loadPreferences } = useUserPreferences();

const ARXIV_CATEGORIES = [
  { id: "cs.AI", label: "AI" },
  { id: "cs.CL", label: "NLP" },
  { id: "cs.CV", label: "Computer Vision" },
  { id: "cs.LG", label: "Machine Learning" },
  { id: "cs.NE", label: "Neural & Evolutionary" },
  { id: "cs.RO", label: "Robotics" },
  { id: "cs.IR", label: "Information Retrieval" },
  { id: "cs.CR", label: "Cryptography" },
  { id: "cs.SE", label: "Software Engineering" },
  { id: "cs.DC", label: "Distributed Computing" },
  { id: "stat.ML", label: "Statistics / ML" },
  { id: "math.ST", label: "Math Statistics" },
  { id: "eess.IV", label: "Image & Video" },
  { id: "eess.SP", label: "Signal Processing" },
  { id: "q-bio.BM", label: "Biomolecules" },
  { id: "q-bio.NC", label: "Neurons & Cognition" },
  { id: "physics.data-an", label: "Data Analysis" },
  { id: "astro-ph", label: "Astrophysics" },
  { id: "cond-mat", label: "Condensed Matter" },
  { id: "quant-ph", label: "Quantum Physics" },
];

const step = ref(1);
const selectedCategories = ref<string[]>([
  ...preferences.value.subscribed_categories,
]);
const keywordInput = ref("");
const keywords = ref<string[]>([...preferences.value.keywords]);
const saving = ref(false);
const saveError = ref("");

onMounted(async () => {
  try {
    await loadPreferences();
    selectedCategories.value = [...preferences.value.subscribed_categories];
    keywords.value = [...preferences.value.keywords];
  } catch {
    // Leave empty defaults; onboarding can still continue offline-ish.
  }
});

function toggleCategory(id: string) {
  const idx = selectedCategories.value.indexOf(id);
  if (idx >= 0) {
    selectedCategories.value.splice(idx, 1);
  } else {
    selectedCategories.value.push(id);
  }
}

function addKeyword() {
  const kw = keywordInput.value.trim();
  if (kw && !keywords.value.includes(kw)) {
    keywords.value.push(kw);
  }
  keywordInput.value = "";
}

function handleKeywordKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" && event.key !== ",") return;
  event.preventDefault();
  addKeyword();
}

function removeKeyword(kw: string) {
  keywords.value = keywords.value.filter((k) => k !== kw);
}

async function handleFinish() {
  saving.value = true;
  saveError.value = "";
  try {
    await savePreferences({
      subscribed_categories: selectedCategories.value,
      keywords: keywords.value,
      interests_set: true,
    });
    emit("close");
  } catch {
    saveError.value = "Could not save your interests right now.";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="ks-interests-overlay" @click.self="emit('close')">
      <div
        class="ks-interests-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Set your research interests"
      >
        <!-- Header -->
        <div class="ks-interests-header">
          <div class="ks-interests-header-text">
            <h2 class="ks-interests-title">
              {{ step === 1 ? "What do you research?" : "Track keywords" }}
            </h2>
            <p class="ks-interests-subtitle">
              {{
                step === 1
                  ? "Choose your arXiv categories to personalize your dashboard."
                  : "Add keywords to surface relevant papers."
              }}
            </p>
          </div>
          <button
            class="ks-interests-close"
            :aria-label="'Close'"
            @click="emit('close')"
          >
            <X :size="18" :stroke-width="2" />
          </button>
        </div>

        <!-- Step indicator -->
        <div class="ks-interests-steps" aria-hidden="true">
          <div
            :class="[
              'ks-interests-step',
              { 'ks-interests-step--active': step >= 1 },
            ]"
          />
          <div
            :class="[
              'ks-interests-step',
              { 'ks-interests-step--active': step >= 2 },
            ]"
          />
        </div>

        <!-- Step 1: Categories -->
        <div v-if="step === 1" class="ks-interests-body">
          <div class="ks-interests-chips">
            <button
              v-for="cat in ARXIV_CATEGORIES"
              :key="cat.id"
              type="button"
              :class="[
                'ks-chip',
                { 'ks-chip--active': selectedCategories.includes(cat.id) },
              ]"
              @click="toggleCategory(cat.id)"
            >
              <Check
                v-if="selectedCategories.includes(cat.id)"
                :size="12"
                :stroke-width="2.5"
              />
              {{ cat.label }}
              <span class="ks-chip-id">{{ cat.id }}</span>
            </button>
          </div>
        </div>

        <!-- Step 2: Keywords -->
        <div v-else class="ks-interests-body">
          <div class="ks-interests-tag-input">
            <input
              v-model="keywordInput"
              type="text"
              class="ks-interests-input"
              placeholder="e.g. diffusion models, RAG, LLM safety…"
              @keydown="handleKeywordKeydown"
            />
            <button
              type="button"
              class="ks-interests-add-btn"
              :disabled="!keywordInput.trim()"
              @click="addKeyword"
            >
              Add
            </button>
          </div>
          <div v-if="keywords.length > 0" class="ks-interests-tags">
            <span v-for="kw in keywords" :key="kw" class="ks-tag">
              {{ kw }}
              <button
                type="button"
                class="ks-tag-remove"
                :aria-label="`Remove ${kw}`"
                @click="removeKeyword(kw)"
              >
                ×
              </button>
            </span>
          </div>
          <p v-else class="ks-interests-hint">
            Press Enter or comma to add keywords. Leave empty to skip.
          </p>
        </div>

        <!-- Footer actions -->
        <div class="ks-interests-footer">
          <p v-if="saveError" class="ks-interests-error">{{ saveError }}</p>
          <button
            v-if="step === 2"
            type="button"
            class="ks-btn-ghost"
            @click="step = 1"
          >
            Back
          </button>
          <div class="ks-interests-footer-right">
            <button
              v-if="step === 1"
              type="button"
              class="ks-btn-ghost"
              @click="emit('close')"
            >
              Skip
            </button>
            <button
              v-if="step === 1"
              type="button"
              class="ks-btn-primary"
              @click="step = 2"
            >
              Next →
            </button>
            <button
              v-else
              type="button"
              class="ks-btn-primary"
              :disabled="saving"
              @click="handleFinish"
            >
              <span v-if="!saving">Save & finish</span>
              <span v-else>Saving…</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.ks-interests-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(10, 10, 10, 0.5);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.ks-interests-modal {
  width: min(100%, 560px);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ks-interests-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 24px 0;
}

.ks-interests-title {
  font: 700 1.25rem / 1.2 var(--font-display);
  color: var(--color-text);
  margin: 0 0 4px;
}

.ks-interests-subtitle {
  font: 400 0.875rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

.ks-interests-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--color-secondary);
  cursor: pointer;
  transition: background-color 0.15s;
}

.ks-interests-close:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.ks-interests-steps {
  display: flex;
  gap: 6px;
  padding: 16px 24px 0;
}

.ks-interests-step {
  flex: 1;
  height: 3px;
  border-radius: 2px;
  background: var(--color-border);
  transition: background-color 0.2s;
}

.ks-interests-step--active {
  background: var(--color-primary);
}

.ks-interests-body {
  padding: 20px 24px;
  flex: 1;
  overflow-y: auto;
  max-height: 360px;
}

.ks-interests-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ks-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 20px;
  background: var(--color-bg);
  font: 500 0.8125rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color 0.15s,
    background-color 0.15s,
    color 0.15s;
}

.ks-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-chip--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.ks-chip-id {
  font: 400 0.625rem / 1 var(--font-mono);
  opacity: 0.6;
  margin-left: 2px;
}

/* Tag input */
.ks-interests-tag-input {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.ks-interests-input {
  flex: 1;
  padding: 9px 12px;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  font: 400 0.9rem / 1.4 var(--font-sans);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.15s;
}

.ks-interests-input:focus {
  border-color: var(--color-primary);
}

.ks-interests-add-btn {
  padding: 9px 18px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font: 600 0.8125rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
}

.ks-interests-add-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ks-interests-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.ks-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 4px;
  font: 500 0.8125rem / 1 var(--font-sans);
}

.ks-tag-remove {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.15s;
}

.ks-tag-remove:hover {
  opacity: 1;
}

.ks-interests-hint {
  font: 400 0.8125rem / 1.4 var(--font-sans);
  color: var(--color-secondary);
  margin: 0;
}

/* Footer */
.ks-interests-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  gap: 12px;
}

.ks-interests-error {
  margin: 0;
  color: var(--color-danger, #c23b22);
  font: 500 0.8125rem / 1.4 var(--font-sans);
}

.ks-interests-footer-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.ks-btn-ghost {
  padding: 9px 18px;
  background: none;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  font: 500 0.875rem / 1 var(--font-sans);
  color: var(--color-text);
  cursor: pointer;
  transition:
    background-color 0.15s,
    border-color 0.15s;
}

.ks-btn-ghost:hover {
  background: var(--color-bg);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.ks-btn-primary {
  padding: 9px 20px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font: 600 0.875rem / 1 var(--font-sans);
  cursor: pointer;
  transition: opacity 0.15s;
}

.ks-btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>

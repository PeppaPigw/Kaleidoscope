<script setup lang="ts">
/**
 * CaptureCorner — Quick-capture textarea for fleeting research ideas.
 *
 * Provides a minimal text input for capturing questions, hypotheses, or
 * notes before they evaporate. Actions to save to Notes or a Workspace.
 */

const captureText = ref("");
const uid = useId();

const emit = defineEmits<{
  "save-note": [text: string];
  "save-workspace": [text: string];
}>();

function handleSaveNote() {
  if (!captureText.value.trim()) return;
  emit("save-note", captureText.value.trim());
  captureText.value = "";
}

function handleSaveWorkspace() {
  if (!captureText.value.trim()) return;
  emit("save-workspace", captureText.value.trim());
  captureText.value = "";
}
</script>

<template>
  <section
    class="ks-capture-corner ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-5"
    :aria-labelledby="`${uid}-title`"
  >
    <h3 :id="`${uid}-title`" class="ks-type-section-title">Capture</h3>
    <textarea
      v-model="captureText"
      class="ks-capture-corner__input"
      placeholder="Capture a question before it evaporates…"
      rows="4"
      aria-label="Quick research note"
    />
    <div class="ks-capture-corner__actions">
      <KsButton
        variant="primary"
        size="sm"
        :disabled="!captureText.trim()"
        @click="handleSaveNote"
      >
        Save to Notes
      </KsButton>
      <KsButton
        variant="secondary"
        size="sm"
        :disabled="!captureText.trim()"
        @click="handleSaveWorkspace"
      >
        Save to Workspace
      </KsButton>
    </div>
  </section>
</template>

<style scoped>
.ks-capture-corner {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ks-capture-corner__input {
  width: 100%;
  padding: 12px;
  background: rgba(250, 250, 247, 0.72);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font: 400 1rem / 1.5 var(--font-serif);
  color: var(--color-text);
  resize: vertical;
  transition: border-color var(--duration-fast) var(--ease-smooth);
}

.ks-capture-corner__input:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
  border-color: var(--color-primary);
}

.ks-capture-corner__input::placeholder {
  color: rgba(107, 107, 107, 0.8);
}

.ks-capture-corner__actions {
  display: flex;
  gap: 8px;
}
</style>

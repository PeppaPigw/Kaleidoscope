<script setup lang="ts">
import type { AdminProbeCard } from "~/composables/useAdminConsole";

const props = defineProps<{
  probes: AdminProbeCard[];
  pending?: boolean;
  lastLoadedAt?: string | null;
}>();

function statusLabel(status: AdminProbeCard["status"]) {
  switch (status) {
    case "ok":
      return "Healthy";
    case "warning":
      return "Degraded";
    case "error":
      return "Broken";
    default:
      return "Pending";
  }
}

function tagVariant(status: AdminProbeCard["status"]) {
  switch (status) {
    case "ok":
      return "success";
    case "warning":
      return "accent";
    case "error":
      return "danger";
    default:
      return "neutral";
  }
}

function formatLoadedAt(timestamp?: string | null) {
  if (!timestamp) {
    return "Not refreshed yet";
  }

  return new Date(timestamp).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
</script>

<template>
  <section class="admin-health">
    <div class="admin-health__head">
      <div>
        <p class="ks-type-eyebrow">Live Probes</p>
        <h2 class="ks-type-section-title admin-health__title">System Health</h2>
      </div>
      <p class="ks-type-data admin-health__meta">
        {{
          pending
            ? "Refreshing…"
            : `Last refresh ${formatLoadedAt(props.lastLoadedAt)}`
        }}
      </p>
    </div>

    <div class="admin-health__grid">
      <KsCard
        v-for="probe in props.probes"
        :key="probe.id"
        variant="teal-top"
        class="admin-health__card"
        :class="`admin-health__card--${probe.status}`"
      >
        <div class="admin-health__card-top">
          <p class="ks-type-label">{{ probe.title }}</p>
          <KsTag :variant="tagVariant(probe.status)">
            {{ statusLabel(probe.status) }}
          </KsTag>
        </div>
        <div class="admin-health__value">{{ probe.value }}</div>
        <p class="ks-type-body-sm admin-health__detail">{{ probe.detail }}</p>
        <p v-if="probe.note" class="ks-type-data admin-health__note">
          {{ probe.note }}
        </p>
      </KsCard>
    </div>
  </section>
</template>

<style scoped>
.admin-health {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.admin-health__head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 16px;
}

.admin-health__title {
  margin-top: 6px;
}

.admin-health__meta {
  color: var(--color-secondary);
}

.admin-health__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.admin-health__card {
  min-height: 180px;
}

.admin-health__card--warning {
  border-top-color: var(--color-accent-decorative);
}

.admin-health__card--error {
  border-top-color: #b54a4a;
}

.admin-health__card-top {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
}

.admin-health__value {
  margin-top: 18px;
  font: 600 clamp(1.5rem, 2.6vw, 2.15rem) / 1 var(--font-display);
  color: var(--color-text);
}

.admin-health__detail {
  margin-top: 14px;
  color: var(--color-text);
}

.admin-health__note {
  margin-top: 10px;
  color: var(--color-secondary);
}

@media (max-width: 1080px) {
  .admin-health__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .admin-health__head {
    flex-direction: column;
    align-items: start;
  }

  .admin-health__grid {
    grid-template-columns: 1fr;
  }
}
</style>

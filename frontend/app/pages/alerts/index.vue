<script setup lang="ts">
import type { Alert, AlertRule } from "~/composables/useApi";

definePageMeta({ layout: "default" });

const { getAlerts, markAlertRead, getAlertRules, createAlertRule } = useApi();
const alerts = ref<Alert[]>([]);
const rules = ref<AlertRule[]>([]);
const isLoading = ref(true);
const isSaving = ref(false);
const form = reactive({ name: "", keywords: "" });

useHead({
  title: "Alerts — Kaleidoscope",
  meta: [
    {
      name: "description",
      content: "Manage alert notifications and keyword rules.",
    },
  ],
});

async function loadPage() {
  isLoading.value = true;
  try {
    const [alertsResp, rulesResp] = await Promise.all([
      getAlerts(true),
      getAlertRules(),
    ]);
    alerts.value = alertsResp.alerts;
    rules.value = rulesResp.rules;
  } finally {
    isLoading.value = false;
  }
}

async function handleMarkRead(alertId: string) {
  await markAlertRead(alertId);
  alerts.value = alerts.value.filter((alert) => alert.id !== alertId);
}

async function handleCreateRule() {
  const keywords = form.keywords
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!form.name.trim() || !keywords.length) return;
  isSaving.value = true;
  try {
    const rule = await createAlertRule({ name: form.name.trim(), keywords });
    rules.value = [rule, ...rules.value];
    form.name = "";
    form.keywords = "";
  } finally {
    isSaving.value = false;
  }
}

onMounted(loadPage);
</script>

<template>
  <div>
    <KsPageHeader
      title="Alerts"
      subtitle="Unread notifications and keyword rules"
    />
    <div
      style="
        max-width: 1040px;
        margin: 0 auto;
        padding: 0 24px 80px;
        display: grid;
        gap: 24px;
      "
    >
      <KsSkeleton v-if="isLoading" variant="paragraph" :lines="6" />

      <template v-else>
        <section
          class="ks-card"
          style="padding: 24px; display: grid; gap: 16px"
        >
          <span class="ks-type-eyebrow">Unread Alerts</span>
          <KsEmptyState
            v-if="!alerts.length"
            title="Inbox clear"
            description="Unread alerts will show up here as new papers and matches arrive."
          />
          <template v-else>
            <div
              v-for="alert in alerts"
              :key="alert.id"
              style="display: grid; gap: 8px"
            >
              <strong>{{ alert.title || alert.message }}</strong>
              <span>{{ alert.message }}</span>
              <div style="display: flex; gap: 12px; align-items: center">
                <span class="ks-type-data">{{
                  new Date(alert.created_at).toLocaleString()
                }}</span>
                <button
                  type="button"
                  style="cursor: pointer"
                  @click="handleMarkRead(alert.id)"
                >
                  Mark read
                </button>
              </div>
            </div>
          </template>
        </section>

        <section
          class="ks-card"
          style="padding: 24px; display: grid; gap: 16px"
        >
          <span class="ks-type-eyebrow">Alert Rules</span>
          <KsEmptyState
            v-if="!rules.length"
            title="No rules yet"
            description="Create a keyword rule to get notified when matching papers land."
          />
          <template v-else>
            <div
              v-for="rule in rules"
              :key="rule.id"
              style="display: grid; gap: 4px"
            >
              <strong>{{ rule.name }}</strong>
              <span>{{ rule.condition }}</span>
              <span class="ks-type-data">{{
                rule.is_active ? "Active" : "Paused"
              }}</span>
            </div>
          </template>
        </section>

        <section
          class="ks-card"
          style="padding: 24px; display: grid; gap: 16px"
        >
          <span class="ks-type-eyebrow">New Keyword Rule</span>
          <label style="display: grid; gap: 8px">
            <span>Name</span>
            <input
              v-model="form.name"
              type="text"
              placeholder="Transformer monitoring"
            >
          </label>
          <label style="display: grid; gap: 8px">
            <span>Keywords</span>
            <input
              v-model="form.keywords"
              type="text"
              placeholder="transformer, retrieval, benchmark"
            >
          </label>
          <button
            type="button"
            :disabled="isSaving"
            style="cursor: pointer; width: fit-content"
            @click="handleCreateRule"
          >
            {{ isSaving ? "Saving…" : "Create rule" }}
          </button>
        </section>
      </template>
    </div>
  </div>
</template>

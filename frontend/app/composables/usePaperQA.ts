import { withKaleidoscopeApiKeyHeaders } from "../utils/apiKey";

/**
 * usePaperQA — reactive Paper QA composable.
 *
 * Manages embedding status, prepare pipeline, conversational QA history,
 * staged loading feedback, and auto-polling while the paper index is being built.
 */

export type EmbeddingStatus =
  | "not_started"
  | "pending"
  | "running"
  | "completed"
  | "failed";

export interface QASource {
  section_title: string;
  normalized_section: string;
  text_snippet: string;
  score?: number | null;
}

export const PAPER_QA_LOADING_STAGES = [
  { key: "embedding", label: "正在进行embedding" },
  { key: "retrieval", label: "检索chunks" },
  { key: "rerank", label: "ReRank重新排序" },
  { key: "answer", label: "生成答案中" },
] as const;

export type QALoadingStageKey = (typeof PAPER_QA_LOADING_STAGES)[number]["key"];

export interface QAHistoryItem {
  id: string;
  question: string;
  answer: string | null;
  streamingAnswer: string;
  sources: QASource[];
  loading: boolean;
  loadingStage: QALoadingStageKey;
  error: string | null;
  timestamp: number;
}

export function usePaperQA(paperId: Ref<string>) {
  const { apiFetch } = useApi();
  const config = useRuntimeConfig();
  const streamBaseUrl = `${config.public.apiUrl}/api/v1`;

  const status = ref<EmbeddingStatus>("not_started");
  const chunkCount = ref(0);
  const errorMessage = ref<string | null>(null);
  const history = ref<QAHistoryItem[]>([]);
  const preparing = ref(false);
  const asking = computed(() => history.value.some((item) => item.loading));

  const stageTimers = new Map<string, ReturnType<typeof setTimeout>[]>();
  let requestCounter = 0;

  function updateHistoryItem(
    itemId: string,
    updater: (item: QAHistoryItem) => void,
  ) {
    const item = history.value.find((entry) => entry.id === itemId);
    if (!item) return;
    updater(item);
  }

  function clearStageTimers(itemId: string) {
    const timers = stageTimers.get(itemId) ?? [];
    for (const timer of timers) {
      clearTimeout(timer);
    }
    stageTimers.delete(itemId);
  }

  function scheduleLoadingStages(itemId: string) {
    clearStageTimers(itemId);
    const schedule: Array<[number, QALoadingStageKey]> = [
      [350, "retrieval"],
      [900, "rerank"],
      [1700, "answer"],
    ];
    const timers = schedule.map(([delay, stage]) =>
      setTimeout(() => {
        updateHistoryItem(itemId, (item) => {
          if (!item.loading) return;
          item.loadingStage = stage;
        });
      }, delay),
    );
    stageTimers.set(itemId, timers);
  }

  function buildConversationHistory() {
    return history.value
      .filter((item) => item.answer && !item.loading && !item.error)
      .slice(-6)
      .map((item) => ({
        question: item.question,
        answer: item.answer as string,
      }));
  }

  function normalizeSources(
    sources: QASource[] | null | undefined,
  ): QASource[] {
    return (sources ?? []).map((source) => ({ ...source }));
  }

  async function checkStatus() {
    if (!paperId.value) return;
    try {
      const data = await apiFetch<{
        status: EmbeddingStatus;
        chunk_count: number;
        error_message?: string | null;
      }>(`/paper-qa/${paperId.value}/status`);
      status.value = data.status;
      chunkCount.value = data.chunk_count ?? 0;
      errorMessage.value = data.error_message ?? null;
    } catch {
      // Network error — don't crash the panel
    }
  }

  async function prepare() {
    if (!paperId.value) return;
    preparing.value = true;
    try {
      const data = await apiFetch<{ status: string; chunk_count?: number }>(
        `/paper-qa/${paperId.value}/prepare`,
        { method: "POST" },
      );
      status.value =
        data.status === "already_complete" ? "completed" : "pending";
      if (data.chunk_count) chunkCount.value = data.chunk_count;
    } catch (e) {
      errorMessage.value =
        e instanceof Error ? e.message : "Failed to prepare paper index";
    } finally {
      preparing.value = false;
    }
  }

  async function ask(question: string, contextSnippet?: string) {
    if (!paperId.value || !question.trim()) return;

    const trimmedQuestion = question.trim();
    const priorTurns = buildConversationHistory();
    const itemId = `qa-${Date.now()}-${requestCounter++}`;

    history.value.push({
      id: itemId,
      question: trimmedQuestion,
      answer: null,
      streamingAnswer: "",
      sources: [],
      loading: true,
      loadingStage: "embedding",
      error: null,
      timestamp: Date.now(),
    });
    scheduleLoadingStages(itemId);

    try {
      const token = import.meta.client
        ? localStorage.getItem("ks_access_token")
        : null;
      const headers: Record<string, string> = withKaleidoscopeApiKeyHeaders({
        "Content-Type": "application/json",
      });
      if (token && token !== "single-user-mode") {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const body: Record<string, unknown> = {
        question: trimmedQuestion,
        history: priorTurns,
      };
      if (contextSnippet?.trim()) body.context_snippet = contextSnippet.trim();

      const resp = await fetch(
        `${streamBaseUrl}/paper-qa/${paperId.value}/ask/stream`,
        {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        },
      );

      if (!resp.ok || !resp.body) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulatedAnswer = "";
      let finalSources: QASource[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw || raw === "[DONE]") continue;
          try {
            const event = JSON.parse(raw) as {
              type: string;
              content?: string;
              sources?: QASource[];
              message?: string;
            };
            if (event.type === "chunk" && event.content) {
              accumulatedAnswer += event.content;
              updateHistoryItem(itemId, (item) => {
                item.streamingAnswer = accumulatedAnswer;
                item.loadingStage = "answer";
              });
            } else if (event.type === "sources" && event.sources) {
              finalSources = normalizeSources(event.sources);
            } else if (event.type === "error") {
              throw new Error(event.message ?? "Stream error");
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }

      updateHistoryItem(itemId, (item) => {
        item.answer = accumulatedAnswer;
        item.sources = finalSources;
        item.loading = false;
        item.loadingStage = "answer";
      });
    } catch (e) {
      updateHistoryItem(itemId, (item) => {
        item.error = e instanceof Error ? e.message : "Failed to get answer";
        item.loading = false;
        item.loadingStage = "answer";
      });
    } finally {
      clearStageTimers(itemId);
    }
  }

  function newChat() {
    for (const item of history.value) {
      clearStageTimers(item.id);
    }
    history.value = [];
  }

  // ── Auto-lifecycle ────────────────────────────────────────────────────────

  watch(
    paperId,
    async (id) => {
      if (!id) return;
      newChat();
      status.value = "not_started";
      errorMessage.value = null;
      await checkStatus();
      if (status.value === "not_started" || status.value === "failed") {
        await prepare();
      }
    },
    { immediate: true },
  );

  let pollTimer: ReturnType<typeof setInterval> | null = null;

  watch(status, (s) => {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    if (s === "pending" || s === "running") {
      pollTimer = setInterval(checkStatus, 3000);
    }
  });

  onUnmounted(() => {
    if (pollTimer) clearInterval(pollTimer);
    for (const item of history.value) {
      clearStageTimers(item.id);
    }
  });

  return {
    status,
    chunkCount,
    errorMessage,
    history,
    preparing,
    asking,
    ask,
    prepare,
    checkStatus,
    newChat,
  };
}

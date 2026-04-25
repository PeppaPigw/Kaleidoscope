/**
 * useAlertStream — Subscribe to real-time alert event stream.
 */

export interface StreamAlert {
  id: string;
  type: string;
  title: string;
  message: string;
  created_at: string;
}

type StreamPayload = {
  type?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
};

function isAlertPayload(payload: StreamPayload): boolean {
  return (payload.type ?? "").startsWith("alert.");
}

function normalizeStreamAlert(payload: StreamPayload): StreamAlert | null {
  if (!payload.type || payload.type === "connected") return null;
  const data = payload.data ?? {};
  return {
    id: String(
      data.alert_id ??
        data.id ??
        data.paper_id ??
        `${payload.type}-${Date.now()}`,
    ),
    type: String(data.alert_type ?? payload.type ?? "NEW"),
    title: String(data.title ?? data.message ?? "New activity"),
    message: String(data.message ?? data.body ?? data.title ?? ""),
    created_at: String(
      data.created_at ?? payload.timestamp ?? new Date().toISOString(),
    ),
  };
}

export function useAlertStream() {
  const lastAlert = ref<StreamAlert | null>(null);
  const isConnected = ref(false);
  const unreadCount = ref(0);
  let eventSource: EventSource | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  function connect() {
    if (!import.meta.client || eventSource) return;
    const apiUrl = (useRuntimeConfig().public.apiUrl as string) || "";
    eventSource = new EventSource(`${apiUrl}/api/v1/sse`);
    eventSource.onopen = () => {
      isConnected.value = true;
    };
    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as StreamPayload;
        const alert = normalizeStreamAlert(payload);
        if (!alert) return;
        lastAlert.value = alert;
        if (isAlertPayload(payload)) unreadCount.value += 1;
      } catch {
        // Ignore malformed alert data
      }
    };
    eventSource.onerror = () => {
      isConnected.value = false;
      eventSource?.close();
      eventSource = null;
      reconnectTimer = setTimeout(connect, 5000);
    };
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer);
    eventSource?.close();
    eventSource = null;
    isConnected.value = false;
  }

  function clearUnread() {
    unreadCount.value = 0;
  }

  onMounted(connect);
  onUnmounted(disconnect);

  return {
    lastAlert,
    isConnected,
    unreadCount,
    connect,
    disconnect,
    clearUnread,
  };
}

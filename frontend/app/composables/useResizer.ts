/**
 * useResizer — draggable split between main content and a sidebar.
 *
 * Uses the Pointer Events API for smooth drag on mouse, touch, and pen.
 * Persists sidebar width to localStorage.
 *
 * @example
 * const { sidebarWidth, isResizing, resizerProps } = useResizer({
 *   storageKey: 'ks-reader-sidebar-width',
 *   defaultWidth: 340,
 *   minSidebarWidth: 280,
 *   minMainWidth: 400,
 * })
 */
export interface UseResizerOptions {
  storageKey: string;
  defaultWidth: number;
  minSidebarWidth: number;
  minMainWidth: number;
  containerSelector?: string;
}

export function useResizer(options: UseResizerOptions) {
  const {
    storageKey,
    defaultWidth,
    minSidebarWidth,
    minMainWidth,
    containerSelector = ".ks-reader__layout",
  } = options;

  const sidebarWidth = ref(defaultWidth);
  const isResizing = ref(false);

  onMounted(() => {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const parsed = Number(stored);
      if (!Number.isNaN(parsed) && parsed >= minSidebarWidth) {
        sidebarWidth.value = parsed;
      }
    }
  });

  function onPointerDown(e: PointerEvent) {
    if (e.button !== 0) return; // left click only
    e.preventDefault();

    isResizing.value = true;
    const startX = e.clientX;
    const startWidth = sidebarWidth.value;
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);

    function onPointerMove(ev: PointerEvent) {
      const delta = startX - ev.clientX; // drag left → wider sidebar
      const container = document.querySelector(containerSelector);
      const containerWidth = container?.clientWidth ?? window.innerWidth;
      const newWidth = Math.min(
        Math.max(startWidth + delta, minSidebarWidth),
        containerWidth - minMainWidth,
      );
      sidebarWidth.value = newWidth;
    }

    function onPointerUp() {
      isResizing.value = false;
      localStorage.setItem(storageKey, String(Math.round(sidebarWidth.value)));
      document.removeEventListener("pointermove", onPointerMove);
      document.removeEventListener("pointerup", onPointerUp);
    }

    document.addEventListener("pointermove", onPointerMove);
    document.addEventListener("pointerup", onPointerUp);
  }

  const resizerProps = computed(() => ({
    onPointerdown: onPointerDown,
    class: isResizing.value
      ? "ks-reader__resizer ks-reader__resizer--active"
      : "ks-reader__resizer",
    role: "separator" as const,
    "aria-orientation": "vertical" as const,
    "aria-label": "Resize panel",
    tabindex: 0 as const,
  }));

  return { sidebarWidth, isResizing, resizerProps };
}

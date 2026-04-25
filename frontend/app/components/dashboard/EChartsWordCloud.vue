<script setup lang="ts">
/**
 * Dashboard keyword cloud with deterministic multi-direction layout.
 * It places words with collision detection so they spread across the panel
 * instead of collapsing into list rows.
 */

interface WordCloudWord {
  text: string;
  weight: number;
}

interface StyledWord extends WordCloudWord {
  color: string;
  fontSize: number;
  opacity: number;
  renderScale: number;
}

interface Bounds {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

interface PlacedWord extends StyledWord {
  x: number;
  y: number;
  rotation: number;
  width: number;
  height: number;
  zIndex: number;
}

const props = defineProps<{
  words: WordCloudWord[];
}>();

const emit = defineEmits<{
  click: [word: string];
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const containerWidth = ref(0);
const containerHeight = ref(0);
const placedWords = ref<PlacedWord[]>([]);

const MIN_SIZE = 32;
const MAX_SIZE = 180;
const MIN_LAYOUT_SIZE = 10;
const WORD_LIMIT = 120;
const PANEL_PADDING = -2;
const COLLISION_PADDING = -1;
const SCALE_STEPS = [
  2, 1.82, 1.66, 1.52, 1.38, 1.26, 1.14, 1.04, 0.96, 0.88, 0.8, 0.72, 0.64,
  0.56, 0.48, 0.42, 0.36, 0.3,
] as const;
const ROTATIONS = [0, -18, 18, 90, -28, 28, 0, -12, 12, -36, 36, 90] as const;
const ANCHORS = [
  { x: 0.5, y: 0.5 },
  { x: 0.32, y: 0.28 },
  { x: 0.68, y: 0.28 },
  { x: 0.3, y: 0.72 },
  { x: 0.7, y: 0.72 },
  { x: 0.5, y: 0.18 },
  { x: 0.5, y: 0.82 },
  { x: 0.18, y: 0.5 },
  { x: 0.82, y: 0.5 },
  { x: 0.2, y: 0.22 },
  { x: 0.8, y: 0.22 },
  { x: 0.22, y: 0.8 },
  { x: 0.78, y: 0.8 },
  { x: 0.14, y: 0.36 },
  { x: 0.86, y: 0.36 },
  { x: 0.14, y: 0.64 },
  { x: 0.86, y: 0.64 },
  { x: 0.38, y: 0.16 },
  { x: 0.62, y: 0.16 },
  { x: 0.36, y: 0.84 },
  { x: 0.64, y: 0.84 },
  { x: 0.06, y: 0.5 },
  { x: 0.94, y: 0.5 },
] as const;
const COLORS = [
  "var(--color-primary)",
  "var(--color-primary)",
  "var(--color-accent)",
  "var(--color-secondary)",
  "var(--color-tertiary)",
];

let resizeObserver: ResizeObserver | null = null;
let layoutFrame = 0;

function getDisplayPriority(word: WordCloudWord): number {
  const length = word.text.length;
  const phrasePenalty = word.text.includes(" ") ? 1.18 : 1;
  const lengthPenalty =
    length >= 24
      ? 1.55
      : length >= 18
        ? 1.35
        : length >= 14
          ? 1.18
          : length >= 10
            ? 1.08
            : 1;

  return word.weight / (phrasePenalty * lengthPenalty);
}

const displayWords = computed(() =>
  [...props.words]
    .filter((word) => !/^[a-z]{2,4}\.[A-Z]{2,4}$/.test(word.text))
    .sort(
      (a, b) =>
        getDisplayPriority(b) - getDisplayPriority(a) ||
        b.weight - a.weight ||
        a.text.length - b.text.length,
    )
    .slice(0, WORD_LIMIT),
);

const weightBounds = computed(() => {
  const values = displayWords.value.map((word) => word.weight);
  return {
    min: values.length > 0 ? Math.min(...values) : 0,
    max: values.length > 0 ? Math.max(...values) : 0,
  };
});

function getRatio(weight: number): number {
  const { min, max } = weightBounds.value;
  if (!Number.isFinite(weight) || max <= min) return 0.5;
  return (weight - min) / (max - min);
}

function getFontSize(weight: number): number {
  return Math.round(MIN_SIZE + getRatio(weight) * (MAX_SIZE - MIN_SIZE));
}

function getTextScale(text: string): number {
  const length = text.length;
  const isPhrase = text.includes(" ");
  if (isPhrase && length >= 22) return 0.42;
  if (isPhrase && length >= 16) return 0.54;
  if (isPhrase && length >= 12) return 0.64;
  if (length >= 28) return 0.52;
  if (length >= 22) return 0.6;
  if (length >= 18) return 0.7;
  if (length >= 14) return 0.8;
  if (length >= 11) return 0.9;
  return 1;
}

function getColor(weight: number): string {
  const ratio = getRatio(weight);
  if (ratio > 0.72) return COLORS[0]!;
  if (ratio > 0.48) return COLORS[1]!;
  if (ratio > 0.24) return COLORS[2]!;
  if (ratio > 0.12) return COLORS[3]!;
  return COLORS[4]!;
}

const styledWords = computed<StyledWord[]>(() =>
  displayWords.value.map((word) => {
    const ratio = getRatio(word.weight);
    const adjustedSize = Math.round(
      getFontSize(word.weight) * getTextScale(word.text),
    );
    return {
      ...word,
      color: getColor(word.weight),
      fontSize: adjustedSize,
      opacity: 0.48 + ratio * 0.52,
      renderScale: ratio >= 0.86 ? 1.12 : ratio >= 0.62 ? 1.06 : 1,
    };
  }),
);

function getFontFamily(): string {
  if (!import.meta.client) return '"Playfair Display", serif';
  const configured = getComputedStyle(document.documentElement)
    .getPropertyValue("--font-display")
    .trim();
  return configured || '"Playfair Display", serif';
}

function getMeasurementContext(): CanvasRenderingContext2D | null {
  if (!import.meta.client) return null;
  const canvas = document.createElement("canvas");
  return canvas.getContext("2d");
}

function measureWord(
  text: string,
  fontSize: number,
  fontFamily: string,
): { width: number; height: number } {
  const context = getMeasurementContext();
  if (!context) {
    return { width: text.length * fontSize * 0.64, height: fontSize };
  }

  context.font = `600 ${fontSize}px ${fontFamily}`;
  const metrics = context.measureText(text);
  return {
    width: Math.ceil(metrics.width),
    height: Math.ceil(fontSize * 1.08),
  };
}

function getRotatedBounds(
  width: number,
  height: number,
  rotation: number,
): { width: number; height: number } {
  const radians = (Math.abs(rotation) * Math.PI) / 180;
  const sin = Math.sin(radians);
  const cos = Math.cos(radians);

  return {
    width: Math.ceil(Math.abs(width * cos) + Math.abs(height * sin)),
    height: Math.ceil(Math.abs(width * sin) + Math.abs(height * cos)),
  };
}

function overlaps(a: Bounds, b: Bounds): boolean {
  return !(
    a.right <= b.left ||
    a.left >= b.right ||
    a.bottom <= b.top ||
    a.top >= b.bottom
  );
}

function getRotation(index: number, ratio: number): number {
  if (index < 2) return 0;
  if (ratio > 0.82) return index % 3 === 0 ? -12 : 12;
  return ROTATIONS[index % ROTATIONS.length] ?? 0;
}

function placeWord(
  word: StyledWord,
  index: number,
  existing: PlacedWord[],
  width: number,
  height: number,
  fontFamily: string,
  scale: number,
): PlacedWord | null {
  const ratio = getRatio(word.weight);
  const anchor =
    index < ANCHORS.length ? ANCHORS[index]! : ANCHORS[index % ANCHORS.length]!;
  const anchorX = width * anchor.x;
  const anchorY = height * anchor.y;
  const rotation = getRotation(index, ratio);
  const baseFontSize = Math.max(
    MIN_LAYOUT_SIZE,
    Math.round(word.fontSize * scale),
  );
  const base = measureWord(word.text, baseFontSize, fontFamily);
  let size = baseFontSize;
  const collisionPadding = Math.max(-2, Math.round(COLLISION_PADDING * scale));
  const panelPadding = Math.max(-4, Math.round(PANEL_PADDING * scale));

  while (size >= MIN_LAYOUT_SIZE) {
    const measured =
      size === baseFontSize ? base : measureWord(word.text, size, fontFamily);
    const rotated = getRotatedBounds(measured.width, measured.height, rotation);

    for (let step = 0; step < 920; step++) {
      const radius = step * (2.2 + (1 - Math.min(scale, 1)) * 0.7);
      const angle = step * 0.68 + index * 1.47;
      const x = anchorX + Math.cos(angle) * radius * 1.1;
      const y = anchorY + Math.sin(angle) * radius * 0.8;
      const bounds = {
        left: x - rotated.width / 2 - collisionPadding,
        top: y - rotated.height / 2 - collisionPadding,
        right: x + rotated.width / 2 + collisionPadding,
        bottom: y + rotated.height / 2 + collisionPadding,
      };

      if (
        bounds.left < panelPadding ||
        bounds.top < panelPadding ||
        bounds.right > width - panelPadding ||
        bounds.bottom > height - panelPadding
      )
        continue;
      if (
        existing.some((item) =>
          overlaps(bounds, {
            left: item.x - item.width / 2 - collisionPadding,
            top: item.y - item.height / 2 - collisionPadding,
            right: item.x + item.width / 2 + collisionPadding,
            bottom: item.y + item.height / 2 + collisionPadding,
          }),
        )
      )
        continue;

      return {
        ...word,
        fontSize: size,
        x,
        y,
        rotation,
        width: rotated.width,
        height: rotated.height,
        zIndex: 1000 - index,
      };
    }

    size -= size > 22 ? 2 : 1;
  }

  return null;
}

function buildLayout() {
  const width = Math.floor(containerWidth.value);
  const height = Math.floor(containerHeight.value);

  if (width < 120 || height < 120) {
    placedWords.value = [];
    return;
  }

  const fontFamily = getFontFamily();
  let bestLayout: PlacedWord[] = [];
  let bestScore = -1;

  for (const scale of SCALE_STEPS) {
    const nextLayout: PlacedWord[] = [];

    styledWords.value.forEach((word, index) => {
      const placed = placeWord(
        word,
        index,
        nextLayout,
        width,
        height,
        fontFamily,
        scale,
      );
      if (placed) nextLayout.push(placed);
    });

    const layoutScore =
      nextLayout.length * 1000 +
      nextLayout.reduce((sum, word) => sum + word.fontSize, 0);

    if (layoutScore > bestScore) {
      bestLayout = nextLayout;
      bestScore = layoutScore;
    }

    if (nextLayout.length >= styledWords.value.length) {
      bestLayout = nextLayout;
      break;
    }
  }

  placedWords.value = bestLayout;
}

function scheduleLayout() {
  if (!import.meta.client) return;
  cancelAnimationFrame(layoutFrame);
  layoutFrame = requestAnimationFrame(() => {
    buildLayout();
  });
}

onMounted(() => {
  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0];
    if (!entry) return;
    containerWidth.value = entry.contentRect.width;
    containerHeight.value = entry.contentRect.height;
    scheduleLayout();
  });

  if (containerRef.value) {
    resizeObserver.observe(containerRef.value);
    const rect = containerRef.value.getBoundingClientRect();
    containerWidth.value = rect.width;
    containerHeight.value = rect.height;
  }

  if (document.fonts?.ready) {
    document.fonts.ready.then(() => scheduleLayout()).catch(() => {});
  }

  nextTick(() => scheduleLayout());
});

onUnmounted(() => {
  resizeObserver?.disconnect();
  cancelAnimationFrame(layoutFrame);
  layoutFrame = 0;
});

watch(
  styledWords,
  () => {
    nextTick(() => scheduleLayout());
  },
  { deep: true },
);
</script>

<template>
  <div ref="containerRef" class="ks-cloud">
    <button
      v-for="word in placedWords"
      :key="word.text"
      type="button"
      class="ks-cloud__word"
      :style="{
        left: `${word.x}px`,
        top: `${word.y}px`,
        color: word.color,
        fontSize: `${word.fontSize}px`,
        opacity: word.opacity,
        '--ks-scale': `${word.renderScale}`,
        '--ks-rotation': `${word.rotation}deg`,
        transform: `translate(-50%, -50%) rotate(${word.rotation}deg) scale(${word.renderScale})`,
        zIndex: word.zIndex,
      }"
      @click="emit('click', word.text)"
    >
      {{ word.text }}
    </button>
  </div>
</template>

<style scoped>
.ks-cloud {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 200px;
  overflow: hidden;
}

.ks-cloud__word {
  position: absolute;
  background: none;
  border: none;
  padding: 0;
  font-family: var(--font-display);
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.02em;
  white-space: nowrap;
  cursor: pointer;
  transform-origin: center center;
  transition:
    transform 0.16s ease,
    opacity 0.16s ease,
    color 0.16s ease;
}

.ks-cloud__word:hover {
  opacity: 1 !important;
  transform: translate(-50%, -50%) rotate(var(--ks-rotation, 0deg))
    scale(calc(var(--ks-scale, 1) * 1.06));
}
</style>

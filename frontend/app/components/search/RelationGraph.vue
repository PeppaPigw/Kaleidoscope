<script setup lang="ts">
/**
 * RelationGraph — SVG force-directed citation graph.
 *
 * Design rules:
 *  - No text inside circles; author last-name + year appear below each node.
 *  - Origin nodes (user-selected) are larger with a double-ring marker.
 *  - Default: all arrows gray + near-invisible. Edges only highlight when
 *    a node is selected.
 *  - When a node is selected: connected neighbours highlight, others fade to 12%.
 *  - Click empty background → deselect.
 *  - During drag: spring forces disabled entirely (no pull-back tension).
 *  - After drop: 180 settle ticks with no-overlap enforcement push neighbours apart.
 */

export interface GraphNode {
  openalex_id: string
  title: string
  year?: number | null
  authors: string[]
  cited_by_count?: number
  is_origin: boolean
  abstract?: string
  venue?: string | null
}

export interface GraphEdge {
  source: string
  target: string
}

const props = defineProps<{
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedId: string | null
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'deselect'): void
}>()

// ── Sim node type ─────────────────────────────────────────────

interface SimNode {
  id: string
  x: number
  y: number
  vx: number
  vy: number
  r: number         // circle radius
  isOrigin: boolean
  lastName: string  // first author last name
  year: string
}

const containerRef = ref<HTMLDivElement>()
const svgRef = ref<SVGSVGElement>()
const width = ref(800)
const height = ref(600)
const simNodes = ref<SimNode[]>([])

let animFrame = 0
let ticksLeft = 0

// Drag state
const draggingId = ref<string | null>(null)
let svgRect = { left: 0, top: 0 }
let dragOffX = 0
let dragOffY = 0

// Pan state
const panOffset = ref({ x: 0, y: 0 })
let isPanning = false
let panHasMoved = false
let panAnchorClient = { x: 0, y: 0 }
let panAnchorOffset = { x: 0, y: 0 }
const PAN_CLICK_THRESHOLD = 4

// ── Connected-node set for highlighting ───────────────────────

const connectedIds = computed<Set<string>>(() => {
  if (!props.selectedId) return new Set()
  const s = new Set<string>()
  for (const e of props.edges) {
    if (e.source === props.selectedId) s.add(e.target)
    if (e.target === props.selectedId) s.add(e.source)
  }
  return s
})

// ── Init / reset ──────────────────────────────────────────────

function initSim() {
  cancelAnimationFrame(animFrame)
  const n = props.nodes.length
  if (!n) { simNodes.value = []; return }

  const cx = width.value / 2
  const cy = height.value / 2
  // Spread across a large radius for sparse initial layout
  const spread = Math.min(width.value, height.value) * 0.40

  simNodes.value = props.nodes.map((node, i) => {
    const angle = (2 * Math.PI * i) / n + (Math.random() - 0.5) * 0.4
    const r = spread * (0.5 + Math.random() * 0.5)
    const radius = node.is_origin ? 24 : 14
    const firstName = node.authors?.[0] ?? ''
    // Extract last name: last space-separated token
    const nameParts = firstName.trim().split(/\s+/)
    const lastName = nameParts[nameParts.length - 1] ?? '?'

    return {
      id: node.openalex_id,
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
      vx: 0,
      vy: 0,
      r: radius,
      isOrigin: node.is_origin,
      lastName,
      year: node.year ? String(node.year) : '—',
    } satisfies SimNode
  })

  ticksLeft = 500
  simulate()
}

// ── Physics ───────────────────────────────────────────────────

const REPULSION = 14000
const SPRING_K = 0.012
const SPRING_LEN = 220
const DAMPING = 0.78
const CENTER_PULL = 0.0008
const MIN_GAP = 28  // minimum gap between circle edges

function simulate() {
  const ns = simNodes.value
  if (!ns.length) return

  const cx = width.value / 2
  const cy = height.value / 2
  const dragging = draggingId.value !== null

  for (const n of ns) {
    if (n.id === draggingId.value) continue

    // Centering pull
    n.vx += (cx - n.x) * CENTER_PULL
    n.vy += (cy - n.y) * CENTER_PULL

    // Repulsion from every other node
    for (const m of ns) {
      if (m === n) continue
      const dx = n.x - m.x
      const dy = n.y - m.y
      const dist2 = dx * dx + dy * dy || 0.01
      const dist = Math.sqrt(dist2)
      // Coulomb repulsion
      const f = REPULSION / dist2
      n.vx += (dx / dist) * f
      n.vy += (dy / dist) * f
      // Hard separation: push apart if overlapping
      const minDist = n.r + m.r + MIN_GAP
      if (dist < minDist) {
        const overlap = (minDist - dist) * 0.35
        n.vx += (dx / dist) * overlap
        n.vy += (dy / dist) * overlap
      }
    }

    // Edge springs — DISABLED during drag
    if (!dragging) {
      for (const e of props.edges) {
        let other: SimNode | undefined
        if (e.source === n.id) other = ns.find(x => x.id === e.target)
        else if (e.target === n.id) other = ns.find(x => x.id === e.source)
        if (!other) continue
        const dx = other.x - n.x
        const dy = other.y - n.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        const stretch = dist - SPRING_LEN
        n.vx += (dx / dist) * SPRING_K * stretch
        n.vy += (dy / dist) * SPRING_K * stretch
      }
    }

    n.vx *= DAMPING
    n.vy *= DAMPING
    n.x += n.vx
    n.y += n.vy

    // Boundary clamp
    const pad = n.r + 8
    n.x = Math.max(pad, Math.min(width.value - pad, n.x))
    n.y = Math.max(pad, Math.min(height.value - pad - 28, n.y)) // 28 = label space
  }

  if (ticksLeft > 0) {
    ticksLeft--
    animFrame = requestAnimationFrame(simulate)
  }
}

// ── Resize observer ───────────────────────────────────────────

let ro: ResizeObserver | null = null
onMounted(() => {
  ro = new ResizeObserver(([e]) => {
    width.value = e.contentRect.width || 800
    height.value = e.contentRect.height || 600
    initSim()
  })
  if (containerRef.value) ro.observe(containerRef.value)
})
onUnmounted(() => { ro?.disconnect(); cancelAnimationFrame(animFrame) })
watch(() => [props.nodes, props.edges], () => {
  panOffset.value = { x: 0, y: 0 }
  initSim()
}, { deep: false })

// ── Edge geometry ─────────────────────────────────────────────

interface LineCoords { x1: number; y1: number; x2: number; y2: number }

function edgeLine(e: GraphEdge): LineCoords | null {
  const src = simNodes.value.find(n => n.id === e.source)
  const tgt = simNodes.value.find(n => n.id === e.target)
  if (!src || !tgt) return null
  const dx = tgt.x - src.x
  const dy = tgt.y - src.y
  const dist = Math.sqrt(dx * dx + dy * dy) || 1
  const nx = dx / dist
  const ny = dy / dist
  return {
    x1: src.x + nx * src.r,
    y1: src.y + ny * src.r,
    x2: tgt.x - nx * (tgt.r + 7),
    y2: tgt.y - ny * (tgt.r + 7),
  }
}

function isEdgeActive(e: GraphEdge): boolean {
  return !!props.selectedId && (e.source === props.selectedId || e.target === props.selectedId)
}

// ── Visual helpers ────────────────────────────────────────────

function nodeOpacity(n: SimNode): number {
  if (!props.selectedId) return 1.0
  if (n.id === props.selectedId || connectedIds.value.has(n.id)) return 1.0
  return 0.1
}

function nodeFill(n: SimNode): string {
  const sel = n.id === props.selectedId
  const conn = connectedIds.value.has(n.id)
  if (n.isOrigin) {
    if (sel) return '#0d7377'
    if (conn) return '#cce8e9'
    return '#e8f4f4'
  }
  if (sel) return '#e6f4f4'
  if (conn) return '#f0fafa'
  return '#ffffff'
}

function nodeStroke(n: SimNode): string {
  if (n.id === props.selectedId) return '#0d7377'
  if (connectedIds.value.has(n.id)) return '#2a9d8f'
  if (n.isOrigin) return '#00595c'
  return '#9eacac'
}

function nodeStrokeWidth(n: SimNode): number {
  if (n.id === props.selectedId) return 2.5
  if (n.isOrigin) return 2
  return 1.2
}

function labelColor(n: SimNode): string {
  if (!props.selectedId) return '#3e4949'
  if (n.id === props.selectedId || connectedIds.value.has(n.id)) return '#1a1c1b'
  return '#c0c8c8'
}

// ── Drag ─────────────────────────────────────────────────────

function onNodePointerDown(e: PointerEvent, n: SimNode) {
  e.stopPropagation()
  ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
  svgRect = svgRef.value!.getBoundingClientRect()
  // Subtract panOffset so node coords stay consistent with the panned viewport
  const svgX = e.clientX - svgRect.left - panOffset.value.x
  const svgY = e.clientY - svgRect.top - panOffset.value.y
  dragOffX = n.x - svgX
  dragOffY = n.y - svgY
  draggingId.value = n.id
  if (!animFrame) { ticksLeft = 9999; simulate() }
}

function onSvgPointerDown(e: PointerEvent) {
  // Only trigger pan for direct SVG background clicks (nodes use .stop)
  if (draggingId.value) return
  svgRect = svgRef.value!.getBoundingClientRect()
  isPanning = true
  panHasMoved = false
  panAnchorClient = { x: e.clientX, y: e.clientY }
  panAnchorOffset = { x: panOffset.value.x, y: panOffset.value.y }
  ;(svgRef.value as Element).setPointerCapture(e.pointerId)
}

function onSvgPointerMove(e: PointerEvent) {
  if (draggingId.value) {
    // Node drag
    const n = simNodes.value.find(x => x.id === draggingId.value)
    if (!n) return
    const svgX = e.clientX - svgRect.left - panOffset.value.x
    const svgY = e.clientY - svgRect.top - panOffset.value.y
    n.x = Math.max(n.r + 8, Math.min(width.value - n.r - 8, svgX + dragOffX))
    n.y = Math.max(n.r + 8, Math.min(height.value - n.r - 36, svgY + dragOffY))
    n.vx = 0
    n.vy = 0
  } else if (isPanning) {
    // Pan viewport
    const dx = e.clientX - panAnchorClient.x
    const dy = e.clientY - panAnchorClient.y
    if (Math.abs(dx) > PAN_CLICK_THRESHOLD || Math.abs(dy) > PAN_CLICK_THRESHOLD) {
      panHasMoved = true
    }
    panOffset.value = { x: panAnchorOffset.x + dx, y: panAnchorOffset.y + dy }
  }
}

function onSvgPointerUp() {
  if (draggingId.value) {
    draggingId.value = null
    ticksLeft = 180
    simulate()
  } else if (isPanning) {
    isPanning = false
    if (!panHasMoved) {
      // Treat as background click → deselect
      emit('deselect')
    }
  }
}
</script>

<template>
  <div ref="containerRef" class="rg-wrap">
    <svg
      ref="svgRef"
      class="rg-svg"
      :viewBox="`0 0 ${width} ${height}`"
      @pointerdown="onSvgPointerDown"
      @pointermove="onSvgPointerMove"
      @pointerup="onSvgPointerUp"
      @pointercancel="onSvgPointerUp"
    >
      <defs>
        <!-- Default arrowhead -->
        <marker id="arr" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">
          <path d="M0,0.5 L0,5.5 L6.5,3 z" fill="#8fa8a8" />
        </marker>
        <!-- Active (highlighted) arrowhead -->
        <marker id="arr-hi" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto">
          <path d="M0,0.5 L0,5.5 L6.5,3 z" fill="#0d7377" />
        </marker>
      </defs>

      <!-- Pan group: all content offset by panOffset -->
      <g :transform="`translate(${panOffset.x},${panOffset.y})`">

      <!-- Edges -->
      <g>
        <line
          v-for="(e, i) in edges"
          :key="i"
          v-bind="edgeLine(e) ?? {}"
          :class="['rg-edge', isEdgeActive(e) && 'rg-edge--hi']"
          :marker-end="isEdgeActive(e) ? 'url(#arr-hi)' : 'url(#arr)'"
        />
      </g>

      <!-- Nodes -->
      <g
        v-for="n in simNodes"
        :key="n.id"
        :transform="`translate(${n.x},${n.y})`"
        :style="{ opacity: nodeOpacity(n), cursor: 'grab' }"
        @pointerdown.stop="onNodePointerDown($event, n)"
        @click.stop="emit('select', n.id)"
      >
        <!-- Origin outer ring (dashed) -->
        <circle
          v-if="n.isOrigin"
          :r="n.r + 7"
          fill="none"
          :stroke="n.id === selectedId ? '#0d7377' : '#00595c'"
          stroke-width="1"
          stroke-dasharray="4 3"
          opacity="0.6"
        />

        <!-- Main circle -->
        <circle
          :r="n.r"
          :fill="nodeFill(n)"
          :stroke="nodeStroke(n)"
          :stroke-width="nodeStrokeWidth(n)"
        />

        <!-- Selection pulse ring -->
        <circle
          v-if="n.id === selectedId"
          :r="n.r + 4"
          fill="none"
          stroke="#0d7377"
          stroke-width="1.5"
          opacity="0.25"
        />

        <!-- Author last name (line 1) -->
        <text
          text-anchor="middle"
          :y="n.r + 13"
          class="rg-label-name"
          :fill="labelColor(n)"
        >{{ n.lastName }}</text>

        <!-- Year (line 2) -->
        <text
          text-anchor="middle"
          :y="n.r + 23"
          class="rg-label-year"
          :fill="labelColor(n)"
        >{{ n.year }}</text>
      </g>

      </g><!-- /pan group -->
    </svg>

    <!-- Empty state -->
    <div v-if="!nodes.length" class="rg-empty">
      <span class="rg-empty-icon">⬡</span>
      <p>Select papers and click "Build Graph"</p>
    </div>
  </div>
</template>

<style scoped>
.rg-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--color-bg, #f9f9f6);
}

.rg-svg {
  display: block;
  width: 100%;
  height: 100%;
  user-select: none;
  touch-action: none;
  cursor: grab;
}
.rg-svg:active { cursor: grabbing; }

/* ── Edges ── */
.rg-edge {
  stroke: #8fa8a8;
  stroke-width: 1;
  fill: none;
  opacity: 0.40;
  transition: opacity 0.2s, stroke 0.2s;
}
.rg-edge--hi {
  stroke: #0d7377;
  stroke-width: 1.5;
  opacity: 0.90;
}

/* ── Labels ── */
.rg-label-name {
  font: 500 9px/1 'Inter', sans-serif;
  pointer-events: none;
}
.rg-label-year {
  font: 400 8px/1 'JetBrains Mono', monospace;
  pointer-events: none;
}

/* ── Empty ── */
.rg-empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  pointer-events: none;
}
.rg-empty-icon {
  font-size: 52px;
  opacity: 0.12;
}
.rg-empty p {
  font: 400 0.8rem/1 'Noto Serif', serif;
  font-style: italic;
  color: #9eacac;
}
</style>

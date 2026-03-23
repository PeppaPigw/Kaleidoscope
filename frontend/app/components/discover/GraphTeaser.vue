<script setup lang="ts">
/**
 * GraphTeaser — Concept graph SVG preview with call-to-action.
 *
 * Renders a miniature node-link concept graph using inline SVG.
 * Provides a CTA to explore the full graph view.
 */

export interface GraphNode {
  id: string
  label: string
  cx: number
  cy: number
  r: number
  type: 'primary' | 'bridge'
}

export interface GraphEdge {
  from: string
  to: string
}

export interface GraphTeaserProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

const props = defineProps<GraphTeaserProps>()

defineEmits<{
  'explore': []
}>()

const uid = useId()

/** Pre-compute a Map for O(1) node lookups */
const nodeMap = computed(() => {
  const map = new Map<string, GraphNode>()
  for (const n of props.nodes) map.set(n.id, n)
  return map
})

/** Resolve edges to { from, to, x1, y1, x2, y2 } with coordinates */
const resolvedEdges = computed(() => {
  return props.edges
    .map(e => {
      const from = nodeMap.value.get(e.from)
      const to = nodeMap.value.get(e.to)
      if (!from || !to) return null
      return { key: `${e.from}-${e.to}`, x1: from.cx, y1: from.cy, x2: to.cx, y2: to.cy }
    })
    .filter(Boolean) as { key: string; x1: number; y1: number; x2: number; y2: number }[]
})
</script>

<template>
  <section
    class="ks-graph-teaser ks-card ks-motion-paper-reveal ks-motion-paper-reveal--delay-3"
    :aria-labelledby="`${uid}-title`"
  >
    <h4 :id="`${uid}-title`" class="ks-type-section-title">Concept Graph</h4>
    <p class="ks-type-body-sm ks-graph-teaser__desc">
      Connection landscape for current query
    </p>
    <div class="ks-graph-teaser__canvas" role="img" aria-label="Concept connection graph">
      <svg viewBox="0 0 264 152" class="ks-graph-teaser__svg">
        <!-- Edges -->
        <line
          v-for="edge in resolvedEdges"
          :key="edge.key"
          :x1="edge.x1"
          :y1="edge.y1"
          :x2="edge.x2"
          :y2="edge.y2"
          stroke="rgba(26,26,26,0.08)"
          stroke-width="1"
        />
        <!-- Nodes -->
        <g v-for="node in nodes" :key="node.id">
          <circle
            :cx="node.cx"
            :cy="node.cy"
            :r="node.r"
            :fill="node.type === 'primary' ? 'rgba(13,115,119,0.22)' : 'rgba(196,163,90,0.35)'"
            :stroke="node.type === 'primary' ? 'var(--color-primary)' : 'var(--color-accent-decorative)'"
            stroke-width="1.5"
          />
          <text
            :x="node.cx"
            :y="node.cy + node.r + 12"
            text-anchor="middle"
            class="ks-graph-teaser__label"
          >
            {{ node.label }}
          </text>
        </g>
      </svg>
    </div>
    <KsButton
      variant="secondary"
      class="ks-graph-teaser__cta"
      @click="$emit('explore')"
    >
      Explore full graph →
    </KsButton>
  </section>
</template>

<style scoped>
.ks-graph-teaser {
  padding: 20px;
}

.ks-graph-teaser__desc {
  color: var(--color-secondary);
  margin-bottom: 8px;
}

.ks-graph-teaser__canvas {
  width: 100%;
  background: rgba(250, 250, 247, 0.5);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
}

.ks-graph-teaser__svg {
  width: 100%;
  height: auto;
}

.ks-graph-teaser__label {
  font: 500 9px / 1 var(--font-sans);
  fill: var(--color-text);
}

.ks-graph-teaser__cta {
  width: 100%;
  margin-top: 8px;
}
</style>

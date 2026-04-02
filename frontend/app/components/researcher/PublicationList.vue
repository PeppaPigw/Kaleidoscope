<script setup lang="ts">
/**
 * PublicationList — Full browsable list of a researcher's papers.
 *
 * Features:
 * - Search by title / keyword
 * - Sort by year (desc/asc) or citations (desc)
 * - Expand individual papers to see abstract + keywords
 * - ArXiv link chip, corresponding-author badge, author position
 */

export interface PaperEntry {
  id: string
  title: string
  doi?: string | null
  arxiv_id?: string | null
  s2_paper_id?: string | null
  abstract?: string | null
  keywords?: string[]
  published_at?: string | null
  year?: number | null
  citation_count: number
  venue?: string | null
  in_library?: boolean
  library_paper_id?: string | null
  has_full_text?: boolean
  author_position?: number | null
  is_corresponding?: boolean
}

interface Props {
  papers: PaperEntry[]
}

const props = defineProps<Props>()
defineEmits<{ 'paper-click': [paper: PaperEntry] }>()

const uid = useId()

type SortKey = 'year_desc' | 'year_asc' | 'citations_desc'
const sortKey = ref<SortKey>('year_desc')
const query = ref('')
const expandedIds = ref<Set<string>>(new Set())

function toggleExpand(id: string) {
  const s = new Set(expandedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedIds.value = s
}

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  let list = props.papers
  if (q) {
    list = list.filter(p =>
      p.title.toLowerCase().includes(q) ||
      (p.keywords ?? []).some(k => k.toLowerCase().includes(q)) ||
      (p.abstract ?? '').toLowerCase().includes(q) ||
      (p.venue ?? '').toLowerCase().includes(q)
    )
  }
  return [...list].sort((a, b) => {
    if (sortKey.value === 'citations_desc') return b.citation_count - a.citation_count
    const ya = a.year ?? 0, yb = b.year ?? 0
    return sortKey.value === 'year_asc' ? ya - yb : yb - ya
  })
})

const inLibraryCount = computed(() => props.papers.filter(p => p.in_library).length)

function positionLabel(pos: number) {
  if (pos === 0) return '1st author'
  if (pos === 1) return '2nd author'
  if (pos === 2) return '3rd author'
  return `${pos + 1}th author`
}
</script>

<template>
  <section class="ks-pub-list ks-motion-paper-reveal" :aria-labelledby="`${uid}-title`">
    <div class="ks-pub-list__header">
      <h2 :id="`${uid}-title`" class="ks-type-section-title">
        Publications
        <span class="ks-pub-list__count ks-type-data">{{ filtered.length }} / {{ papers.length }}</span>
        <span v-if="inLibraryCount" class="ks-pub-list__lib-badge">
          {{ inLibraryCount }} in library
        </span>
      </h2>

      <div class="ks-pub-list__controls">
        <input
          v-model="query"
          type="search"
          placeholder="Search title, keyword…"
          class="ks-pub-list__search"
          :aria-label="'Filter publications'"
        />
        <select v-model="sortKey" class="ks-pub-list__sort" aria-label="Sort order">
          <option value="year_desc">Newest first</option>
          <option value="year_asc">Oldest first</option>
          <option value="citations_desc">Most cited</option>
        </select>
      </div>
    </div>

    <p v-if="filtered.length === 0" class="ks-pub-list__empty ks-type-data">
      No papers match "{{ query }}"
    </p>

    <ol class="ks-pub-list__list">
      <li
        v-for="paper in filtered"
        :key="paper.id"
        class="ks-pub-list__item"
        :class="{
          'ks-pub-list__item--expanded': expandedIds.has(paper.id),
          'ks-pub-list__item--in-library': paper.in_library,
        }"
      >
        <!-- Library indicator stripe -->
        <div v-if="paper.in_library" class="ks-pub-list__lib-stripe" aria-hidden="true" />

        <!-- Main row -->
        <div class="ks-pub-list__row">
          <div class="ks-pub-list__meta-left">
            <span class="ks-pub-list__year ks-type-data">{{ paper.year ?? '—' }}</span>
          </div>

          <div class="ks-pub-list__body">
            <!-- Title: clickable to our reader if in library, else opens arXiv -->
            <button
              v-if="paper.in_library && paper.library_paper_id"
              type="button"
              class="ks-pub-list__title-btn"
              @click="$emit('paper-click', paper)"
            >
              {{ paper.title }}
            </button>
            <a
              v-else-if="paper.arxiv_id"
              :href="`https://arxiv.org/abs/${paper.arxiv_id}`"
              target="_blank" rel="noopener"
              class="ks-pub-list__title-link"
            >{{ paper.title }}</a>
            <span v-else class="ks-pub-list__title-plain">{{ paper.title }}</span>

            <!-- Venue -->
            <span v-if="paper.venue" class="ks-pub-list__venue ks-type-data">{{ paper.venue }}</span>

            <div class="ks-pub-list__chips">
              <!-- Library status badges -->
              <span v-if="paper.in_library && paper.has_full_text" class="ks-pub-list__chip ks-pub-list__chip--library">
                ✓ In Library · Full Text
              </span>
              <span v-else-if="paper.in_library" class="ks-pub-list__chip ks-pub-list__chip--library-meta">
                ✓ In Library
              </span>

              <!-- Author role (only for library papers) -->
              <span v-if="paper.in_library && paper.author_position != null" class="ks-pub-list__chip ks-pub-list__chip--role">
                {{ positionLabel(paper.author_position!) }}
              </span>
              <span v-if="paper.is_corresponding" class="ks-pub-list__chip ks-pub-list__chip--corr">
                Corresponding
              </span>

              <!-- arXiv link -->
              <a
                v-if="paper.arxiv_id && !paper.in_library"
                :href="`https://arxiv.org/abs/${paper.arxiv_id}`"
                target="_blank" rel="noopener"
                class="ks-pub-list__chip ks-pub-list__chip--arxiv"
                @click.stop
              >
                arXiv ↗
              </a>

              <!-- Keywords -->
              <span
                v-for="kw in (paper.keywords ?? []).slice(0, 3)"
                :key="kw"
                class="ks-pub-list__chip ks-pub-list__chip--kw"
              >{{ kw }}</span>
            </div>
          </div>

          <div class="ks-pub-list__meta-right">
            <span v-if="paper.citation_count > 0" class="ks-pub-list__cite ks-type-data">
              {{ paper.citation_count.toLocaleString() }} <span class="ks-pub-list__cite-label">cited</span>
            </span>
            <button
              v-if="paper.abstract"
              type="button"
              class="ks-pub-list__expand-btn"
              :aria-expanded="expandedIds.has(paper.id)"
              :aria-controls="`${uid}-abs-${paper.id}`"
              @click="toggleExpand(paper.id)"
            >
              {{ expandedIds.has(paper.id) ? '▲' : '▼' }}
            </button>
          </div>
        </div>

        <!-- Expandable abstract -->
        <div
          v-if="paper.abstract && expandedIds.has(paper.id)"
          :id="`${uid}-abs-${paper.id}`"
          class="ks-pub-list__abstract"
        >
          <p>{{ paper.abstract }}</p>
          <div class="ks-pub-list__abstract-footer">
            <KsTranslateBtn :text="paper.abstract" />
            <div v-if="(paper.keywords ?? []).length" class="ks-pub-list__kw-all">
              <span
                v-for="kw in paper.keywords"
                :key="kw"
                class="ks-pub-list__chip ks-pub-list__chip--kw"
              >{{ kw }}</span>
            </div>
          </div>
        </div>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.ks-pub-list__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.ks-pub-list__count {
  font-weight: 400;
  color: var(--color-secondary);
  margin-left: 8px;
}

.ks-pub-list__controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.ks-pub-list__search {
  padding: 6px 10px;
  font-size: 13px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text);
  width: 200px;
  outline: none;
}
.ks-pub-list__search:focus {
  border-color: var(--color-primary);
}

.ks-pub-list__sort {
  padding: 6px 8px;
  font-size: 13px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text);
  cursor: pointer;
  outline: none;
}
.ks-pub-list__sort:focus {
  border-color: var(--color-primary);
}

.ks-pub-list__empty {
  color: var(--color-secondary);
  padding: 24px 0;
  text-align: center;
}

.ks-pub-list__list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ks-pub-list__lib-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  padding: 2px 8px;
  border-radius: 3px;
  margin-left: 10px;
  vertical-align: middle;
}

.ks-pub-list__item {
  border-radius: 6px;
  transition: background 0.12s ease;
  position: relative;
  overflow: hidden;
}
.ks-pub-list__item:hover {
  background: var(--color-surface, #f8f8f6);
}
.ks-pub-list__item--expanded {
  background: var(--color-surface, #f8f8f6);
}
.ks-pub-list__item--in-library {
  background: color-mix(in srgb, var(--color-primary) 4%, transparent);
  border: 1px solid color-mix(in srgb, var(--color-primary) 20%, transparent);
}
.ks-pub-list__item--in-library:hover {
  background: color-mix(in srgb, var(--color-primary) 7%, transparent);
}

.ks-pub-list__lib-stripe {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--color-primary);
  border-radius: 6px 0 0 6px;
}

.ks-pub-list__row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 12px 10px;
}

.ks-pub-list__meta-left {
  flex-shrink: 0;
  width: 40px;
  padding-top: 3px;
  text-align: right;
}

.ks-pub-list__year {
  font-size: 12px;
  color: var(--color-secondary);
  font-variant-numeric: tabular-nums;
}

.ks-pub-list__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ks-pub-list__title-btn {
  background: none;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  font: 600 0.9375rem / 1.45 var(--font-serif, serif);
  color: var(--color-text);
  transition: color 0.12s;
}
.ks-pub-list__title-btn:hover {
  color: var(--color-primary);
}
.ks-pub-list__title-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  border-radius: 2px;
}

.ks-pub-list__title-link {
  font: 600 0.9375rem / 1.45 var(--font-serif, serif);
  color: var(--color-text);
  text-decoration: none;
  transition: color 0.12s;
}
.ks-pub-list__title-link:hover { color: var(--color-primary); }

.ks-pub-list__title-plain {
  font: 600 0.9375rem / 1.45 var(--font-serif, serif);
  color: var(--color-text);
}

.ks-pub-list__venue {
  font-size: 12px;
  color: var(--color-secondary);
  font-style: italic;
}

.ks-pub-list__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ks-pub-list__chip {
  display: inline-block;
  font-size: 11px;
  line-height: 1;
  padding: 3px 7px;
  border-radius: 3px;
  white-space: nowrap;
}
.ks-pub-list__chip--role {
  background: color-mix(in srgb, var(--color-primary) 10%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}
.ks-pub-list__chip--corr {
  background: color-mix(in srgb, var(--color-accent-decorative, #c4a35a) 15%, transparent);
  color: color-mix(in srgb, var(--color-accent-decorative, #c4a35a) 90%, #000);
  font-weight: 600;
}
.ks-pub-list__chip--library {
  background: color-mix(in srgb, var(--color-primary) 12%, transparent);
  color: var(--color-primary);
  font-weight: 700;
  border: 1px solid color-mix(in srgb, var(--color-primary) 30%, transparent);
}
.ks-pub-list__chip--library-meta {
  background: color-mix(in srgb, var(--color-primary) 8%, transparent);
  color: var(--color-primary);
  font-weight: 600;
}
.ks-pub-list__chip--arxiv {
  background: color-mix(in srgb, #e65100 10%, transparent);
  color: #c84b00;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.12s;
}
.ks-pub-list__chip--arxiv:hover {
  background: color-mix(in srgb, #e65100 18%, transparent);
}
.ks-pub-list__chip--kw {
  background: var(--color-surface, #f0f0ee);
  color: var(--color-secondary);
  border: 1px solid var(--color-border);
}

.ks-pub-list__meta-right {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  padding-top: 3px;
}

.ks-pub-list__cite {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}
.ks-pub-list__cite-label {
  font-weight: 400;
  color: var(--color-secondary);
}

.ks-pub-list__expand-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 10px;
  color: var(--color-secondary);
  padding: 2px 4px;
  border-radius: 3px;
  transition: color 0.12s;
}
.ks-pub-list__expand-btn:hover { color: var(--color-primary); }
.ks-pub-list__expand-btn:focus-visible {
  outline: 2px solid var(--color-primary);
}

.ks-pub-list__abstract {
  padding: 0 12px 14px 64px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ks-pub-list__abstract p {
  font: 400 0.875rem / 1.65 var(--font-serif, serif);
  color: var(--color-secondary);
  margin: 0;
}
.ks-pub-list__abstract-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ks-pub-list__kw-all {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

@media (max-width: 600px) {
  .ks-pub-list__header { flex-direction: column; }
  .ks-pub-list__abstract { padding-left: 24px; }
  .ks-pub-list__search { width: 100%; }
}
</style>

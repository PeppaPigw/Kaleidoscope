<script setup lang="ts">
import { renderRagflowAnswer } from '~/utils/ragflowAnswer'
import type {
  Collection,
  CollectionChatMessage,
  CollectionChatThread,
  CollectionFeedSubscription,
  Feed,
  Paper,
} from '~/composables/useApi'

definePageMeta({ layout: 'default', hideTopbar: true, flushContent: true })

useHead({
  title: 'Research Chat — Kaleidoscope',
  meta: [{ name: 'description', content: 'Chat across your workspaces, subscription collections, and paper groups.' }],
})

type CollectionKind = NonNullable<Collection['kind']>

const api = useApi()

// ── Data ──────────────────────────────────────────────────────────────────────
const collections = ref<Collection[]>([])
const feedCatalog = ref<Feed[]>([])
const collectionFeeds = ref<CollectionFeedSubscription[]>([])
const threads = ref<CollectionChatThread[]>([])
const messages = ref<CollectionChatMessage[]>([])
const activeCollectionPapers = ref<Paper[]>([])
const parentCollectionPapers = ref<Paper[]>([])

const activeCollectionId = ref<string | null>(null)
const activeThreadId = ref<string | null>(null)
const chatInput = ref('')
const sending = ref(false)
const syncing = ref(false)
const loadingCollections = ref(true)
const loadingContext = ref(false)
const pageError = ref<string | null>(null)

// ── Create form visibility ────────────────────────────────────────────────────
const showWorkspaceForm = ref(false)
const showSubscriptionForm = ref(false)
const showGroupForm = ref(false)

// ── Create form values ────────────────────────────────────────────────────────
const workspaceName = ref('')
const workspaceDescription = ref('')
const subscriptionName = ref('')
const subscriptionDescription = ref('')
const selectedFeedIds = ref<string[]>([])
const groupName = ref('')
const selectedParentPaperIds = ref<string[]>([])

// ── UI state ──────────────────────────────────────────────────────────────────
const messagesEnd = ref<HTMLElement | null>(null)
const inputFocused = ref(false)
const renderedMessages = ref<Record<string, string>>({})
const expandedSources = ref<Record<string, boolean>>({})

// ── Computed ──────────────────────────────────────────────────────────────────
const collectionMap = computed(() => new Map(collections.value.map(c => [c.id, c])))
const workspaces = computed(() => collections.value.filter(c => c.kind === 'workspace'))
const subscriptionCollections = computed(() => collections.value.filter(c => c.kind === 'subscription_collection'))
const paperGroups = computed(() => collections.value.filter(c => c.kind === 'paper_group'))
const activeCollection = computed(() => activeCollectionId.value ? collectionMap.value.get(activeCollectionId.value) ?? null : null)
const groupParentCollection = computed(() => {
  if (!activeCollection.value || activeCollection.value.kind !== 'paper_group') return null
  const parentId = activeCollection.value.parent_collection_id
  return parentId ? collectionMap.value.get(parentId) ?? null : null
})
const activeParentContainer = computed(() => {
  if (!activeCollection.value) return null
  if (activeCollection.value.kind === 'paper_group') return groupParentCollection.value
  return activeCollection.value
})
const visiblePaperGroups = computed(() => {
  const parentId = activeParentContainer.value?.id
  if (!parentId) return paperGroups.value
  return paperGroups.value.filter(g => g.parent_collection_id === parentId)
})
const activeThread = computed(() => activeThreadId.value ? threads.value.find(t => t.id === activeThreadId.value) ?? null : null)
const createGroupParent = computed(() => {
  if (!activeCollection.value) return workspaces.value[0] ?? subscriptionCollections.value[0] ?? null
  if (activeCollection.value.kind === 'paper_group') return groupParentCollection.value
  if (activeCollection.value.kind === 'workspace' || activeCollection.value.kind === 'subscription_collection') return activeCollection.value
  return null
})

// ── Helpers ───────────────────────────────────────────────────────────────────
function normalizeCollectionKind(kind: Collection['kind']): CollectionKind {
  if (kind === 'subscription_collection' || kind === 'paper_group') return kind
  return 'workspace'
}

function kindLabel(kind: Collection['kind']): string {
  const normalized = normalizeCollectionKind(kind)
  if (normalized === 'subscription_collection') return 'Subscription'
  if (normalized === 'paper_group') return 'Paper Group'
  return 'Workspace'
}

function kindMonoLabel(kind: Collection['kind']): string {
  const normalized = normalizeCollectionKind(kind)
  if (normalized === 'subscription_collection') return 'SUBSCRIPTION COLLECTION'
  if (normalized === 'paper_group') return 'PAPER GROUP'
  return 'WORKSPACE'
}

function suggestedQuestions(kind: Collection['kind']): string[] {
  const normalized = normalizeCollectionKind(kind)
  if (normalized === 'subscription_collection') return [
    "What's most important in this feed recently?",
    'Summarize the emerging research trends',
    'Which papers should I prioritize reading?',
  ]
  if (normalized === 'paper_group') return [
    'Compare and contrast these papers',
    'What do these papers agree on?',
    'What are the key methodological differences?',
  ]
  return [
    'What are the main themes in my research?',
    'Which papers should I read next?',
    'What research gaps have I not addressed?',
  ]
}

function sourceCount(message: CollectionChatMessage): number {
  return Array.isArray(message.sources?.items) ? (message.sources?.items?.length ?? 0) : 0
}

function formatTimestamp(value?: string | null): string {
  if (!value) return ''
  try { return new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) }
  catch { return '' }
}

async function scrollToBottom() {
  await nextTick()
  messagesEnd.value?.scrollIntoView({ behavior: 'smooth' })
}

function toggleSources(msgId: string) {
  expandedSources.value[msgId] = !expandedSources.value[msgId]
}

// ── API ───────────────────────────────────────────────────────────────────────
async function loadCollections() {
  loadingCollections.value = true
  pageError.value = null
  try {
    collections.value = await api.listCollections()
    if (!activeCollectionId.value || !collectionMap.value.has(activeCollectionId.value)) {
      activeCollectionId.value = workspaces.value[0]?.id ?? subscriptionCollections.value[0]?.id ?? paperGroups.value[0]?.id ?? null
    }
  }
  catch (error: unknown) {
    pageError.value = error instanceof Error ? error.message : 'Failed to load collections'
    collections.value = []
  }
  finally {
    loadingCollections.value = false
  }
}

async function loadFeedCatalog() {
  try {
    const response = await api.listFeeds()
    feedCatalog.value = response.items ?? []
  }
  catch { feedCatalog.value = [] }
}

async function ensureThread(collectionId: string): Promise<string | null> {
  threads.value = await api.listCollectionThreads(collectionId)
  if (!threads.value.length) {
    const created = await api.createCollectionThread(collectionId, 'New chat')
    threads.value = [created]
  }
  const preferredId = activeThreadId.value && threads.value.some(t => t.id === activeThreadId.value)
    ? activeThreadId.value
    : threads.value[0]?.id ?? null
  activeThreadId.value = preferredId
  return preferredId
}

async function loadActiveCollectionContext() {
  const collection = activeCollection.value
  if (!collection) {
    collectionFeeds.value = []
    activeCollectionPapers.value = []
    parentCollectionPapers.value = []
    threads.value = []
    messages.value = []
    activeThreadId.value = null
    return
  }
  loadingContext.value = true
  selectedParentPaperIds.value = []
  try {
    const paperResponse = await api.getCollectionPapers(collection.id)
    activeCollectionPapers.value = paperResponse.papers
    if (collection.kind === 'subscription_collection') {
      collectionFeeds.value = await api.listCollectionFeeds(collection.id)
    }
    else { collectionFeeds.value = [] }
    if (collection.kind === 'paper_group' && collection.parent_collection_id) {
      const parentPaperResponse = await api.getCollectionPapers(collection.parent_collection_id)
      parentCollectionPapers.value = parentPaperResponse.papers
    }
    else { parentCollectionPapers.value = [] }
    const threadId = await ensureThread(collection.id)
    messages.value = threadId ? await api.listCollectionThreadMessages(collection.id, threadId) : []
  }
  catch (error: unknown) {
    pageError.value = error instanceof Error ? error.message : 'Failed to load collection context'
    collectionFeeds.value = []
    activeCollectionPapers.value = []
    parentCollectionPapers.value = []
    threads.value = []
    messages.value = []
  }
  finally { loadingContext.value = false }
}

async function selectCollection(collectionId: string) {
  if (activeCollectionId.value === collectionId) return
  activeCollectionId.value = collectionId
}

async function createWorkspace() {
  const name = workspaceName.value.trim()
  if (!name) return
  const created = await api.createCollection({ name, description: workspaceDescription.value.trim() || undefined, kind: 'workspace' })
  workspaceName.value = ''
  workspaceDescription.value = ''
  showWorkspaceForm.value = false
  await loadCollections()
  await selectCollection(created.id)
}

async function createSubscriptionCollection() {
  const name = subscriptionName.value.trim()
  if (!name) return
  const created = await api.createCollection({ name, description: subscriptionDescription.value.trim() || undefined, kind: 'subscription_collection' })
  if (selectedFeedIds.value.length) await api.attachCollectionFeeds(created.id, selectedFeedIds.value)
  subscriptionName.value = ''
  subscriptionDescription.value = ''
  selectedFeedIds.value = []
  showSubscriptionForm.value = false
  await loadCollections()
  await selectCollection(created.id)
}

async function createPaperGroup() {
  const name = groupName.value.trim()
  const parent = createGroupParent.value
  if (!name || !parent) return
  const created = await api.createCollection({ name, description: `Paper group inside ${parent.name}`, kind: 'paper_group', parent_collection_id: parent.id })
  groupName.value = ''
  showGroupForm.value = false
  await loadCollections()
  await selectCollection(created.id)
}

async function createFreshThread() {
  if (!activeCollection.value) return
  const created = await api.createCollectionThread(activeCollection.value.id, 'New chat')
  threads.value = [created, ...threads.value]
  activeThreadId.value = created.id
  messages.value = []
  renderedMessages.value = {}
  expandedSources.value = {}
}

async function reloadActiveMessages() {
  if (!activeCollection.value || !activeThreadId.value) return
  messages.value = await api.listCollectionThreadMessages(activeCollection.value.id, activeThreadId.value)
}

async function sendMessage() {
  const content = chatInput.value.trim()
  if (!content || !activeCollection.value || !activeThreadId.value || sending.value) return

  const tempUserId = `temp-user-${Date.now()}`
  const optimisticUser: CollectionChatMessage = {
    id: tempUserId,
    thread_id: activeThreadId.value,
    role: 'user',
    content,
    created_at: new Date().toISOString(),
  }
  messages.value = [...messages.value, optimisticUser]
  chatInput.value = ''
  sending.value = true
  pageError.value = null
  await scrollToBottom()

  try {
    const response = await api.askCollectionThread(
      activeCollection.value.id,
      activeThreadId.value,
      content,
      activeCollection.value.kind === 'paper_group' ? 6 : 10,
    )
    messages.value = messages.value
      .filter(m => m.id !== tempUserId)
      .concat([response.user_message, response.assistant_message])
  }
  catch (error: unknown) {
    messages.value = messages.value.filter(m => m.id !== tempUserId)
    pageError.value = error instanceof Error ? error.message : 'Failed to send message'
  }
  finally {
    sending.value = false
    await scrollToBottom()
  }
}

async function syncActiveCollection() {
  if (!activeCollection.value || syncing.value) return
  syncing.value = true
  try { await api.triggerCollectionSync(activeCollection.value.id) }
  catch (error: unknown) { pageError.value = error instanceof Error ? error.message : 'Failed to trigger sync' }
  finally { syncing.value = false }
}

async function addSelectedParentPapersToGroup() {
  if (!activeCollection.value || activeCollection.value.kind !== 'paper_group') return
  if (!selectedParentPaperIds.value.length) return
  await api.addPapersToCollection(activeCollection.value.id, selectedParentPaperIds.value, 'Added from landscape group manager')
  selectedParentPaperIds.value = []
  await loadActiveCollectionContext()
}

async function handleSuggestedQuestion(question: string) {
  chatInput.value = question
  await sendMessage()
}

// ── Watchers ──────────────────────────────────────────────────────────────────
watch(activeCollectionId, async () => {
  renderedMessages.value = {}
  expandedSources.value = {}
  await loadActiveCollectionContext()
})

watch(activeThreadId, async (threadId, prevThreadId) => {
  if (!activeCollection.value || !threadId || threadId === prevThreadId) return
  renderedMessages.value = {}
  expandedSources.value = {}
  await reloadActiveMessages()
})

watch(
  messages,
  async (newMessages) => {
    for (const msg of newMessages) {
      if (msg.role === 'assistant' && msg.content && !renderedMessages.value[msg.id]) {
        try {
          renderedMessages.value[msg.id] = await renderRagflowAnswer(msg.content)
        }
        catch {
          renderedMessages.value[msg.id] = `<p>${msg.content.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</p>`
        }
      }
    }
    await scrollToBottom()
  },
  { deep: true },
)

onMounted(async () => {
  await Promise.all([loadCollections(), loadFeedCatalog()])
})
</script>

<template>
  <div class="rc-shell">
    <!-- ── Left panel: Collection browser ─────────────────────────────────── -->
    <aside class="rc-left">
      <!-- Search / Filter input -->
      <div class="rc-left__top">
        <p class="rc-eyebrow">Research Space</p>
        <div class="rc-search-row">
          <input
            type="text"
            class="rc-search-input"
            placeholder="Filter collections…"
            readonly
          >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="rc-search-icon" aria-hidden="true">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>
      </div>

      <!-- Error -->
      <div v-if="pageError" class="rc-error">
        {{ pageError }}
      </div>

      <!-- Collections list -->
      <div class="rc-left__list">
        <!-- Workspaces -->
        <div class="rc-section">
          <div class="rc-section__head">
            <p class="rc-eyebrow">Workspaces</p>
            <button type="button" class="rc-new-btn" @click="showWorkspaceForm = !showWorkspaceForm">
              {{ showWorkspaceForm ? '×' : '+' }}
            </button>
          </div>
          <transition name="form-drop">
            <div v-if="showWorkspaceForm" class="rc-form">
              <input v-model="workspaceName" type="text" class="rc-form__input" placeholder="Clinical reasoning review" >
              <textarea v-model="workspaceDescription" rows="2" class="rc-form__input rc-form__input--area" placeholder="What is this workspace for?" />
              <button type="button" class="rc-form__submit" :disabled="!workspaceName.trim()" @click="createWorkspace">
                Create workspace
              </button>
            </div>
          </transition>
          <p v-if="loadingCollections" class="rc-loading">Loading…</p>
          <button
            v-for="ws in workspaces"
            :key="ws.id"
            type="button"
            class="rc-coll-card"
            :class="{ 'rc-coll-card--active': activeCollectionId === ws.id }"
            @click="selectCollection(ws.id)"
          >
            <p class="rc-coll-card__kind">WORKSPACE</p>
            <h4 class="rc-coll-card__name">{{ ws.name }}</h4>
            <div class="rc-coll-card__foot">
              <span class="rc-coll-card__meta">{{ ws.paper_count ?? 0 }} papers</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="rc-coll-card__arrow" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>
        </div>

        <!-- Subscription Collections -->
        <div class="rc-section">
          <div class="rc-section__head">
            <p class="rc-eyebrow">Subscriptions</p>
            <button type="button" class="rc-new-btn" @click="showSubscriptionForm = !showSubscriptionForm">
              {{ showSubscriptionForm ? '×' : '+' }}
            </button>
          </div>
          <transition name="form-drop">
            <div v-if="showSubscriptionForm" class="rc-form">
              <input v-model="subscriptionName" type="text" class="rc-form__input" placeholder="AI safety signals" >
              <textarea v-model="subscriptionDescription" rows="2" class="rc-form__input rc-form__input--area" placeholder="Describe this feed cluster…" />
              <div class="rc-feed-picker">
                <label v-for="feed in feedCatalog.slice(0, 8)" :key="feed.id" class="rc-feed-opt">
                  <input v-model="selectedFeedIds" type="checkbox" :value="feed.id" >
                  <span>{{ feed.name }}</span>
                </label>
                <p v-if="!feedCatalog.length" class="rc-muted">No feeds configured yet.</p>
              </div>
              <button type="button" class="rc-form__submit" :disabled="!subscriptionName.trim()" @click="createSubscriptionCollection">
                Create subscription
              </button>
            </div>
          </transition>
          <button
            v-for="sc in subscriptionCollections"
            :key="sc.id"
            type="button"
            class="rc-coll-card"
            :class="{ 'rc-coll-card--active': activeCollectionId === sc.id }"
            @click="selectCollection(sc.id)"
          >
            <p class="rc-coll-card__kind rc-coll-card__kind--gold">SUBSCRIPTION</p>
            <h4 class="rc-coll-card__name">{{ sc.name }}</h4>
            <div class="rc-coll-card__foot">
              <span class="rc-coll-card__meta">{{ sc.paper_count ?? 0 }} papers</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="rc-coll-card__arrow" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>
        </div>

        <!-- Paper Groups -->
        <div class="rc-section">
          <div class="rc-section__head">
            <p class="rc-eyebrow">Paper Groups</p>
            <button type="button" class="rc-new-btn" @click="showGroupForm = !showGroupForm">
              {{ showGroupForm ? '×' : '+' }}
            </button>
          </div>
          <transition name="form-drop">
            <div v-if="showGroupForm" class="rc-form">
              <input v-model="groupName" type="text" class="rc-form__input" placeholder="Week 3 screening set" >
              <p class="rc-muted">
                Parent: <strong>{{ createGroupParent?.name || 'Select a workspace first' }}</strong>
              </p>
              <button type="button" class="rc-form__submit" :disabled="!groupName.trim() || !createGroupParent" @click="createPaperGroup">
                Create group
              </button>
            </div>
          </transition>
          <button
            v-for="pg in visiblePaperGroups"
            :key="pg.id"
            type="button"
            class="rc-coll-card rc-coll-card--group"
            :class="{ 'rc-coll-card--active': activeCollectionId === pg.id }"
            @click="selectCollection(pg.id)"
          >
            <p class="rc-coll-card__kind rc-coll-card__kind--ink">PAPER GROUP</p>
            <h4 class="rc-coll-card__name">{{ pg.name }}</h4>
            <div class="rc-coll-card__foot">
              <span class="rc-coll-card__meta">{{ collectionMap.get(pg.parent_collection_id || '')?.name || 'Standalone' }}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="rc-coll-card__arrow" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
              </svg>
            </div>
          </button>
        </div>
      </div>

      <!-- New thread CTA at bottom -->
      <div class="rc-left__foot">
        <button type="button" class="rc-cta-btn" :disabled="!activeCollection" @click="createFreshThread">
          New Thread
        </button>
      </div>
    </aside>

    <!-- ── Center: Chat ────────────────────────────────────────────────────── -->
    <main class="rc-center">
      <template v-if="activeCollection">
        <!-- Header -->
        <header class="rc-center__header">
          <div>
            <h2 class="rc-center__title">{{ activeCollection.name }}</h2>
            <p class="rc-center__subtitle">{{ kindMonoLabel(activeCollection.kind) }} · {{ activeCollectionPapers.length }} papers indexed</p>
          </div>
          <div class="rc-center__actions">
            <!-- Thread tabs -->
            <div v-if="threads.length > 1" class="rc-thread-tabs">
              <button
                v-for="thread in threads.slice(0, 5)"
                :key="thread.id"
                type="button"
                class="rc-thread-tab"
                :class="{ 'rc-thread-tab--active': activeThreadId === thread.id }"
                @click="activeThreadId = thread.id"
              >
                {{ thread.title || 'Thread' }}
              </button>
            </div>
            <button type="button" class="rc-ghost-btn" :disabled="syncing" @click="syncActiveCollection">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rc-spin': syncing }" aria-hidden="true">
                <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
              </svg>
              {{ syncing ? 'Syncing…' : 'Sync' }}
            </button>
          </div>
        </header>

        <!-- Divider line like design ref -->
        <div class="rc-divider" />

        <!-- Messages area -->
        <div class="rc-messages">
          <!-- Loading -->
          <div v-if="loadingContext" class="rc-state-center">
            <div class="rc-dots">
              <span /><span /><span />
            </div>
          </div>

          <!-- Empty with suggestions -->
          <div v-else-if="!messages.length" class="rc-state-center">
            <div class="rc-empty">
              <div class="rc-empty__eyebrow-row">
                <span class="rc-empty__line" />
                <p class="rc-eyebrow rc-eyebrow--teal">Start a Conversation</p>
              </div>
              <h3 class="rc-empty__heading">What do you want to know about<br ><em>{{ activeCollection.name }}</em>?</h3>
              <div class="rc-suggestions">
                <button
                  v-for="q in suggestedQuestions(activeCollection.kind)"
                  :key="q"
                  type="button"
                  class="rc-suggestion"
                  @click="handleSuggestedQuestion(q)"
                >
                  <span class="rc-suggestion__arrow">→</span>
                  <span>{{ q }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Message list -->
          <transition-group v-else name="msg" tag="div" class="rc-msg-list">
            <div
              v-for="msg in messages"
              :key="msg.id"
              class="rc-msg"
              :class="msg.role === 'user' ? 'rc-msg--user' : 'rc-msg--ai'"
            >
              <!-- User message card -->
              <div v-if="msg.role === 'user'" class="rc-msg__user-card">
                <p class="rc-msg__role-label">YOU</p>
                <p class="rc-msg__user-text">{{ msg.content }}</p>
              </div>

              <!-- AI message card -->
              <div v-else class="rc-msg__ai-card">
                <div class="rc-msg__ai-header">
                  <span class="rc-msg__line" />
                  <p class="rc-eyebrow rc-eyebrow--teal">Kaleidoscope</p>
                  <time class="rc-msg__time">{{ formatTimestamp(msg.created_at) }}</time>
                </div>
                <!-- Rendered answer -->
                <!-- eslint-disable-next-line vue/no-v-html -->
                <div v-if="renderedMessages[msg.id]" class="rc-msg__body ks-prose" v-html="renderedMessages[msg.id]" />
                <div v-else-if="msg.content" class="rc-msg__body rc-msg__body--plain">
                  {{ msg.content }}
                </div>

                <!-- Sources -->
                <div v-if="sourceCount(msg) > 0" class="rc-sources">
                  <button type="button" class="rc-sources__toggle" @click="toggleSources(msg.id)">
                    <svg
                      width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"
                      :class="{ 'rc-caret--open': expandedSources[msg.id] }"
                      class="rc-caret"
                      aria-hidden="true"
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                    {{ sourceCount(msg) }} cited source{{ sourceCount(msg) > 1 ? 's' : '' }}
                  </button>
                  <div v-if="expandedSources[msg.id]" class="rc-sources__list">
                    <div v-for="(src, i) in msg.sources?.items ?? []" :key="i" class="rc-source-item">
                      <span class="rc-source-item__idx">[{{ i + 1 }}]</span>
                      <div>
                        <p v-if="src.section_title || src.title" class="rc-source-item__title">
                          {{ src.section_title || src.title }}
                        </p>
                        <p v-if="src.text_snippet || src.text || src.content" class="rc-source-item__snippet">
                          {{ src.text_snippet || src.text || src.content }}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </transition-group>

          <!-- AI thinking indicator -->
          <div v-if="sending" class="rc-msg rc-msg--ai">
            <div class="rc-msg__ai-card">
              <div class="rc-msg__ai-header">
                <span class="rc-msg__line" />
                <p class="rc-eyebrow rc-eyebrow--teal">Kaleidoscope</p>
              </div>
              <div class="rc-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>

          <div ref="messagesEnd" />
        </div>

        <!-- Input bar -->
        <div class="rc-composer">
          <form class="rc-composer__form" @submit.prevent="sendMessage">
            <div class="rc-composer__inner" :class="{ 'rc-composer__inner--focused': inputFocused }">
              <input
                v-model="chatInput"
                type="text"
                class="rc-composer__input"
                :placeholder="`Ask about ${activeCollection.name}…`"
                :disabled="sending || loadingContext"
                aria-label="Send a message"
                @focus="inputFocused = true"
                @blur="inputFocused = false"
                @keydown.enter.prevent="sendMessage"
              >
              <button
                type="submit"
                class="rc-composer__send"
                :class="{ 'rc-composer__send--active': chatInput.trim() && !sending }"
                :disabled="sending || !chatInput.trim() || !activeThread"
                aria-label="Send"
              >
                <svg v-if="!sending" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                </svg>
                <span v-else class="rc-spinner" />
              </button>
            </div>
          </form>
          <p class="rc-composer__hint">Press Enter to send · {{ activeCollection.paper_count ?? activeCollectionPapers.length }} papers available</p>
        </div>
      </template>

      <!-- No collection selected -->
      <div v-else class="rc-state-center">
        <div class="rc-no-coll">
          <div class="rc-empty__eyebrow-row">
            <span class="rc-empty__line" />
            <p class="rc-eyebrow rc-eyebrow--teal">Research Chat</p>
          </div>
          <h3 class="rc-empty__heading">Select a research space<br >to start the conversation.</h3>
          <p class="rc-muted">Create a workspace, subscription collection, or paper group from the left panel.</p>
        </div>
      </div>
    </main>

    <!-- ── Right panel: Context ────────────────────────────────────────────── -->
    <aside class="rc-right">
      <template v-if="activeCollection">
        <!-- Featured collection header -->
        <section class="rc-right__hero">
          <div class="rc-eyebrow-row">
            <span class="rc-eyebrow-line" />
            <p class="rc-eyebrow rc-eyebrow--teal">{{ kindLabel(activeCollection.kind) }}</p>
          </div>
          <h1 class="rc-right__title">{{ activeCollection.name }}</h1>
          <div v-if="activeCollection.description" class="rc-right__desc-wrap">
            <div class="rc-right__desc-bar" />
            <p class="rc-right__desc">{{ activeCollection.description }}</p>
          </div>
        </section>

        <!-- Stats grid -->
        <section class="rc-stats-grid">
          <div class="rc-stats-grid__cell">
            <p class="rc-stats-grid__label">Papers</p>
            <p class="rc-stats-grid__value">{{ activeCollectionPapers.length }}</p>
          </div>
          <div class="rc-stats-grid__cell">
            <p class="rc-stats-grid__label">Threads</p>
            <p class="rc-stats-grid__value">{{ threads.length }}</p>
          </div>
          <div class="rc-stats-grid__cell rc-stats-grid__cell--last">
            <p class="rc-stats-grid__label">Kind</p>
            <p class="rc-stats-grid__value rc-stats-grid__value--gold">{{ kindLabel(activeCollection.kind) }}</p>
          </div>
        </section>

        <!-- Feeds (subscription) -->
        <section v-if="activeCollection.kind === 'subscription_collection'" class="rc-right__section">
          <p class="rc-eyebrow">Attached Feeds</p>
          <ul class="rc-right__list">
            <li v-for="feed in collectionFeeds" :key="feed.id" class="rc-right__list-item">
              <strong>{{ feed.feed_name || feed.feed_id }}</strong>
              <small v-if="feed.publisher">{{ feed.publisher }}</small>
            </li>
            <li v-if="!collectionFeeds.length" class="rc-muted">No feeds attached yet.</li>
          </ul>
        </section>

        <!-- Add papers (paper group) -->
        <section v-if="activeCollection.kind === 'paper_group'" class="rc-right__section">
          <p class="rc-eyebrow">Populate from Parent</p>
          <p class="rc-muted">Select papers from the parent collection.</p>
          <div class="rc-paper-picker">
            <label v-for="paper in parentCollectionPapers.slice(0, 8)" :key="paper.id" class="rc-paper-opt">
              <input v-model="selectedParentPaperIds" type="checkbox" :value="paper.id" >
              <span>{{ paper.title }}</span>
            </label>
            <p v-if="!parentCollectionPapers.length" class="rc-muted">Parent has no papers yet.</p>
          </div>
          <button
            v-if="parentCollectionPapers.length"
            type="button"
            class="rc-add-btn"
            :disabled="!selectedParentPaperIds.length"
            @click="addSelectedParentPapersToGroup"
          >
            Add {{ selectedParentPaperIds.length || '' }} selected
          </button>
        </section>

        <!-- Actions -->
        <section class="rc-right__actions">
          <button type="button" class="rc-action-link" @click="createFreshThread">
            <span>New Thread</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
          <button type="button" class="rc-action-link" :disabled="syncing" @click="syncActiveCollection">
            <span>{{ syncing ? 'Syncing…' : 'Trigger Sync' }}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" :class="{ 'rc-spin': syncing }" aria-hidden="true">
              <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
          </button>
        </section>

        <!-- Current papers -->
        <section class="rc-right__section">
          <p class="rc-eyebrow">Papers in Collection</p>
          <ul class="rc-right__list">
            <li v-for="paper in activeCollectionPapers.slice(0, 10)" :key="paper.id" class="rc-right__list-item">
              <strong>{{ paper.title }}</strong>
              <small>{{ paper.venue || paper.published_at || '' }}</small>
            </li>
            <li v-if="!activeCollectionPapers.length" class="rc-muted">No papers yet.</li>
          </ul>
          <p v-if="activeCollectionPapers.length > 10" class="rc-muted" style="margin-top:8px">
            +{{ activeCollectionPapers.length - 10 }} more papers
          </p>
        </section>
      </template>

      <div v-else class="rc-right__placeholder">
        <p class="rc-muted">Select a collection to see its context.</p>
      </div>
    </aside>
  </div>
</template>

<style scoped>
/* ── Design tokens ─────────────────────────────────────────────────────────── */
.rc-shell {
  /* Color system matching search.html */
  --rc-primary: #00595c;
  --rc-primary-dark: #004043;
  --rc-tertiary: #654c09;
  --rc-tertiary-fixed: #ffdf9c;
  --rc-tertiary-dim: #e5c276;
  --rc-surface: #f9f9f6;
  --rc-surface-container: #eeeeeb;
  --rc-surface-container-high: #e8e8e5;
  --rc-surface-container-highest: #e2e3e0;
  --rc-surface-white: #ffffff;
  --rc-outline: rgba(110, 121, 121, 0.25);
  --rc-outline-solid: #bec9c9;
  --rc-on-surface: #1a1c1b;
  --rc-on-surface-variant: #3e4949;
  --rc-slate-400: #94a3b8;
  --rc-slate-500: #64748b;
  --rc-error: #ba1a1a;

  /* Typography — map to app vars */
  --rc-headline: var(--font-display, "Newsreader", "Playfair Display", serif);
  --rc-body: var(--font-serif, "Noto Serif", "Source Serif Pro", serif);
  --rc-label: var(--font-sans, "Inter", sans-serif);
  --rc-mono: var(--font-mono, "JetBrains Mono", monospace);

  /* Layout */
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr) 400px;
  height: 100vh;
  overflow: hidden;
  background: var(--rc-surface);
  font-family: var(--rc-body);
  color: var(--rc-on-surface);
}

/* ── Shared utilities ──────────────────────────────────────────────────────── */
.rc-eyebrow {
  font-family: var(--rc-label);
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--rc-slate-500);
  margin: 0;
}

.rc-eyebrow--teal {
  color: var(--rc-primary);
  font-weight: 700;
}

.rc-muted {
  font-family: var(--rc-label);
  font-size: 12px;
  color: var(--rc-slate-500);
  margin: 0;
}

.rc-divider {
  height: 1px;
  background: rgba(110, 121, 121, 0.15);
  flex-shrink: 0;
}

.rc-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 0;
}

.rc-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--rc-primary);
  opacity: 0.4;
  animation: dot-pulse 1.2s ease-in-out infinite;
}

.rc-dots span:nth-child(2) { animation-delay: 0.2s; }
.rc-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-pulse {
  0%, 80%, 100% { transform: scale(1); opacity: 0.35; }
  40% { transform: scale(1.25); opacity: 1; }
}

/* ── Left panel ────────────────────────────────────────────────────────────── */
.rc-left {
  display: flex;
  flex-direction: column;
  background: var(--rc-surface-container);
  border-right: 1px solid var(--rc-outline);
  overflow: hidden;
}

.rc-left__top {
  padding: 24px 20px 16px;
  border-bottom: 1px solid var(--rc-outline);
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-shrink: 0;
}

.rc-search-row {
  position: relative;
}

.rc-search-input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--rc-outline-solid);
  padding: 8px 28px 8px 0;
  font-family: var(--rc-body);
  font-style: italic;
  font-size: 14px;
  color: var(--rc-primary);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.rc-search-input:focus {
  border-bottom-color: var(--rc-tertiary-dim);
}

.rc-search-input::placeholder {
  color: var(--rc-slate-400);
  font-style: italic;
}

.rc-search-icon {
  position: absolute;
  right: 0;
  top: 8px;
  color: var(--rc-primary);
  opacity: 0.45;
  pointer-events: none;
}

.rc-error {
  margin: 8px 16px;
  padding: 8px 10px;
  background: rgba(186, 26, 26, 0.06);
  border-left: 3px solid var(--rc-error);
  font-family: var(--rc-label);
  font-size: 11px;
  color: var(--rc-error);
  flex-shrink: 0;
}

.rc-left__list {
  flex: 1;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 121, 121, 0.2) transparent;
  display: flex;
  flex-direction: column;
}

.rc-section {
  padding: 16px 20px 8px;
  border-bottom: 1px solid var(--rc-outline);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rc-section__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.rc-new-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: 1px solid var(--rc-outline-solid);
  color: var(--rc-primary);
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  border-radius: 2px;
}

.rc-new-btn:hover {
  background: rgba(0, 89, 92, 0.08);
  border-color: var(--rc-primary);
}

/* Collection cards — like paper cards in search.html */
.rc-coll-card {
  width: 100%;
  text-align: left;
  background: var(--rc-surface-white);
  border: 1px solid rgba(190, 201, 201, 0.15);
  border-radius: 2px;
  padding: 12px 14px;
  cursor: pointer;
  transition: border-color 0.2s;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rc-coll-card:hover {
  border-color: var(--rc-primary);
}

.rc-coll-card--active {
  background: var(--rc-surface-container-highest);
  border-left: 4px solid var(--rc-primary);
  border-color: var(--rc-primary);
}

.rc-coll-card--group {
  margin-left: 10px;
}

.rc-coll-card__kind {
  font-family: var(--rc-mono);
  font-size: 9px;
  color: var(--rc-primary);
  margin: 0;
  letter-spacing: 0.04em;
}

.rc-coll-card__kind--gold { color: var(--rc-tertiary); }
.rc-coll-card__kind--ink { color: #3949ab; }

.rc-coll-card__name {
  margin: 0;
  font-family: var(--rc-body);
  font-weight: 700;
  font-size: 13px;
  line-height: 1.3;
  color: var(--rc-on-surface);
}

.rc-coll-card:hover .rc-coll-card__name,
.rc-coll-card--active .rc-coll-card__name {
  color: var(--rc-primary);
}

.rc-coll-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2px;
}

.rc-coll-card__meta {
  font-family: var(--rc-label);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rc-slate-400);
}

.rc-coll-card__arrow {
  color: var(--rc-slate-400);
  transition: color 0.15s;
  flex-shrink: 0;
}

.rc-coll-card:hover .rc-coll-card__arrow {
  color: var(--rc-primary);
}

.rc-loading {
  font-family: var(--rc-label);
  font-size: 11px;
  color: var(--rc-slate-400);
  padding: 4px 0;
}

/* Inline create forms */
.rc-form {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid var(--rc-outline);
  border-radius: 2px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 4px;
}

.rc-form__input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--rc-outline-solid);
  padding: 6px 0;
  font-family: var(--rc-body);
  font-size: 13px;
  color: var(--rc-on-surface);
  outline: none;
  resize: vertical;
  box-sizing: border-box;
  transition: border-color 0.15s;
}

.rc-form__input:focus {
  border-bottom-color: var(--rc-primary);
}

.rc-form__input--area {
  min-height: 48px;
}

.rc-form__submit {
  background: var(--rc-primary);
  color: white;
  border: none;
  padding: 10px 16px;
  font-family: var(--rc-label);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  border-radius: 0;
}

.rc-form__submit:hover:not(:disabled) {
  background: var(--rc-primary-dark);
}

.rc-form__submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.rc-feed-picker {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-height: 120px;
  overflow-y: auto;
}

.rc-feed-opt {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--rc-label);
  font-size: 11px;
  color: var(--rc-on-surface-variant);
  cursor: pointer;
}

/* Bottom CTA */
.rc-left__foot {
  padding: 16px 20px;
  border-top: 1px solid var(--rc-outline);
  background: rgba(232, 232, 229, 0.5);
  flex-shrink: 0;
}

.rc-cta-btn {
  width: 100%;
  background: var(--rc-primary);
  color: white;
  border: none;
  padding: 14px;
  font-family: var(--rc-label);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  cursor: pointer;
  transition: background 0.18s;
  border-radius: 0;
}

.rc-cta-btn:hover:not(:disabled) {
  background: var(--rc-primary-dark);
}

.rc-cta-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* ── Center panel ──────────────────────────────────────────────────────────── */
.rc-center {
  display: flex;
  flex-direction: column;
  background: var(--rc-surface);
  overflow: hidden;
  position: relative;
}

.rc-center__header {
  padding: 28px 36px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.rc-center__title {
  margin: 0;
  font-family: var(--rc-headline);
  font-size: 28px;
  font-weight: 700;
  font-style: italic;
  letter-spacing: -0.02em;
  line-height: 1.05;
  color: var(--rc-primary);
}

.rc-center__subtitle {
  margin: 6px 0 0;
  font-family: var(--rc-mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--rc-slate-400);
}

.rc-center__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.rc-thread-tabs {
  display: flex;
  gap: 4px;
}

.rc-thread-tab {
  padding: 5px 10px;
  border: 1px solid var(--rc-outline-solid);
  background: transparent;
  border-radius: 0;
  font-family: var(--rc-label);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--rc-slate-500);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.rc-thread-tab:hover,
.rc-thread-tab--active {
  border-color: var(--rc-primary);
  color: var(--rc-primary);
  background: rgba(0, 89, 92, 0.04);
}

.rc-ghost-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--rc-outline-solid);
  background: transparent;
  font-family: var(--rc-label);
  font-size: 9px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--rc-slate-500);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
  border-radius: 0;
}

.rc-ghost-btn:hover:not(:disabled) {
  border-color: var(--rc-primary);
  color: var(--rc-primary);
}

.rc-ghost-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Messages */
.rc-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 28px 36px;
  display: flex;
  flex-direction: column;
  gap: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 121, 121, 0.18) transparent;
}

/* State center (empty / loading) */
.rc-state-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}

.rc-empty {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 460px;
}

.rc-empty__eyebrow-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.rc-empty__line {
  display: block;
  width: 40px;
  height: 1px;
  background: var(--rc-primary);
}

.rc-empty__heading {
  margin: 0;
  font-family: var(--rc-headline);
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--rc-on-surface);
}

.rc-empty__heading em {
  color: var(--rc-primary);
}

.rc-suggestions {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin-top: 4px;
}

.rc-suggestion {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid var(--rc-outline);
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
  text-align: left;
  cursor: pointer;
  font-family: var(--rc-body);
  font-size: 14px;
  color: var(--rc-on-surface-variant);
  transition: color 0.16s;
}

.rc-suggestion__arrow {
  font-family: var(--rc-mono);
  font-size: 13px;
  color: var(--rc-tertiary);
  transition: transform 0.16s;
}

.rc-suggestion:hover {
  color: var(--rc-primary);
}

.rc-suggestion:hover .rc-suggestion__arrow {
  transform: translateX(3px);
}

.rc-no-coll {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 400px;
  text-align: left;
}

/* Message list */
.rc-msg-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rc-msg {}

.rc-msg--user {
  display: flex;
  justify-content: flex-end;
}

.rc-msg--ai {
  display: flex;
  justify-content: flex-start;
}

/* User message card */
.rc-msg__user-card {
  max-width: 68%;
  background: var(--rc-surface-container-highest);
  border-left: 4px solid var(--rc-primary);
  padding: 14px 18px;
  border-radius: 0;
}

.rc-msg__role-label {
  font-family: var(--rc-mono);
  font-size: 9px;
  color: var(--rc-primary);
  margin: 0 0 6px;
  letter-spacing: 0.08em;
}

.rc-msg__user-text {
  margin: 0;
  font-family: var(--rc-body);
  font-size: 14px;
  line-height: 1.6;
  color: var(--rc-on-surface);
  word-break: break-word;
}

/* AI message card */
.rc-msg__ai-card {
  max-width: 82%;
  background: var(--rc-surface-white);
  border: 1px solid rgba(190, 201, 201, 0.15);
  border-radius: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rc-msg__ai-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rc-msg__line {
  display: block;
  width: 28px;
  height: 1px;
  background: var(--rc-primary);
  flex-shrink: 0;
}

.rc-msg__time {
  margin-left: auto;
  font-family: var(--rc-mono);
  font-size: 9px;
  color: var(--rc-slate-400);
  letter-spacing: 0.04em;
}

/* Answer body */
.rc-msg__body.ks-prose {
  max-width: none;
  font-family: var(--rc-body);
  font-size: 14px;
  line-height: 1.75;
  color: var(--rc-on-surface-variant);
}

.rc-msg__body :deep(p:first-child),
.rc-msg__body :deep(ul:first-child),
.rc-msg__body :deep(ol:first-child) { margin-top: 0; }

.rc-msg__body :deep(p:last-child),
.rc-msg__body :deep(ul:last-child),
.rc-msg__body :deep(ol:last-child) { margin-bottom: 0; }

.rc-msg__body :deep(p),
.rc-msg__body :deep(li) { color: var(--rc-on-surface-variant); }

.rc-msg__body :deep(code) {
  font-family: var(--rc-mono);
  font-size: 0.85em;
  background: var(--rc-surface-container);
  padding: 1px 4px;
}

.rc-msg__body--plain {
  font-family: var(--rc-body);
  font-size: 14px;
  line-height: 1.7;
  color: var(--rc-on-surface-variant);
  white-space: pre-wrap;
  word-break: break-word;
}

/* Sources */
.rc-sources {
  border-top: 1px solid var(--rc-outline);
  padding-top: 8px;
}

.rc-sources__toggle {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  padding: 0;
  font-family: var(--rc-label);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--rc-slate-500);
  cursor: pointer;
  transition: color 0.15s;
}

.rc-sources__toggle:hover { color: var(--rc-primary); }

.rc-caret {
  transition: transform 0.18s ease;
}

.rc-caret--open {
  transform: rotate(180deg);
}

.rc-sources__list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 8px;
  border-left: 2px solid rgba(0, 89, 92, 0.15);
}

.rc-source-item {
  display: flex;
  gap: 10px;
}

.rc-source-item__idx {
  font-family: var(--rc-mono);
  font-size: 9px;
  font-weight: 700;
  color: var(--rc-primary);
  flex-shrink: 0;
  padding-top: 2px;
}

.rc-source-item__title {
  margin: 0 0 3px;
  font-family: var(--rc-label);
  font-size: 11px;
  font-weight: 600;
  color: var(--rc-on-surface);
}

.rc-source-item__snippet {
  margin: 0;
  font-family: var(--rc-body);
  font-size: 12px;
  line-height: 1.5;
  color: var(--rc-slate-500);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ── Input / Composer ──────────────────────────────────────────────────────── */
.rc-composer {
  flex-shrink: 0;
  padding: 16px 36px 20px;
  border-top: 1px solid var(--rc-outline);
  background: var(--rc-surface);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rc-composer__form {
  width: 100%;
}

.rc-composer__inner {
  display: flex;
  align-items: center;
  gap: 0;
  border-bottom: 2px solid var(--rc-outline-solid);
  transition: border-color 0.2s;
}

.rc-composer__inner--focused {
  border-bottom-color: var(--rc-primary);
}

.rc-composer__input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  padding: 12px 0;
  font-family: var(--rc-body);
  font-style: italic;
  font-size: 15px;
  color: var(--rc-primary);
}

.rc-composer__input::placeholder {
  color: var(--rc-slate-400);
  font-style: italic;
}

.rc-composer__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rc-composer__send {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--rc-slate-400);
  cursor: pointer;
  transition: color 0.15s;
  flex-shrink: 0;
}

.rc-composer__send--active {
  color: var(--rc-primary);
}

.rc-composer__send:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.rc-spinner {
  width: 13px;
  height: 13px;
  border: 1.5px solid rgba(0, 89, 92, 0.25);
  border-top-color: var(--rc-primary);
  border-radius: 50%;
  animation: rc-spin 0.55s linear infinite;
}

@keyframes rc-spin {
  to { transform: rotate(360deg); }
}

.rc-composer__hint {
  font-family: var(--rc-label);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--rc-slate-400);
  margin: 0;
}

/* ── Right panel ───────────────────────────────────────────────────────────── */
.rc-right {
  background: var(--rc-surface-white);
  border-left: 1px solid var(--rc-outline);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(110, 121, 121, 0.18) transparent;
  display: flex;
  flex-direction: column;
}

.rc-right__hero {
  padding: 36px 32px 24px;
  border-bottom: 1px solid var(--rc-outline);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rc-eyebrow-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rc-eyebrow-line {
  display: block;
  width: 40px;
  height: 1px;
  background: var(--rc-tertiary);
  flex-shrink: 0;
}

.rc-right__title {
  margin: 0;
  font-family: var(--rc-headline);
  font-size: 32px;
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.02em;
  color: var(--rc-on-surface);
}

.rc-right__desc-wrap {
  position: relative;
  padding-left: 18px;
}

.rc-right__desc-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(101, 76, 9, 0.2);
}

.rc-right__desc {
  margin: 0;
  font-family: var(--rc-body);
  font-size: 13px;
  line-height: 1.65;
  color: var(--rc-on-surface-variant);
  font-style: italic;
}

/* Stats grid like search.html */
.rc-stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-bottom: 1px solid var(--rc-outline);
  flex-shrink: 0;
}

.rc-stats-grid__cell {
  padding: 20px 16px;
  text-align: center;
  border-right: 1px solid var(--rc-outline);
}

.rc-stats-grid__cell--last {
  border-right: none;
}

.rc-stats-grid__label {
  font-family: var(--rc-label);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--rc-slate-400);
  margin: 0 0 4px;
}

.rc-stats-grid__value {
  font-family: var(--rc-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--rc-primary);
  margin: 0;
}

.rc-stats-grid__value--gold {
  color: var(--rc-tertiary);
  font-size: 13px;
  margin-top: 4px;
}

/* Right sections */
.rc-right__section {
  padding: 20px 32px;
  border-bottom: 1px solid var(--rc-outline);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rc-right__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rc-right__list-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rc-right__list-item strong {
  font-family: var(--rc-body);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--rc-on-surface);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rc-right__list-item small {
  font-family: var(--rc-mono);
  font-size: 9px;
  color: var(--rc-slate-400);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Paper picker */
.rc-paper-picker {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rc-paper-opt {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: start;
  cursor: pointer;
}

.rc-paper-opt span {
  font-family: var(--rc-body);
  font-size: 12px;
  line-height: 1.4;
  color: var(--rc-on-surface);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rc-add-btn {
  align-self: flex-start;
  padding: 8px 14px;
  background: var(--rc-primary);
  color: white;
  border: none;
  font-family: var(--rc-label);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  border-radius: 0;
}

.rc-add-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Actions links like search.html */
.rc-right__actions {
  padding: 8px 32px;
  border-bottom: 1px solid var(--rc-outline);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.rc-action-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border: none;
  border-bottom: 1px solid rgba(101, 76, 9, 0.2);
  background: none;
  cursor: pointer;
  font-family: var(--rc-label);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--rc-tertiary);
  transition: color 0.15s;
}

.rc-action-link:last-child {
  border-bottom: none;
}

.rc-action-link:hover:not(:disabled) {
  color: var(--rc-primary);
}

.rc-action-link:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.rc-action-link svg {
  transition: transform 0.15s;
}

.rc-action-link:hover:not(:disabled) svg {
  transform: translateX(3px);
}

.rc-right__placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 32px;
  text-align: center;
}

/* ── Animations ────────────────────────────────────────────────────────────── */
.rc-spin {
  animation: rc-spin 1s linear infinite;
}

.msg-enter-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.msg-leave-active {
  transition: opacity 0.15s ease;
  position: absolute;
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.msg-leave-to {
  opacity: 0;
}

.msg-move {
  transition: transform 0.22s ease;
}

.form-drop-enter-active,
.form-drop-leave-active {
  transition: opacity 0.18s, transform 0.18s;
  overflow: hidden;
}

.form-drop-enter-from,
.form-drop-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}

/* ── Responsive ────────────────────────────────────────────────────────────── */
@media (max-width: 1280px) {
  .rc-shell {
    grid-template-columns: 260px minmax(0, 1fr) 320px;
  }
}

@media (max-width: 1024px) {
  .rc-shell {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 100vh;
    overflow: auto;
  }

  .rc-left,
  .rc-right {
    height: auto;
  }

  .rc-center {
    min-height: 80vh;
  }

  .rc-messages {
    min-height: 360px;
  }

  .rc-msg__user-card,
  .rc-msg__ai-card {
    max-width: 96%;
  }
}
</style>

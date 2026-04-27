/**
 * useTranslation — Bilingual (EN / ZH) support for Kaleidoscope.
 *
 * - Provides a global reactive `locale` (default: 'en').
 * - When locale === 'zh', auto-translates paper titles (shown as small subtitle).
 * - On-demand abstract translation via a small button.
 * - Uses the external LLM translation API.
 */
import { withKaleidoscopeApiKeyHeaders } from "../utils/apiKey";

// ─── Shared singleton state ─────────────────────────────────
const locale = ref<"en" | "zh">("en");
const translationCache = reactive<Map<string, string>>(new Map());
const pendingKeys = reactive<Set<string>>(new Set());
const errorKeys = reactive<Set<string>>(new Set());
const pendingPromises = new Map<string, Promise<string>>();

// ─── LocalStorage persistence ───────────────────────────────
let _localeInitialized = false;
function _initLocale() {
  if (_localeInitialized) return;
  _localeInitialized = true;
  if (import.meta.client) {
    try {
      const stored = localStorage.getItem("ks-locale");
      if (stored === "zh" || stored === "en") {
        locale.value = stored;
      }
    } catch {
      // Ignore storage access failures in restricted browser contexts.
    }
    // Watch for changes and persist
    watch(locale, (v) => {
      try {
        localStorage.setItem("ks-locale", v);
      } catch {
        // Ignore storage write failures in restricted browser contexts.
      }
    });
  }
}

// ─── API constants ──────────────────────────────────────────
// Translation is proxied through the backend — no API key in client code.
const TRANSLATE_ENDPOINT = "/api/v1/translate";

// ─── UI labels ──────────────────────────────────────────────
export const UI_LABELS = {
  en: {
    // Sidebar sections
    home: "HOME",
    explore: "EXPLORE",
    research: "RESEARCH",
    create: "CREATE",
    developer: "DEVELOPER",
    // Sidebar items
    dashboard: "Dashboard",
    discover: "Discovery Explorer",
    search: "Search",
    insights: "Insights",
    workspaces: "Workspaces",
    evidenceLab: "Evidence Lab",
    synthesis: "Synthesis",
    writing: "Writing",
    knowledge: "Knowledge Garden",
    admin: "Admin Console",
    settings: "Settings",
    collections: "Collections",
    subscriptions: "Subscriptions",
    apiDocs: "API Docs",
    // DeepXiv
    deepxiv: "DeepXiv",
    deepxivSearch: "arXiv Search",
    deepxivTrending: "Trending Papers",
    deepxivReader: "Paper Reader",
    deepxivAgent: "Research Agent",
    deepxivPmc: "PMC Papers",
    // Topbar
    notifications: "Notifications",
    markAllRead: "Mark all read",
    profile: "Profile",
    myWorkspaces: "My Workspaces",
    darkMode: "Dark Mode",
    lightMode: "Light Mode",
    signOut: "Sign Out",
    searchPlaceholder: "Search papers, claims, authors…",
    language: "Language",
    switchToChinese: "切换为中文",
    switchToEnglish: "Switch to English",
    // Translation
    translateAbstract: "Translate",
    translating: "Translating…",
    translated: "Translated",
    hideTranslation: "Hide translation",
    showTranslation: "Show translation",
    // Paper actions
    readPaper: "Read Paper",
    save: "Save",
    cite: "Cite",
    compare: "Compare",
    // Dashboard
    todaysResearchTheme: "Today's Research Theme",
    recommendedReading: "Recommended Reading",
    forYou: "For You",
    trending: "Trending",
    controversial: "Controversial",
    briefing: "BRIEFING",
    systemMonitor: "SYSTEM MONITOR",
    newPapers: "NEW PAPERS",
    conflicts: "CONFLICTS",
    codeReleases: "CODE RELEASES",
    // Search page
    searchResults: "SEARCH RESULTS",
    keyword: "Keyword",
    semantic: "Semantic",
    claimFirst: "Claim-first",
    resultsIn: "results in",
    clearFilters: "Clear Filters",
    // Knowledge page
    knowledgeGardenSubtitle: "YOUR NOTES",
    editNote: "Edit Note",
    deleteNote: "Delete",
    linkedNotes: "Linked Notes",
    backlinks: "backlinks",
    // Workspaces page
    newWorkspace: "+ New Workspace",
    createNewWorkspace: "Create New Workspace",
    name: "Name",
    description: "Description",
    cancel: "Cancel",
    createBtn: "Create",
    papers: "papers",
    members: "members",
    // Discover page
    featuredCollection: "Featured Collection",
    hotThisMonth: "Hot This Month",
    emerging: "Emerging",
    controversy: "Controversy",
    // Evidence Lab
    evidenceLabSubtitle: "DEEP ANALYSIS",
    // Analytics
    analytics: "Analytics",
    analyticsSubtitle: "LIBRARY INSIGHTS",
    // Synthesis
    synthesisSubtitle: "RESEARCH SYNTHESIS",
    // Writing
    writingSubtitle: "MANUSCRIPT STUDIO",
    // Insights
    insightsSubtitle: "RESEARCH LANDSCAPE",
    // Reader
    readerSubtitle: "READER",
    // Paper Profile
    paperProfile: "Paper Profile",
    relatedPapers: "Related Papers",
    claims: "Claims",
    methodsAndResults: "Methods & Results",
    figures: "Figures",
    reproducibility: "Reproducibility",
    supplements: "Supplements",
    citations: "citations",
    references: "references",
    // Common
    loading: "Loading...",
    close: "Close",
    open: "Open",
    viewAll: "View All",
    noResults: "No results found",
  },
  zh: {
    // Sidebar sections
    home: "首页",
    explore: "探索",
    research: "研究",
    create: "创作",
    developer: "开发者",
    // Sidebar items
    dashboard: "仪表板",
    discover: "发现探索",
    search: "搜索",
    insights: "洞察",
    workspaces: "工作空间",
    evidenceLab: "证据实验室",
    synthesis: "综合分析",
    writing: "写作",
    knowledge: "知识花园",
    admin: "管理控制台",
    settings: "设置",
    collections: "收藏夹",
    subscriptions: "订阅管理",
    apiDocs: "API 文档",
    // DeepXiv
    deepxiv: "DeepXiv",
    deepxivSearch: "arXiv 搜索",
    deepxivTrending: "热门论文",
    deepxivReader: "论文阅读器",
    deepxivAgent: "研究助手",
    deepxivPmc: "PMC 论文",
    // Topbar
    notifications: "通知",
    markAllRead: "全部已读",
    profile: "个人资料",
    myWorkspaces: "我的工作空间",
    darkMode: "深色模式",
    lightMode: "浅色模式",
    signOut: "退出登录",
    searchPlaceholder: "搜索论文、观点、作者…",
    language: "语言",
    switchToChinese: "切换为中文",
    switchToEnglish: "Switch to English",
    // Translation
    translateAbstract: "翻译",
    translating: "翻译中…",
    translated: "已翻译",
    hideTranslation: "隐藏翻译",
    showTranslation: "显示翻译",
    // Paper actions
    readPaper: "阅读论文",
    save: "保存",
    cite: "引用",
    compare: "比较",
    // Dashboard
    todaysResearchTheme: "今日研究主题",
    recommendedReading: "推荐阅读",
    forYou: "为您推荐",
    trending: "热门",
    controversial: "争议",
    briefing: "简报",
    systemMonitor: "系统监控",
    newPapers: "新论文",
    conflicts: "冲突",
    codeReleases: "代码发布",
    // Search page
    searchResults: "搜索结果",
    keyword: "关键词",
    semantic: "语义",
    claimFirst: "声明优先",
    resultsIn: "结果，用时",
    clearFilters: "清除筛选",
    // Knowledge page
    knowledgeGardenSubtitle: "您的笔记",
    editNote: "编辑笔记",
    deleteNote: "删除",
    linkedNotes: "关联笔记",
    backlinks: "条反向链接",
    // Workspaces page
    newWorkspace: "+ 新建工作空间",
    createNewWorkspace: "创建新工作空间",
    name: "名称",
    description: "描述",
    cancel: "取消",
    createBtn: "创建",
    papers: "篇论文",
    members: "位成员",
    // Discover page
    featuredCollection: "精选合集",
    hotThisMonth: "本月热门",
    emerging: "新兴方向",
    controversy: "争议话题",
    // Evidence Lab
    evidenceLabSubtitle: "深度分析",
    // Analytics
    analytics: "数据分析",
    analyticsSubtitle: "文库洞察",
    // Synthesis
    synthesisSubtitle: "研究综合",
    // Writing
    writingSubtitle: "论文写作",
    // Insights
    insightsSubtitle: "研究图景",
    // Reader
    readerSubtitle: "阅读器",
    // Paper Profile
    paperProfile: "论文详情",
    relatedPapers: "相关论文",
    claims: "论证",
    methodsAndResults: "方法与结果",
    figures: "图表",
    reproducibility: "可复现性",
    supplements: "补充材料",
    citations: "次引用",
    references: "篇参考文献",
    // Common
    loading: "加载中…",
    close: "关闭",
    open: "打开",
    viewAll: "查看全部",
    noResults: "未找到结果",
  },
};

// ─── Composable ─────────────────────────────────────────────
export function useTranslation() {
  // Initialize locale from localStorage (only once)
  _initLocale();

  const isZh = computed(() => locale.value === "zh");

  /**
   * Get a UI label in the current locale.
   */
  function t(key: keyof typeof UI_LABELS.en): string {
    return UI_LABELS[locale.value][key] || UI_LABELS.en[key];
  }

  /**
   * Toggle between en ↔ zh.
   */
  function toggleLocale() {
    locale.value = locale.value === "en" ? "zh" : "en";
  }

  /**
   * Set locale explicitly.
   */
  function setLocale(l: "en" | "zh") {
    locale.value = l;
  }

  /**
   * Translate text using the LLM API.
   * Returns cached result immediately if available.
   * Triggers async API call if not cached.
   *
   * @param text - Text to translate
   * @param options - Optional paper_id and field_type for persistence
   */
  async function translate(
    text: string,
    options?: { paperId?: string; fieldType?: "title" | "abstract" },
  ): Promise<string> {
    if (!text || text.length < 2) return text;

    // Cache hit
    const cacheKey = text.slice(0, 200); // Use first 200 chars as key
    if (translationCache.has(cacheKey)) {
      return translationCache.get(cacheKey)!;
    }

    // Already pending — await the same promise instead of returning ""
    if (pendingPromises.has(cacheKey)) {
      return pendingPromises.get(cacheKey)!;
    }

    // Mark pending and start the request
    pendingKeys.add(cacheKey);
    errorKeys.delete(cacheKey);

    const promise = (async () => {
      try {
        // Call backend translate proxy — API key stays server-side
        const config = useRuntimeConfig();
        const apiBase = config.public.apiUrl as string;

        const body: Record<string, unknown> = { text, direction: "en2zh" };
        if (options?.paperId) {
          body.paper_id = options.paperId;
        }
        if (options?.fieldType) {
          body.field_type = options.fieldType;
        }

        const response = await $fetch<{ translated: string; original: string }>(
          `${apiBase}${TRANSLATE_ENDPOINT}`,
          {
            method: "POST",
            body,
            headers: withKaleidoscopeApiKeyHeaders(),
          },
        );

        const translated = response.translated?.trim() || "";
        if (translated) {
          translationCache.set(cacheKey, translated);
        }
        return translated;
      } catch (e) {
        console.error("[useTranslation] API error:", e);
        errorKeys.add(cacheKey);
        return "";
      } finally {
        pendingKeys.delete(cacheKey);
        pendingPromises.delete(cacheKey);
      }
    })();

    pendingPromises.set(cacheKey, promise);
    return promise;
  }

  /**
   * Get the cached translation of a text (non-blocking).
   * Returns undefined if not yet translated.
   */
  function getCached(text: string): string | undefined {
    const cacheKey = text.slice(0, 200);
    return translationCache.get(cacheKey);
  }

  /**
   * Manually set a cached translation (for pre-loading from database).
   */
  function setCached(text: string, translation: string): void {
    const cacheKey = text.slice(0, 200);
    translationCache.set(cacheKey, translation);
  }

  /**
   * Check if a translation is in progress.
   */
  function isPending(text: string): boolean {
    const cacheKey = text.slice(0, 200);
    return pendingKeys.has(cacheKey);
  }

  /**
   * Check if a translation had an error.
   */
  function hasError(text: string): boolean {
    const cacheKey = text.slice(0, 200);
    return errorKeys.has(cacheKey);
  }

  return {
    locale,
    isZh,
    t,
    toggleLocale,
    setLocale,
    translate,
    getCached,
    setCached,
    isPending,
    hasError,
  };
}

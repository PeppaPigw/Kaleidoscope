<script setup lang="ts">
/* eslint-disable vue/html-self-closing */
import {
  AlertTriangle,
  BookOpen,
  Braces,
  CheckCircle2,
  Copy,
  KeyRound,
  Loader2,
  Play,
  RefreshCcw,
  Search,
  Terminal,
  Timer,
  XCircle,
} from "lucide-vue-next";

import {
  createRunnerSeed,
  normalizeOpenApiCatalog,
  type AdminEndpoint,
  type AdminMethod,
  type AdminRunResult,
} from "~/composables/useAdminConsole";
import {
  buildApiHeaders,
  buildApiRequestPath,
  buildCurlCommand,
  createJsonExample,
  formatJsonPreview,
  maskApiKeyForDisplay,
  parseJsonBodyInput,
  parseJsonObjectInput,
  resolveApiRequestUrl,
} from "~/utils/apiDocs";
import { getKaleidoscopeApiKey } from "~/utils/apiKey";

definePageMeta({ layout: "default", apiDocsChrome: true });

type OpenApiCatalog = Parameters<typeof normalizeOpenApiCatalog>[0];
type MethodFilter = "all" | AdminMethod;
type EndpointParameter = AdminEndpoint["parameters"][number];

interface EndpointGroup {
  domain: string;
  endpoints: AdminEndpoint[];
}

const API_DOCS_KEY_STORAGE = "ks-api-docs-api-key";
const METHOD_OPTIONS: MethodFilter[] = [
  "all",
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
];

const API_DOCS_COPY = {
  en: {
    eyebrow: "Developer Surface · Agent-ready JSON APIs",
    title: "API atlas for paper-analysis agents.",
    subtitle:
      "Browse every public route, inspect schemas, fill an API key once, and send real requests from the same control surface.",
    apiKeyLabel: "API Key",
    apiKeyHelp:
      "Sent as X-API-Key for catalog loading and every debugger request.",
    apiKeyPlaceholder: "sk-kaleidoscope",
    baseUrlLabel: "Base URL",
    reloadSchema: "Reload Schema",
    loadingSchema: "Loading Schema",
    schemaReady: "Schema Ready",
    schemaFailed: "Schema Failed",
    catalogTitle: "Endpoint Catalog",
    searchPlaceholder: "Search path, tag, operation…",
    allDomains: "All Domains",
    allMethods: "All",
    endpoints: "Endpoints",
    domains: "Domains",
    jsonFirst: "JSON-first",
    liveDebug: "Live Debug",
    selectedContract: "Selected Contract",
    noEndpoint: "No endpoint selected",
    noEndpointDetail:
      "Load the OpenAPI schema or relax filters to choose an endpoint.",
    operation: "Operation",
    path: "Path",
    domain: "Domain",
    operationId: "Operation ID",
    parameters: "Parameters",
    noParameters:
      "This endpoint declares no path, query, header, or cookie parameters.",
    location: "Location",
    required: "Required",
    schema: "Schema",
    description: "Description",
    requestBody: "Request Body",
    noRequestBody: "No request body is declared for this endpoint.",
    responses: "Responses",
    responseCodes: "Response Codes",
    debugger: "Online Debugger",
    debuggerHint: "Edit JSON inputs, preview cURL, then send a live request.",
    pathParams: "Path Params JSON",
    queryParams: "Query Params JSON",
    bodyJson: "Body JSON",
    sendRequest: "Send Request",
    sending: "Sending",
    resetExample: "Reset Example",
    curlPreview: "cURL Preview",
    copyCurl: "Copy cURL",
    copied: "Copied",
    response: "Response",
    awaitingResponse: "Awaiting a request run.",
    status: "Status",
    duration: "Duration",
    timestamp: "Timestamp",
    requestUrl: "Request URL",
    validJsonRequired: "Runner inputs must be valid JSON before sending.",
    apiKeyRequired: "API key is required before sending a request.",
    safeRoute: "Safe GET route",
    mutatingRoute: "Mutating route",
    streamRoute: "Streaming route",
    manualRoute: "Manual route",
    openApiVersion: "OpenAPI",
  },
  zh: {
    eyebrow: "开发者服务 · 面向 Agent 的 JSON API",
    title: "论文分析的 API 地图。",
    subtitle:
      "在同一页面浏览所有对外路由、查看 schema、顶部填写 API key，并直接发起真实调试请求。",
    apiKeyLabel: "API Key",
    apiKeyHelp: "用于加载目录和调试请求，统一通过 X-API-Key 发送。",
    apiKeyPlaceholder: "sk-kaleidoscope",
    baseUrlLabel: "基础地址",
    reloadSchema: "重新加载 Schema",
    loadingSchema: "加载中",
    schemaReady: "Schema 已就绪",
    schemaFailed: "Schema 加载失败",
    catalogTitle: "接口目录",
    searchPlaceholder: "搜索路径、标签、operation…",
    allDomains: "全部领域",
    allMethods: "全部",
    endpoints: "接口数",
    domains: "领域数",
    jsonFirst: "JSON 优先",
    liveDebug: "在线调试",
    selectedContract: "接口契约",
    noEndpoint: "尚未选择接口",
    noEndpointDetail: "请先加载 OpenAPI schema，或放宽筛选条件后选择接口。",
    operation: "操作",
    path: "路径",
    domain: "领域",
    operationId: "Operation ID",
    parameters: "参数",
    noParameters: "此接口未声明 path、query、header 或 cookie 参数。",
    location: "位置",
    required: "必填",
    schema: "Schema",
    description: "说明",
    requestBody: "请求体",
    noRequestBody: "此接口未声明请求体。",
    responses: "响应",
    responseCodes: "响应码",
    debugger: "在线调试器",
    debuggerHint: "编辑 JSON 输入，预览 cURL，然后发送真实请求。",
    pathParams: "路径参数 JSON",
    queryParams: "查询参数 JSON",
    bodyJson: "请求体 JSON",
    sendRequest: "发送请求",
    sending: "发送中",
    resetExample: "重置示例",
    curlPreview: "cURL 预览",
    copyCurl: "复制 cURL",
    copied: "已复制",
    response: "响应",
    awaitingResponse: "等待发起请求。",
    status: "状态",
    duration: "耗时",
    timestamp: "时间",
    requestUrl: "请求 URL",
    validJsonRequired: "发送前请确保调试输入都是合法 JSON。",
    apiKeyRequired: "发送请求前必须填写 API key。",
    safeRoute: "安全 GET 路由",
    mutatingRoute: "写入/变更路由",
    streamRoute: "流式路由",
    manualRoute: "手动路由",
    openApiVersion: "OpenAPI",
  },
} as const;

const DOMAIN_LABELS = {
  en: {
    admin: "Admin & Operations",
    "agent-acquisition": "Agent Acquisition",
    "agent-citation-intelligence": "Agent Citation Intelligence",
    "agent-external-artifacts": "Agent External Artifacts",
    "agent-monitoring-memory": "Agent Monitoring & Memory",
    "agent-orchestration": "Agent Orchestration",
    "agent-paper-access": "Agent Paper Access",
    "agent-reproducibility-quality": "Agent Reproducibility & Quality",
    "agent-research-output": "Agent Research Output",
    "agent-scientific-extraction": "Agent Scientific Extraction",
    "agent-synthesis-planning": "Agent Synthesis & Planning",
    "agent-topic-intelligence": "Agent Topic Intelligence",
    "agent-visual-artifacts": "Agent Visual Artifacts",
    analytics: "Analytics",
    auth: "Authentication",
    claims: "Claims & Evidence",
    collections: "Collections",
    deepxiv: "DeepXiv Proxy",
    experiments: "Experiments",
    governance: "Governance",
    papers: "Papers",
    ragflow: "RAGFlow Sync",
    search: "Search",
    system: "System",
    trends: "Trends",
  },
  zh: {
    admin: "管理与运维",
    "agent-acquisition": "Agent 论文获取",
    "agent-citation-intelligence": "Agent 引用智能",
    "agent-external-artifacts": "Agent 外部资产",
    "agent-monitoring-memory": "Agent 监控与记忆",
    "agent-orchestration": "Agent 编排",
    "agent-paper-access": "Agent 论文精读",
    "agent-reproducibility-quality": "Agent 复现与质量",
    "agent-research-output": "Agent 科研输出",
    "agent-scientific-extraction": "Agent 科学抽取",
    "agent-synthesis-planning": "Agent 综合与规划",
    "agent-topic-intelligence": "Agent 主题趋势",
    "agent-visual-artifacts": "Agent 图表资产",
    analytics: "分析统计",
    auth: "身份与用户",
    claims: "论证与证据",
    collections: "论文集合",
    deepxiv: "DeepXiv 代理",
    experiments: "实验管理",
    governance: "治理与审计",
    papers: "论文信息",
    ragflow: "RAGFlow 同步",
    search: "搜索检索",
    system: "系统状态",
    trends: "趋势洞察",
  },
} as const;

const API_TERM_ZH: Record<string, string> = {
  acquisition: "获取",
  ablation: "消融",
  ablations: "消融",
  abstract: "摘要",
  algorithm: "算法",
  algorithms: "算法",
  appendix: "附录",
  artifact: "资产",
  artifacts: "资产",
  assumption: "假设",
  assumptions: "假设",
  benchmark: "基准",
  benchmarks: "基准",
  bibliography: "参考文献",
  blog: "博客",
  card: "卡片",
  cards: "卡片",
  chart: "图表",
  charts: "图表",
  checklist: "清单",
  code: "代码",
  community: "社区",
  context: "上下文",
  contribution: "贡献",
  contributions: "贡献",
  controversy: "争议",
  controversies: "争议",
  corpus: "语料库",
  coverage: "覆盖度",
  dataset: "数据集",
  datasets: "数据集",
  decision: "决策",
  definition: "定义",
  definitions: "定义",
  digest: "摘要",
  discovery: "发现",
  draft: "草稿",
  equation: "公式",
  equations: "公式",
  extraction: "抽取",
  fit: "匹配",
  frontier: "前沿",
  glance: "速览",
  grounding: "证据锚定",
  hypothesis: "假设",
  identifier: "标识符",
  influence: "影响力",
  ingest: "导入",
  intent: "意图",
  latex: "LaTeX",
  leakage: "泄漏",
  lineage: "脉络",
  limitation: "局限",
  limitations: "局限",
  locator: "定位",
  markdown: "Markdown",
  matrix: "矩阵",
  memory: "记忆",
  method: "方法",
  methods: "方法",
  minimal: "最小",
  model: "模型",
  monitor: "监控",
  monitoring: "监控",
  novelty: "新颖性",
  onboarding: "接入",
  open: "开放",
  orchestration: "编排",
  outline: "大纲",
  overreach: "过度外推",
  paragraph: "段落",
  paragraphs: "段落",
  provenance: "来源",
  quality: "质量",
  quote: "引用原文",
  rebuttal: "回复审稿",
  regenerate: "重新生成",
  related: "相关",
  replication: "复现",
  repo: "代码仓库",
  repository: "代码仓库",
  research: "科研",
  reproducibility: "可复现性",
  roadmap: "路线图",
  runbook: "运行手册",
  scholar: "Scholar",
  section: "章节",
  sections: "章节",
  semantic: "语义",
  seminal: "奠基",
  source: "来源",
  statistical: "统计",
  structured: "结构化",
  synthesis: "综合",
  table: "表格",
  tables: "表格",
  terminology: "术语",
  threat: "威胁",
  threats: "威胁",
  validity: "有效性",
  venue: "会议/期刊",
  visual: "视觉",
  watchlist: "观察列表",
  workflow: "工作流",
  workflows: "工作流",
  writing: "写作",
  add: "添加",
  admin: "管理",
  agent: "Agent",
  alert: "告警",
  alerts: "告警",
  all: "全部",
  analysis: "分析",
  analytics: "分析统计",
  arxiv: "arXiv",
  ask: "问答",
  audit: "审计",
  author: "作者",
  authors: "作者",
  batch: "批量",
  bibliographic: "文献计量",
  bridge: "桥接",
  browse: "浏览",
  citation: "引用",
  citations: "引用",
  claim: "论证",
  claims: "论证",
  collection: "集合",
  collections: "集合",
  compare: "对比",
  content: "内容",
  correction: "更正",
  corrections: "更正",
  create: "创建",
  data: "数据",
  deduplicate: "去重",
  delete: "删除",
  detail: "详情",
  details: "详情",
  document: "文档",
  documents: "文档",
  duplicate: "重复",
  evidence: "证据",
  experiment: "实验",
  experiments: "实验",
  export: "导出",
  feed: "订阅源",
  feeds: "订阅源",
  figure: "图表",
  figures: "图表",
  full: "完整",
  get: "获取",
  governance: "治理",
  graph: "图谱",
  health: "健康状态",
  highlights: "亮点",
  import: "导入",
  imports: "导入任务",
  intelligence: "智能分析",
  job: "任务",
  jobs: "任务",
  library: "文库",
  list: "列出",
  log: "记录",
  metadata: "元数据",
  neighborhood: "邻域",
  order: "顺序",
  paper: "论文",
  papers: "论文",
  path: "路径",
  poll: "轮询",
  prerequisite: "前置知识",
  prerequisites: "前置知识",
  qa: "问答",
  ragflow: "RAGFlow",
  reading: "阅读",
  recommend: "推荐",
  recent: "最近",
  reorder: "重排",
  reproduction: "复现",
  reproductions: "复现",
  resolve: "解析",
  result: "结果",
  results: "结果",
  retraction: "撤稿",
  retrieve: "检索",
  saved: "保存的",
  search: "搜索",
  searches: "搜索",
  similar: "相似",
  stats: "统计",
  status: "状态",
  submit: "提交",
  summarize: "总结",
  summary: "摘要",
  sync: "同步",
  tag: "标签",
  tags: "标签",
  timeline: "时间线",
  topic: "主题",
  topics: "主题",
  trend: "趋势",
  trends: "趋势",
  trigger: "触发",
  update: "更新",
  upload: "上传",
  version: "版本",
  versions: "版本",
  webhook: "Webhook",
  webhooks: "Webhook",
};

const AGENT_DOMAIN_PURPOSE_ZH: Record<string, string> = {
  "agent-acquisition": "论文解析、导入、去重和处理状态追踪",
  "agent-paper-access": "按章节、段落、公式、算法和上下文窗口读取论文",
  "agent-visual-artifacts": "一图速览、图像、表格和可复用视觉资产读取",
  "agent-scientific-extraction": "问题、贡献、方法、实验、结果、局限和证据抽取",
  "agent-external-artifacts": "代码仓库、数据集、模型卡、项目页和社区资料发现",
  "agent-citation-intelligence": "参考文献树、被引树、引用意图、相关工作和影响力分析",
  "agent-topic-intelligence": "主题趋势、前沿地图、奠基论文、开放问题和争议追踪",
  "agent-synthesis-planning": "多论文证据矩阵、方法对比、差距分析和实验规划",
  "agent-reproducibility-quality": "复现计划、环境规格、统计检查和审稿风险识别",
  "agent-orchestration": "上下文包、批量任务、工作流状态和能力发现",
  "agent-research-output": "引用安全写作、参考文献导出、LaTeX 上下文和 rebuttal 证据包",
  "agent-monitoring-memory": "主题监控、研究笔记、决策日志、开放问题和下一步行动",
};

const API_SUMMARY_ZH: Record<string, string> = {
  "Add Papers To Collection": "向集合添加论文",
  "Add Tag To Paper": "给论文添加标签",
  "Ask About Paper": "基于论文分析数据回答问题",
  "Batch Import Papers": "批量导入论文",
  "Bibliographic Coupling": "查询文献耦合关系",
  "Browse Papers": "浏览论文发现流",
  "Compare Papers": "对比多篇论文",
  "Create Collection": "创建论文集合",
  "Create Feed": "创建 RSS 订阅源",
  "Create Saved Search": "创建保存的搜索",
  "Create Webhook": "创建 Webhook",
  "Deduplicate Library": "扫描文库重复论文",
  "Delete Collection": "删除论文集合",
  "Delete Feed": "删除 RSS 订阅源",
  "Delete Paper": "删除论文",
  "Delete Saved Search": "删除保存的搜索",
  "Delete Webhook": "删除 Webhook",
  "Export Paper Citation": "导出论文引用",
  "Get Agent Summary": "获取 Agent 友好的结构化论文摘要",
  "Get Bridge Papers": "查找连接两个主题领域的桥接论文",
  "Get Citation Timeline": "获取论文引用时间线",
  "Get Collection": "获取集合详情",
  "Get Collection Papers": "获取集合内论文",
  "Get Graph Neighborhood": "获取图谱邻域",
  "Get Import Status": "查询导入状态",
  "Get Job": "获取任务状态与结果",
  "Get Paper": "获取论文详情",
  "Get Paper Corrections": "获取论文元数据更正记录",
  "Get Paper Highlights": "获取论文亮点、贡献与局限",
  "Get Paper Tags": "获取论文标签",
  "Get Paper Versions": "获取论文版本历史",
  "Get Prerequisites": "获取论文前置知识",
  "Get Reading Order": "生成阅读顺序",
  "Get Reading Path": "查找论文之间的引用路径",
  "Get Reading Status": "获取阅读状态",
  "Get Related Work Pack": "获取相关工作包",
  "Get Reproductions": "获取复现记录",
  "Get Similar Papers": "获取相似论文",
  "Graph Stats": "获取图谱统计",
  "Import Paper": "导入单篇论文",
  "List Audit Log": "列出审计日志",
  "List Child Collections": "列出子集合",
  "List Collections": "列出论文集合",
  "List Feeds": "列出 RSS 订阅源",
  "List Jobs": "列出任务",
  "List Papers": "列出论文",
  "List Saved Searches": "列出保存的搜索",
  "List Webhooks": "列出 Webhook",
  "Log Reproduction": "记录复现尝试",
  "Recent Imports": "获取最近导入记录",
  "Recommend Similar": "推荐相似论文",
  "Remove Paper From Collection": "从集合移除论文",
  "Remove Tag From Paper": "移除论文标签",
  "Reorder Collection Papers": "重排集合内论文",
  "Resolve Papers By Arxiv": "通过 arXiv ID 解析论文",
  "Search Health": "检查搜索服务健康状态",
  "Search Papers": "搜索论文",
  "Submit Correction": "提交论文元数据更正",
  "Summarize Paper": "生成论文摘要",
  "Sync All Papers": "同步全部论文到图谱",
  "Sync Paper To Graph": "同步论文到图谱",
  "Trigger Poll": "触发 RSS 订阅源轮询",
  "Update Collection": "更新论文集合",
  "Update Reading Status": "更新阅读状态",
};

const config = useRuntimeConfig();
const { locale } = useTranslation();
const { isDark } = useTheme();

const apiKey = ref(getKaleidoscopeApiKey());
const endpoints = ref<AdminEndpoint[]>([]);
const openApiVersion = ref<string | null>(null);
const catalogPending = ref(false);
const catalogError = ref<string | null>(null);
const catalogLoadedAt = ref<string | null>(null);
const selectedEndpointId = ref<string | null>(null);
const searchQuery = ref("");
const activeDomain = ref("all");
const activeMethod = ref<MethodFilter>("all");
const pathParamsText = ref("{}");
const queryText = ref("{}");
const bodyText = ref("");
const runnerPending = ref(false);
const runnerResult = ref<AdminRunResult | null>(null);
const runnerError = ref<string | null>(null);
const copiedCurl = ref(false);

const uiText = computed(() => API_DOCS_COPY[locale.value]);
const apiBaseUrl = computed(() => String(config.public.apiUrl || ""));

const domainOptions = computed(() => [
  "all",
  ...new Set(endpoints.value.map((endpoint) => endpoint.domain)),
]);

const selectedEndpoint = computed(() => {
  return (
    endpoints.value.find(
      (endpoint) => endpoint.id === selectedEndpointId.value,
    ) ?? null
  );
});

const filteredEndpoints = computed(() => {
  const normalizedQuery = searchQuery.value.trim().toLowerCase();

  return endpoints.value.filter((endpoint) => {
    if (
      activeDomain.value !== "all" &&
      endpoint.domain !== activeDomain.value
    ) {
      return false;
    }

    if (
      activeMethod.value !== "all" &&
      endpoint.method !== activeMethod.value
    ) {
      return false;
    }

    if (!normalizedQuery) {
      return true;
    }

    return [
      endpoint.path,
      endpoint.summary,
      endpoint.description,
      endpointTitle(endpoint),
      endpointPurpose(endpoint),
      endpoint.domain,
      endpoint.tag,
      endpoint.operationId,
    ].some((value) => value.toLowerCase().includes(normalizedQuery));
  });
});

const endpointGroups = computed<EndpointGroup[]>(() => {
  const groups = filteredEndpoints.value.reduce<
    Record<string, AdminEndpoint[]>
  >((accumulator, endpoint) => {
    accumulator[endpoint.domain] ||= [];
    accumulator[endpoint.domain]!.push(endpoint);
    return accumulator;
  }, {});

  return Object.entries(groups).map(([domain, groupEndpoints]) => ({
    domain,
    endpoints: groupEndpoints,
  }));
});

const summaryCards = computed(() => {
  const domainCount = new Set(
    endpoints.value.map((endpoint) => endpoint.domain),
  ).size;
  const safeCount = endpoints.value.filter(
    (endpoint) => endpoint.probeMode === "safe",
  ).length;

  return [
    {
      label: uiText.value.endpoints,
      value: endpoints.value.length,
      tone: "ink",
    },
    {
      label: uiText.value.domains,
      value: domainCount,
      tone: "cyan",
    },
    {
      label: uiText.value.jsonFirst,
      value: safeCount,
      tone: "green",
    },
    {
      label: uiText.value.liveDebug,
      value: "X-API-Key",
      tone: "amber",
    },
  ];
});

const selectedParameters = computed(
  () => selectedEndpoint.value?.parameters ?? [],
);
const selectedRequestBody = computed(
  () => selectedEndpoint.value?.requestBody ?? null,
);
const responseCodes = computed(
  () => selectedEndpoint.value?.responseCodes ?? [],
);

const requestPathPreview = computed(() => {
  const endpoint = selectedEndpoint.value;
  if (!endpoint) {
    return "";
  }

  const preview = readRunnerPreview(endpoint);
  return buildApiRequestPath(endpoint.path, preview);
});

const requestUrlPreview = computed(() => {
  if (!requestPathPreview.value) {
    return "";
  }
  return resolveApiRequestUrl(apiBaseUrl.value, requestPathPreview.value);
});

const curlSnippet = computed(() => {
  const endpoint = selectedEndpoint.value;
  if (!endpoint) {
    return "";
  }

  const preview = readRunnerPreview(endpoint);
  return buildCurlCommand({
    baseUrl: apiBaseUrl.value,
    path: endpoint.path,
    method: endpoint.method,
    apiKey: maskApiKeyForDisplay(apiKey.value),
    pathParams: preview.pathParams,
    query: preview.query,
    body: preview.body,
  });
});

const requestBodySchemaText = computed(() => {
  return formatJsonPreview(selectedRequestBody.value?.schema ?? null, "null");
});

const responseBodyText = computed(() => {
  return runnerResult.value
    ? formatJsonPreview(runnerResult.value.data, "null")
    : "";
});

useHead({
  title: "API Docs — Kaleidoscope",
  meta: [
    {
      name: "description",
      content:
        "Kaleidoscope API documentation and live debugger for paper-analysis agents.",
    },
  ],
});

watch(
  selectedEndpoint,
  (endpoint) => {
    runnerError.value = null;
    runnerResult.value = null;
    if (!endpoint) {
      pathParamsText.value = "{}";
      queryText.value = "{}";
      bodyText.value = "";
      return;
    }

    resetRunnerSeed(endpoint);
  },
  { immediate: true },
);

watch(apiKey, (nextKey) => {
  if (!import.meta.client) {
    return;
  }

  try {
    localStorage.setItem(API_DOCS_KEY_STORAGE, nextKey);
  } catch {
    // Local persistence is optional for restricted browser contexts.
  }
});

onMounted(() => {
  try {
    const storedKey = localStorage.getItem(API_DOCS_KEY_STORAGE);
    if (storedKey) {
      apiKey.value = storedKey;
    }
  } catch {
    // Restricted storage should not block the documentation page.
  }

  void loadCatalog();
});

function resetRunnerSeed(endpoint = selectedEndpoint.value) {
  if (!endpoint) {
    return;
  }

  const seed = createRunnerSeed(endpoint);
  const generatedBody = endpoint.requestBody
    ? createJsonExample(endpoint.requestBody.schema)
    : null;

  pathParamsText.value = seed.pathParamsText;
  queryText.value = seed.queryText;
  bodyText.value = endpoint.requestBody
    ? seed.bodyText && seed.bodyText !== "{}"
      ? seed.bodyText
      : formatJsonPreview(generatedBody, "{}")
    : "";
}

function selectEndpoint(endpoint: AdminEndpoint) {
  selectedEndpointId.value = endpoint.id;
}

function ensureSelectedEndpoint() {
  if (
    selectedEndpointId.value &&
    endpoints.value.some((endpoint) => endpoint.id === selectedEndpointId.value)
  ) {
    return;
  }

  selectedEndpointId.value =
    endpoints.value.find((endpoint) => endpoint.id === "GET /health")?.id ??
    endpoints.value[0]?.id ??
    null;
}

async function loadCatalog() {
  catalogPending.value = true;
  catalogError.value = null;

  try {
    const response = await $fetch.raw(
      resolveApiRequestUrl(apiBaseUrl.value, "/api/openapi.json"),
      {
        method: "GET",
        headers: buildApiHeaders(apiKey.value),
      },
    );
    const document = response._data as OpenApiCatalog;
    endpoints.value = normalizeOpenApiCatalog(document);
    openApiVersion.value = document.openapi ?? null;
    catalogLoadedAt.value = new Date().toISOString();
    ensureSelectedEndpoint();
  } catch (error: unknown) {
    const fetchError = error as {
      message?: string;
      response?: { status?: number; _data?: unknown };
      data?: unknown;
    };
    const status = fetchError.response?.status;
    const detail = summarizeError(
      fetchError.response?._data ?? fetchError.data,
    );
    catalogError.value = status
      ? `HTTP ${status}${detail ? ` · ${detail}` : ""}`
      : (fetchError.message ?? "Failed to load OpenAPI schema");
    endpoints.value = [];
    selectedEndpointId.value = null;
  } finally {
    catalogPending.value = false;
  }
}

function readRunnerInputs(endpoint: AdminEndpoint) {
  const pathParams = parseJsonObjectInput(
    pathParamsText.value,
    uiText.value.pathParams,
  );
  const query = parseJsonObjectInput(queryText.value, uiText.value.queryParams);
  const parsedBody =
    endpoint.method === "GET" ? null : parseJsonBodyInput(bodyText.value);
  const body =
    parsedBody === null || parsedBody === undefined ? undefined : parsedBody;

  return {
    pathParams,
    query,
    body,
  };
}

function readRunnerPreview(endpoint: AdminEndpoint) {
  try {
    return readRunnerInputs(endpoint);
  } catch {
    return {
      pathParams: {},
      query: {},
      body: undefined,
    };
  }
}

async function runSelectedEndpoint() {
  const endpoint = selectedEndpoint.value;
  if (!endpoint) {
    return;
  }

  runnerError.value = null;
  if (!apiKey.value.trim()) {
    runnerError.value = uiText.value.apiKeyRequired;
    return;
  }

  let payload: ReturnType<typeof readRunnerInputs>;
  try {
    payload = readRunnerInputs(endpoint);
  } catch (error) {
    runnerError.value =
      error instanceof Error ? error.message : uiText.value.validJsonRequired;
    return;
  }

  const path = buildApiRequestPath(endpoint.path, payload);
  const url = resolveApiRequestUrl(apiBaseUrl.value, path);
  const startedAt = Date.now();
  runnerPending.value = true;

  try {
    const response = await $fetch.raw(url, {
      method: endpoint.method,
      body: payload.body as
        | BodyInit
        | Record<string, unknown>
        | null
        | undefined,
      headers: buildApiHeaders(apiKey.value, payload.body !== undefined),
    });

    runnerResult.value = {
      ok: response.status < 400,
      status: response.status,
      method: endpoint.method,
      path,
      url,
      durationMs: Date.now() - startedAt,
      timestamp: new Date().toISOString(),
      data: response._data,
      errorMessage: null,
    };
  } catch (error: unknown) {
    const fetchError = error as {
      message?: string;
      response?: { status?: number; _data?: unknown };
      data?: unknown;
    };

    runnerResult.value = {
      ok: false,
      status: fetchError.response?.status ?? 0,
      method: endpoint.method,
      path,
      url,
      durationMs: Date.now() - startedAt,
      timestamp: new Date().toISOString(),
      data: fetchError.response?._data ?? fetchError.data ?? null,
      errorMessage: fetchError.message ?? "Request failed",
    };
  } finally {
    runnerPending.value = false;
  }
}

async function copyCurlSnippet() {
  if (!import.meta.client || !curlSnippet.value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(curlSnippet.value);
    copiedCurl.value = true;
    window.setTimeout(() => {
      copiedCurl.value = false;
    }, 1600);
  } catch {
    copiedCurl.value = false;
  }
}

function normalizeSummaryKey(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function translateApiLabelToZh(value: string): string {
  const normalized = normalizeSummaryKey(value);
  const exact = API_SUMMARY_ZH[normalized];
  if (exact) {
    return exact;
  }

  return normalized
    .split(/\s+/)
    .filter(Boolean)
    .map((token) => {
      const cleaned = token.replace(/[^A-Za-z0-9]/g, "");
      const mapped = API_TERM_ZH[cleaned.toLowerCase()];
      return mapped ?? token;
    })
    .join(" ")
    .replace(/\s+(到|从|通过|与)\s+/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function endpointTitle(endpoint: AdminEndpoint): string {
  if (locale.value === "en") {
    return endpoint.summary;
  }

  return translateApiLabelToZh(endpoint.summary);
}

function endpointPurposeVerb(endpoint: AdminEndpoint): string {
  if (endpoint.probeMode === "stream") {
    return "建立事件流或持续订阅";
  }

  switch (endpoint.method) {
    case "GET":
      return "查询结构化数据";
    case "POST":
      return endpoint.path.includes("trigger") || endpoint.path.includes("sync")
        ? "触发后台工作流"
        : "提交数据或创建资源";
    case "PUT":
      return "整体更新资源";
    case "PATCH":
      return "部分更新资源状态";
    case "DELETE":
      return "删除或移除资源关系";
  }
}

function endpointParameterHint(endpoint: AdminEndpoint): string {
  const pathParams = endpoint.parameters
    .filter((parameter) => parameter.location === "path")
    .map((parameter) => translateApiLabelToZh(humanize(parameter.name)));
  const requiredQuery = endpoint.parameters
    .filter((parameter) => parameter.location === "query" && parameter.required)
    .map((parameter) => translateApiLabelToZh(humanize(parameter.name)));

  const hints = [
    pathParams.length ? `路径参数：${pathParams.join("、")}` : "",
    requiredQuery.length ? `必填查询参数：${requiredQuery.join("、")}` : "",
  ].filter(Boolean);

  return hints.length ? `调用时需要关注${hints.join("；")}。` : "";
}

function endpointPurpose(endpoint: AdminEndpoint): string {
  if (locale.value === "en") {
    return endpoint.description || `${endpoint.summary} in ${endpoint.domain}.`;
  }

  const title = endpointTitle(endpoint);
  const domain = domainLabel(endpoint.domain);
  const payload = endpoint.requestBody
    ? "请求体使用 JSON，响应也按结构化 JSON 返回。"
    : "响应按结构化 JSON 返回，便于下游 Agent 直接解析。";
  const parameters = endpointParameterHint(endpoint);

  if (endpoint.path.startsWith("/api/v1/agent/")) {
    const agentPurpose = AGENT_DOMAIN_PURPOSE_ZH[endpoint.domain];
    return `用于${title}。这是${domain}接口，面向自主科研 Agent 提供${agentPurpose ?? "论文分析与科研任务编排"}能力，主要用途是${endpointPurposeVerb(endpoint)}。${parameters}${payload}`;
  }

  return `用于${title}，属于${domain}能力，主要用途是${endpointPurposeVerb(endpoint)}。${parameters}${payload}`;
}

function domainLabel(domain: string): string {
  const labels = DOMAIN_LABELS[locale.value] as Record<string, string>;
  return labels[domain] ?? humanize(domain);
}

function humanize(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function methodClass(method: MethodFilter): string {
  return `api-docs-method--${method.toLowerCase()}`;
}

function routeModeText(endpoint: AdminEndpoint): string {
  if (endpoint.probeMode === "safe") {
    return uiText.value.safeRoute;
  }
  if (endpoint.probeMode === "mutating") {
    return uiText.value.mutatingRoute;
  }
  if (endpoint.probeMode === "stream") {
    return uiText.value.streamRoute;
  }
  return uiText.value.manualRoute;
}

function schemaSummary(schema: Record<string, unknown> | null): string {
  if (!schema) {
    return "—";
  }

  const type = typeof schema.type === "string" ? schema.type : null;
  const format = typeof schema.format === "string" ? schema.format : null;
  const enumValues = Array.isArray(schema.enum) ? schema.enum : null;
  const items =
    schema.items && typeof schema.items === "object"
      ? (schema.items as Record<string, unknown>)
      : null;

  if (enumValues && enumValues.length > 0) {
    return `enum(${enumValues.join(", ")})`;
  }

  if (items && typeof items.type === "string") {
    return `${type ?? "array"}<${items.type}>`;
  }

  if (format) {
    return `${type ?? "value"}:${format}`;
  }

  return type ?? "object";
}

function parameterRequirement(parameter: EndpointParameter): string {
  return parameter.required ? "yes" : "no";
}

function summarizeError(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "";
  }

  const record = payload as Record<string, unknown>;
  const detail = record.detail;
  if (typeof detail === "string") {
    return detail;
  }
  const message = record.message;
  if (typeof message === "string") {
    return message;
  }
  return "";
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) {
    return "—";
  }

  return new Intl.DateTimeFormat(locale.value === "zh" ? "zh-CN" : "en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}
</script>

<template>
  <div :class="['api-docs-page', { 'api-docs-page--dark': isDark }]">
    <section class="api-docs-hero" aria-labelledby="api-docs-title">
      <div class="api-docs-hero__grain" aria-hidden="true" />
      <div class="api-docs-hero__copy">
        <div class="api-docs-hero__eyebrow">
          <Braces :size="18" />
          <span>{{ uiText.eyebrow }}</span>
        </div>
        <h1 id="api-docs-title">{{ uiText.title }}</h1>
        <p>{{ uiText.subtitle }}</p>
        <div class="api-docs-metrics" aria-label="API summary">
          <div
            v-for="card in summaryCards"
            :key="card.label"
            :class="['api-docs-metric', `api-docs-metric--${card.tone}`]"
          >
            <span>{{ card.label }}</span>
            <strong>{{ card.value }}</strong>
          </div>
        </div>
      </div>

      <div class="api-docs-access" aria-label="API access controls">
        <div class="api-docs-access__row api-docs-access__row--key">
          <label for="api-docs-key">
            <KeyRound :size="16" />
            {{ uiText.apiKeyLabel }}
          </label>
          <input
            id="api-docs-key"
            v-model="apiKey"
            type="password"
            autocomplete="off"
            spellcheck="false"
            :placeholder="uiText.apiKeyPlaceholder"
          />
          <p>{{ uiText.apiKeyHelp }}</p>
        </div>

        <div class="api-docs-access__grid">
          <div class="api-docs-access__row">
            <span class="api-docs-access__label">{{
              uiText.baseUrlLabel
            }}</span>
            <code>{{ apiBaseUrl }}</code>
          </div>
          <div class="api-docs-access__row">
            <span class="api-docs-access__label">{{
              uiText.openApiVersion
            }}</span>
            <code>{{ openApiVersion ?? "—" }}</code>
          </div>
        </div>

        <div class="api-docs-access__actions">
          <button
            type="button"
            class="api-docs-action"
            :disabled="catalogPending"
            @click="loadCatalog"
          >
            <Loader2 v-if="catalogPending" :size="16" class="api-docs-spin" />
            <RefreshCcw v-else :size="16" />
            {{ catalogPending ? uiText.loadingSchema : uiText.reloadSchema }}
          </button>
        </div>

        <div
          :class="[
            'api-docs-schema-state',
            catalogError
              ? 'api-docs-schema-state--error'
              : 'api-docs-schema-state--ok',
          ]"
        >
          <XCircle v-if="catalogError" :size="16" />
          <CheckCircle2 v-else :size="16" />
          <span>{{
            catalogError ? uiText.schemaFailed : uiText.schemaReady
          }}</span>
          <small v-if="catalogLoadedAt">{{
            formatTimestamp(catalogLoadedAt)
          }}</small>
        </div>
      </div>
    </section>

    <section v-if="catalogError" class="api-docs-error" role="alert">
      <AlertTriangle :size="18" />
      <span>{{ catalogError }}</span>
    </section>

    <section class="api-docs-shell">
      <aside class="api-docs-catalog" aria-label="Endpoint catalog">
        <div class="api-docs-panel-title">
          <BookOpen :size="18" />
          <h2>{{ uiText.catalogTitle }}</h2>
        </div>

        <label class="api-docs-search">
          <Search :size="16" />
          <input
            v-model="searchQuery"
            type="search"
            :placeholder="uiText.searchPlaceholder"
          />
        </label>

        <div class="api-docs-filter-row">
          <button
            v-for="domain in domainOptions"
            :key="domain"
            type="button"
            :class="[
              'api-docs-filter-chip',
              { 'api-docs-filter-chip--active': activeDomain === domain },
            ]"
            @click="activeDomain = domain"
          >
            {{ domain === "all" ? uiText.allDomains : domainLabel(domain) }}
          </button>
        </div>

        <div class="api-docs-filter-row api-docs-filter-row--methods">
          <button
            v-for="method in METHOD_OPTIONS"
            :key="method"
            type="button"
            :class="[
              'api-docs-filter-chip',
              method !== 'all' ? methodClass(method) : '',
              { 'api-docs-filter-chip--active': activeMethod === method },
            ]"
            @click="activeMethod = method"
          >
            {{ method === "all" ? uiText.allMethods : method }}
          </button>
        </div>

        <div class="api-docs-endpoint-groups">
          <section
            v-for="group in endpointGroups"
            :key="group.domain"
            class="api-docs-endpoint-group"
          >
            <header>
              <span>{{ domainLabel(group.domain) }}</span>
              <small>{{ group.endpoints.length }}</small>
            </header>

            <button
              v-for="endpoint in group.endpoints"
              :key="endpoint.id"
              type="button"
              :class="[
                'api-docs-endpoint-card',
                {
                  'api-docs-endpoint-card--active':
                    endpoint.id === selectedEndpointId,
                },
              ]"
              @click="selectEndpoint(endpoint)"
            >
              <span :class="['api-docs-method', methodClass(endpoint.method)]">
                {{ endpoint.method }}
              </span>
              <span class="api-docs-endpoint-card__summary">
                {{ endpointTitle(endpoint) }}
              </span>
              <code>{{ endpoint.path }}</code>
            </button>
          </section>
        </div>
      </aside>

      <main class="api-docs-contract" aria-live="polite">
        <template v-if="selectedEndpoint">
          <div class="api-docs-contract__header">
            <div>
              <p class="api-docs-kicker">{{ uiText.selectedContract }}</p>
              <h2>{{ endpointTitle(selectedEndpoint) }}</h2>
            </div>
            <span
              :class="[
                'api-docs-method api-docs-method--large',
                methodClass(selectedEndpoint.method),
              ]"
            >
              {{ selectedEndpoint.method }}
            </span>
          </div>

          <p class="api-docs-contract__description">
            {{ endpointPurpose(selectedEndpoint) }}
          </p>

          <dl class="api-docs-facts">
            <div>
              <dt>{{ uiText.path }}</dt>
              <dd>
                <code>{{ selectedEndpoint.path }}</code>
              </dd>
            </div>
            <div>
              <dt>{{ uiText.domain }}</dt>
              <dd>{{ domainLabel(selectedEndpoint.domain) }}</dd>
            </div>
            <div>
              <dt>{{ uiText.operationId }}</dt>
              <dd>
                <code>{{ selectedEndpoint.operationId }}</code>
              </dd>
            </div>
            <div>
              <dt>{{ uiText.operation }}</dt>
              <dd>{{ routeModeText(selectedEndpoint) }}</dd>
            </div>
          </dl>

          <section class="api-docs-section">
            <div class="api-docs-section__heading">
              <h3>{{ uiText.parameters }}</h3>
              <span>{{ selectedParameters.length }}</span>
            </div>

            <div v-if="selectedParameters.length" class="api-docs-table-wrap">
              <table class="api-docs-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>{{ uiText.location }}</th>
                    <th>{{ uiText.required }}</th>
                    <th>{{ uiText.schema }}</th>
                    <th>{{ uiText.description }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="parameter in selectedParameters"
                    :key="`${parameter.location}-${parameter.name}`"
                  >
                    <td>
                      <code>{{ parameter.name }}</code>
                    </td>
                    <td>{{ parameter.location }}</td>
                    <td>{{ parameterRequirement(parameter) }}</td>
                    <td>{{ schemaSummary(parameter.schema) }}</td>
                    <td>{{ parameter.description || "—" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p v-else class="api-docs-empty-line">{{ uiText.noParameters }}</p>
          </section>

          <section class="api-docs-section">
            <div class="api-docs-section__heading">
              <h3>{{ uiText.requestBody }}</h3>
              <span v-if="selectedRequestBody">
                {{ selectedRequestBody.contentTypes.join(", ") }}
              </span>
            </div>
            <pre
              v-if="selectedRequestBody"
              class="api-docs-code-block"
            ><code>{{ requestBodySchemaText }}</code></pre>
            <p v-else class="api-docs-empty-line">{{ uiText.noRequestBody }}</p>
          </section>

          <section class="api-docs-section api-docs-section--responses">
            <div class="api-docs-section__heading">
              <h3>{{ uiText.responses }}</h3>
              <span>{{ uiText.responseCodes }}</span>
            </div>
            <div class="api-docs-response-codes">
              <span v-for="code in responseCodes" :key="code">{{ code }}</span>
            </div>
          </section>
        </template>

        <div v-else class="api-docs-empty-state">
          <Terminal :size="34" />
          <h2>{{ uiText.noEndpoint }}</h2>
          <p>{{ uiText.noEndpointDetail }}</p>
        </div>
      </main>

      <aside class="api-docs-runner" aria-label="Online API debugger">
        <div class="api-docs-runner__sticky">
          <div class="api-docs-panel-title">
            <Terminal :size="18" />
            <h2>{{ uiText.debugger }}</h2>
          </div>
          <p class="api-docs-runner__hint">{{ uiText.debuggerHint }}</p>

          <div v-if="selectedEndpoint" class="api-docs-runner__request-line">
            <span
              :class="['api-docs-method', methodClass(selectedEndpoint.method)]"
            >
              {{ selectedEndpoint.method }}
            </span>
            <code>{{ requestPathPreview }}</code>
          </div>
          <code v-if="requestUrlPreview" class="api-docs-runner__url">
            {{ requestUrlPreview }}
          </code>

          <label class="api-docs-runner-field">
            <span>{{ uiText.pathParams }}</span>
            <textarea v-model="pathParamsText" rows="4" spellcheck="false" />
          </label>

          <label class="api-docs-runner-field">
            <span>{{ uiText.queryParams }}</span>
            <textarea v-model="queryText" rows="4" spellcheck="false" />
          </label>

          <label class="api-docs-runner-field">
            <span>{{ uiText.bodyJson }}</span>
            <textarea
              v-model="bodyText"
              :disabled="!selectedRequestBody"
              rows="7"
              spellcheck="false"
            />
          </label>

          <div v-if="runnerError" class="api-docs-runner-error" role="alert">
            <AlertTriangle :size="16" />
            <span>{{ runnerError }}</span>
          </div>

          <div class="api-docs-runner__actions">
            <button
              type="button"
              class="api-docs-send"
              :disabled="!selectedEndpoint || runnerPending"
              @click="runSelectedEndpoint"
            >
              <Loader2 v-if="runnerPending" :size="16" class="api-docs-spin" />
              <Play v-else :size="16" />
              {{ runnerPending ? uiText.sending : uiText.sendRequest }}
            </button>
            <button
              type="button"
              class="api-docs-reset"
              @click="resetRunnerSeed()"
            >
              {{ uiText.resetExample }}
            </button>
          </div>

          <section class="api-docs-curl">
            <div class="api-docs-curl__header">
              <h3>{{ uiText.curlPreview }}</h3>
              <button type="button" @click="copyCurlSnippet">
                <Copy :size="14" />
                {{ copiedCurl ? uiText.copied : uiText.copyCurl }}
              </button>
            </div>
            <pre><code>{{ curlSnippet }}</code></pre>
          </section>

          <section class="api-docs-live-response">
            <div class="api-docs-live-response__header">
              <h3>{{ uiText.response }}</h3>
              <span
                v-if="runnerResult"
                :class="[
                  'api-docs-status-pill',
                  runnerResult.ok
                    ? 'api-docs-status-pill--ok'
                    : 'api-docs-status-pill--error',
                ]"
              >
                {{ runnerResult.status || "ERR" }}
              </span>
            </div>

            <dl v-if="runnerResult" class="api-docs-response-meta">
              <div>
                <dt>{{ uiText.duration }}</dt>
                <dd><Timer :size="13" /> {{ runnerResult.durationMs }} ms</dd>
              </div>
              <div>
                <dt>{{ uiText.timestamp }}</dt>
                <dd>{{ formatTimestamp(runnerResult.timestamp) }}</dd>
              </div>
              <div>
                <dt>{{ uiText.requestUrl }}</dt>
                <dd>
                  <code>{{ runnerResult.url }}</code>
                </dd>
              </div>
            </dl>
            <p v-else class="api-docs-empty-line">
              {{ uiText.awaitingResponse }}
            </p>
            <pre
              v-if="runnerResult"
              class="api-docs-response-json"
            ><code>{{ responseBodyText }}</code></pre>
          </section>
        </div>
      </aside>
    </section>
  </div>
</template>

<style scoped>
.api-docs-page {
  --api-docs-text: #2c261f;
  --api-docs-text-strong: #171412;
  --api-docs-text-muted: rgba(44, 38, 31, 0.7);
  --api-docs-text-soft: rgba(44, 38, 31, 0.58);
  --api-docs-text-faint: rgba(44, 38, 31, 0.45);
  --api-docs-accent: #c4a35a;
  --api-docs-accent-strong: #6f4f16;
  --api-docs-cyan: var(--color-primary, #0d7377);
  --api-docs-green: #157f57;
  --api-docs-danger: #b8433c;
  --api-docs-danger-soft: rgba(184, 67, 60, 0.1);
  --api-docs-border: rgba(44, 38, 31, 0.14);
  --api-docs-border-strong: rgba(136, 101, 32, 0.28);
  --api-docs-surface: rgba(255, 255, 255, 0.82);
  --api-docs-surface-soft: rgba(255, 255, 255, 0.64);
  --api-docs-surface-tint: rgba(13, 115, 119, 0.08);
  --api-docs-input-bg: rgba(255, 255, 255, 0.72);
  --api-docs-code-bg: rgba(26, 26, 26, 0.045);
  --api-docs-hero-bg:
    linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.78),
      rgba(255, 250, 238, 0.42) 48%,
      rgba(13, 115, 119, 0.08)
    ),
    rgba(250, 250, 247, 0.86);
  --api-docs-page-bg:
    radial-gradient(
      circle at 15% 8%,
      rgba(196, 163, 90, 0.2),
      transparent 34rem
    ),
    radial-gradient(
      circle at 88% 12%,
      rgba(13, 115, 119, 0.13),
      transparent 30rem
    ),
    linear-gradient(145deg, #fafaf7 0%, #f3efe6 45%, #eae5da 100%);
  --api-docs-grid-line: rgba(26, 26, 26, 0.055);
  --api-docs-grain: rgba(136, 101, 32, 0.1);
  --api-docs-shadow: 0 18px 52px rgba(26, 26, 26, 0.11);
  --api-docs-panel-shadow: 0 16px 44px rgba(26, 26, 26, 0.1);
  --api-docs-inset: inset 0 1px 0 rgba(255, 255, 255, 0.68);
  --api-docs-focus: rgba(13, 115, 119, 0.14);
  --api-docs-method-ink: #101214;

  display: flex;
  flex-direction: column;
  min-height: calc(100dvh - var(--topbar-height));
  padding: clamp(14px, 2vw, 28px);
  color: var(--api-docs-text);
  background: var(--api-docs-page-bg);
}

.api-docs-page--dark,
:global(html.ks-dark .api-docs-page) {
  --api-docs-text: #f4efe4;
  --api-docs-text-strong: #fff8e8;
  --api-docs-text-muted: rgba(244, 239, 228, 0.76);
  --api-docs-text-soft: rgba(244, 239, 228, 0.58);
  --api-docs-text-faint: rgba(244, 239, 228, 0.45);
  --api-docs-accent: #e8b952;
  --api-docs-accent-strong: #e8b952;
  --api-docs-cyan: #98f4ee;
  --api-docs-green: #5edd9a;
  --api-docs-danger: #ff756b;
  --api-docs-danger-soft: rgba(255, 117, 107, 0.09);
  --api-docs-border: rgba(255, 255, 255, 0.13);
  --api-docs-border-strong: rgba(232, 185, 82, 0.28);
  --api-docs-surface: rgba(9, 11, 13, 0.72);
  --api-docs-surface-soft: rgba(244, 239, 228, 0.055);
  --api-docs-surface-tint: rgba(152, 244, 238, 0.075);
  --api-docs-input-bg: rgba(0, 0, 0, 0.34);
  --api-docs-code-bg: rgba(0, 0, 0, 0.34);
  --api-docs-hero-bg:
    linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent 42%),
    rgba(13, 15, 16, 0.82);
  --api-docs-page-bg:
    radial-gradient(
      circle at 15% 8%,
      rgba(232, 185, 82, 0.22),
      transparent 34rem
    ),
    radial-gradient(
      circle at 88% 12%,
      rgba(71, 199, 202, 0.18),
      transparent 30rem
    ),
    linear-gradient(145deg, #111416 0%, #171612 42%, #090b0d 100%);
  --api-docs-grid-line: rgba(255, 255, 255, 0.045);
  --api-docs-grain: rgba(232, 185, 82, 0.12);
  --api-docs-shadow: 0 18px 52px rgba(0, 0, 0, 0.32);
  --api-docs-panel-shadow: 0 16px 50px rgba(0, 0, 0, 0.22);
  --api-docs-inset: inset 0 1px 0 rgba(255, 255, 255, 0.08);
  --api-docs-focus: rgba(152, 244, 238, 0.08);
  --api-docs-method-ink: #101214;
}

.api-docs-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(320px, 0.82fr);
  gap: clamp(14px, 2vw, 24px);
  padding: clamp(16px, 2.4vw, 28px);
  overflow: hidden;
  border: 1px solid var(--api-docs-border-strong);
  border-radius: 24px;
  background: var(--api-docs-hero-bg);
  box-shadow: var(--api-docs-shadow);
}

.api-docs-hero::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: "";
  background-image:
    linear-gradient(var(--api-docs-grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--api-docs-grid-line) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(120deg, black, transparent 78%);
}

.api-docs-hero__grain {
  position: absolute;
  inset: -40%;
  pointer-events: none;
  opacity: 0.22;
  background-image: repeating-linear-gradient(
    115deg,
    transparent 0,
    transparent 12px,
    var(--api-docs-grain) 13px,
    transparent 14px
  );
  transform: rotate(-3deg);
}

.api-docs-hero__copy,
.api-docs-access {
  position: relative;
  z-index: 1;
}

.api-docs-hero__eyebrow,
.api-docs-kicker,
.api-docs-access__label,
.api-docs-panel-title,
.api-docs-section__heading span,
.api-docs-endpoint-group header {
  font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.api-docs-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  color: var(--api-docs-cyan);
  border: 1px solid color-mix(in srgb, var(--api-docs-cyan) 32%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--api-docs-surface-tint) 74%, transparent);
  font-size: 0.68rem;
}

.api-docs-hero h1 {
  max-width: 900px;
  margin: 16px 0 10px;
  font-family: "Playfair Display", Georgia, serif;
  font-size: clamp(2.2rem, 5.4vw, 4.9rem);
  font-weight: 800;
  line-height: 0.9;
  letter-spacing: -0.06em;
}

.api-docs-hero__copy > p {
  max-width: 640px;
  margin: 0;
  color: var(--api-docs-text-muted);
  font-family: "Source Serif Pro", Georgia, serif;
  font-size: clamp(0.96rem, 1.25vw, 1.12rem);
  line-height: 1.38;
}

.api-docs-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 18px;
}

.api-docs-metric {
  min-height: 72px;
  padding: 10px;
  border: 1px solid var(--api-docs-border);
  border-radius: 14px;
  background: var(--api-docs-surface-soft);
}

.api-docs-metric span {
  display: block;
  color: var(--api-docs-text-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.64rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-metric strong {
  display: block;
  margin-top: 10px;
  color: var(--api-docs-text-strong);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: clamp(1rem, 1.45vw, 1.45rem);
  line-height: 1;
}

.api-docs-metric--cyan {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 32%, transparent);
}

.api-docs-metric--green {
  border-color: color-mix(in srgb, var(--api-docs-green) 38%, transparent);
}

.api-docs-metric--amber {
  border-color: color-mix(in srgb, var(--api-docs-accent) 40%, transparent);
}

.api-docs-access {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-self: start;
  padding: 12px;
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
  background: var(--api-docs-surface);
  box-shadow: var(--api-docs-inset);
  backdrop-filter: blur(18px);
}

.api-docs-access__row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.api-docs-access__row label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--api-docs-accent-strong);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-access input,
.api-docs-search input,
.api-docs-runner-field textarea {
  width: 100%;
  color: var(--api-docs-text-strong);
  border: 1px solid var(--api-docs-border);
  border-radius: 16px;
  background: var(--api-docs-input-bg);
  outline: none;
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease,
    background 160ms ease;
}

.api-docs-access input {
  padding: 10px 12px;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.84rem;
}

.api-docs-access input:focus,
.api-docs-search input:focus,
.api-docs-runner-field textarea:focus {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 72%, transparent);
  background: color-mix(
    in srgb,
    var(--api-docs-input-bg) 86%,
    var(--api-docs-text-strong)
  );
  box-shadow: 0 0 0 4px var(--api-docs-focus);
}

.api-docs-access p {
  margin: 0;
  color: var(--api-docs-text-soft);
  font-size: 0.76rem;
  line-height: 1.35;
}

.api-docs-access__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.api-docs-access__grid code,
.api-docs-facts code,
.api-docs-runner__request-line code,
.api-docs-response-meta code {
  overflow-wrap: anywhere;
  color: var(--api-docs-cyan);
  font-family: "JetBrains Mono", ui-monospace, monospace;
}

.api-docs-access__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
}

.api-docs-action,
.api-docs-send,
.api-docs-reset,
.api-docs-curl__header button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 10px;
  color: var(--api-docs-text-strong);
  border: 1px solid var(--api-docs-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.76rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.api-docs-action,
.api-docs-send,
.api-docs-reset,
.api-docs-curl__header button,
.api-docs-filter-chip,
.api-docs-endpoint-card {
  cursor: pointer;
}

.api-docs-action:disabled,
.api-docs-send:disabled,
.api-docs-runner-field textarea:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.api-docs-schema-state,
.api-docs-error,
.api-docs-runner-error {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--api-docs-text-muted);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.78rem;
}

.api-docs-schema-state small {
  margin-left: auto;
  color: var(--api-docs-text-faint);
}

.api-docs-schema-state--ok svg {
  color: var(--api-docs-green);
}

.api-docs-schema-state--error svg,
.api-docs-error svg,
.api-docs-runner-error svg {
  color: var(--api-docs-danger);
}

.api-docs-error {
  margin-top: 18px;
  padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--api-docs-danger) 34%, transparent);
  border-radius: 18px;
  background: var(--api-docs-danger-soft);
}

.api-docs-shell {
  display: grid;
  grid-template-columns: minmax(280px, 0.76fr) minmax(0, 1.42fr) minmax(
      360px,
      0.92fr
    );
  gap: 18px;
  align-items: stretch;
  flex: 1;
  margin-top: 22px;
  min-height: 0;
}

.api-docs-catalog,
.api-docs-contract,
.api-docs-runner__sticky {
  min-height: 100%;
  border: 1px solid var(--api-docs-border);
  border-radius: 28px;
  background: var(--api-docs-surface-soft);
  box-shadow: var(--api-docs-panel-shadow);
}

.api-docs-catalog,
.api-docs-contract {
  padding: 18px;
}

.api-docs-catalog,
.api-docs-runner__sticky {
  position: sticky;
  top: 20px;
  max-height: calc(100vh - 40px);
  overflow: auto;
}

.api-docs-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--api-docs-accent-strong);
}

.api-docs-panel-title h2,
.api-docs-section h3,
.api-docs-curl h3,
.api-docs-live-response h3 {
  margin: 0;
  color: var(--api-docs-text-strong);
  font-size: 0.88rem;
}

.api-docs-search {
  position: relative;
  display: block;
  margin-top: 18px;
}

.api-docs-search svg {
  position: absolute;
  top: 50%;
  left: 14px;
  color: var(--api-docs-text-faint);
  transform: translateY(-50%);
}

.api-docs-search input {
  padding: 13px 14px 13px 42px;
}

.api-docs-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.api-docs-filter-chip {
  padding: 8px 10px;
  color: var(--api-docs-text-soft);
  border: 1px solid var(--api-docs-border);
  border-radius: 999px;
  background: color-mix(in srgb, var(--api-docs-surface-soft) 72%, transparent);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.7rem;
}

.api-docs-filter-chip--active {
  color: var(--api-docs-method-ink);
  border-color: var(--api-docs-accent);
  background: var(--api-docs-accent);
}

.api-docs-endpoint-groups {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 20px;
}

.api-docs-endpoint-group header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--api-docs-text-faint);
  font-size: 0.7rem;
}

.api-docs-endpoint-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 10px;
  width: 100%;
  padding: 12px;
  text-align: left;
  color: var(--api-docs-text-strong);
  border: 1px solid transparent;
  border-radius: 17px;
  background: transparent;
}

.api-docs-endpoint-card:hover,
.api-docs-endpoint-card--active {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 28%, transparent);
  background: var(--api-docs-surface-tint);
}

.api-docs-endpoint-card__summary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.api-docs-endpoint-card code {
  grid-column: 1 / -1;
  overflow: hidden;
  color: var(--api-docs-text-faint);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.75rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.api-docs-method {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 54px;
  padding: 4px 7px;
  color: var(--api-docs-method-ink);
  border-radius: 8px;
  background: #d7d1c4;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.api-docs-method--large {
  min-width: 74px;
  padding: 8px 10px;
  font-size: 0.82rem;
}

.api-docs-method--get {
  background: #5edd9a;
}

.api-docs-method--post {
  background: #98f4ee;
}

.api-docs-method--put {
  background: var(--api-docs-accent);
}

.api-docs-method--patch {
  background: #c9a8ff;
}

.api-docs-method--delete {
  color: var(--api-docs-method-ink);
  background: #d94b43;
}

.api-docs-filter-chip.api-docs-method--get,
.api-docs-filter-chip.api-docs-method--post,
.api-docs-filter-chip.api-docs-method--put,
.api-docs-filter-chip.api-docs-method--patch,
.api-docs-filter-chip.api-docs-method--delete {
  color: var(--api-docs-method-ink);
}

.api-docs-contract__header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

.api-docs-kicker {
  margin: 0 0 8px;
  color: var(--api-docs-cyan);
  font-size: 0.72rem;
}

.api-docs-contract h2 {
  margin: 0;
  color: var(--api-docs-text-strong);
  font-family: "Playfair Display", Georgia, serif;
  font-size: clamp(2rem, 3.4vw, 3.8rem);
  line-height: 0.96;
  letter-spacing: -0.045em;
}

.api-docs-contract__description {
  margin: 16px 0 0;
  color: var(--api-docs-text-muted);
  font-family: "Source Serif Pro", Georgia, serif;
  font-size: 1.08rem;
  line-height: 1.55;
}

.api-docs-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin: 20px 0 0;
}

.api-docs-facts div {
  padding: 14px;
  border: 1px solid var(--api-docs-border);
  border-radius: 17px;
  background: color-mix(in srgb, var(--api-docs-code-bg) 42%, transparent);
}

.api-docs-facts dt,
.api-docs-response-meta dt {
  margin-bottom: 6px;
  color: var(--api-docs-text-faint);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-facts dd,
.api-docs-response-meta dd {
  margin: 0;
  color: var(--api-docs-text-strong);
}

.api-docs-section {
  margin-top: 20px;
}

.api-docs-section__heading,
.api-docs-curl__header,
.api-docs-live-response__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.api-docs-section__heading span {
  color: color-mix(
    in srgb,
    var(--api-docs-accent) 82%,
    var(--api-docs-text-strong)
  );
  font-size: 0.7rem;
}

.api-docs-table-wrap {
  overflow: auto;
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
}

.api-docs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}

.api-docs-table th,
.api-docs-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--api-docs-border);
}

.api-docs-table th {
  color: var(--api-docs-text-faint);
  background: color-mix(in srgb, var(--api-docs-code-bg) 48%, transparent);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-table tr:last-child td {
  border-bottom: 0;
}

.api-docs-table code,
.api-docs-code-block code,
.api-docs-curl code,
.api-docs-response-json code {
  font-family: "JetBrains Mono", ui-monospace, monospace;
}

.api-docs-empty-line {
  margin: 0;
  color: var(--api-docs-text-faint);
}

.api-docs-code-block,
.api-docs-curl pre,
.api-docs-response-json {
  overflow: auto;
  margin: 0;
  color: color-mix(
    in srgb,
    var(--api-docs-cyan) 78%,
    var(--api-docs-text-strong)
  );
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
  background: var(--api-docs-input-bg);
}

.api-docs-code-block {
  max-height: 340px;
  padding: 16px;
}

.api-docs-response-codes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.api-docs-response-codes span,
.api-docs-status-pill {
  padding: 7px 10px;
  color: var(--api-docs-method-ink);
  border-radius: 999px;
  background: #d7d1c4;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.72rem;
  font-weight: 800;
}

.api-docs-empty-state {
  display: grid;
  min-height: 460px;
  place-items: center;
  align-content: center;
  gap: 12px;
  color: var(--api-docs-text-soft);
  text-align: center;
}

.api-docs-empty-state h2 {
  margin: 0;
  color: var(--api-docs-text-strong);
}

.api-docs-empty-state p {
  max-width: 420px;
  margin: 0;
}

.api-docs-runner {
  min-height: 0;
}

.api-docs-runner__sticky {
  padding: 16px;
}

.api-docs-runner__hint {
  margin: 10px 0 16px;
  color: var(--api-docs-text-soft);
  line-height: 1.45;
}

.api-docs-runner__request-line {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--api-docs-cyan) 22%, transparent);
  border-radius: 17px;
  background: color-mix(in srgb, var(--api-docs-surface-tint) 70%, transparent);
}

.api-docs-runner__url {
  display: block;
  margin-top: 8px;
  overflow-wrap: anywhere;
  color: color-mix(
    in srgb,
    var(--api-docs-cyan) 72%,
    var(--api-docs-text-strong)
  );
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.72rem;
}

.api-docs-runner-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
}

.api-docs-runner-field span {
  color: var(--api-docs-text-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-runner-field textarea {
  min-height: 92px;
  padding: 12px;
  resize: vertical;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.82rem;
  line-height: 1.45;
}

.api-docs-runner-error {
  margin-top: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 117, 107, 0.26);
  border-radius: 14px;
  background: rgba(255, 117, 107, 0.08);
}

.api-docs-runner__actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.api-docs-send {
  color: var(--api-docs-method-ink);
  border-color: var(--api-docs-accent);
  background: var(--api-docs-accent);
  font-weight: 900;
}

.api-docs-reset {
  color: var(--api-docs-text-muted);
}

.api-docs-curl,
.api-docs-live-response {
  margin-top: 18px;
}

.api-docs-curl__header button {
  min-height: 32px;
  padding: 0 10px;
}

.api-docs-curl pre,
.api-docs-response-json {
  max-height: 320px;
  padding: 13px;
  font-size: 0.76rem;
  line-height: 1.55;
}

.api-docs-status-pill--ok {
  background: #5edd9a;
}

.api-docs-status-pill--error {
  color: var(--api-docs-text-strong);
  background: #d94b43;
}

.api-docs-response-meta {
  display: grid;
  gap: 8px;
  margin: 0 0 12px;
}

.api-docs-response-meta div {
  padding: 10px;
  border: 1px solid var(--api-docs-border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--api-docs-code-bg) 48%, transparent);
}

.api-docs-response-meta dd {
  display: flex;
  gap: 6px;
  align-items: center;
  overflow-wrap: anywhere;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.76rem;
}

.api-docs-spin {
  animation: api-docs-spin 900ms linear infinite;
}

@keyframes api-docs-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1280px) {
  .api-docs-shell {
    grid-template-columns: minmax(280px, 0.86fr) minmax(0, 1.14fr);
  }

  .api-docs-runner {
    grid-column: 1 / -1;
  }

  .api-docs-runner__sticky {
    position: static;
    max-height: none;
  }
}

@media (max-width: 980px) {
  .api-docs-page {
    padding: 16px;
  }

  .api-docs-hero,
  .api-docs-shell {
    grid-template-columns: 1fr;
  }

  .api-docs-catalog {
    position: static;
    max-height: none;
  }

  .api-docs-metrics,
  .api-docs-facts,
  .api-docs-access__grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .api-docs-spin {
    animation: none;
  }
}
</style>

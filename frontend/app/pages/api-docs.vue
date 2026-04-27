<script setup lang="ts">
/* eslint-disable vue/html-self-closing */
import {
  AlertTriangle,
  BookOpen,
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
  normalizeOpenApiWorkflows,
  normalizeOpenApiCatalog,
  type AgentWorkflowProfile,
  type AgentWorkflowStep,
  type AdminEndpoint,
  type AdminMethod,
  type AdminRunResult,
} from "~/composables/useAdminConsole";
import {
  buildApiHeaders,
  buildApiRequestPath,
  buildCurlCommand,
  createJsonExample,
  applyApiExampleProfileToRunnerSeed,
  formatJsonPreview,
  maskApiKeyForDisplay,
  parseJsonBodyInput,
  parseJsonObjectInput,
  resolveApiRequestUrl,
} from "~/utils/apiDocs";
import { getApiExampleProfile } from "~/utils/apiExampleRegistry";
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
    title: "Agent API Workbench.",
    subtitle:
      "Start from production research workflows, inspect each endpoint contract, then run the same requests captured by runtime verification.",
    apiKeyLabel: "API Key",
    apiKeyHelp:
      "Sent as X-API-Key for catalog loading and every debugger request.",
    apiKeyPlaceholder: "$KS_API_KEY",
    baseUrlLabel: "Base URL",
    reloadSchema: "Reload Schema",
    loadingSchema: "Loading Schema",
    schemaReady: "Schema Ready",
    schemaFailed: "Schema Failed",
    catalogTitle: "Endpoint Catalog",
    workflowTitle: "Workflow Library",
    workflowLead: "Production workflows for autonomous research agents.",
    workflowSteps: "Workflow Steps",
    workflowStatus: "Status",
    workflowInputs: "Inputs",
    workflowOutput: "Final Deliverable",
    workflowEmpty: "No workflow contracts were published by OpenAPI.",
    agentContract: "Agent Contract",
    whenToUse: "When To Use",
    fallbacks: "Fallbacks",
    responseMode: "Response Mode",
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
    name: "Name",
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
    expectedShape: "Runtime Example Response",
    expectedShapeHint: "Response body captured by the real HTTP verifier.",
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
    eyebrow: "开发者服务 · 面向智能体的 JSON API",
    title: "Agent API Workbench.",
    subtitle:
      "Start from production research workflows, inspect each endpoint contract, then run the same requests captured by runtime verification.",
    apiKeyLabel: "API Key",
    apiKeyHelp: "用于加载目录和调试请求，统一通过 X-API-Key 发送。",
    apiKeyPlaceholder: "$KS_API_KEY",
    baseUrlLabel: "基础地址",
    reloadSchema: "重新加载 Schema",
    loadingSchema: "加载中",
    schemaReady: "Schema 已就绪",
    schemaFailed: "Schema 加载失败",
    catalogTitle: "接口目录",
    workflowTitle: "Workflow Library",
    workflowLead: "Production workflows for autonomous research agents.",
    workflowSteps: "Workflow Steps",
    workflowStatus: "Status",
    workflowInputs: "Inputs",
    workflowOutput: "Final Deliverable",
    workflowEmpty: "No workflow contracts were published by OpenAPI.",
    agentContract: "Agent Contract",
    whenToUse: "When To Use",
    fallbacks: "Fallbacks",
    responseMode: "Response Mode",
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
    name: "名称",
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
    expectedShape: "运行时示例响应",
    expectedShapeHint: "真实 HTTP verifier 捕获的响应体。",
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
    "agent-acquisition": "智能体论文获取",
    "agent-citation-intelligence": "智能体引用分析",
    "agent-external-artifacts": "智能体外部资产",
    "agent-monitoring-memory": "智能体监控与记忆",
    "agent-orchestration": "智能体编排",
    "agent-paper-access": "智能体论文精读",
    "agent-reproducibility-quality": "智能体复现与质量",
    "agent-research-output": "智能体科研输出",
    "agent-scientific-extraction": "智能体科学抽取",
    "agent-synthesis-planning": "智能体综合与规划",
    "agent-topic-intelligence": "智能体主题趋势",
    "agent-visual-artifacts": "智能体图表资产",
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
  related_work: "相关工作",
  related_work_pack: "相关工作包",
  literature: "文献",
  build: "构建",
  map: "图谱",
  maps: "图谱",
  pack: "包",
  packs: "包",
  plan: "计划",
  review: "综述",
  reviews: "综述",
  work: "工作",
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
  agent: "智能体",
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
  "Get Agent Summary": "获取智能体友好的结构化论文摘要",
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
  "Related Work Pack": "生成相关工作包",
  "Build Related Work Pack": "生成相关工作包",
  "Review Map": "生成综述图谱",
  "Literature Review Map": "生成文献综述图谱",
  "Contradiction Map": "生成矛盾图谱",
  "Minimal Reading Set": "生成最小阅读集合",
  "Research Timeline": "生成研究时间线",
  "Plan Review": "评审研究计划",
  "Literature Plan Review": "评审文献综述计划",
  "Consensus Map": "生成共识图谱",
  "Literature Consensus Map": "生成文献共识图谱",
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
const workflows = ref<AgentWorkflowProfile[]>([]);
const openApiVersion = ref<string | null>(null);
const catalogPending = ref(false);
const catalogError = ref<string | null>(null);
const catalogLoadedAt = ref<string | null>(null);
const selectedEndpointId = ref<string | null>(null);
const selectedWorkflowId = ref<string | null>(null);
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
let endpointObserver: IntersectionObserver | null = null;

const uiText = computed(() => API_DOCS_COPY[locale.value]);
const apiBaseUrl = computed(() => String(config.public.apiUrl || ""));

const domainOptions = computed(() => [
  "all",
  ...new Set(endpoints.value.map((endpoint) => endpoint.domain)),
]);

function domainEndpointCount(domain: string): number {
  return endpoints.value.filter((endpoint) => endpoint.domain === domain).length;
}

const selectedEndpoint = computed(() => {
  return (
    endpoints.value.find(
      (endpoint) => endpoint.id === selectedEndpointId.value,
    ) ?? null
  );
});

const selectedWorkflow = computed(() => {
  return (
    workflows.value.find((workflow) => workflow.id === selectedWorkflowId.value) ??
    workflows.value[0] ??
    null
  );
});

const selectedWorkflowSteps = computed(() => selectedWorkflow.value?.steps ?? []);

const workflowEndpointIds = computed(
  () =>
    new Set(
      workflows.value.flatMap((workflow) =>
        workflow.steps.map((step) => step.endpoint),
      ),
    ),
);

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

const selectedRequestBody = computed(
  () => selectedEndpoint.value?.requestBody ?? null,
);

const selectedExampleProfile = computed(() =>
  selectedEndpoint.value
    ? getApiExampleProfile(selectedEndpoint.value.id)
    : null,
);

const expectedResponseText = computed(() => {
  const profileShape = selectedExampleProfile.value?.responseShape;
  if (profileShape !== undefined) {
    return formatJsonPreview(profileShape, "");
  }

  const endpoint = selectedEndpoint.value;
  if (!endpoint?.responseSchema) {
    return "";
  }

  return formatJsonPreview(createJsonExample(endpoint.responseSchema), "");
});

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
    mode: "display",
  });
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

watch(
  endpointGroups,
  async () => {
    await nextTick();
    setupEndpointObserver();
  },
  { flush: "post" },
);

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
  void nextTick().then(setupEndpointObserver);
});

onBeforeUnmount(() => {
  endpointObserver?.disconnect();
  endpointObserver = null;
});

function resetRunnerSeed(endpoint = selectedEndpoint.value) {
  if (!endpoint) {
    return;
  }

  const seed = createRunnerSeed(endpoint);
  const profile = getApiExampleProfile(endpoint.id);
  const generatedBody = endpoint.requestBody
    ? createJsonExample(endpoint.requestBody.schema)
    : null;
  const runnerSeed = applyApiExampleProfileToRunnerSeed({
    seed,
    profile,
    generatedBody,
    hasRequestBody: Boolean(endpoint.requestBody),
  });

  pathParamsText.value = runnerSeed.pathParamsText;
  queryText.value = runnerSeed.queryText;
  bodyText.value = runnerSeed.bodyText;
}

function selectEndpoint(endpoint: AdminEndpoint) {
  selectedEndpointId.value = endpoint.id;
}

function selectWorkflow(workflow: AgentWorkflowProfile) {
  selectedWorkflowId.value = workflow.id;
  const firstStep = workflow.steps.find((step) =>
    endpoints.value.some((endpoint) => endpoint.id === step.endpoint),
  );
  if (firstStep) {
    selectWorkflowStep(firstStep);
  }
}

function selectWorkflowStep(step: AgentWorkflowStep) {
  const endpoint = endpoints.value.find((item) => item.id === step.endpoint);
  if (!endpoint) {
    return;
  }

  selectedEndpointId.value = endpoint.id;
  resetRunnerSeed(endpoint);
  if (!import.meta.client) {
    return;
  }

  document
    .getElementById(endpointAnchorId(endpoint))
    ?.scrollIntoView({ block: "start", behavior: "smooth" });
}

function anchorSlug(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function domainAnchorId(domain: string): string {
  return `api-domain-${anchorSlug(domain)}`;
}

function endpointAnchorId(endpoint: AdminEndpoint): string {
  return `api-endpoint-${anchorSlug(endpoint.id)}`;
}

function endpointRequestBodySchemaText(endpoint: AdminEndpoint): string {
  return formatJsonPreview(endpoint.requestBody?.schema ?? null, "null");
}

function setupEndpointObserver() {
  if (!import.meta.client) {
    return;
  }

  endpointObserver?.disconnect();
  endpointObserver = null;

  const visibleEndpoints = endpointGroups.value.flatMap((group) => group.endpoints);
  const endpointByAnchor = new Map(
    visibleEndpoints.map((endpoint) => [endpointAnchorId(endpoint), endpoint]),
  );
  const targets = visibleEndpoints
    .map((endpoint) => document.getElementById(endpointAnchorId(endpoint)))
    .filter((element): element is HTMLElement => Boolean(element));

  if (!targets.length) {
    return;
  }

  endpointObserver = new IntersectionObserver(
    (entries) => {
      const activeEntry = entries
        .filter((entry) => entry.isIntersecting)
        .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];
      const endpoint = activeEntry
        ? endpointByAnchor.get(activeEntry.target.id)
        : null;

      if (endpoint && endpoint.id !== selectedEndpointId.value) {
        selectedEndpointId.value = endpoint.id;
      }
    },
    {
      rootMargin: "-18% 0px -68% 0px",
      threshold: [0, 0.16, 0.35, 0.6],
    },
  );

  for (const target of targets) {
    endpointObserver.observe(target);
  }
}


function ensureSelectedEndpoint() {
  if (
    selectedEndpointId.value &&
    endpoints.value.some((endpoint) => endpoint.id === selectedEndpointId.value)
  ) {
    return;
  }

  const firstWorkflowEndpoint = workflows.value
    .flatMap((workflow) => workflow.steps)
    .map((step) => step.endpoint)
    .find((endpointId) =>
      endpoints.value.some((endpoint) => endpoint.id === endpointId),
    );

  selectedEndpointId.value =
    firstWorkflowEndpoint ??
    endpoints.value.find((endpoint) => endpoint.id === "GET /health")?.id ??
    endpoints.value[0]?.id ??
    null;
}

function ensureSelectedWorkflow() {
  if (
    selectedWorkflowId.value &&
    workflows.value.some((workflow) => workflow.id === selectedWorkflowId.value)
  ) {
    return;
  }

  selectedWorkflowId.value = workflows.value[0]?.id ?? null;
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
    workflows.value = normalizeOpenApiWorkflows(document);
    openApiVersion.value = document.openapi ?? null;
    catalogLoadedAt.value = new Date().toISOString();
    ensureSelectedWorkflow();
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
    workflows.value = [];
    selectedWorkflowId.value = null;
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
  const endpoint = selectedEndpoint.value;
  if (!import.meta.client || !endpoint) {
    return;
  }

  try {
    const preview = readRunnerPreview(endpoint);
    await navigator.clipboard.writeText(
      buildCurlCommand({
        baseUrl: apiBaseUrl.value,
        path: endpoint.path,
        method: endpoint.method,
        apiKey: apiKey.value,
        pathParams: preview.pathParams,
        query: preview.query,
        body: preview.body,
        mode: "copy",
      }),
    );
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
  const normalized = normalizeSummaryKey(value.replace(/[_-]+/g, " "));
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

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function endpointAgentContract(endpoint: AdminEndpoint) {
  return asRecord(endpoint.agentProfile?.contract);
}

function endpointAgentPurpose(endpoint: AdminEndpoint): string {
  const contract = endpointAgentContract(endpoint);
  const purpose = contract?.purpose;
  return typeof purpose === "string" && purpose.trim()
    ? purpose
    : endpoint.description;
}

function endpointAgentUseCases(endpoint: AdminEndpoint): string[] {
  return asStringList(endpointAgentContract(endpoint)?.when_to_use).slice(0, 3);
}

function endpointAgentFallbacks(endpoint: AdminEndpoint): string[] {
  return asStringList(endpointAgentContract(endpoint)?.fallbacks).slice(0, 4);
}

function endpointAgentResponseMode(endpoint: AdminEndpoint): string {
  const contract = endpointAgentContract(endpoint);
  const responseMode = contract?.response_mode;
  return typeof responseMode === "string" ? responseMode : "unspecified";
}

function endpointAgentStatus(endpoint: AdminEndpoint): string {
  const status = endpoint.agentProfile?.status;
  return typeof status === "string" ? status : "unknown";
}

function endpointAgentWorkflowRefs(endpoint: AdminEndpoint): string[] {
  return asStringList(endpoint.agentProfile?.workflow_refs);
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
  const agentPurpose = endpointAgentPurpose(endpoint);

  if (locale.value === "en") {
    return agentPurpose || `${endpoint.summary} in ${endpoint.domain}.`;
  }

  const title = endpointTitle(endpoint);
  const domain = domainLabel(endpoint.domain);
  const payload = endpoint.requestBody
    ? "请求体使用 JSON，响应也按结构化 JSON 返回。"
    : "响应按结构化 JSON 返回，便于下游智能体直接解析。";
  const parameters = endpointParameterHint(endpoint);

  if (endpoint.path.startsWith("/api/v1/agent/")) {
    const domainPurpose = AGENT_DOMAIN_PURPOSE_ZH[endpoint.domain];
    return `${agentPurpose || `用于${title}`}。这是${domain}接口，面向自主科研智能体提供${domainPurpose ?? "论文分析与科研任务编排"}能力。${parameters}${payload}`;
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

function parameterLocationLabel(location: string): string {
  if (locale.value === "en") {
    return location;
  }

  const labels: Record<string, string> = {
    path: "路径",
    query: "查询",
    header: "请求头",
    cookie: "Cookie",
  };
  return labels[location] ?? location;
}

function parameterRequirement(parameter: EndpointParameter): string {
  if (locale.value === "en") {
    return parameter.required ? "yes" : "no";
  }

  return parameter.required ? "是" : "否";
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
    <section v-if="catalogError" class="api-docs-error" role="alert">
      <AlertTriangle :size="18" />
      <span>{{ catalogError }}</span>
    </section>

    <section class="api-docs-shell api-docs-shell--reader">
      <div class="api-docs-reader">
        <aside class="api-docs-toc" aria-label="Endpoint table of contents">
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

          <div class="api-docs-filter-stack">
            <p class="api-docs-toc-label">{{ uiText.domain }}</p>
            <button
              v-for="domain in domainOptions"
              :key="domain"
              type="button"
              :class="[
                'api-docs-filter-row-button',
                { 'api-docs-filter-row-button--active': activeDomain === domain },
              ]"
              @click="activeDomain = domain"
            >
              <span>{{ domain === "all" ? uiText.allDomains : domainLabel(domain) }}</span>
              <small v-if="domain !== 'all'">{{ domainEndpointCount(domain) }}</small>
            </button>
          </div>

          <div class="api-docs-filter-stack">
            <p class="api-docs-toc-label">{{ uiText.operation }}</p>
            <button
              v-for="method in METHOD_OPTIONS"
              :key="method"
              type="button"
              :class="[
                'api-docs-filter-row-button',
                method !== 'all' ? methodClass(method) : '',
                { 'api-docs-filter-row-button--active': activeMethod === method },
              ]"
              @click="activeMethod = method"
            >
              <span>{{ method === "all" ? uiText.allMethods : method }}</span>
            </button>
          </div>

          <nav class="api-docs-toc__groups">
            <p class="api-docs-toc-label">{{ uiText.catalogTitle }}</p>
            <section
              v-for="group in endpointGroups"
              :key="group.domain"
              class="api-docs-toc-group"
            >
              <a
                class="api-docs-toc-group__title"
                :href="`#${domainAnchorId(group.domain)}`"
              >
                <span>{{ domainLabel(group.domain) }}</span>
                <small>{{ group.endpoints.length }}</small>
              </a>

              <a
                v-for="endpoint in group.endpoints"
                :key="endpoint.id"
                :href="`#${endpointAnchorId(endpoint)}`"
                :class="[
                  'api-docs-toc-link',
                  {
                    'api-docs-toc-link--active': endpoint.id === selectedEndpointId,
                    'api-docs-toc-link--workflow': workflowEndpointIds.has(endpoint.id),
                  },
                ]"
                @click="selectEndpoint(endpoint)"
              >
                <span :class="['api-docs-method', methodClass(endpoint.method)]">
                  {{ endpoint.method }}
                </span>
                <span>{{ endpointTitle(endpoint) }}</span>
              </a>
            </section>
          </nav>
        </aside>

        <main class="api-docs-document" aria-live="polite">
          <section class="api-docs-document__lead">
            <p class="api-docs-kicker">{{ uiText.selectedContract }}</p>
            <h2>{{ uiText.workflowTitle }}</h2>
            <p>{{ uiText.subtitle }}</p>
          </section>

          <section class="api-docs-workflows" aria-label="Agent workflow library">
            <header class="api-docs-workflows__header">
              <div>
                <p class="api-docs-kicker">{{ uiText.workflowTitle }}</p>
                <h2>{{ uiText.workflowLead }}</h2>
              </div>
              <span v-if="workflows.length">{{ workflows.length }}</span>
            </header>

            <div v-if="workflows.length" class="api-docs-workflow-grid">
              <button
                v-for="workflow in workflows"
                :key="workflow.id"
                type="button"
                :class="[
                  'api-docs-workflow-card',
                  { 'api-docs-workflow-card--active': workflow.id === selectedWorkflow?.id },
                ]"
                @click="selectWorkflow(workflow)"
              >
                <span>{{ workflow.title }}</span>
                <small>{{ workflow.goal }}</small>
              </button>
            </div>
            <p v-else class="api-docs-empty-line">{{ uiText.workflowEmpty }}</p>

            <div v-if="selectedWorkflow" class="api-docs-workflow-detail">
              <dl class="api-docs-facts api-docs-facts--compact">
                <div>
                  <dt>{{ uiText.workflowStatus }}</dt>
                  <dd>{{ selectedWorkflow.status }}</dd>
                </div>
                <div>
                  <dt>{{ uiText.workflowInputs }}</dt>
                  <dd>{{ selectedWorkflow.entryInputs.join(", ") }}</dd>
                </div>
                <div>
                  <dt>{{ uiText.workflowOutput }}</dt>
                  <dd>{{ selectedWorkflow.finalDeliverable }}</dd>
                </div>
              </dl>

              <div class="api-docs-workflow-steps">
                <p class="api-docs-toc-label">{{ uiText.workflowSteps }}</p>
                <button
                  v-for="step in selectedWorkflowSteps"
                  :key="`${selectedWorkflow.id}-${step.id}`"
                  type="button"
                  :class="[
                    'api-docs-workflow-step',
                    { 'api-docs-workflow-step--active': step.endpoint === selectedEndpointId },
                  ]"
                  @click="selectWorkflowStep(step)"
                >
                  <span :class="['api-docs-method', methodClass(step.method)]">
                    {{ step.method }}
                  </span>
                  <span>
                    <strong>{{ step.name }}</strong>
                    <small>{{ step.endpoint }}</small>
                  </span>
                </button>
              </div>
            </div>
          </section>

          <template v-if="endpointGroups.length">
            <section
              v-for="group in endpointGroups"
              :id="domainAnchorId(group.domain)"
              :key="group.domain"
              class="api-docs-doc-domain"
            >
              <header class="api-docs-doc-domain__header">
                <p class="api-docs-kicker">{{ group.endpoints.length }} {{ uiText.endpoints }}</p>
                <h2>{{ domainLabel(group.domain) }}</h2>
              </header>

              <article
                v-for="endpoint in group.endpoints"
                :id="endpointAnchorId(endpoint)"
                :key="endpoint.id"
                :class="[
                  'api-docs-doc-endpoint',
                  {
                    'api-docs-doc-endpoint--active': endpoint.id === selectedEndpointId,
                    'api-docs-doc-endpoint--workflow': workflowEndpointIds.has(endpoint.id),
                  },
                ]"
                @click="selectEndpoint(endpoint)"
              >
                <header class="api-docs-doc-endpoint__header">
                  <div>
                    <p class="api-docs-kicker">{{ routeModeText(endpoint) }}</p>
                    <h3>{{ endpointTitle(endpoint) }}</h3>
                  </div>
                  <span :class="['api-docs-method api-docs-method--large', methodClass(endpoint.method)]">
                    {{ endpoint.method }}
                  </span>
                </header>

                <p class="api-docs-contract__description">
                  {{ endpointPurpose(endpoint) }}
                </p>

                <code class="api-docs-doc-path">{{ endpoint.path }}</code>

                <section
                  v-if="endpoint.agentProfile"
                  class="api-docs-agent-contract"
                >
                  <div class="api-docs-section__heading">
                    <h3>{{ uiText.agentContract }}</h3>
                    <span>{{ endpointAgentStatus(endpoint) }}</span>
                  </div>

                  <dl class="api-docs-facts api-docs-facts--compact">
                    <div>
                      <dt>{{ uiText.responseMode }}</dt>
                      <dd>{{ endpointAgentResponseMode(endpoint) }}</dd>
                    </div>
                    <div>
                      <dt>{{ uiText.workflowSteps }}</dt>
                      <dd>{{ endpointAgentWorkflowRefs(endpoint).join(", ") || "—" }}</dd>
                    </div>
                    <div>
                      <dt>{{ uiText.fallbacks }}</dt>
                      <dd>{{ endpointAgentFallbacks(endpoint).join(", ") || "—" }}</dd>
                    </div>
                  </dl>

                  <div v-if="endpointAgentUseCases(endpoint).length" class="api-docs-agent-contract__uses">
                    <p class="api-docs-toc-label">{{ uiText.whenToUse }}</p>
                    <ul>
                      <li
                        v-for="useCase in endpointAgentUseCases(endpoint)"
                        :key="`${endpoint.id}-${useCase}`"
                      >
                        {{ useCase }}
                      </li>
                    </ul>
                  </div>
                </section>

                <dl class="api-docs-facts api-docs-facts--compact">
                  <div>
                    <dt>{{ uiText.domain }}</dt>
                    <dd>{{ domainLabel(endpoint.domain) }}</dd>
                  </div>
                  <div>
                    <dt>{{ uiText.operationId }}</dt>
                    <dd><code>{{ endpoint.operationId }}</code></dd>
                  </div>
                </dl>

                <details class="api-docs-doc-details">
                  <summary>
                    <span>{{ uiText.parameters }}</span>
                    <small>{{ endpoint.parameters.length }}</small>
                  </summary>

                  <div v-if="endpoint.parameters.length" class="api-docs-table-wrap">
                    <table class="api-docs-table">
                      <thead>
                        <tr>
                          <th>{{ uiText.name }}</th>
                          <th>{{ uiText.location }}</th>
                          <th>{{ uiText.required }}</th>
                          <th>{{ uiText.schema }}</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="parameter in endpoint.parameters"
                          :key="`${endpoint.id}-${parameter.location}-${parameter.name}`"
                        >
                          <td><code>{{ parameter.name }}</code></td>
                          <td>{{ parameterLocationLabel(parameter.location) }}</td>
                          <td>{{ parameterRequirement(parameter) }}</td>
                          <td>{{ schemaSummary(parameter.schema) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <p v-else class="api-docs-empty-line">{{ uiText.noParameters }}</p>
                </details>

                <details class="api-docs-doc-details">
                  <summary>
                    <span>{{ uiText.requestBody }}</span>
                    <small v-if="endpoint.requestBody">
                      {{ endpoint.requestBody.contentTypes.join(", ") }}
                    </small>
                  </summary>
                  <pre
                    v-if="endpoint.requestBody"
                    class="api-docs-code-block"
                  ><code>{{ endpointRequestBodySchemaText(endpoint) }}</code></pre>
                  <p v-else class="api-docs-empty-line">{{ uiText.noRequestBody }}</p>
                </details>

                <section class="api-docs-section api-docs-section--responses">
                  <div class="api-docs-section__heading">
                    <h3>{{ uiText.responses }}</h3>
                    <span>{{ uiText.responseCodes }}</span>
                  </div>
                  <div class="api-docs-response-codes">
                    <span v-for="code in endpoint.responseCodes" :key="`${endpoint.id}-${code}`">
                      {{ code }}
                    </span>
                  </div>
                </section>
              </article>
            </section>
          </template>

          <div v-else class="api-docs-empty-state">
            <Terminal :size="34" />
            <h2>{{ uiText.noEndpoint }}</h2>
            <p>{{ uiText.noEndpointDetail }}</p>
          </div>
        </main>
      </div>

      <aside class="api-docs-runner" aria-label="Online API debugger">
        <div class="api-docs-runner__sticky">
          <div class="api-docs-panel-title">
            <Terminal :size="18" />
            <h2>{{ uiText.debugger }}</h2>
          </div>

          <div class="api-docs-runner-access" aria-label="API access controls">
            <label class="api-docs-runner-field api-docs-runner-field--key" for="api-docs-key">
              <span><KeyRound :size="14" /> {{ uiText.apiKeyLabel }}</span>
              <input
                id="api-docs-key"
                v-model="apiKey"
                type="password"
                autocomplete="off"
                spellcheck="false"
                :placeholder="uiText.apiKeyPlaceholder"
              />
            </label>

            <div class="api-docs-runner-access__meta">
              <code>{{ apiBaseUrl }}</code>
              <code>{{ openApiVersion ?? "—" }}</code>
            </div>

            <button
              type="button"
              class="api-docs-action api-docs-action--compact"
              :disabled="catalogPending"
              @click="loadCatalog"
            >
              <Loader2 v-if="catalogPending" :size="14" class="api-docs-spin" />
              <RefreshCcw v-else :size="14" />
              {{ catalogPending ? uiText.loadingSchema : uiText.reloadSchema }}
            </button>

            <div
              :class="[
                'api-docs-schema-state',
                catalogError
                  ? 'api-docs-schema-state--error'
                  : 'api-docs-schema-state--ok',
              ]"
            >
              <XCircle v-if="catalogError" :size="14" />
              <CheckCircle2 v-else :size="14" />
              <span>{{ catalogError ? uiText.schemaFailed : uiText.schemaReady }}</span>
            </div>
          </div>

          <p class="api-docs-runner__hint">{{ uiText.debuggerHint }}</p>

          <div v-if="selectedEndpoint" class="api-docs-runner__request-line">
            <span :class="['api-docs-method', methodClass(selectedEndpoint.method)]">
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
            <button type="button" class="api-docs-reset" @click="resetRunnerSeed()">
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

          <section
            v-if="expectedResponseText"
            class="api-docs-live-response api-docs-live-response--expected"
          >
            <div class="api-docs-live-response__header">
              <h3>{{ uiText.expectedShape }}</h3>
              <span>{{ uiText.expectedShapeHint }}</span>
            </div>
            <pre class="api-docs-response-json"><code>{{ expectedResponseText }}</code></pre>
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
  height: calc(100dvh - var(--topbar-height));
  min-height: 0;
  overflow: hidden;
  padding: clamp(10px, 1.4vw, 18px);
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

.api-docs-kicker,
.api-docs-panel-title,
.api-docs-section__heading span {
  font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.api-docs-runner-field input,
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

.api-docs-runner-field input {
  padding: 10px 12px;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.78rem;
}

.api-docs-runner-field input:focus,
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

.api-docs-facts code,
.api-docs-runner-access__meta code,
.api-docs-runner__request-line code,
.api-docs-response-meta code {
  overflow-wrap: anywhere;
  color: var(--api-docs-cyan);
  font-family: "JetBrains Mono", ui-monospace, monospace;
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
.api-docs-filter-row-button {
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
  grid-template-columns: minmax(0, 1fr) minmax(252px, 292px);
  gap: 12px;
  align-items: stretch;
  height: 100%;
  flex: 1;
  margin-top: 0;
  min-height: 0;
  overflow: hidden;
}

.api-docs-reader,
.api-docs-runner__sticky {
  border: 1px solid var(--api-docs-border);
  border-radius: 28px;
  background: var(--api-docs-surface-soft);
  box-shadow: var(--api-docs-panel-shadow);
}

.api-docs-reader {
  display: grid;
  grid-template-columns: minmax(148px, 188px) minmax(0, 1fr);
  align-items: stretch;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.api-docs-toc {
  height: 100%;
  min-height: 0;
  overflow: auto;
  padding: 12px;
  border-right: 1px solid var(--api-docs-border);
}

.api-docs-document {
  min-width: 0;
  height: 100%;
  min-height: 0;
  overflow: auto;
  padding: clamp(18px, 2.2vw, 34px);
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

.api-docs-filter-stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 16px;
}

.api-docs-toc-label {
  margin: 0 0 4px;
  color: var(--api-docs-text-faint);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.api-docs-filter-row-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  min-height: 32px;
  padding: 7px 9px;
  color: var(--api-docs-text-soft);
  text-align: left;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.72rem;
  cursor: pointer;
}

.api-docs-filter-row-button small {
  color: var(--api-docs-text-faint);
}

.api-docs-filter-row-button:hover,
.api-docs-filter-row-button--active {
  color: var(--api-docs-text-strong);
  border-color: color-mix(in srgb, var(--api-docs-cyan) 28%, transparent);
  background: var(--api-docs-surface-tint);
}

.api-docs-filter-row-button.api-docs-method--get,
.api-docs-filter-row-button.api-docs-method--post,
.api-docs-filter-row-button.api-docs-method--put,
.api-docs-filter-row-button.api-docs-method--patch,
.api-docs-filter-row-button.api-docs-method--delete {
  color: var(--api-docs-method-ink);
  font-weight: 800;
}

.api-docs-toc__groups {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 18px;
}

.api-docs-toc-group {
  padding-top: 12px;
  border-top: 1px solid var(--api-docs-border);
}

.api-docs-toc-group:first-child {
  padding-top: 0;
  border-top: 0;
}

.api-docs-toc-group__title,
.api-docs-toc-link {
  display: flex;
  align-items: center;
  gap: 9px;
  color: var(--api-docs-text-muted);
  text-decoration: none;
}

.api-docs-toc-group__title {
  justify-content: space-between;
  margin-bottom: 7px;
  color: var(--api-docs-text-strong);
  font-size: 0.78rem;
  font-weight: 800;
}

.api-docs-toc-group__title small {
  color: var(--api-docs-text-faint);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
}

.api-docs-toc-link {
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: 13px;
  font-size: 0.74rem;
  line-height: 1.25;
}

.api-docs-toc-link span:last-child {
  min-width: 0;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.api-docs-toc-link:hover,
.api-docs-toc-link--active {
  color: var(--api-docs-text-strong);
  border-color: color-mix(in srgb, var(--api-docs-cyan) 28%, transparent);
  background: var(--api-docs-surface-tint);
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

.api-docs-document__lead {
  padding-bottom: 28px;
  border-bottom: 1px solid var(--api-docs-border);
}

.api-docs-workflows {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 0 28px;
  border-bottom: 1px solid var(--api-docs-border);
}

.api-docs-workflows__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.api-docs-workflows__header h2 {
  margin: 6px 0 0;
  color: var(--api-docs-text-strong);
  font-size: clamp(1.15rem, 2vw, 1.7rem);
}

.api-docs-workflows__header span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 34px;
  min-height: 34px;
  border: 1px solid var(--api-docs-border);
  border-radius: 999px;
  color: var(--api-docs-cyan);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-weight: 800;
}

.api-docs-workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}

.api-docs-workflow-card,
.api-docs-workflow-step {
  color: var(--api-docs-text-muted);
  border: 1px solid var(--api-docs-border);
  background: var(--api-docs-surface-soft);
  text-align: left;
  cursor: pointer;
}

.api-docs-workflow-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 118px;
  padding: 14px;
  border-radius: 18px;
}

.api-docs-workflow-card span {
  color: var(--api-docs-text-strong);
  font-weight: 800;
}

.api-docs-workflow-card small {
  color: var(--api-docs-text-soft);
  line-height: 1.45;
}

.api-docs-workflow-card--active,
.api-docs-workflow-card:hover,
.api-docs-workflow-step--active,
.api-docs-workflow-step:hover {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 34%, transparent);
  background: var(--api-docs-surface-tint);
}

.api-docs-workflow-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.api-docs-workflow-steps {
  display: grid;
  gap: 8px;
}

.api-docs-workflow-step {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 10px;
  border-radius: 14px;
}

.api-docs-workflow-step strong,
.api-docs-workflow-step small {
  display: block;
}

.api-docs-workflow-step strong {
  color: var(--api-docs-text-strong);
  font-size: 0.86rem;
}

.api-docs-workflow-step small {
  margin-top: 3px;
  overflow-wrap: anywhere;
  color: var(--api-docs-text-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
}

.api-docs-agent-contract {
  display: grid;
  gap: 12px;
  margin-top: 14px;
  padding: 14px;
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
  background: var(--api-docs-surface-tint);
}

.api-docs-agent-contract__uses ul {
  display: grid;
  gap: 6px;
  margin: 0;
  padding-left: 18px;
  color: var(--api-docs-text-muted);
}

.api-docs-toc-link--workflow,
.api-docs-doc-endpoint--workflow {
  border-color: color-mix(in srgb, var(--api-docs-accent) 18%, transparent);
}

.api-docs-document__lead h2,
.api-docs-doc-domain__header h2 {
  margin: 0;
  color: var(--api-docs-text-strong);
  font-family: "Playfair Display", Georgia, serif;
  line-height: 0.98;
  letter-spacing: -0.04em;
}

.api-docs-document__lead h2 {
  font-size: clamp(2.4rem, 5vw, 5.6rem);
}

.api-docs-document__lead p:last-child {
  max-width: 760px;
  margin: 16px 0 0;
  color: var(--api-docs-text-muted);
  font-family: "Source Serif Pro", Georgia, serif;
  font-size: 1.16rem;
  line-height: 1.6;
}

.api-docs-doc-domain {
  scroll-margin-top: 24px;
  margin-top: 48px;
}

.api-docs-doc-domain__header {
  margin-bottom: 18px;
}

.api-docs-doc-domain__header h2 {
  font-size: clamp(2rem, 3.4vw, 4rem);
}

.api-docs-doc-endpoint {
  scroll-margin-top: 24px;
  padding: clamp(18px, 2.4vw, 28px);
  border: 1px solid transparent;
  border-radius: 24px;
  background: color-mix(in srgb, var(--api-docs-surface) 58%, transparent);
}

.api-docs-doc-endpoint + .api-docs-doc-endpoint {
  margin-top: 18px;
}

.api-docs-doc-endpoint:hover {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 30%, transparent);
  background: color-mix(in srgb, var(--api-docs-surface-tint) 72%, var(--api-docs-surface));
}

.api-docs-doc-endpoint--active,
.api-docs-doc-endpoint--active:hover {
  border-color: color-mix(in srgb, var(--api-docs-cyan) 62%, transparent);
  background: color-mix(in srgb, var(--api-docs-surface) 58%, transparent);
}

.api-docs-doc-endpoint__header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
}

.api-docs-doc-endpoint__header h3 {
  margin: 0;
  color: var(--api-docs-text-strong);
  font-family: "Source Serif Pro", Georgia, serif;
  font-size: clamp(1.45rem, 2vw, 2.2rem);
  line-height: 1.08;
}

.api-docs-doc-path {
  display: block;
  margin-top: 16px;
  overflow-wrap: anywhere;
  color: color-mix(in srgb, var(--api-docs-cyan) 75%, var(--api-docs-text-strong));
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.82rem;
}

.api-docs-facts--compact {
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
}

.api-docs-doc-details {
  margin-top: 14px;
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
  background: color-mix(in srgb, var(--api-docs-code-bg) 38%, transparent);
}

.api-docs-doc-details summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 15px;
  color: var(--api-docs-text-strong);
  cursor: pointer;
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.api-docs-doc-details summary::marker {
  color: var(--api-docs-cyan);
}

.api-docs-doc-details summary small {
  color: var(--api-docs-text-faint);
  font-weight: 600;
  text-transform: none;
}

.api-docs-doc-details > :not(summary) {
  margin: 0 14px 14px;
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

.api-docs-live-response__header span {
  color: var(--api-docs-text-faint);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.68rem;
  text-align: right;
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
  position: sticky;
  top: 0;
  height: 100%;
  max-height: 100%;
  overflow: auto;
  padding: 14px;
}

.api-docs-runner-access {
  display: grid;
  gap: 9px;
  margin-top: 14px;
  padding: 10px;
  border: 1px solid var(--api-docs-border);
  border-radius: 18px;
  background: var(--api-docs-surface);
  box-shadow: var(--api-docs-inset);
}

.api-docs-runner-field--key {
  margin-top: 0;
}

.api-docs-runner-access__meta {
  display: grid;
  gap: 6px;
}

.api-docs-runner-access__meta code {
  display: block;
  min-width: 0;
  padding: 7px 8px;
  border: 1px solid var(--api-docs-border);
  border-radius: 12px;
  background: color-mix(in srgb, var(--api-docs-code-bg) 64%, transparent);
  font-size: 0.68rem;
}

.api-docs-action--compact {
  justify-content: center;
  width: 100%;
  min-height: 32px;
  font-size: 0.68rem;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--api-docs-text-soft);
  font-family: "JetBrains Mono", ui-monospace, monospace;
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.api-docs-runner-field textarea {
  min-height: 66px;
  padding: 10px;
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
    grid-template-columns: minmax(0, 1fr) minmax(248px, 280px);
  }

  .api-docs-reader {
    grid-template-columns: minmax(140px, 176px) minmax(0, 1fr);
  }
}

@media (max-width: 980px) {
  .api-docs-page {
    height: auto;
    min-height: calc(100dvh - var(--topbar-height));
    overflow: auto;
    padding: 16px;
  }

  .api-docs-shell {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .api-docs-reader {
    grid-template-columns: 1fr;
    height: auto;
  }

  .api-docs-toc,
  .api-docs-document,
  .api-docs-runner__sticky {
    position: static;
    height: auto;
    max-height: none;
    overflow: auto;
  }

  .api-docs-toc {
    border-right: 0;
    border-bottom: 1px solid var(--api-docs-border);
  }

  .api-docs-facts {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .api-docs-spin {
    animation: none;
  }
}
</style>

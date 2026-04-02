import type { SupplementItem, SupplementItemType } from '../components/paper/supplements'

type RemoteUrl = {
  url?: string | null
  source?: string | null
  type?: string | null
}

type ArtifactRecord = {
  url?: string | null
  type?: string | null
  label?: string | null
}

type PaperRawMetadata = {
  pdf_url?: string | null
  best_oa_url?: string | null
  github_url?: string | null
  code_url?: string | null
  artifact_links?: ArtifactRecord[] | null
}

type Candidate = {
  url: string
  snippet: string
  source: 'metadata' | 'remote_url' | 'markdown'
  explicitType?: string | null
}

const URL_PATTERN = /https?:\/\/[^\s<>"')\]}]+/g
const TRAILING_PUNCTUATION = /[),.;:\]>}]+$/
const LEADING_PUNCTUATION = /^[([{<]+/
const IMAGE_EXTENSION_PATTERN = /\.(png|jpe?g|gif|webp|svg)$/i
const CODE_HOSTS = ['github.com', 'gitlab.com', 'bitbucket.org']
const DATASET_HOSTS = [
  'zenodo.org',
  'figshare.com',
  'kaggle.com',
  'openml.org',
  'physionet.org',
  'dataverse.harvard.edu',
]
const DATASET_KEYWORDS = [
  'dataset',
  'data availability',
  'data and code availability',
  'data available',
  'survey instrument',
  'benchmark',
  'corpus',
  'download',
]
const WEIGHTS_KEYWORDS = [
  'weights',
  'model weights',
  'checkpoint',
  'checkpoints',
  'pretrained',
  'pre-trained',
  'safetensors',
  'ckpt',
]
const CODE_KEYWORDS = [
  'code',
  'source code',
  'repository',
  'repo',
  'implementation',
  'github',
  'gitlab',
]

function normalizeUrl(rawUrl: string): string {
  return rawUrl
    .replace(/\s+/g, '')
    .replace(LEADING_PUNCTUATION, '')
    .replace(TRAILING_PUNCTUATION, '')
}

function parseUrl(url: string): URL | null {
  try {
    return new URL(url)
  }
  catch {
    return null
  }
}

function hasKeyword(snippet: string, keywords: string[]): boolean {
  const normalized = snippet.toLowerCase()
  return keywords.some(keyword => normalized.includes(keyword))
}

function getProvider(url: string): string | null {
  const parsed = parseUrl(url)
  if (!parsed)
    return null

  const host = parsed.hostname.replace(/^www\./, '').toLowerCase()
  if (host === 'github.com')
    return 'GitHub'
  if (host === 'gitlab.com')
    return 'GitLab'
  if (host === 'bitbucket.org')
    return 'Bitbucket'
  if (host === 'huggingface.co' || host === 'hf.co')
    return 'Hugging Face'
  if (host === 'zenodo.org' || url.includes('doi.org/10.5281/zenodo'))
    return 'Zenodo'
  if (host === 'figshare.com')
    return 'Figshare'
  if (host === 'kaggle.com')
    return 'Kaggle'
  if (host === 'modelscope.cn')
    return 'ModelScope'
  return null
}

function classifyCandidate(candidate: Candidate): {
  type: SupplementItemType
  label: string
} | null {
  const url = candidate.url.toLowerCase()
  const parsed = parseUrl(candidate.url)
  const host = parsed?.hostname.replace(/^www\./, '').toLowerCase() ?? ''
  const path = parsed?.pathname.toLowerCase() ?? ''
  const snippet = candidate.snippet.toLowerCase()
  const provider = getProvider(candidate.url)
  const datasetContext = hasKeyword(snippet, DATASET_KEYWORDS)
  const weightsContext = hasKeyword(snippet, WEIGHTS_KEYWORDS)
  const codeContext = hasKeyword(snippet, CODE_KEYWORDS)

  if (candidate.explicitType === 'code') {
    return { type: 'code', label: provider ? `${provider} Repository` : 'Code Repository' }
  }

  if (candidate.explicitType === 'dataset') {
    return { type: 'dataset', label: provider ? `${provider} Dataset` : 'Dataset Download' }
  }

  if (candidate.explicitType === 'weights' || candidate.explicitType === 'model') {
    return { type: 'weights', label: provider ? `${provider} Weights` : 'Model Weights' }
  }

  if (candidate.explicitType === 'pdf' || path.endsWith('.pdf')) {
    return { type: 'appendix', label: 'PDF' }
  }

  if (CODE_HOSTS.includes(host)) {
    const label = provider ? `${provider} Repository` : 'Code Repository'
    return { type: 'code', label }
  }

  const isHuggingFace = host === 'huggingface.co' || host === 'hf.co'
  const isModelScope = host === 'modelscope.cn'
  const isZenodoDoi = url.includes('doi.org/10.5281/zenodo')

  if (IMAGE_EXTENSION_PATTERN.test(path)) {
    return null
  }

  if (isHuggingFace && path.startsWith('/datasets/')) {
    return { type: 'dataset', label: 'Hugging Face Dataset' }
  }

  if (isHuggingFace && !path.startsWith('/datasets/') && !path.startsWith('/spaces/')) {
    return { type: 'weights', label: 'Hugging Face Weights' }
  }

  if (DATASET_HOSTS.includes(host) || isZenodoDoi || datasetContext) {
    return { type: 'dataset', label: provider ? `${provider} Dataset` : 'Dataset Download' }
  }

  if (isModelScope || weightsContext) {
    return { type: 'weights', label: provider ? `${provider} Weights` : 'Model Weights' }
  }

  if (codeContext) {
    return { type: 'code', label: provider ? `${provider} Repository` : 'Code Repository' }
  }

  return null
}

function createItemId(type: SupplementItemType, url: string, index: number): string {
  const slug = url
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48) || 'link'

  return `sup-${type}-${slug}-${index}`
}

function collectMetadataCandidates(rawMetadata: PaperRawMetadata | null | undefined): Candidate[] {
  if (!rawMetadata)
    return []

  const candidates: Candidate[] = []

  if (rawMetadata.pdf_url) {
    candidates.push({
      url: rawMetadata.pdf_url,
      snippet: 'pdf',
      source: 'metadata',
      explicitType: 'pdf',
    })
  }

  if (rawMetadata.best_oa_url) {
    candidates.push({
      url: rawMetadata.best_oa_url,
      snippet: 'open access pdf',
      source: 'metadata',
      explicitType: 'pdf',
    })
  }

  if (rawMetadata.github_url) {
    candidates.push({
      url: rawMetadata.github_url,
      snippet: 'github repository',
      source: 'metadata',
      explicitType: 'code',
    })
  }

  if (rawMetadata.code_url) {
    candidates.push({
      url: rawMetadata.code_url,
      snippet: 'code repository',
      source: 'metadata',
      explicitType: 'code',
    })
  }

  for (const artifact of rawMetadata.artifact_links ?? []) {
    if (!artifact?.url)
      continue

    candidates.push({
      url: artifact.url,
      snippet: `${artifact.label ?? ''} ${artifact.type ?? ''}`.trim(),
      source: 'metadata',
      explicitType: artifact.type,
    })
  }

  return candidates
}

function collectRemoteUrlCandidates(remoteUrls: RemoteUrl[] | null | undefined): Candidate[] {
  return (remoteUrls ?? [])
    .filter((record): record is RemoteUrl & { url: string } => Boolean(record?.url))
    .map(record => ({
      url: record.url,
      snippet: `${record.source ?? ''} ${record.type ?? ''}`.trim(),
      source: 'remote_url',
      explicitType: record.type,
    }))
}

function collectMarkdownCandidates(markdown: string | null | undefined): Candidate[] {
  if (!markdown)
    return []

  const candidates: Candidate[] = []
  let currentHeading = ''
  let previousLine = ''

  for (const rawLine of markdown.split('\n')) {
    const line = rawLine.trim()
    if (!line)
      continue

    if (line.startsWith('#')) {
      currentHeading = line.replace(/^#+\s*/, '').trim()
    }

    if (line.includes('http://') || line.includes('https://')) {
      for (const match of line.matchAll(URL_PATTERN)) {
        const rawUrl = match[0]
        const continuation = line.slice((match.index ?? 0) + rawUrl.length)
        const doiContinuation = rawUrl.includes('doi.org/')
          ? continuation.match(/^\s+([A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+)/)
          : null

        candidates.push({
          url: rawUrl + (doiContinuation?.[1] ?? ''),
          snippet: [currentHeading, previousLine, line].filter(Boolean).join(' '),
          source: 'markdown',
        })
      }
    }

    previousLine = line
  }

  return candidates
}

export function extractPaperSupplements(input: {
  doi?: string | null
  arxivId?: string | null
  rawMetadata?: PaperRawMetadata | null
  remoteUrls?: RemoteUrl[] | null
  markdown?: string | null
}): SupplementItem[] {
  const candidates = [
    ...collectMetadataCandidates(input.rawMetadata),
    ...collectRemoteUrlCandidates(input.remoteUrls),
    ...collectMarkdownCandidates(input.markdown),
  ]

  const items: SupplementItem[] = []
  const seenUrls = new Set<string>()

  for (const candidate of candidates) {
    const normalizedUrl = normalizeUrl(candidate.url)
    if (!normalizedUrl || seenUrls.has(normalizedUrl))
      continue

    const classification = classifyCandidate({
      ...candidate,
      url: normalizedUrl,
    })
    if (!classification)
      continue

    items.push({
      id: createItemId(classification.type, normalizedUrl, items.length),
      label: classification.label,
      type: classification.type,
      url: normalizedUrl,
    })
    seenUrls.add(normalizedUrl)
  }

  if (input.doi) {
    const doiUrl = `https://doi.org/${input.doi}`
    if (!seenUrls.has(doiUrl)) {
      items.push({
        id: createItemId('appendix', doiUrl, items.length),
        label: 'DOI Link',
        type: 'appendix',
        url: doiUrl,
      })
      seenUrls.add(doiUrl)
    }
  }

  if (input.arxivId) {
    const arxivUrl = `https://arxiv.org/abs/${input.arxivId}`
    if (!seenUrls.has(arxivUrl)) {
      items.push({
        id: createItemId('appendix', arxivUrl, items.length),
        label: 'arXiv',
        type: 'appendix',
        url: arxivUrl,
      })
    }
  }

  const order: Record<SupplementItemType, number> = {
    code: 0,
    dataset: 1,
    weights: 2,
    slides: 3,
    demo: 4,
    video: 5,
    appendix: 6,
  }

  return items.sort((left, right) => {
    const orderDelta = order[left.type] - order[right.type]
    if (orderDelta !== 0)
      return orderDelta

    return left.label.localeCompare(right.label)
  })
}

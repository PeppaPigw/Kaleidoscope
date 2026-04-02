import { describe, expect, it } from 'vitest'

import { extractPaperSupplements } from './paperSupplements'

describe('extractPaperSupplements', () => {
  it('extracts code and dataset links from markdown availability notes', () => {
    const items = extractPaperSupplements({
      arxivId: '2603.29651',
      markdown: [
        '# Data and Code Availability',
        'The source code for NMVT is publicly available at https://github.com/briankeithn/narrative-maps.',
        'The news dataset, survey instruments, and anonymized coded insights are available via Zenodo at: https://doi.org/10.5281/zenodo. 18930804.',
      ].join('\n'),
      remoteUrls: [
        { url: 'https://arxiv.org/pdf/2603.29651.pdf', source: 'arxiv', type: 'pdf' },
      ],
    })

    expect(items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: 'GitHub Repository',
          type: 'code',
          url: 'https://github.com/briankeithn/narrative-maps',
        }),
        expect.objectContaining({
          label: 'Zenodo Dataset',
          type: 'dataset',
          url: 'https://doi.org/10.5281/zenodo.18930804',
        }),
        expect.objectContaining({
          label: 'PDF',
          type: 'appendix',
          url: 'https://arxiv.org/pdf/2603.29651.pdf',
        }),
        expect.objectContaining({
          label: 'arXiv',
          type: 'appendix',
          url: 'https://arxiv.org/abs/2603.29651',
        }),
      ]),
    )
  })

  it('distinguishes Hugging Face datasets from model weights', () => {
    const items = extractPaperSupplements({
      markdown: [
        'Resources.',
        'Dataset: https://huggingface.co/datasets/acme/news-benchmark',
        'Pretrained checkpoints: https://huggingface.co/acme/narrative-map-large',
      ].join('\n'),
    })

    expect(items).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          label: 'Hugging Face Dataset',
          type: 'dataset',
          url: 'https://huggingface.co/datasets/acme/news-benchmark',
        }),
        expect.objectContaining({
          label: 'Hugging Face Weights',
          type: 'weights',
          url: 'https://huggingface.co/acme/narrative-map-large',
        }),
      ]),
    )
  })

  it('deduplicates repeated links across metadata and markdown', () => {
    const items = extractPaperSupplements({
      rawMetadata: {
        github_url: 'https://github.com/acme/project',
      },
      markdown: 'Code availability: https://github.com/acme/project.',
    })

    expect(items.filter(item => item.type === 'code')).toHaveLength(1)
  })
})

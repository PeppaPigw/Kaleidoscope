下面是我根据你给的 HTML 整理出的 Markdown 版本。内容来自你上传的文件

````markdown
# 📚 API Documentation

Welcome to the Agentic Data Interface API. This REST API provides AI agents and developers with efficient access to arXiv academic papers in various formats.

## 🎁 Free Testing

Papers **2409.05591** and **2504.21776** are available without authentication for testing purposes.

## ⚡ Key Features

- 🚀 Fast - Redis Cached
- 🎯 On-Demand Loading
- 📦 Multiple Formats
- 🔍 Built-in Search

## 🌐 Base URL

`https://data.rag.ac.cn/arxiv/`

---

# 🔑 Authentication

Most endpoints require a valid API token. You can provide the token in two ways:

## Method 1: Authorization Header

```http
Authorization: Bearer YOUR_TOKEN_HERE
```
````

## Method 2: Query Parameter

```text
?token=YOUR_TOKEN_HERE
```

## 🎁 Free Papers (No Token Required)

Papers `2409.05591` and `2504.21776` can be accessed without a token.

## 📝 Getting a Token

Visit `/register` to create an account and get your API token. Each token includes **10,000 free daily requests**. Need more? Contact us with your use case.

---

# 🔌 API Endpoints

All endpoints use the same base URL with different `type` parameters to specify the data format.

---

# 📋 Get Paper Metadata

**GET** `/arxiv/?type=head&arxiv_id={PAPER_ID}`

Returns structured metadata including title, abstract, authors, sections, and statistics.

## Parameters

| Parameter  | Type   | Required | Description                                   |
| ---------- | ------ | -------- | --------------------------------------------- |
| `arxiv_id` | string | Required | arXiv paper ID (e.g., 2409.05591, 2504.21776) |
| `type`     | string | Required | Must be `"head"`                              |
| `token`    | string | Optional | API token (not required for free papers)      |

## Response Fields

- **title**: Paper title
- **abstract**: Paper abstract
- **authors**: List of authors
- **sections**: Section names and metadata
- **token_count**: Total tokens in the paper
- **categories**: arXiv categories
- **publish_at**: Publication date

---

# 📌 Get Brief Information

**GET** `/arxiv/?type=brief&arxiv_id={PAPER_ID}`

Returns concise paper information including title, TLDR, keywords, publication date, and citation count. Perfect for quick summaries and list views.

## Parameters

| Parameter  | Type   | Required | Description                                   |
| ---------- | ------ | -------- | --------------------------------------------- |
| `arxiv_id` | string | Required | arXiv paper ID (e.g., 2409.05591, 2504.21776) |
| `type`     | string | Required | Must be `"brief"`                             |
| `token`    | string | Optional | API token (not required for free papers)      |

## Response Fields

- **arxiv_id**: arXiv paper ID
- **src_url**: Direct link to PDF
- **title**: Paper title
- **tldr**: AI-generated summary (if available)
- **keywords**: List of keywords (if available)
- **publish_at**: Publication date
- **citations**: Citation count

## Example Response

```json
{
  "arxiv_id": "2409.05591",
  "src_url": "https://arxiv.org/pdf/2409.05591",
  "title": "Paper Title",
  "tldr": "Brief summary...",
  "keywords": ["AI", "Machine Learning"],
  "publish_at": "2024-09-05",
  "citations": 42
}
```

---

# 👀 Preview Paper Content

**GET** `/arxiv/?type=preview&arxiv_id={PAPER_ID}`

Returns a configurable number of characters from the paper for quick preview.

Default is **10,000 characters**, but you can adjust it from 100 to 100,000. Useful for mobile devices or when you want to quickly scan the introduction.

## Parameters

| Parameter    | Type    | Required | Description                                                        |
| ------------ | ------- | -------- | ------------------------------------------------------------------ |
| `arxiv_id`   | string  | Required | arXiv paper ID                                                     |
| `type`       | string  | Required | Must be `"preview"`                                                |
| `characters` | integer | Optional | Number of characters to return (default: 10000, range: 100-100000) |

## Response Fields

- **preview**: First N characters (configurable)
- **is_truncated**: Whether content was truncated
- **total_characters**: Total characters in full document
- **preview_characters**: Actual characters in preview

---

# 📄 Get Full Content

**GET** `/arxiv/?type=raw&arxiv_id={PAPER_ID}`

Returns the complete paper content in Markdown format.

## Parameters

| Parameter  | Type   | Required | Description     |
| ---------- | ------ | -------- | --------------- |
| `arxiv_id` | string | Required | arXiv paper ID  |
| `type`     | string | Required | Must be `"raw"` |

---

# 📑 Get Specific Section

**GET** `/arxiv/?type=section&arxiv_id={PAPER_ID}&section={SECTION_NAME}`

Returns content from a specific section of the paper (e.g., `"Introduction"`, `"Conclusion"`).

## Parameters

| Parameter  | Type   | Required | Description                                        |
| ---------- | ------ | -------- | -------------------------------------------------- |
| `arxiv_id` | string | Required | arXiv paper ID                                     |
| `type`     | string | Required | Must be `"section"`                                |
| `section`  | string | Required | Section name (e.g., `"Introduction"`, `"Methods"`) |

---

# 📊 Get Complete JSON

**GET** `/arxiv/?type=json&arxiv_id={PAPER_ID}`

Returns the complete structured JSON file with all sections and metadata.

---

# 🌐 Get HTML View

**GET** `/arxiv/?type=markdown&arxiv_id={PAPER_ID}`

Returns a beautifully rendered HTML page for viewing in a browser.

## Quick Access

- 🌐 HTML View (2409.05591): `https://data.rag.ac.cn/arxiv/?arxiv_id=2409.05591&type=markdown`
- 👀 Preview Content: `https://data.rag.ac.cn/arxiv/?arxiv_id=2409.05591&type=preview`
- 📋 Formatted Metadata (2504.21776): `https://data.rag.ac.cn/arxiv/?arxiv_id=2504.21776&type=head_str`

---

# 🔍 Search & Retrieve

**POST** `/arxiv/?type=retrieve&query={QUERY}`

Search for relevant papers using **Elasticsearch hybrid search** (BM25 + Vector). Supports multiple search modes and advanced filtering.

## Search Modes

- 🔤 BM25 - Keyword Match
- 🧠 Vector - Semantic Search
- 🎯 Hybrid - Combined (Default)

## Parameters

| Parameter       | Type          | Required | Description                                                            |
| --------------- | ------------- | -------- | ---------------------------------------------------------------------- |
| `query`         | string        | Required | Search query                                                           |
| `type`          | string        | Required | Must be `"retrieve"`                                                   |
| `size`          | integer       | Optional | Number of results (default: 10)                                        |
| `offset`        | integer       | Optional | Result offset for pagination (default: 0)                              |
| `search_mode`   | string        | Optional | Search mode: `"bm25"`, `"vector"`, or `"hybrid"` (default: `"hybrid"`) |
| `bm25_weight`   | float         | Optional | BM25 weight for hybrid search (default: 0.5)                           |
| `vector_weight` | float         | Optional | Vector weight for hybrid search (default: 0.5)                         |
| `categories`    | array[string] | Optional | Filter by categories (e.g., `["cs.AI", "cs.CL"]`)                      |
| `authors`       | array[string] | Optional | Filter by authors                                                      |
| `min_citation`  | integer       | Optional | Minimum citation count                                                 |
| `date_from`     | string        | Optional | Publication date from (format: YYYY-MM-DD)                             |
| `date_to`       | string        | Optional | Publication date to (format: YYYY-MM-DD)                               |

## Response Format

Returns a JSON object with search results:

```json
{
  "total": 1234,
  "took": 45,
  "results": [
    {
      "arxiv_id": "2301.12345",
      "score": 0.95,
      "title": "Paper Title",
      "abstract": "...",
      "authors": [...],
      "categories": [...],
      "citation": 42
    }
  ]
}
```

## 🎁 Free Queries

These queries don't require a token:

- transformer
- attention mechanism
- large language model

---

# 📈 Get Trending Signal

**GET** `/arxiv/trending_signal?arxiv_id={PAPER_ID}`

Get social media engagement metrics for a paper, including tweets, likes, views, and replies. Track how papers are trending in the research community.

## Parameters

| Parameter  | Type   | Required | Description                           |
| ---------- | ------ | -------- | ------------------------------------- |
| `arxiv_id` | string | Required | arXiv paper ID (e.g., 2409.05591)     |
| `token`    | string | Required | API token (required for all requests) |

## Response Fields

- **arxiv_id**: arXiv paper ID
- **total_tweets**: Total number of tweets mentioning the paper
- **total_likes**: Total likes across all tweets
- **total_views**: Total views across all tweets
- **total_replies**: Total replies to tweets about the paper
- **first_seen_date**: When the paper was first mentioned
- **last_seen_date**: Most recent mention

## Example Response

```json
{
  "arxiv_id": "2409.05591",
  "total_tweets": 150,
  "total_likes": 3200,
  "total_views": 25000,
  "total_replies": 45,
  "first_seen_date": "2024-09-05T10:30:00",
  "last_seen_date": "2024-09-10T14:20:00"
}
```

## Use Cases

- 📊 Track paper virality and impact
- 🔥 Identify trending papers in your field
- 📅 Monitor engagement timeline
- 🎯 Discover influential research

> **💡 Note:** If a paper has no social media engagement, you'll receive a 404 error. This is normal for papers that haven't been discussed on Twitter yet.

---

# 🏥 PMC Endpoints

Access PubMed Central (PMC) research articles. PMC is a free full-text archive of biomedical and life sciences journal literature.

## 🎁 Free Testing

Papers **PMC544940** and **PMC514704** are available without authentication for testing purposes.

## 🌐 Base URL

`https://data.rag.ac.cn/pmc/`

---

# 📋 Get PMC Paper Metadata

**GET** `/pmc/?type=head&pmc_id={PMC_ID}`

Returns structured metadata including title, DOI, abstract, authors, categories, and publication date.

## Parameters

| Parameter | Type   | Required | Description                               |
| --------- | ------ | -------- | ----------------------------------------- |
| `pmc_id`  | string | Required | PMC paper ID (e.g., PMC544940, PMC514704) |
| `type`    | string | Optional | Must be `"head"` (default)                |
| `token`   | string | Optional | API token (not required for free papers)  |

## Response Fields

- **pmc_id**: PMC paper ID
- **title**: Paper title
- **doi**: Digital Object Identifier
- **abstract**: Paper abstract
- **authors**: List of authors
- **categories**: Medical subject categories
- **publish_at**: Publication date

---

# 📊 Get PMC Complete JSON

**GET** `/pmc/?type=json&pmc_id={PMC_ID}`

Returns the complete structured JSON file with full paper content and metadata.

## Parameters

| Parameter | Type   | Required | Description                               |
| --------- | ------ | -------- | ----------------------------------------- |
| `pmc_id`  | string | Required | PMC paper ID (e.g., PMC544940, PMC514704) |
| `type`    | string | Required | Must be `"json"`                          |
| `token`   | string | Optional | API token (not required for free papers)  |

## Quick Access

- 📋 PMC Metadata (PMC544940): `https://data.rag.ac.cn/pmc/?pmc_id=PMC544940&type=head`
- 📊 Full JSON (PMC514704): `https://data.rag.ac.cn/pmc/?pmc_id=PMC514704&type=json`

---

# ⚠️ Error Handling

## HTTP Status Codes

| Code    | Meaning             | Description              |
| ------- | ------------------- | ------------------------ |
| **200** | Success             | Request successful       |
| **400** | Bad Request         | Invalid parameters       |
| **401** | Unauthorized        | Invalid or missing token |
| **404** | Not Found           | Paper not found          |
| **429** | Too Many Requests   | Rate limit exceeded      |
| **503** | Service Unavailable | Retrieval service error  |

---

# 📊 Rate Limits

Each API token has a daily limit of **10,000 free requests**.

When you exceed this limit, you'll receive a `429 Too Many Requests` error.

Need higher limits? Contact `tommy[at]chien.io` with your use case.

## Checking Usage

**GET** `/stats/usage?days=7`

View your usage statistics for the past N days (1-30).

```

```

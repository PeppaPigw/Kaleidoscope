# RAG系统现状分析与改进方案

**日期:** 2026-04-18  
**状态:** 🟡 部分完成，需要集成

---

## 📊 当前系统架构

### 1. 已实现的组件

#### ✅ 论文摄取流程 (Ingestion Pipeline)

```
ingest_paper → acquire_fulltext → parse_via_mineru/parse_fulltext → index_paper
```

**功能:**

- DOI/arXiv/PMID/URL 标识符规范化
- 元数据丰富（CrossRef, OpenAlex, Semantic Scholar）
- 全文获取（PDF下载）
- 两种解析方式：
  - **MinerU**: PDF/HTML → Markdown（云API）
  - **GROBID**: PDF → 结构化文本（本地）
- 搜索索引（Meilisearch）

**文件位置:**

- `backend/app/tasks/ingest_tasks.py`
- `backend/app/services/ingestion/`

#### ✅ Embedding系统

```
embed_paper_async → parse_sections → batch_embed → store_vectors
```

**功能:**

- Markdown分段解析（H1-H6标题识别）
- 批量embedding（GLM-Embedding-2，batch_size=16）
- 向量存储（PostgreSQL pgvector）
- 定期扫描未embedding的论文

**文件位置:**

- `backend/app/tasks/embedding_tasks.py`
- `backend/app/models/paper_qa.py` (PaperChunk, PaperEmbeddingJob)

#### ✅ RAGFlow集成（外部服务）

```
RagflowClient → chat_completion / retrieve
```

**功能:**

- Dataset管理（创建、同步）
- 文档上传到RAGFlow
- 聊天补全（带引用）
- 向量检索

**文件位置:**

- `backend/app/services/ragflow/ragflow_client.py`
- `backend/app/services/ragflow/ragflow_query_service.py`
- `backend/app/services/ragflow/ragflow_sync_tasks.py`

#### ✅ Collection系统

```
Collections (workspace/subscription/paper_group) → Papers → Threads → Messages
```

**功能:**

- 三种collection类型
- 论文管理（添加、删除、排序）
- 聊天线程管理
- 消息持久化

**文件位置:**

- `backend/app/services/collection_service.py`
- `backend/app/api/v1/collections.py`

---

## 🔴 当前问题

### 问题1: RAG系统未完全集成

**现状:**

- ✅ Embedding已实现（向量存储在本地PostgreSQL）
- ✅ RAGFlow客户端已实现
- ❌ **两个系统未连接** - embedding数据未被RAG查询使用
- ❌ RAGFlow当前被禁用（`RAGFLOW_SYNC_ENABLED=false`）

**影响:**

- Landscape聊天功能返回："Group chat is unavailable because RAGFlow sync is disabled."
- 已生成的embedding向量未被利用
- 用户无法对论文进行智能问答

### 问题2: Collection论文未自动触发全流程

**现状:**
当用户添加论文到collection时：

```python
# app/services/collection_service.py
async def add_papers(collection_id, paper_ids):
    # 只是创建 CollectionPaper 关联
    # ❌ 不触发任何处理流程
    return added_count
```

**缺失的流程:**

1. ❌ 不检查论文是否已解析（MinerU/GROBID）
2. ❌ 不触发embedding生成
3. ❌ 不同步到RAGFlow
4. ❌ 不进行LLM分析

**影响:**

- 用户添加论文后无法立即聊天
- 需要手动触发sync
- 用户体验差

### 问题3: 双RAG系统架构混乱

**当前有两套系统:**

1. **本地Embedding系统**
   - 数据: `paper_chunks` + `paper_embedding_jobs`
   - 向量: PostgreSQL pgvector
   - 查询: 未实现

2. **RAGFlow外部服务**
   - 数据: 上传到RAGFlow云端
   - 向量: RAGFlow管理
   - 查询: `ragflow_client.chat_completion()`

**问题:**

- 重复存储（本地+云端）
- 不清楚应该使用哪个系统
- 维护成本高

---

## 🎯 改进方案

### 方案A: 统一使用本地RAG系统（推荐）

**优点:**

- ✅ 数据完全自主控制
- ✅ 无外部依赖
- ✅ 成本低（无API费用）
- ✅ 延迟低（本地查询）
- ✅ 隐私保护

**需要实现:**

#### 1. 本地向量检索服务

```python
# backend/app/services/vector_search_service.py
class VectorSearchService:
    async def search_similar_chunks(
        self,
        query_embedding: list[float],
        paper_ids: list[str] | None = None,
        top_k: int = 10
    ) -> list[PaperChunk]:
        """使用pgvector进行相似度搜索"""
        # SELECT * FROM paper_chunks
        # WHERE paper_id = ANY(paper_ids)
        # ORDER BY embedding <=> query_embedding
        # LIMIT top_k
```

#### 2. 本地RAG查询服务

```python
# backend/app/services/local_rag_service.py
class LocalRAGService:
    async def ask_collection(
        self,
        collection_id: str,
        question: str,
        top_k: int = 10
    ) -> dict:
        """基于collection中的论文回答问题"""
        # 1. 获取collection中的所有paper_ids
        # 2. 对question进行embedding
        # 3. 向量检索相关chunks
        # 4. 构建prompt + context
        # 5. 调用LLM生成答案
        # 6. 返回答案 + 引用来源
```

#### 3. 自动触发流程

```python
# backend/app/services/collection_service.py
async def add_papers(self, collection_id, paper_ids):
    added = 0
    for pid in paper_ids:
        # ... 添加到collection ...

        # 🆕 触发全流程处理
        paper = await self._get_paper(pid)

        # 检查是否需要解析
        if not paper.full_text_markdown:
            # 触发MinerU解析
            from app.tasks.ingest_tasks import parse_via_mineru
            if paper.remote_urls:
                url = paper.remote_urls[0]['url']
                parse_via_mineru.delay(pid, url)

        # 检查是否需要embedding
        job = await self._get_embedding_job(pid)
        if not job or job.status == 'failed':
            from app.tasks.embedding_tasks import process_paper_embedding
            process_paper_embedding.delay(pid, priority=10)

        added += 1

    return added
```

#### 4. LLM分析任务（可选）

```python
# backend/app/tasks/analysis_tasks.py
@celery_app.task(name="analysis.analyze_paper")
def analyze_paper_task(paper_id: str):
    """使用LLM分析论文内容"""
    # 1. 读取full_text_markdown
    # 2. 调用LLM提取：
    #    - 研究问题
    #    - 方法论
    #    - 主要贡献
    #    - 局限性
    # 3. 存储到paper.summary, paper.contributions等字段
```

**实现步骤:**

1. ✅ Embedding系统已完成
2. 🔨 实现VectorSearchService（使用pgvector）
3. 🔨 实现LocalRAGService（LLM + context）
4. 🔨 修改add_papers触发全流程
5. 🔨 实现LLM分析任务（可选）
6. 🔨 更新landscape页面使用本地RAG

---

### 方案B: 统一使用RAGFlow（不推荐）

**优点:**

- ✅ RAGFlow功能完整（chunk、embed、retrieve、chat）
- ✅ 无需自己实现向量检索

**缺点:**

- ❌ 依赖外部服务
- ❌ 数据上传到云端（隐私问题）
- ❌ API费用
- ❌ 网络延迟

**需要实现:**

1. 启用RAGFlow（`RAGFLOW_SYNC_ENABLED=true`）
2. 配置API密钥
3. 修改add_papers触发RAGFlow同步
4. 删除本地embedding系统（或保留作为备份）

---

### 方案C: 混合架构（最灵活）

**架构:**

- 本地embedding作为主系统
- RAGFlow作为可选增强（高级功能）

**实现:**

```python
class HybridRAGService:
    async def ask_collection(self, collection_id, question):
        if settings.ragflow_sync_enabled:
            # 使用RAGFlow（更强大）
            return await self.ragflow_service.ask_workspace(...)
        else:
            # 使用本地RAG（基础功能）
            return await self.local_rag_service.ask_collection(...)
```

---

## 📋 推荐实施计划

### 阶段1: 完成本地RAG系统（1-2天）

**任务清单:**

- [ ] 实现`VectorSearchService`（pgvector查询）
- [ ] 实现`LocalRAGService`（LLM + context）
- [ ] 添加API端点：`POST /api/v1/collections/{id}/ask-local`
- [ ] 测试向量检索准确性

**验收标准:**

- 能够基于collection中的论文回答问题
- 返回答案 + 引用来源（chunk + paper）
- 响应时间 < 3秒

### 阶段2: 自动触发全流程（1天）

**任务清单:**

- [ ] 修改`add_papers`检查论文状态
- [ ] 自动触发MinerU解析（如果需要）
- [ ] 自动触发embedding生成（如果需要）
- [ ] 添加状态追踪（processing/ready）

**验收标准:**

- 添加论文后自动开始处理
- 用户可以看到处理进度
- 处理完成后可以立即聊天

### 阶段3: LLM深度分析（可选，1-2天）

**任务清单:**

- [ ] 实现`analyze_paper_task`
- [ ] 提取summary, contributions, limitations
- [ ] 在论文详情页展示分析结果
- [ ] 添加重新分析按钮

**验收标准:**

- 每篇论文有AI生成的摘要
- 显示主要贡献和局限性
- 用户可以手动触发重新分析

### 阶段4: 优化与增强（持续）

**任务清单:**

- [ ] 优化向量检索算法（重排序、过滤）
- [ ] 添加多轮对话支持（conversation history）
- [ ] 实现跨collection搜索
- [ ] 添加引用可视化（高亮原文）
- [ ] 性能优化（缓存、批处理）

---

## 🔧 技术细节

### PostgreSQL pgvector查询示例

```sql
-- 创建向量索引（如果还没有）
CREATE INDEX ON paper_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 相似度搜索
SELECT
    pc.id,
    pc.paper_id,
    pc.section_title,
    pc.content,
    pc.embedding <=> $1::vector AS distance,
    p.title AS paper_title
FROM paper_chunks pc
JOIN papers p ON p.id = pc.paper_id
WHERE pc.paper_id = ANY($2::uuid[])
ORDER BY pc.embedding <=> $1::vector
LIMIT $3;
```

### LLM Prompt模板

```python
COLLECTION_QA_PROMPT = """你是一个学术研究助手。基于以下论文片段回答用户的问题。

相关论文片段：
{context}

用户问题：{question}

请基于上述论文片段回答问题。如果片段中没有相关信息，请明确说明。
在回答中引用具体的论文和章节。

回答："""

def build_context(chunks: list[PaperChunk]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[{i}] 论文: {chunk.paper.title}\n"
            f"章节: {chunk.section_title}\n"
            f"内容: {chunk.content}\n"
        )
    return "\n\n".join(context_parts)
```

---

## 📊 当前数据库状态

### 已有的表结构

```sql
-- Embedding相关
paper_chunks (
    id, paper_id, section_title, content,
    embedding vector(1024), -- 已有向量数据
    order_index, token_estimate
)

paper_embedding_jobs (
    id, paper_id, status, chunk_count,
    started_at, finished_at, error_message
)

-- RAGFlow相关
ragflow_document_mappings (
    id, paper_id, collection_id,
    ragflow_dataset_id, ragflow_document_id,
    parse_status, last_synced_at
)

-- Collection相关
collections (id, user_id, name, kind, paper_count)
collection_papers (collection_id, paper_id, position)
collection_chat_threads (id, collection_id, title)
collection_chat_messages (id, thread_id, role, content, sources)
```

### 数据统计

```bash
# 检查已embedding的论文数量
SELECT COUNT(DISTINCT paper_id) FROM paper_embedding_jobs WHERE status = 'completed';

# 检查向量数据
SELECT COUNT(*) FROM paper_chunks WHERE embedding IS NOT NULL;

# 检查collection中的论文
SELECT c.name, COUNT(cp.paper_id)
FROM collections c
LEFT JOIN collection_papers cp ON c.id = cp.collection_id
GROUP BY c.id;
```

---

## 🚀 快速启动指南

### 立即可用的功能

1. **Embedding生成**

```bash
# 手动触发embedding
curl -X POST http://localhost:8000/api/v1/papers/{paper_id}/embed
```

2. **向量检索（需要实现）**

```python
# 示例代码
from app.services.vector_search_service import VectorSearchService

service = VectorSearchService(db)
results = await service.search_similar_chunks(
    query_embedding=query_vector,
    paper_ids=["paper-id-1", "paper-id-2"],
    top_k=10
)
```

3. **Collection聊天（需要切换到本地RAG）**

```python
# 当前使用RAGFlow（已禁用）
# 需要切换到LocalRAGService
```

---

## 💡 建议

### 短期（本周）

1. **实现本地RAG系统** - 让landscape聊天功能可用
2. **自动触发流程** - 添加论文后自动处理

### 中期（本月）

3. **LLM深度分析** - 为每篇论文生成AI摘要
4. **优化用户体验** - 进度显示、错误处理

### 长期（持续）

5. **高级功能** - 多轮对话、跨collection搜索
6. **性能优化** - 缓存、批处理、索引优化

---

## 📝 总结

**当前状态:**

- ✅ 基础设施完整（ingestion, embedding, RAGFlow client）
- 🟡 系统未集成（各组件独立运行）
- ❌ 用户体验不完整（无法使用聊天功能）

**核心问题:**

1. 本地embedding未被RAG查询使用
2. Collection论文未自动触发全流程
3. 双RAG系统架构混乱

**推荐方案:**

- **优先实现本地RAG系统**（方案A）
- 保持RAGFlow作为可选增强
- 自动触发全流程处理

**预期效果:**

- 用户添加论文 → 自动解析 → 自动embedding → 立即可聊天
- 完全本地化，无外部依赖
- 数据隐私保护

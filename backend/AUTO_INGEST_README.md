# 自动论文采集与处理系统

## 概述

系统现在具备三层自动化论文采集机制，持续扩展和更新数据库：

## 1. 用户触发的自动采集（Dashboard）

### 触发时机

- 用户访问 Dashboard 页面时自动触发

### 采集内容

1. **Trending Papers**（热门论文）
   - 最近 7 天的热门论文（最多 30 篇）
   - 基于 DeepXiv 的热度排名

2. **For You Papers**（个性化推荐）
   - 基于用户订阅的类别和关键词
   - 最多 6 篇相关论文

### 实现细节

- 前端：`frontend/app/pages/dashboard.vue`
- 后端 API：
  - `POST /api/v1/deepxiv/trending/ingest`
  - `POST /api/v1/deepxiv/papers/ingest`
- 特性：
  - Fire-and-forget 模式（不阻塞页面加载）
  - 自动去重（已存在的论文会被跳过）
  - 失败静默处理（记录日志但不影响用户体验）

## 2. 后台定时自动采集（Celery Beat）

### 任务名称

`auto_discover_papers`

### 执行频率

每小时执行一次

### 采集策略

#### 策略 1：多时间窗口热门论文

- 7 天热门（50 篇）
- 14 天热门（50 篇）
- 30 天热门（50 篇）
- 来源：DeepXiv Trending API

#### 策略 2：高影响力论文（按类别）

针对以下核心类别，搜索高引用论文（引用数 ≥ 10）：

- `cs.AI` - 人工智能
- `cs.LG` - 机器学习
- `cs.CL` - 计算语言学
- `cs.CV` - 计算机视觉
- `stat.ML` - 统计机器学习

每个类别抓取 20 篇论文。

### 实现细节

- 任务定义：`backend/app/tasks/ingest_tasks.py::auto_discover_papers`
- 调度配置：`backend/app/worker.py::beat_schedule`
- 特性：
  - 自动去重（跨所有批次）
  - 失败重试（最多 3 次，间隔 5 分钟）
  - 详细日志记录

## 3. RSS 订阅源轮询（已有功能）

### 任务名称

`poll_rss_feeds`

### 执行频率

根据配置的 `rss_poll_interval_minutes` 参数

### 采集内容

- 用户配置的 RSS 订阅源
- 新发布的论文

## 数据处理流水线

所有采集的论文都会进入统一的处理流水线：

```
ingest_paper → acquire_fulltext → parse_fulltext → index_paper
```

### 各阶段说明

1. **ingest_paper**
   - 从 arXiv 获取元数据
   - 创建数据库记录
   - 提取作者、标题、摘要等信息

2. **acquire_fulltext**
   - 下载 PDF 文件
   - 转换为文本格式
   - 存储全文内容

3. **parse_fulltext**
   - 解析论文结构（章节、引用等）
   - 提取关键信息
   - 生成结构化数据

4. **index_paper**
   - 建立全文索引
   - 生成向量嵌入
   - 更新搜索引擎

## 任务队列配置

### 队列分类

- `ingestion` - 论文采集任务
- `parsing` - 文本解析任务
- `indexing` - 索引构建任务
- `embedding` - 向量嵌入任务
- `ragflow` - RAGFlow 同步任务

### 优先级

- 支持 0-10 级优先级
- 用户触发的任务优先级高于自动任务

## 监控与日志

### 日志记录

所有采集任务都会记录：

- 任务开始/完成时间
- 采集的论文数量
- 新增/跳过的论文数
- 失败的论文 ID 和错误信息

### 查看日志

```bash
# Celery worker 日志
tail -f logs/celery-worker.log

# Beat scheduler 日志
tail -f logs/celery-beat.log
```

### 监控指标

- `total_queued` - 总共入队的论文数
- `total_skipped` - 跳过的已存在论文数
- `failed` - 失败的任务数

## 配置与调优

### 调整采集频率

编辑 `backend/app/worker.py`：

```python
beat_schedule={
    "auto-discover-papers": {
        "task": "app.tasks.ingest_tasks.auto_discover_papers",
        "schedule": 3600,  # 改为其他秒数
    },
}
```

### 调整采集数量

编辑 `backend/app/tasks/ingest_tasks.py::auto_discover_papers`：

```python
# 修改 trending 的 limit 参数
trending_resp = await deepxiv.trending(days=days, limit=50)  # 改为其他数量

# 修改 search 的 size 参数
search_resp = await deepxiv.search(..., size=20, ...)  # 改为其他数量
```

### 添加新的采集类别

在 `auto_discover_papers` 函数中添加：

```python
categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML", "新类别"]
```

## 安全性改进

### API 保护

- 批量 ingest API 需要用户认证
- 限制每次请求最多 100 个 arxiv_id
- 自动去重和验证输入格式

### 错误处理

- 失败任务自动重试
- 详细的错误日志
- 不影响其他任务的执行

## 启动服务

### 启动 Celery Worker

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

### 启动 Celery Beat（定时任务调度器）

```bash
cd backend
celery -A app.worker.celery_app beat --loglevel=info
```

### 使用 Docker Compose（推荐）

```bash
docker-compose up -d celery-worker celery-beat
```

## 预期效果

### 每小时采集量

- Trending papers: ~150 篇（去重后约 50-100 篇新论文）
- Category papers: ~100 篇（去重后约 20-50 篇新论文）
- **总计：每小时约 70-150 篇新论文**

### 每日采集量

- **约 1,680-3,600 篇新论文**

### 数据库增长

- 假设 50% 的论文是新的
- 每日净增长：约 840-1,800 篇论文
- 每月净增长：约 25,000-54,000 篇论文

## 故障排查

### 任务不执行

1. 检查 Celery Beat 是否运行
2. 检查 Redis/RabbitMQ 连接
3. 查看 Beat 日志

### 任务失败率高

1. 检查 DeepXiv API 配额
2. 检查网络连接
3. 查看 Worker 日志

### 数据库增长缓慢

1. 检查去重逻辑（可能大部分论文已存在）
2. 增加采集频率或数量
3. 添加更多采集类别

## 未来改进方向

1. **智能采集**
   - 基于用户行为调整采集策略
   - 优先采集用户感兴趣的领域

2. **质量过滤**
   - 只采集高质量论文（引用数、期刊等级）
   - 过滤重复或低质量内容

3. **分布式采集**
   - 支持多个 Worker 并行采集
   - 负载均衡和任务分配

4. **实时监控**
   - Web 界面查看采集状态
   - 告警和通知机制

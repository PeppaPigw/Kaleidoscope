# 启动后台自动处理系统

## 问题诊断

您之前要求的后台自动处理系统**代码已经完全实现**，但是 **Celery 服务没有启动**，所以没有运行。

## 快速启动（推荐）

### 方法 1：使用启动脚本

```bash
cd backend
./start-celery.sh
```

这会启动：

- ✅ Celery Worker（处理任务）
- ✅ Celery Beat（定时调度器）

### 方法 2：手动启动（两个终端）

**终端 1 - Worker:**

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
```

**终端 2 - Beat:**

```bash
cd backend
celery -A app.worker.celery_app beat --loglevel=info
```

### 方法 3：使用 Docker Compose

```bash
docker-compose up -d celery-worker celery-beat
```

## 验证服务运行

```bash
# 检查进程
ps aux | grep celery

# 应该看到：
# - celery worker
# - celery beat
```

## 自动处理系统功能

一旦 Celery 启动，以下功能会自动运行：

### 1. 用户触发的自动采集

- 用户访问 `/dashboard` 时自动触发
- 采集 Trending 和 For You 论文
- Fire-and-forget 模式，不阻塞页面

### 2. 后台定时自动采集（每小时）

- **任务名称**: `auto_discover_papers`
- **执行频率**: 每小时一次
- **采集内容**:
  - 7/14/30 天热门论文（各 50 篇）
  - 5 个核心类别的高引用论文（各 20 篇）
- **预期**: 每小时 70-150 篇新论文

### 3. 完整处理流水线

所有采集的论文会自动进入：

```
ingest_paper → acquire_fulltext → parse_fulltext → index_paper
```

包括：

- 下载 PDF
- 使用 MinerU 解析
- 提取结构化数据
- 建立索引

## 监控日志

```bash
# Worker 日志
tail -f logs/celery-worker.log

# Beat 日志
tail -f logs/celery-beat.log
```

## 故障排查

### 问题：任务不执行

1. 检查 Redis 是否运行：`redis-cli ping`
2. 检查 PostgreSQL 是否运行
3. 查看 Worker 日志

### 问题：任务失败

1. 检查 DeepXiv API token 是否配置
2. 检查网络连接
3. 查看详细错误日志

## 配置调整

### 修改采集频率

编辑 `backend/app/worker.py`:

```python
"auto-discover-papers": {
    "task": "app.tasks.ingest_tasks.auto_discover_papers",
    "schedule": 3600,  # 改为其他秒数（如 1800 = 30分钟）
},
```

### 修改采集数量

编辑 `backend/app/tasks/ingest_tasks.py`:

```python
# 修改 trending 的 limit
trending_resp = await deepxiv.trending(days=days, limit=50)  # 改为其他数量

# 修改 search 的 size
search_resp = await deepxiv.search(..., size=20, ...)  # 改为其他数量
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

## 重要提示

⚠️ **必须启动 Celery 服务才能使用后台自动处理功能**

代码已经完全实现，只需要启动服务即可。

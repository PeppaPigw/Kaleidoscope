# 一键启动开发环境

## 使用方法

现在您只需要运行一个命令：

```bash
make dev
```

这会自动启动所有服务：

- ✅ Docker 基础设施（PostgreSQL, Redis, Meilisearch, Qdrant, Neo4j, MinIO, GROBID）
- ✅ 数据库迁移
- ✅ FastAPI 后端服务器（端口 8000）
- ✅ Nuxt 前端开发服务器（端口 3000）
- ✅ Celery Worker（处理后台任务）
- ✅ Celery Beat（定时调度器，每小时自动采集论文）

## 自动功能

启动后，以下功能会自动运行：

### 1. 用户触发的自动采集

- 访问 http://localhost:3000/dashboard 时自动采集论文
- 采集 Trending 和 For You 论文
- 不阻塞页面加载

### 2. 后台定时自动采集

- **每小时自动运行**
- 采集 7/14/30 天热门论文
- 采集 5 个核心类别的高引用论文
- 预期每小时 70-150 篇新论文

### 3. 完整处理流水线

所有论文自动走完整流水线：

```
ingest_paper → acquire_fulltext → parse_fulltext → index_paper
```

包括：

- 下载 PDF
- 使用 MinerU 解析
- 提取结构化数据
- 建立索引

## 验证服务运行

```bash
# 检查所有进程
ps aux | grep -E "uvicorn|celery|pnpm"

# 应该看到：
# - uvicorn (FastAPI)
# - celery worker
# - celery beat
# - node (Nuxt)
```

## 停止服务

按 `Ctrl+C` 停止所有服务

## 其他有用的命令

```bash
make help              # 查看所有可用命令
make infra             # 只启动 Docker 基础设施
make backend           # 只启动后端
make frontend          # 只启动前端
make celery            # 只启动 Celery (worker + beat)
make worker            # 只启动 Celery worker
make beat              # 只启动 Celery beat
```

## 首次设置

如果是第一次运行，先执行：

```bash
make setup
```

这会：

1. 启动 Docker 基础设施
2. 安装后端依赖
3. 安装前端依赖
4. 运行数据库迁移

然后就可以使用 `make dev` 了。

## 预期效果

- **每小时采集**: 70-150 篇新论文
- **每日采集**: 1,680-3,600 篇新论文
- **每月增长**: 25,000-54,000 篇论文

所有论文都会自动完成：

- PDF 下载
- MinerU 解析
- 全文索引
- 向量嵌入

## 监控日志

如果需要查看详细日志：

```bash
# 在另一个终端查看 Celery 日志
tail -f backend/logs/celery-worker.log
tail -f backend/logs/celery-beat.log
```

## 故障排查

### 问题：端口被占用

```bash
# 检查端口占用
lsof -i :8000  # FastAPI
lsof -i :3000  # Nuxt
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

### 问题：Docker 服务未启动

```bash
# 检查 Docker 状态
docker ps

# 重启基础设施
make infra-down
make infra
```

### 问题：Celery 任务不执行

```bash
# 检查 Redis 连接
redis-cli ping

# 检查 Celery 进程
ps aux | grep celery
```

## 总结

现在您只需要：

1. 首次运行：`make setup`
2. 日常开发：`make dev`

所有后台处理都会自动运行！

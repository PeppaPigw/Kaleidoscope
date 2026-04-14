# ═══════════════════════════════════════════════════════
#  Kaleidoscope — Development Makefile
# ═══════════════════════════════════════════════════════
.DEFAULT_GOAL := help
SHELL := /bin/bash

# ── Variables ─────────────────────────────────────────
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
DOCKER_DIR   := backend/docker
COMPOSE_FILE := $(DOCKER_DIR)/docker-compose.yml
COMPOSE_PROJECT_NAME := kaleidoscope
COMPOSE := docker compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE)
DEV_INFRA_SERVICES := postgres redis meilisearch qdrant neo4j minio grobid
DEV_CORE_SERVICES := postgres redis
DEV_INFRA_WAIT_TIMEOUT ?= 90
EXPECTED_POSTGRES_VOLUME := kaleidoscope_postgres_data

# ── Help ──────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Infrastructure ────────────────────────────────────
.PHONY: check-docker check-postgres-target infra infra-down infra-logs infra-dev
check-docker: ## Verify Docker is installed and the daemon is running
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required for Kaleidoscope dev."; exit 1; }
	@docker info >/dev/null 2>&1 || { echo "❌ Docker daemon is not running. Start Docker Desktop and retry."; exit 1; }

check-postgres-target: ## Ensure localhost:5432 maps to the expected Kaleidoscope Postgres volume
	@EXPECTED_POSTGRES_VOLUME=$(EXPECTED_POSTGRES_VOLUME) EXPECTED_COMPOSE_PROJECT_NAME=$(COMPOSE_PROJECT_NAME) COMPOSE_FILE=$(COMPOSE_FILE) \
		bash $(DOCKER_DIR)/check-postgres-target.sh

infra: ## Start all infrastructure services (Docker)
	@$(MAKE) check-docker
	@$(MAKE) check-postgres-target
	$(COMPOSE) up -d

infra-dev: ## Start infra needed by make dev and wait for core services
	@$(MAKE) check-docker
	@$(MAKE) check-postgres-target
	@echo "🐳 Ensuring Docker infrastructure is running..."
	@$(COMPOSE) up -d $(DEV_INFRA_SERVICES)
	@echo "⏳ Waiting for PostgreSQL and Redis..."
	@$(COMPOSE) up -d --wait --wait-timeout $(DEV_INFRA_WAIT_TIMEOUT) $(DEV_CORE_SERVICES)

infra-down: ## Stop all infrastructure services
	$(COMPOSE) down

infra-logs: ## Tail infrastructure logs
	$(COMPOSE) logs -f --tail=50

# ── Backend ───────────────────────────────────────────
.PHONY: backend backend-install migrate seed seed-feeds worker
backend: ## Start backend dev server
	cd $(BACKEND_DIR) && uvicorn app.main:create_app --factory --reload --port 8000

backend-install: ## Install backend dependencies
	cd $(BACKEND_DIR) && pip install -e ".[dev]"

migrate: ## Run Alembic migrations
	cd $(BACKEND_DIR) && alembic upgrade head

migrate-new: ## Create new migration (usage: make migrate-new MSG="add xyz")
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed 50 arXiv papers via MinerU
	cd $(BACKEND_DIR) && python -m app.scripts.seed_arxiv

seed-feeds: ## Seed RSS feed sources
	cd $(BACKEND_DIR) && python -m app.scripts.seed_feeds

worker: ## Start Celery worker
	cd $(BACKEND_DIR) && celery -A app.worker worker -l info

# ── Frontend ──────────────────────────────────────────
.PHONY: frontend frontend-install frontend-build
frontend: ## Start frontend dev server
	cd $(FRONTEND_DIR) && pnpm dev

frontend-install: ## Install frontend dependencies
	cd $(FRONTEND_DIR) && pnpm install

frontend-build: ## Build frontend for production
	cd $(FRONTEND_DIR) && pnpm build

# ── Development ───────────────────────────────────────
.PHONY: dev setup dev-bootstrap
dev-bootstrap: infra-dev migrate ## Ensure infra is ready and schema is up to date

dev: ## Start backend + frontend in parallel
	@echo "🚀 Starting Kaleidoscope..."
	@$(MAKE) dev-bootstrap
	@$(MAKE) -j2 backend frontend

setup: infra backend-install frontend-install migrate ## Full project setup
	@echo "✅ Kaleidoscope is ready! Run 'make dev' to start."

# ── Quality ───────────────────────────────────────────
.PHONY: lint lint-backend lint-frontend type-check test test-backend test-frontend
lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint backend (ruff)
	cd $(BACKEND_DIR) && ruff check app/ tests/

lint-frontend: ## Lint frontend (eslint)
	cd $(FRONTEND_DIR) && pnpm lint

type-check: ## Run type checks
	cd $(BACKEND_DIR) && mypy app/
	cd $(FRONTEND_DIR) && pnpm type-check

test: test-backend ## Run all tests

test-backend: ## Run backend tests
	cd $(BACKEND_DIR) && pytest -v

test-frontend: ## Run frontend tests
	cd $(FRONTEND_DIR) && pnpm test

# ── Cleanup ───────────────────────────────────────────
.PHONY: clean clean-deep
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/.nuxt
	rm -rf $(FRONTEND_DIR)/.output
	rm -rf $(BACKEND_DIR)/*.egg-info

clean-deep: clean ## Also remove node_modules and docker volumes
	rm -rf $(FRONTEND_DIR)/node_modules
	docker compose -f $(DOCKER_DIR)/docker-compose.yml down -v

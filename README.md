# OpenReview AI — Autonomous Multi-Agent Code Review Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20v0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20pgvector-336791.svg?style=flat&logo=postgresql)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Queue-Redis%20%26%20Celery-DC382D.svg?style=flat&logo=redis)](https://redis.io/)
[![Tests](https://img.shields.io/badge/Tests-9%20Passed-brightgreen.svg?style=flat)](#testing)

**OpenReview AI** is an autonomous multi-agent code review platform inspired by AI code review products such as CodeRabbit. It connects to GitHub, analyzes Pull Requests, detects bugs, security vulnerabilities, and performance issues, validates AI findings, generates suggested fixes, and publishes review comments.

---

## 🏗️ Project Architecture & Monorepo Structure

```
openreview-ai/
├── frontend/                     # React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
│   ├── src/
│   │   ├── components/           # UI primitives, Monaco diff viewer, finding cards
│   │   ├── pages/                # Dashboard, Repositories, PullRequests, ReviewDetail, Settings
│   │   ├── services/             # TanStack Query & API client wrappers
│   │   └── types/                # TypeScript schema interfaces
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                      # Python FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2
│   ├── alembic/                  # Database migration scripts & async env
│   ├── alembic.ini
│   ├── app/
│   │   ├── api/v1/               # Versioned REST endpoints (/health, /repositories, /reviews, /pull-requests)
│   │   ├── core/                 # Settings (Pydantic Settings v2), logging, exceptions, dependency injection
│   │   ├── db/                   # Async SQLAlchemy engine, session maker, base models
│   │   ├── models/               # ORM models (Repository, PullRequest, Review, ReviewComment)
│   │   ├── repositories/         # Async Data Access Objects (BaseRepository CRUD)
│   │   ├── schemas/              # Pydantic validation models & JSON envelopes
│   │   ├── services/             # Business logic layer (HealthService, ReviewService, LLMFactory)
│   │   └── main.py               # FastAPI application entrypoint, lifespan, CORS, middleware
│   └── requirements.txt
├── workers/                      # Distributed Celery tasks & background review queue
│   ├── celery_app.py             # Celery worker configuration with Redis broker
│   └── tasks/code_review.py      # Multi-agent review execution task
├── infrastructure/               # Containerization & deployment assets
│   ├── docker/                   # Dockerfiles for Backend, Worker, Frontend, NGINX
│   └── postgres/init-pgvector.sql# Database extension initialization (uuid-ossp, pgvector)
├── tests/                        # Comprehensive async test suite
│   ├── conftest.py               # Async test client & in-memory SQLite fixtures
│   ├── test_config.py            # Settings validation & CORS parsing tests
│   ├── test_health.py            # Health, liveness, and readiness probe tests
│   ├── test_repositories.py      # Repository CRUD & conflict prevention tests
│   └── test_reviews.py           # Review simulation & finding persistence tests
├── docs/                         # Architecture & developer documentation
│   ├── architecture.md           # Clean architecture, layering, component diagram
│   ├── api-specification.md      # API contract, schemas, error formats
│   ├── getting-started.md        # Step-by-step developer onboarding
│   └── multi-agent-design.md     # Multi-agent topology (Security, Perf, Quality Arbiter)
├── docker-compose.yml            # PostgreSQL 16 (pgvector), Redis 7, Backend, Worker
├── .env.example                  # Environment configuration template
├── .gitignore
├── pytest.ini
└── README.md
```

---

## 🛠️ Technology Stack

| Domain | Technologies |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui components, React Router v6, TanStack Query v5, Monaco Editor |
| **Backend** | Python 3.14 / 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, Greenlet, HTTPX |
| **AI Integration** | Provider-independent abstraction (OpenAI, Anthropic, Gemini, Groq, Ollama), Structured JSON outputs, LangGraph topology |
| **Infrastructure** | PostgreSQL 16 with `pgvector`, Redis 7, Celery, Docker & Docker Compose, GitHub App integration |

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional for PostgreSQL + pgvector & Redis)

### 2. Environment Configuration
Copy the template to `.env`:
```bash
cp .env.example .env
```
*Note: Local SQLite fallback (`sqlite+aiosqlite:///./openreview_dev.db`) is enabled by default for zero-dependency local runs.*

### 3. Start Backing Services (Docker Compose)
To start PostgreSQL (with `pgvector`) and Redis:
```bash
docker compose up -d postgres redis
```

### 4. Setup & Start Backend
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate      # On Linux / macOS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Apply database migrations
cd backend
alembic upgrade head
cd ..

# 4. Start FastAPI server
$env:PYTHONPATH="backend"       # Windows PowerShell
# export PYTHONPATH=backend     # Linux / macOS
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Interactive OpenAPI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 5. Setup & Start Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

---

## 🧪 Testing

Run the automated async test suite:
```bash
pytest -v tests
```
All 9 unit/integration tests pass with full database isolation:
```
tests/test_config.py::test_cors_origins_parsing PASSED
tests/test_config.py::test_database_url_normalization PASSED
tests/test_config.py::test_environment_flags PASSED
tests/test_health.py::test_root_endpoint PASSED
tests/test_health.py::test_liveness_probe PASSED
tests/test_health.py::test_readiness_probe PASSED
tests/test_health.py::test_full_health_endpoint PASSED
tests/test_repositories.py::test_register_and_list_repository PASSED
tests/test_reviews.py::test_review_simulation_workflow PASSED
============================== 9 passed in 2.24s ==============================
```

---

## 🛡️ Engineering Highlights

1. **Clean Architecture**: Clear separation of API routers, business service use-cases, and database repositories. Business logic is strictly kept out of API route handlers.
2. **Dependency Injection**: Database sessions, services, and configuration objects are injected into routes using FastAPI `Depends`.
3. **Structured Logging**: Context-correlated logging with `X-Request-ID` and timing metadata.
4. **Resilient Health Probes**: `/api/v1/health`, `/health/ready`, and `/health/live` report granular component latency and status without crashing on temporary dependencies.
5. **Secure CORS**: Strictly configurable whitelist of origins via environment variables.
6. **Provider-Independent AI**: Generic `BaseLLMProvider` interface supports OpenAI, Anthropic Claude, Google Gemini, Groq, and Ollama with structured output schemas.

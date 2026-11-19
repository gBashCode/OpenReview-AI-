# OpenReview AI — Architecture Documentation

## 1. System Vision & Overview
**OpenReview AI** is an autonomous multi-agent code review platform inspired by CodeRabbit. It connects to GitHub repositories, evaluates Pull Request diffs, identifies security vulnerabilities, performance bottlenecks, and code quality regressions, synthesizes findings via an Arbiter, and publishes suggested patches directly to GitHub.

---

## 2. Clean Architecture & Layering

The system is designed following strict separation of concerns, domain-driven boundaries, and inversion of control:

```
[ Frontend: React + TS + Tailwind + Vite + Monaco ]
                         │
                         ▼ (HTTP REST / JSON / OpenAPI)
┌────────────────────────────────────────────────────────┐
│               FastAPI API Layer (/api/v1)              │
│   - Endpoints: Health, Repositories, PRs, Reviews      │
│   - Middlewares: RequestContext (Trace ID), Secure CORS│
│   - Exception Handlers: Standardized error envelopes   │
└──────────────────────────┬─────────────────────────────┘
                           │ (Dependency Injection via Depends)
                           ▼
┌────────────────────────────────────────────────────────┐
│                   Service Layer                        │
│   - HealthService: Health check aggregator             │
│   - RepositoryService: Codebase sync & metadata        │
│   - ReviewService: Review pass orchestration           │
│   - LLMProviderService: Provider-independent LLM       │
│     (OpenAI, Anthropic, Gemini, Groq, Ollama)          │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 Repository Layer (DAO)                 │
│   - BaseRepository[T]: Generic async CRUD abstraction  │
│   - RepositoryRepo, ReviewRepo, ReviewCommentRepo      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               Data & Infrastructure Layer              │
│   - PostgreSQL 16 + pgvector (Vector embeddings)       │
│   - Async SQLAlchemy 2.0 (asyncpg / aiosqlite)         │
│   - Redis 7 (Cache, Pub/Sub, Celery Broker)            │
│   - Celery Workers (Distributed asynchronous reviews)  │
└────────────────────────────────────────────────────────┘
```

---

## 3. Multi-Agent Code Review Lifecycle

When a Pull Request is opened or updated on GitHub:

1. **Webhook Ingestion**: GitHub App sends `pull_request` event payload to OpenReview AI webhook receiver.
2. **Context & Diff Extraction**: Unified diff is parsed, identifying changed files, modified hunks, and surrounding abstract syntax tree (AST) context.
3. **Embeddings & Vector Indexing**: Code chunks are vectorized and compared against repository semantic patterns stored in PostgreSQL using `pgvector`.
4. **Specialized Multi-Agent Evaluation (LangGraph)**:
   - **Security Agent**: Specializes in detecting OWASP Top 10, CWE patterns, hardcoded secrets, injection vectors, and broken auth.
   - **Performance Agent**: Evaluates algorithmic complexity, potential memory leaks, N+1 query patterns, and unindexed database queries.
   - **Code Quality & Style Agent**: Enforces clean code principles, idiomatic patterns, naming conventions, and DRY rules.
5. **Arbiter & Synthesis Agent**: Aggregates all agent findings, deduplicates issues, filters false positives, calculates category scores (0-100), and formats unified diff patches.
6. **Publishing**: Verified review comments and the executive summary are posted back to GitHub as PR comments or checks.

---

## 4. Key Architectural Decisions

- **Provider-Independent LLM Design**: Interfaces abstract away the underlying LLM provider, allowing seamless switching or hybrid routing between OpenAI, Anthropic, Google Gemini, Groq, or local Ollama instances.
- **Strict Typing Everywhere**: Pydantic v2 on the backend guarantees input/output validation; TypeScript on the frontend matches all backend schemas.
- **Asynchronous I/O**: FastAPI with asynchronous SQLAlchemy 2.0 (`asyncpg`) and Redis (`redis.asyncio`) ensures high concurrency under heavy webhook loads.
- **Resilient Fallback**: Gracefully handles disconnected backing services with degraded status indicators rather than hard crashes.

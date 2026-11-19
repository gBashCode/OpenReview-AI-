# OpenReview AI — Production Deployment Runbook

This guide covers the deployment, configuration, scaling, and operations of the **OpenReview AI** autonomous multi-agent code review platform across cloud infrastructure (Vercel + Docker / Kubernetes / VM).

---

## 1. Architecture Overview

```
                                [ Cloudflare / Route53 DNS ]
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
       [ Frontend on Vercel Edge ]                       [ NGINX TLS 1.3 Reverse Proxy ]
       (React + Vite + Tailwind)                         (Port 80 -> 443, SSL, Rate Limits)
                     │                                                 │
                     │  /api/v1/* (Rewrites)                           ▼
                     └───────────────────────────────────────► [ FastAPI ASGI Service ]
                                                               (Gunicorn / Uvicorn Pool)
                                                                       │
                         ┌─────────────────────────────────────────────┼──────────────────────────────────┐
                         ▼                                             ▼                                  ▼
               [ PostgreSQL 16 ]                               [ Redis 7 Cluster ]            [ Observability Stack ]
               (pgvector, HNSW, Alembic)                      (Broker & Cache)                (OTel, Sentry, Prometheus)
                         ▲                                             │                                  ▲
                         │                                             ▼                                  │
                         │                                 [ Dedicated Celery Workers ]                    │
                         └──────────────────────────────── (reviews, indexing, autofix) ──────────────────┘
```

---

## 2. Frontend Deployment (React on Vercel)

The React single-page application is configured with [`frontend/vercel.json`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/frontend/vercel.json) to handle client-side routing, enterprise HTTP security headers, and reverse proxy rewrites to the API backend.

### Step 2.1: Connect Vercel Project
1. Import the repository in [Vercel Dashboard](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. Set **Framework Preset** to `Vite`.
4. Build command: `npm run build`
5. Output directory: `dist`

### Step 2.2: Configure Environment Variables in Vercel
Add the following environment variables in **Project Settings > Environment Variables**:

| Variable | Staging Value | Production Value | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `https://staging-api.openreview.ai/api/v1` | `https://api.openreview.ai/api/v1` | Public API base path |
| `VITE_APP_ENV` | `staging` | `production` | Environment name |
| `VITE_GITHUB_APP_NAME` | `openreview-ai-staging` | `openreview-ai` | GitHub App slug |
| `VITE_SENTRY_DSN` | *(Staging Sentry DSN)* | *(Production Sentry DSN)* | Frontend error tracking |
| `VITE_SENTRY_TRACES_SAMPLE_RATE`| `1.0` | `0.2` | APM trace sampling |

---

## 3. Backend Deployment (Dockerized FastAPI & NGINX)

The backend service is containerized via a multi-stage production Dockerfile ([`infrastructure/docker/Dockerfile.backend`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/docker/Dockerfile.backend)) and protected by an NGINX TLS 1.3 reverse proxy ([`infrastructure/docker/nginx.prod.conf`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/docker/nginx.prod.conf)).

### Step 3.1: Environment File Configuration
Create `.env.production` on the production host:
```bash
# Core Application Settings
APP_NAME="OpenReview AI"
APP_ENV=production
DEBUG=false
SECRET_KEY="<generate-random-64-character-secret>"
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# CORS
ALLOWED_ORIGINS="https://openreview.ai,https://app.openreview.ai"

# Database & Connection Pooling
POSTGRES_SERVER=postgres
POSTGRES_PORT=5432
POSTGRES_DB=openreview
POSTGRES_USER=openreview_admin
POSTGRES_PASSWORD="<strong-production-database-password>"
DATABASE_URL="postgresql+asyncpg://openreview_admin:<password>@postgres:5432/openreview"
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
DB_PRE_PING=true

# Redis & Celery Queues
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL="redis://:redis_secure_password@redis:6379/0"
CELERY_BROKER_URL="redis://:redis_secure_password@redis:6379/1"
CELERY_RESULT_BACKEND="redis://:redis_secure_password@redis:6379/2"

# LLM Providers
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="AIza..."

# Observability
LOG_FORMAT=json
LOG_LEVEL=INFO
PROMETHEUS_METRICS_ENABLED=true
SENTRY_DSN="https://...@sentry.io/..."
SENTRY_ENVIRONMENT=production
OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
```

### Step 3.2: Launch Production Services
```bash
# Run database migrations first
bash infrastructure/scripts/migrate.sh

# Start production compose cluster
docker compose -f docker-compose.prod.yml up -d
```

---

## 4. Dedicated Celery Worker Scaling

The background processing fleet is segmented into independent task queues to prevent indexing or long test suites from blocking PR review SLAs:

| Worker Service | Queues Listened | Concurrency | Primary Responsibilities |
| :--- | :--- | :--- | :--- |
| `worker-reviews` | `reviews,default` | 4 | Multi-agent review passes, conference deliberations |
| `worker-indexing` | `indexing` | 2 | Tree-sitter file discovery, chunking, pgvector embedding |
| `worker-autofix` | `autofix` | 2 | Patch generation, ephemeral sandbox test execution |
| `worker-publishing` | `publishing,dead_letter`| 2 | GitHub API inline comments, check runs, DLQ triage |
| `worker-beat` | periodic scheduler | 1 | Database retention cleanup, hourly health checks |

---

## 5. PostgreSQL & pgvector Database Management

### Database Extensions
Automatically enabled via [`infrastructure/postgres/init-pgvector.sql`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/postgres/init-pgvector.sql):
- `vector`: 1536-dimensional semantic chunk embeddings (HNSW indexes).
- `uuid-ossp`: High-performance UUIDv4 generation.
- `pg_trgm`: Trigram indexing for fuzzy symbol and keyword matching.
- `btree_gist`: Multi-column hybrid index acceleration.

### Automated Backups
Automated database backups are handled via [`infrastructure/scripts/backup-postgres.sh`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/scripts/backup-postgres.sh):
- Runs compressed custom dump (`pg_dump -Fc`).
- Computes SHA-256 integrity checksums.
- Automatically prunes archives older than 14 days.
- Uploads to cloud object storage (S3 / GCS).

Setup daily cron job on production host:
```bash
0 2 * * * /opt/openreview/infrastructure/scripts/backup-postgres.sh >> /var/log/openreview-backup.log 2>&1
```

---

## 6. Observability & Monitoring

1. **Prometheus Metrics Endpoint**:
   - Exposed on `GET /metrics` on the backend API.
   - Scraped every 15s by Prometheus.
2. **Alerting Rules**:
   - Configured in [`infrastructure/monitoring/prometheus/alert.rules.yml`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/monitoring/prometheus/alert.rules.yml).
   - Monitors HTTP 5xx error rate (>5%), API latency (>2s), worker failures, and LLM cost spikes (> $50/hr).
3. **Grafana Dashboards**:
   - Pre-provisioned via [`infrastructure/monitoring/grafana/dashboards/openreview_overview.json`](file:///c:/Users/admin/OneDrive/Documents/OpenReview%20AI/infrastructure/monitoring/grafana/dashboards/openreview_overview.json).
   - Access at `http://<host>:3000` (default login: `admin` / `${GRAFANA_ADMIN_PASSWORD}`).

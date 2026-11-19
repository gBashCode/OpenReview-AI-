# OpenReview AI — Production Rollback & Disaster Recovery Procedures

This guide provides step-by-step instructions for rolling back deployments, restoring databases from backups, and mitigating production outages.

---

## 1. Fast Rollback Decision Matrix

| Outage Scenario | Severity | Recommended Rollback Action | Estimated Recovery Time |
| :--- | :--- | :--- | :--- |
| **Frontend UI Regression** | High | Instant rollback via Vercel dashboard / CLI | < 1 minute |
| **Backend API Health Check Failure** | Critical | Revert container image tag to previous stable build | < 3 minutes |
| **Database Migration Error** | Critical | Downgrade Alembic migration (`alembic downgrade -1`) | < 5 minutes |
| **Data Corruption / Data Loss** | Catastrophic | Full PostgreSQL restore from pre-rollout `.dump` | 10–20 minutes |
| **Worker Queue Poison Pill** | High | Purge failed task ID / drain to Dead-Letter Queue | < 2 minutes |

---

## 2. Frontend Instant Rollback (Vercel)

Vercel stores immutable builds for every git commit.

### Method A: Via Vercel Web Dashboard (Fastest)
1. Navigate to **Project > Deployments** in the [Vercel Dashboard](https://vercel.com).
2. Locate the previous healthy deployment (e.g., from prior release).
3. Click the three dots `...` next to the deployment and select **Promote to Production**.
4. Traffic is redirected instantly (0-second cutover).

### Method B: Via Vercel CLI
```bash
# List recent deployments
vercel ls

# Instantly assign production domain to previous healthy deployment URL
vercel alias set <previous-healthy-deployment-url>.vercel.app app.openreview.ai
```

---

## 3. Backend & Worker Container Rollback

If a new Docker release of `backend` or `worker` experiences high error rates or fatal crashes:

### Step 3.1: Revert Container Version
On the production host:
```bash
cd /opt/openreview

# Checkout the previous release git tag
git checkout v0.1.0-stable

# Pull previous stable images
docker compose -f docker-compose.prod.yml pull

# Rolling recreate backend services
docker compose -f docker-compose.prod.yml up -d --no-deps backend

# Restart Celery workers
docker compose -f docker-compose.prod.yml up -d --no-deps worker-reviews worker-indexing worker-autofix worker-publishing

# Verify API health
curl -f http://127.0.0.1:8000/api/v1/health
```

---

## 4. Database Migration Rollback (Alembic)

If a schema migration introduces an unexpected constraint or column incompatibility:

### Step 4.1: Identify Current Revision
```bash
alembic -c backend/alembic.ini current
```

### Step 4.2: Downgrade Migration
```bash
# Downgrade by 1 revision
alembic -c backend/alembic.ini downgrade -1

# Or downgrade to specific target revision ID
alembic -c backend/alembic.ini downgrade 005_finding_verification_fields
```

---

## 5. Full Database Disaster Recovery Restore

If database corruption or irreversible data loss occurs, restore from the automated backup:

```bash
# Syntax: bash infrastructure/scripts/restore-postgres.sh <backup_file.dump>
bash infrastructure/scripts/restore-postgres.sh /backups/openreview_backup_20261119_120000Z.dump
```

The restore script:
1. Validates the SHA-256 cryptographic checksum.
2. Cleans existing corrupt tables.
3. Restores all relations, foreign keys, and 1536-dimensional pgvector embeddings.
4. Verifies database connectivity.

---

## 6. Celery Worker Dead-Letter Queue (DLQ) Triage

When tasks fail repeatedly and exceed the 5-attempt exponential backoff threshold, they are automatically diverted to the `dead_letter` queue:

```bash
# Inspect queued dead-letter tasks in Redis
docker exec -it openreview-prod-redis redis-cli -a redis_secure_password LLEN dead_letter

# Query failed task forensic details from AuditLog table
docker exec -it openreview-prod-postgres psql -U openreview_admin -d openreview -c \
  "SELECT id, action, entity_id, created_at, metadata_json FROM audit_logs WHERE action LIKE 'task_failure_dlq%' ORDER BY created_at DESC LIMIT 5;"
```

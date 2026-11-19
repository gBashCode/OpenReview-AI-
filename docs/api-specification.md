# OpenReview AI — API Specification

The OpenReview AI backend exposes versioned REST APIs under `/api/v1` with interactive OpenAPI documentation available at `/docs` and `/redoc`.

---

## 1. Global Standards

### Error Envelope Format
All non-2xx responses follow a standardized JSON envelope:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed. Please inspect the details.",
    "details": {}
  }
}
```

### Context Headers
Every response includes:
- `X-Request-ID`: Unique UUID tracking request lifecycle across logs.
- `X-Response-Time`: Server processing duration in milliseconds (e.g. `2.45ms`).

---

## 2. Health & Readiness Endpoints

### `GET /api/v1/health`
Performs comprehensive inspection across backing dependencies (PostgreSQL + pgvector, Redis).
- **Response**: `200 OK`
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-11-19T05:20:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 0.57,
      "message": "Connected (pgvector extension active)"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 1.20,
      "message": "PONG received"
    }
  }
}
```

### `GET /api/v1/health/live`
Liveness probe for orchestrators (Kubernetes / Docker).
- **Response**: `{"status": "alive"}`

### `GET /api/v1/health/ready`
Readiness probe verifying database connectivity before accepting user traffic.
- **Response**: `200 OK` with `{"status": "ready", "database": "Connected"}` or `503 Service Unavailable`.

---

## 3. Repositories Endpoints

### `GET /api/v1/repositories`
List active repositories configured for code review.
- Query parameters: `skip` (default 0), `limit` (default 50)
- **Response**: `200 OK` (Array of Repository objects)

### `POST /api/v1/repositories`
Register a GitHub repository.
- **Request Body**:
```json
{
  "github_repo_id": 1296269,
  "owner": "google-deepmind",
  "name": "openreview-ai",
  "default_branch": "main",
  "description": "Multi-agent review platform",
  "is_active": true
}
```
- **Response**: `201 Created`

### `GET /api/v1/repositories/{id}`
Retrieve repository details by ID.

### `PATCH /api/v1/repositories/{id}`
Update repository settings (default branch, description, active state).

### `DELETE /api/v1/repositories/{id}`
Unlink repository (`204 No Content`).

---

## 4. Pull Requests Endpoints

### `GET /api/v1/pull-requests`
List tracked pull requests.
- Optional query param: `repository_id`

### `POST /api/v1/pull-requests`
Register pull request from webhook.
- **Request Body**:
```json
{
  "repository_id": "UUID",
  "pr_number": 42,
  "title": "feat: add payment gateway",
  "head_branch": "feature/payments",
  "base_branch": "main",
  "head_sha": "7f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
  "base_sha": "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b",
  "author_username": "octocat"
}
```

---

## 5. Reviews Endpoints

### `POST /api/v1/reviews`
Initiate a review pass on a pull request.
- **Request Body**: `{"pull_request_id": "UUID", "commit_sha": "string"}`
- **Response**: `201 Created`

### `GET /api/v1/reviews/{id}`
Retrieve review details along with list of findings and suggested patches.

### `POST /api/v1/reviews/{id}/simulate-ai-pass`
Trigger simulation pass of multi-agent review analysis, generating structured findings and scores.

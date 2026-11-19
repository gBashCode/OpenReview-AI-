# OpenReview AI — Getting Started & Local Development

This guide covers setting up and running **OpenReview AI** locally.

---

## 1. Prerequisites

- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Node.js**: v18, v20, or v22+
- **Docker & Docker Compose** (Optional for local PostgreSQL + pgvector and Redis)

---

## 2. Quick Setup

### Step 1: Clone and Configure Environment
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

For zero-dependency local development, SQLite is enabled by default:
```env
DATABASE_URL=sqlite+aiosqlite:///./openreview_dev.db
```
When Docker is running, switch to PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://openreview_admin:openreview_secure_password@localhost:5432/openreview
```

---

## 3. Running with Docker Compose (PostgreSQL & Redis)

To launch backing PostgreSQL (with `pgvector` extension) and Redis:
```bash
docker compose up -d postgres redis
```
To check container status:
```bash
docker compose ps
```

---

## 4. Backend Setup & Execution

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run Database Migrations
```bash
cd backend
alembic upgrade head
cd ..
```

### 4. Run the Backend Server
```bash
# Set PYTHONPATH to include backend/
export PYTHONPATH=backend       # Linux / macOS
$env:PYTHONPATH="backend"        # Windows PowerShell

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API is available at:
- **Root**: `http://localhost:8000/`
- **Swagger UI**: `http://localhost:8000/docs`
- **Health check**: `http://localhost:8000/api/v1/health`

---

## 5. Frontend Setup & Execution

### 1. Install NPM Packages
```bash
cd frontend
npm install
```

### 2. Start Vite Development Server
```bash
npm run dev
```
Open **http://localhost:5173** in your browser.
API calls are automatically proxied to `http://localhost:8000`.

### 3. Production Build
```bash
npm run build
```

---

## 6. Running Tests

Execute the comprehensive test suite with pytest:
```bash
pytest -v tests
```
All tests use in-memory SQLite sessions and isolated mock settings.

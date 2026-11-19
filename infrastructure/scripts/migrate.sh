#!/usr/bin/env bash
# ==============================================================================
# OpenReview AI - Automated Database Migration Runner
# ==============================================================================
set -euo pipefail

echo "======================================================================"
echo " Starting Database Migrations with Alembic"
echo "======================================================================"

MAX_RETRIES=30
RETRY_INTERVAL=2

echo "Checking database connectivity..."
count=0
until python -c "
import asyncio
from app.database.session import check_db_connectivity
assert asyncio.run(check_db_connectivity())
" 2>/dev/null; do
    count=$((count + 1))
    if [ "$count" -ge "$MAX_RETRIES" ]; then
        echo "Error: Database did not become ready after $((MAX_RETRIES * RETRY_INTERVAL)) seconds."
        exit 1
    fi
    echo "Waiting for database to accept connections ($count/$MAX_RETRIES)..."
    sleep "$RETRY_INTERVAL"
done

echo "Database is ready. Executing 'alembic upgrade head'..."
alembic -c backend/alembic.ini upgrade head

echo "======================================================================"
echo " Database Migrations Completed Successfully!"
echo "======================================================================"

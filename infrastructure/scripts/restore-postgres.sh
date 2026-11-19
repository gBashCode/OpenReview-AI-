#!/usr/bin/env bash
# ==============================================================================
# OpenReview AI - Database Restore Runner
# ==============================================================================
set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file.dump>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: Backup file '${BACKUP_FILE}' does not exist."
    exit 1
fi

echo "======================================================================"
echo " Restoring Database from ${BACKUP_FILE}"
echo "======================================================================"

# Verify checksum if present
if [ -f "${BACKUP_FILE}.sha256" ]; then
    echo "Verifying SHA-256 integrity..."
    sha256sum -c "${BACKUP_FILE}.sha256"
fi

echo "Restoring database schemas and pgvector embeddings..."
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    -h "${POSTGRES_SERVER:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-openreview_admin}" \
    -d "${POSTGRES_DB:-openreview}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    -v \
    "${BACKUP_FILE}"

echo "Database restoration completed successfully."

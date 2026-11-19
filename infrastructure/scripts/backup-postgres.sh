#!/usr/bin/env bash
# ==============================================================================
# OpenReview AI - Automated PostgreSQL & pgvector Backup Script
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/openreview_backup_${TIMESTAMP}.dump"
CHECKSUM_FILE="${BACKUP_FILE}.sha256"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -u)] Starting OpenReview AI database backup..."
echo "Target file: ${BACKUP_FILE}"

# Execute custom-format compressed backup
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_SERVER:-localhost}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-openreview_admin}" \
    -d "${POSTGRES_DB:-openreview}" \
    -F c \
    -b \
    -v \
    -f "${BACKUP_FILE}"

# Generate SHA-256 checksum for data integrity validation
sha256sum "${BACKUP_FILE}" > "${CHECKSUM_FILE}"
echo "[$(date -u)] Checksum computed: $(cat "${CHECKSUM_FILE}")"

# Prune old backups exceeding retention policy
echo "[$(date -u)] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f -name "openreview_backup_*.dump*" -mtime +"${RETENTION_DAYS}" -exec rm -f {} +

# Optional Cloud Storage Upload (AWS S3 or Google Cloud Storage)
if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
    echo "[$(date -u)] Uploading backup to S3 bucket ${BACKUP_S3_BUCKET}..."
    aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_S3_BUCKET}/postgres/openreview_backup_${TIMESTAMP}.dump"
    aws s3 cp "${CHECKSUM_FILE}" "s3://${BACKUP_S3_BUCKET}/postgres/openreview_backup_${TIMESTAMP}.dump.sha256"
elif [ -n "${BACKUP_GCS_BUCKET:-}" ]; then
    echo "[$(date -u)] Uploading backup to GCS bucket ${BACKUP_GCS_BUCKET}..."
    gsutil cp "${BACKUP_FILE}" "gs://${BACKUP_GCS_BUCKET}/postgres/openreview_backup_${TIMESTAMP}.dump"
    gsutil cp "${CHECKSUM_FILE}" "gs://${BACKUP_GCS_BUCKET}/postgres/openreview_backup_${TIMESTAMP}.dump.sha256"
fi

echo "[$(date -u)] Backup completed successfully: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

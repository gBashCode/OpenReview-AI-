# ==============================================================================
# OpenReview AI - Automated PostgreSQL & pgvector Backup Script (PowerShell)
# ==============================================================================
param(
    [string]$BackupDir = "backups",
    [int]$RetentionDays = 14,
    [string]$HostName = "localhost",
    [int]$Port = 5432,
    [string]$Database = "openreview",
    [string]$User = "openreview_admin"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmssZ")
$backupFile = Join-Path $BackupDir "openreview_backup_$timestamp.dump"
$checksumFile = "$backupFile.sha256"

Write-Host "[$(Get-Date)] Starting OpenReview AI database backup..." -ForegroundColor Cyan
Write-Host "Destination: $backupFile" -ForegroundColor Yellow

$pgDumpPath = "pg_dump.exe"
if (-not (Get-Command $pgDumpPath -ErrorAction SilentlyContinue)) {
    Write-Warning "pg_dump.exe not in PATH. Checking docker container fallback..."
    & docker exec openreview-postgres pg_dump -U $User -d $Database -F c -b -f "/var/lib/postgresql/data/backup_$timestamp.dump"
    & docker cp "openreview-postgres:/var/lib/postgresql/data/backup_$timestamp.dump" $backupFile
} else {
    & $pgDumpPath -h $HostName -p $Port -U $User -d $Database -F c -b -f $backupFile
}

# Calculate hash
$hash = Get-FileHash -Path $backupFile -Algorithm SHA256
$hash.Hash | Out-File -FilePath $checksumFile -Encoding ascii

Write-Host "[$(Get-Date)] Backup created successfully ($((Get-Item $backupFile).Length / 1MB) MB)" -ForegroundColor Green

# Retention policy: remove backups older than $RetentionDays
$limitDate = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupDir -Filter "openreview_backup_*.dump*" | Where-Object { $_.LastWriteTime -lt $limitDate } | Remove-Item -Force
Write-Host "[$(Get-Date)] Pruned backups older than $RetentionDays days." -ForegroundColor DarkGray

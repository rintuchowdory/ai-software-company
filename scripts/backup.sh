#!/bin/bash
# AI Software Company — Backup Script

set -e

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting backup..."

# PostgreSQL
if [ -n "$DATABASE_URL" ]; then
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/project_state.sql"
    echo "PostgreSQL backed up"
fi

# Redis
if command -v redis-cli &> /dev/null; then
    redis-cli BGSAVE
    cp /var/lib/redis/dump.rdb "$BACKUP_DIR/redis.rdb" 2>/dev/null || true
    echo "Redis backed up"
fi

# Vector DB metadata (Pinecone doesn't export, but we can save index config)
echo "{\"index_name\": \"${PINECONE_INDEX_NAME}\", \"backup_date\": \"$(date -Iseconds)\"}" > "$BACKUP_DIR/pinecone_metadata.json"

# Upload to S3
if command -v aws &> /dev/null; then
    aws s3 sync "$BACKUP_DIR" "s3://${BACKUP_BUCKET:-ai-company-backups}/$(date +%Y%m%d)/"
    echo "Uploaded to S3"
fi

echo "Backup complete: $BACKUP_DIR"

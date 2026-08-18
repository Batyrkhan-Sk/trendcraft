#!/usr/bin/env bash
# Nightly Postgres backup with rotation.
#   crontab -e →  0 4 * * * /opt/trendcraft/deploy/backup.sh >> /var/log/trendcraft-backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/trendcraft}"
BACKUP_DIR="${BACKUP_DIR:-/opt/trendcraft-backups}"
KEEP_DAYS="${KEEP_DAYS:-7}"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$BACKUP_DIR/trendcraft-$STAMP.sql.gz"

# --clean lets the dump restore over an existing database without a manual drop.
docker compose exec -T postgres pg_dump \
	-U "${POSTGRES_USER:-trendcraft}" \
	-d "${POSTGRES_DB:-trendcraft}" \
	--clean --if-exists | gzip > "$OUT"

# Fail loudly on a truncated dump rather than silently keeping a useless file.
if [ ! -s "$OUT" ]; then
	echo "$(date -Is) BACKUP FAILED: empty dump at $OUT" >&2
	rm -f "$OUT"
	exit 1
fi

find "$BACKUP_DIR" -name 'trendcraft-*.sql.gz' -mtime "+$KEEP_DAYS" -delete
echo "$(date -Is) backup ok: $OUT ($(du -h "$OUT" | cut -f1))"

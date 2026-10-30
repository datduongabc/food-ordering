#!/bin/sh
# Dumps the database and the uploaded dish photos into /backups, then deletes copies older
# than BACKUP_KEEP_DAYS. Runs once with "once", otherwise every BACKUP_INTERVAL_SECONDS.
set -eu

backup() {
    stamp=$(date +%Y%m%d-%H%M%S)
    # Written under a temporary name, so a failed dump never looks like a good one.
    pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom \
        --file="/backups/db-$stamp.dump.partial"
    mv "/backups/db-$stamp.dump.partial" "/backups/db-$stamp.dump"
    tar -czf "/backups/media-$stamp.tar.gz.partial" -C /media .
    mv "/backups/media-$stamp.tar.gz.partial" "/backups/media-$stamp.tar.gz"
    find /backups \( -name 'db-*.dump' -o -name 'media-*.tar.gz' \) \
        -mtime +"${BACKUP_KEEP_DAYS:-7}" -delete
    echo "Backup $stamp written"
}

if [ "${1:-}" = "once" ]; then
    backup
    exit
fi

while true; do
    backup || echo "Backup failed" >&2
    sleep "${BACKUP_INTERVAL_SECONDS:-86400}"
done

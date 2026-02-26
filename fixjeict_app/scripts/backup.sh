#!/bin/bash

# FixJeICT v2 - Database Backup Script
# Creates timestamped backups and keeps last 30 days

# Configuration
INSTALL_DIR="/opt/fixjeict"
BACKUP_DIR="/var/backups/fixjeict"
DB_NAME="fixjeict.db"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
DATE=$(date +%Y%m%d_%H%M%S)

# Backup file path
BACKUP_FILE="$BACKUP_DIR/${DB_NAME%.*}_$DATE.db"

echo "FixJeICT v2 - Database Backup"
echo "=============================="
echo "Started at: $(date)"
echo

# Check if database exists
if [ ! -f "$INSTALL_DIR/$DB_NAME" ]; then
    echo "ERROR: Database not found at $INSTALL_DIR/$DB_NAME"
    exit 1
fi

# Perform backup
echo "Copying database..."
cp "$INSTALL_DIR/$DB_NAME" "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "✗ Backup failed!"
    exit 1
fi

echo

# Clean old backups
echo "Cleaning old backups (keeping last $RETENTION_DAYS days)..."
REMOVED=$(ls -t "$BACKUP_DIR"/${DB_NAME%.*}_*.db 2>/dev/null | tail -n +$((RETENTION_DAYS + 1)) | wc -l)

if [ "$REMOVED" -gt 0 ]; then
    ls -t "$BACKUP_DIR"/${DB_NAME%.*}_*.db 2>/dev/null | tail -n +$((RETENTION_DAYS + 1)) | xargs rm -f
    echo -e "✓ Removed $REMOVED old backup(s)"
else
    echo "✓ No old backups to remove"
fi

echo

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/${DB_NAME%.*}_*.db 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}' || echo "  No backups found"

echo
echo "Backup completed at: $(date)"
echo "Total backups: $(ls -1 "$BACKUP_DIR"/${DB_NAME%.*}_*.db 2>/dev/null | wc -l)"

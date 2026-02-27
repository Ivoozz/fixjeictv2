#!/bin/bash

# FixJeICT v2 - Health Check Script
# Checks if both applications are running and responding

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
MAIN_PORT=5000
ADMIN_PORT=5001
MAIN_URL="http://localhost:$MAIN_PORT"
ADMIN_URL="http://localhost:$ADMIN_PORT"

echo "FixJeICT v2 - Health Check"
echo "=========================="
echo

# Check systemd services
echo "Checking systemd services..."

if systemctl is-active --quiet fixjeict.service; then
    echo -e "${GREEN}✓${NC} fixjeict.service is running"
    MAIN_SERVICE=true
else
    echo -e "${RED}✗${NC} fixjeict.service is NOT running"
    MAIN_SERVICE=false
fi

if systemctl is-active --quiet fixjeict-admin.service; then
    echo -e "${GREEN}✓${NC} fixjeict-admin.service is running"
    ADMIN_SERVICE=true
else
    echo -e "${RED}✗${NC} fixjeict-admin.service is NOT running"
    ADMIN_SERVICE=false
fi

echo

# Check HTTP responses
echo "Checking HTTP endpoints..."

if [ "$MAIN_SERVICE" = true ]; then
    MAIN_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "${MAIN_URL}/health" --max-time 5 || echo "000")
    if [ "$MAIN_HTTP" = "200" ]; then
        echo -e "${GREEN}✓${NC} Main app responding (HTTP $MAIN_HTTP)"
    else
        echo -e "${RED}✗${NC} Main app not responding (HTTP $MAIN_HTTP)"
    fi
else
    echo -e "${YELLOW}⊘${NC} Main app service not running, skipping HTTP check"
fi

if [ "$ADMIN_SERVICE" = true ]; then
    ADMIN_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "${ADMIN_URL}/admin/health" --max-time 5 || echo "000")
    if [ "$ADMIN_HTTP" = "200" ]; then
        echo -e "${GREEN}✓${NC} Admin portal responding (HTTP $ADMIN_HTTP)"
    else
        echo -e "${RED}✗${NC} Admin portal not responding (HTTP $ADMIN_HTTP)"
    fi
else
    echo -e "${YELLOW}⊘${NC} Admin service not running, skipping HTTP check"
fi

echo

# Check database
echo "Checking database..."
DB_PATH="/opt/fixjeictv2/data/fixjeict.db"

if [ ! -f "$DB_PATH" ]; then
    # Fall back to old location
    DB_PATH="/opt/fixjeictv2/fixjeict.db"
fi

if [ -f "$DB_PATH" ]; then
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    DB_MODIFIED=$(stat -c %y "$DB_PATH" | cut -d' ' -f1,2)
    echo -e "${GREEN}✓${NC} Database exists (Size: $DB_SIZE, Modified: $DB_MODIFIED)"
else
    echo -e "${RED}✗${NC} Database not found at $DB_PATH"
fi

echo

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Disk usage: $DISK_USAGE%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠${NC} Disk usage: $DISK_USAGE% (Warning)"
else
    echo -e "${RED}✗${NC} Disk usage: $DISK_USAGE% (Critical)"
fi

echo

# Check backups
echo "Checking recent backups..."
BACKUP_DIR="/var/backups/fixjeictv2"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/fixjeict_*.db 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$((($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 86400))
        BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
        if [ "$BACKUP_AGE" -lt 2 ]; then
            echo -e "${GREEN}✓${NC} Latest backup: $LATEST_BACKUP ($BACKUP_SIZE, ${BACKUP_AGE} days old)"
        else
            echo -e "${YELLOW}⚠${NC} Latest backup is ${BACKUP_AGE} days old: $LATEST_BACKUP"
        fi
    else
        echo -e "${YELLOW}⚠${NC} No backups found in $BACKUP_DIR"
    fi
else
    echo -e "${YELLOW}⊘${NC} Backup directory not found"
fi

echo

# Summary
echo "=========================="
if [ "$MAIN_SERVICE" = true ] && [ "$ADMIN_SERVICE" = true ]; then
    echo -e "${GREEN}Overall Status: HEALTHY${NC}"
    exit 0
else
    echo -e "${RED}Overall Status: UNHEALTHY${NC}"
    exit 1
fi

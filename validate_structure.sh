#!/bin/bash

# FixJeICT v3 - Structure Validation Script
# Checks if all required files and directories exist

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "FixJeICT v3 - Structure Validation"
echo "===================================="
echo ""

# Required files
FILES=(
    "app.py"
    "admin_app.py"
    "requirements.txt"
    ".env.example"
    "install.sh"
    "run.sh"
    "fixjeict_app/__init__.py"
    "fixjeict_app/config.py"
    "fixjeict_app/database.py"
    "fixjeict_app/models.py"
    "fixjeict_app/schemas.py"
    "fixjeict_app/auth.py"
    "fixjeict_app/email_service.py"
    "fixjeict_app/cloudflare_service.py"
    "fixjeict_app/routers/__init__.py"
    "fixjeict_app/routers/public.py"
    "fixjeict_app/routers/auth.py"
    "fixjeict_app/routers/tickets.py"
    "fixjeict_app/routers/admin.py"
    "fixjeict_app/services/__init__.py"
    "fixjeict_app/services/template_service.py"
)

# Required directories
DIRS=(
    "fixjeict_app/routers"
    "fixjeict_app/services"
    "fixjeict_app/templates"
    "fixjeict_app/static"
    "scripts"
)

# Check files
echo "Checking required files..."
ERRORS=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check directories
echo "Checking required directories..."
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir/"
    else
        echo -e "${RED}✗${NC} $dir/"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check executable scripts
echo "Checking executable scripts..."
SCRIPTS=(
    "install.sh"
    "run.sh"
    "scripts/backup.sh"
    "scripts/health-check.sh"
    "scripts/start.sh"
    "scripts/stop.sh"
    "scripts/restart.sh"
)
for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo -e "${GREEN}✓${NC} $script (executable)"
    elif [ -f "$script" ]; then
        echo -e "${RED}✗${NC} $script (not executable)"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${RED}✗${NC} $script (missing)"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "===================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$ERRORS error(s) found${NC}"
    exit 1
fi

#!/bin/bash

# FixJeICT v2 Installer Script
# Installeert de FastAPI versie van FixJeICT

set -e

# Kleuren
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuratie
INSTALL_DIR="/opt/fixjeictv2"
SERVICE_USER="fixjeict"
REPO_URL="https://github.com/Ivoozz/fixjeictv2.git"

# Logging functie
log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check root
if [ "$EUID" -ne 0 ]; then
    error "Dit script moet als root uitgevoerd worden"
    exit 1
fi

# Check Python 3.13
log "Python versie checken..."
if ! command -v python3.13 &> /dev/null; then
    log "Python 3.13 installeren..."
    apt-get update
    apt-get install -y software-properties-common
    add-apt-repository -y ppa:deadsnakes/ppa
    apt-get update
    apt-get install -y python3.13 python3.13-venv python3.13-dev
fi

PYTHON_VERSION=$(python3.13 --version 2>&1 | awk '{print $2}')
success "Python $PYTHON_VERSION gevonden"

# Check git
if ! command -v git &> /dev/null; then
    log "Git installeren..."
    apt-get install -y git
fi

# Install dependencies
log "Systeem dependencies installeren..."
apt-get update
apt-get install -y python3-pip sqlite3 curl

# Create service user
log "Service user aanmaken..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /bin/false "$SERVICE_USER"
    success "Service user $SERVICE_USER aangemaakt"
else
    warning "Service user $SERVICE_USER bestaat al"
fi

# Backup oude installatie
if [ -d "$INSTALL_DIR" ]; then
    log "Backup maken van oude installatie..."
    BACKUP_DIR="${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    mv "$INSTALL_DIR" "$BACKUP_DIR"
    warning "Oude installatie verplaatst naar $BACKUP_DIR"
fi

# Clone repository
log "Repository clonen naar $INSTALL_DIR..."
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Maak data directory
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"

# Genereer secret key
SECRET_KEY=$(python3.13 -c "import secrets; print(secrets.token_urlsafe(32))")

# Vraag admin credentials
log "Admin configuratie..."
read -p "Admin gebruikersnaam [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

while true; do
    read -s -p "Admin wachtwoord: " ADMIN_PASSWORD
    echo
    if [ ${#ADMIN_PASSWORD} -ge 6 ]; then
        break
    else
        warning "Wachtwoord moet minimaal 6 tekens bevatten"
    fi
done

# Maak .env bestand
log "Environment configuratie aanmaken..."
cat > "$INSTALL_DIR/.env" << EOF
# FixJeICT Configuration
SECRET_KEY=${SECRET_KEY}
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}

# Database
DATABASE_URL=sqlite:///${INSTALL_DIR}/data/fixjeict.db

# Server Settings
PUBLIC_HOST=0.0.0.0
PUBLIC_PORT=5000
ADMIN_HOST=0.0.0.0
ADMIN_PORT=5001

# URLs (pas aan voor productie)
PUBLIC_URL=https://fixjeict.nl
ADMIN_URL=https://admin.fixjeict.nl

# Email (optioneel)
RESEND_API_KEY=
FROM_EMAIL=noreply@fixjeict.nl
EOF

success ".env bestand aangemaakt"

# Create virtual environment
log "Virtual environment aanmaken..."
python3.13 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies
log "Python dependencies installeren..."
pip install -r requirements.txt

# Set permissions
log "Permissies instellen..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 700 "$INSTALL_DIR/data"
chmod 600 "$INSTALL_DIR/.env"

# Initialize database
log "Database initialiseren..."
cd "$INSTALL_DIR"
python3.13 -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from app.database import init_db
init_db()
print('Database geinitialiseerd!')
"

chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/data"

# Create systemd service - PUBLIC
log "Systemd service aanmaken (public)..."
cat > /etc/systemd/system/fixjeict-public.service << EOF
[Unit]
Description=FixJeICT Public Server (FastAPI)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:public_app --host 0.0.0.0 --port 5000 --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service - ADMIN
log "Systemd service aanmaken (admin)..."
cat > /etc/systemd/system/fixjeict-admin.service << EOF
[Unit]
Description=FixJeICT Admin Server (FastAPI)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/uvicorn app.main:admin_app --host 0.0.0.0 --port 5001 --proxy-headers
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
log "Systemd herladen..."
systemctl daemon-reload

# Enable services
systemctl enable fixjeict-public.service
systemctl enable fixjeict-admin.service

# Start services
log "Services starten..."
systemctl start fixjeict-public.service
systemctl start fixjeict-admin.service

# Wait a moment and check status
sleep 3

# Check if services are running
if systemctl is-active --quiet fixjeict-public.service; then
    success "FixJeICT Public service draait op poort 5000"
else
    error "FixJeICT Public service startte niet correct"
    systemctl status fixjeict-public.service
    exit 1
fi

if systemctl is-active --quiet fixjeict-admin.service; then
    success "FixJeICT Admin service draait op poort 5001"
else
    error "FixJeICT Admin service startte niet correct"
    systemctl status fixjeict-admin.service
    exit 1
fi

# Health check
log "Health check uitvoeren..."
sleep 2

if curl -sf http://localhost:5000/health > /dev/null; then
    success "Public server health check OK"
else
    warning "Public server health check mislukt"
fi

if curl -sf http://localhost:5001/health > /dev/null; then
    success "Admin server health check OK"
else
    warning "Admin server health check mislukt"
fi

echo ""
echo "========================================"
echo "  FixJeICT v2 Installatie Compleet!"
echo "========================================"
echo ""
echo "Public server:  http://0.0.0.0:5000"
echo "Admin server:   http://0.0.0.0:5001"
echo ""
echo "Admin login:"
echo "  Gebruikersnaam: $ADMIN_USERNAME"
echo "  Wachtwoord:     (ingesteld tijdens installatie)"
echo ""
echo "Logs bekijken:"
echo "  journalctl -u fixjeict-public -f"
echo "  journalctl -u fixjeict-admin -f"
echo ""
echo "Services beheren:"
echo "  systemctl start|stop|restart fixjeict-public"
echo "  systemctl start|stop|restart fixjeict-admin"
echo ""
success "Installatie succesvol voltooid!"

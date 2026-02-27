#!/bin/bash

# FixJeICT v3 - One-Line Installer
# FastAPI-based IT Support Platform
# Install: bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_header "FixJeICT v3 Installer"

INSTALL_DIR="/opt/fixjeictv2"
REPO_OWNER="Ivoozz"
REPO_NAME="fixjeictv2"
ARCHIVE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/main.tar.gz"

print_info "Installation directory: $INSTALL_DIR"

# Check prerequisites
print_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed. Aborting."; exit 1; }
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_success "Python $PYTHON_VERSION found"

command -v pip3 >/dev/null 2>&1 || { print_error "pip3 is required but not installed. Aborting."; exit 1; }
print_success "pip3 found"

if ! command -v curl >/dev/null 2>&1; then
    print_info "Installing curl..."
    apt-get update -qq
    apt-get install -y curl -qq || { print_error "Failed to install curl. Aborting."; exit 1; }
fi
print_success "Prerequisites OK"

# Download and extract repository
if [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
    print_warning "$INSTALL_DIR exists and is not empty"

    # Check if this is already a FixJeICT installation
    if [ -f "$INSTALL_DIR/app.py" ] || [ -f "$INSTALL_DIR/fixjeict_app/config.py" ]; then
        print_warning "Detected existing FixJeICT installation"
        read -p "Backup and reinstall? [y/N]: " CONFIRM_REINSTALL
        if [[ $CONFIRM_REINSTALL =~ ^[Yy]$ ]]; then
            BACKUP_DIR="${INSTALL_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
            print_info "Creating backup to $BACKUP_DIR..."
            cp -rp "$INSTALL_DIR" "$BACKUP_DIR"
            print_success "Backup created"

            rm -rf "$INSTALL_DIR"
            INSTALL_FRESH=true
        else
            print_info "Using existing files in $INSTALL_DIR"
            INSTALL_FRESH=false
        fi
    else
        read -p "Remove existing directory and reinstall? [y/N]: " CONFIRM_REMOVE
        if [[ $CONFIRM_REMOVE =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            INSTALL_FRESH=true
        else
            print_info "Using existing files in $INSTALL_DIR"
            INSTALL_FRESH=false
        fi
    fi
else
    INSTALL_FRESH=true
fi

if [ "$INSTALL_FRESH" = true ]; then
    print_info "Downloading FixJeICT v3..."
    mkdir -p "$INSTALL_DIR"
    TMP_DIR=$(mktemp -d)

    if ! curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/fixjeictv2.tar.gz"; then
        print_error "Failed to download archive. Aborting."
        rm -rf "$TMP_DIR"
        exit 1
    fi

    print_info "Extracting archive..."
    if ! tar -xzf "$TMP_DIR/fixjeictv2.tar.gz" -C "$TMP_DIR"; then
        print_error "Failed to extract archive. Aborting."
        rm -rf "$TMP_DIR"
        exit 1
    fi

    # Move extracted files to install directory
    if [ -d "$TMP_DIR/${REPO_NAME}-main" ]; then
        cp -rp "$TMP_DIR/${REPO_NAME}-main/"* "$INSTALL_DIR/"
        cp -rp "$TMP_DIR/${REPO_NAME}-main/".[^.]* "$INSTALL_DIR/" 2>/dev/null || true
    else
        print_error "Extracted directory structure not found. Aborting."
        rm -rf "$TMP_DIR"
        exit 1
    fi

    # Cleanup
    rm -rf "$TMP_DIR"

    print_success "FixJeICT v3 downloaded and extracted"
fi

cd "$INSTALL_DIR"

# Create virtual environment
print_info "Creating Python virtual environment..."

if [ ! -d "$INSTALL_DIR/venv" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

source "$INSTALL_DIR/venv/bin/activate"

print_info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
print_info "Installing Python dependencies..."

if ! pip install -r "$INSTALL_DIR/requirements.txt" --quiet; then
    print_error "Failed to install dependencies. Aborting."
    exit 1
fi

print_success "Dependencies installed"

# Interactive configuration
print_header "Configuration"

# Generate secret key
if [ ! -f "$INSTALL_DIR/.env" ] || ! grep -q "SECRET_KEY=" "$INSTALL_DIR/.env" 2>/dev/null; then
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    print_success "Generated SECRET_KEY"
else
    SECRET_KEY=$(grep "^SECRET_KEY=" "$INSTALL_DIR/.env" | cut -d'=' -f2)
    print_info "Using existing SECRET_KEY"
fi

read -p "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

ADMIN_PASSWORD=""
ADMIN_PASSWORD_CONFIRM=""

while true; do
    read -s -p "Admin password: " ADMIN_PASSWORD
    echo
    read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
    echo

    if [ -z "$ADMIN_PASSWORD" ]; then
        print_error "Password cannot be empty"
        continue
    fi

    if [ "$ADMIN_PASSWORD" = "$ADMIN_PASSWORD_CONFIRM" ]; then
        break
    else
        print_error "Passwords do not match. Try again."
    fi
done

print_info "\nEmail Configuration (Resend)"
read -p "Resend API Key [leave empty to skip]: " RESEND_API_KEY
read -p "From email [noreply@fixjeict.nl]: " RESEND_FROM
RESEND_FROM=${RESEND_FROM:-noreply@fixjeict.nl}

print_info "\nCloudflare Configuration (Email Routing)"
read -p "Cloudflare API Key [leave empty to skip]: " CLOUDFLARE_API_KEY
read -p "Cloudflare Account ID [leave empty to skip]: " CLOUDFLARE_ACCOUNT_ID
read -p "Cloudflare Zone ID [leave empty to skip]: " CLOUDFLARE_ZONE_ID
read -p "Email Domain [fixjeict.nl]: " EMAIL_DOMAIN
EMAIL_DOMAIN=${EMAIL_DOMAIN:-fixjeict.nl}

read -p "App URL [http://localhost:5000]: " APP_URL
APP_URL=${APP_URL:-http://localhost:5000}

read -p "Production mode? [y/N]: " PRODUCTION_MODE
if [[ $PRODUCTION_MODE =~ ^[Yy]$ ]]; then
    DEBUG=false
else
    DEBUG=true
fi

# Create .env file
print_info "Creating .env file..."

# Use absolute path for database
mkdir -p "$INSTALL_DIR/data"

cat > "$INSTALL_DIR/.env" << EOF
DATABASE_URL=sqlite:////opt/fixjeictv2/data/fixjeict.db
SECRET_KEY=${SECRET_KEY}
DEBUG=${DEBUG}
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
APP_URL=${APP_URL}
HOST=0.0.0.0
PORT=5000
ADMIN_PORT=5001
WORKERS=4
RESEND_API_KEY=${RESEND_API_KEY}
RESEND_FROM=${RESEND_FROM}
CLOUDFLARE_API_KEY=${CLOUDFLARE_API_KEY}
CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID}
CLOUDFLARE_ZONE_ID=${CLOUDFLARE_ZONE_ID}
EMAIL_DOMAIN=${EMAIL_DOMAIN}
EOF

print_success ".env file created"

# Initialize database
print_info "Initializing database..."

if ! "$INSTALL_DIR/venv/bin/python3" -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from fixjeict_app.database import init_db
init_db()
print('Database initialized successfully')
"; then
    print_error "Failed to initialize database. Check the error above."
    exit 1
fi

print_success "Database initialized"

# Prepare scripts directory
print_info "Preparing scripts..."

mkdir -p "$INSTALL_DIR/scripts"

for script in backup.sh health-check.sh; do
    if [ -f "$INSTALL_DIR/scripts/$script" ]; then
        print_success "Script $script exists"
    fi
done

chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true

print_success "Scripts prepared"

# Create systemd services
print_info "Creating systemd services..."

cat > /etc/systemd/system/fixjeict.service << 'EOF'
[Unit]
Description=FixJeICT Main Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fixjeictv2
Environment="PATH=/opt/fixjeictv2/venv/bin"
EnvironmentFile=/opt/fixjeictv2/.env
ExecStart=/opt/fixjeictv2/venv/bin/uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/fixjeict-admin.service << 'EOF'
[Unit]
Description=FixJeICT Admin Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/fixjeictv2
Environment="PATH=/opt/fixjeictv2/venv/bin"
EnvironmentFile=/opt/fixjeictv2/.env
ExecStart=/opt/fixjeictv2/venv/bin/uvicorn admin_app:admin_app --host 0.0.0.0 --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

print_success "Systemd services created"

# Enable and start services
print_header "Service Configuration"

read -p "Enable and start services on boot? [Y/n]: " ENABLE_SERVICES
ENABLE_SERVICES=${ENABLE_SERVICES:-Y}

if [[ $ENABLE_SERVICES =~ ^[Yy]$ ]]; then
    print_info "Enabling and starting services..."
    systemctl enable fixjeict.service
    systemctl enable fixjeict-admin.service
    systemctl start fixjeict.service
    systemctl start fixjeict-admin.service

    print_info "Waiting for services to start..."
    sleep 3

    if systemctl is-active --quiet fixjeict.service; then
        print_success "Main app service (fixjeict) is running on port 5000"
    else
        print_error "Main app service failed to start. Check: journalctl -u fixjeict -n 50"
        FAILED=true
    fi

    if systemctl is-active --quiet fixjeict-admin.service; then
        print_success "Admin portal service (fixjeict-admin) is running on port 5001"
    else
        print_error "Admin portal service failed to start. Check: journalctl -u fixjeict-admin -n 50"
        FAILED=true
    fi
fi

# Health check
if [ -z "$FAILED" ]; then
    print_info "Running health check..."
    sleep 2

    if command -v curl >/dev/null 2>&1; then
        if curl -fs "http://localhost:5000/health" >/dev/null; then
            print_success "Main app health check passed"
        else
            print_warning "Main app health check failed"
        fi

        if curl -fs "http://localhost:5001/admin/health" >/dev/null; then
            print_success "Admin app health check passed"
        else
            print_warning "Admin app health check failed"
        fi
    fi
fi

# Firewall configuration
print_info "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 5000/tcp 2>/dev/null || true
    ufw allow 5001/tcp 2>/dev/null || true
    print_warning "Remember to firewall port 5001 from public access if using cloudflare!"
fi

# Add cron job for daily backups
CRON_EXISTS=$(crontab -l 2>/dev/null | grep -c "fixjeictv2/scripts/backup.sh" || true)
if [ "$CRON_EXISTS" -eq 0 ]; then
    (crontab -l 2>/dev/null; echo "0 2 * * * $INSTALL_DIR/scripts/backup.sh >> /var/log/fixjeictv2-backup.log 2>&1") | crontab -
    print_success "Daily backup scheduled (2 AM)"
else
    print_info "Backup cron job already exists"
fi

# Summary
print_header "Installation Complete!"

echo -e "${GREEN}✓ FixJeICT v3 installed successfully!${NC}\n"

echo "Installation Directory: $INSTALL_DIR"
echo "Main App:               http://0.0.0.0:5000"
echo "Admin Portal:           http://0.0.0.0:5001"
echo ""
echo "Services:"
echo "  - fixjeict.service       (main app on port 5000)"
echo "  - fixjeict-admin.service (admin portal on port 5001)"
echo ""
echo "Useful Commands:"
echo "  - Start services:   systemctl start fixjeict fixjeict-admin"
echo "  - Stop services:    systemctl stop fixjeict fixjeict-admin"
echo "  - Restart services: systemctl restart fixjeict fixjeict-admin"
echo "  - View logs:        journalctl -u fixjeict -f"
echo "  - View admin logs:  journalctl -u fixjeict-admin -f"
echo ""
echo "Configuration:"
echo "  - Config file:      $INSTALL_DIR/.env"
echo "  - Database:         $INSTALL_DIR/data/fixjeict.db"
echo ""
echo "Next Steps:"
echo "1. Configure Cloudflare tunnel to point to your server"
echo "2. Configure HTTPS (recommended: use Cloudflare SSL)"
echo "3. Configure MX records for email routing (optional)"
echo "4. Verify Resend domain (if using email)"
echo ""
print_warning "Remember to firewall port 5001 from public access in production!"
print_warning "Admin credentials: $ADMIN_USERNAME / [your password]"
echo ""
if [ "$DEBUG" = "true" ]; then
    print_warning "Running in DEBUG mode - set DEBUG=false in .env for production"
fi

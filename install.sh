#!/bin/bash

# FixJeICT v2 - Installer
# Installs the complete FixJeICT platform to /opt/fixjeictv2
# One-line installer: bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)

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

print_header "FixJeICT v2 Installer"

INSTALL_DIR="/opt/fixjeictv2"
REPO_OWNER="Ivoozz"
REPO_NAME="fixjeictv2"
ARCHIVE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/main.tar.gz"

print_info "Installation directory: $INSTALL_DIR"

# Check prerequisites
print_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed. Aborting."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { print_error "pip3 is required but not installed. Aborting."; exit 1; }

if ! command -v curl >/dev/null 2>&1; then
    print_info "Installing curl..."
    apt-get update >/dev/null 2>&1
    apt-get install -y curl >/dev/null 2>&1 || { print_error "Failed to install curl. Aborting."; exit 1; }
fi

print_success "Prerequisites OK"

# Download and extract repository
if [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
    print_warning "$INSTALL_DIR exists and is not empty"
    read -p "Remove existing directory and reinstall? [y/N]: " CONFIRM_REMOVE
    if [[ $CONFIRM_REMOVE =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        INSTALL_FRESH=true
    else
        print_info "Using existing files in $INSTALL_DIR"
        INSTALL_FRESH=false
    fi
else
    INSTALL_FRESH=true
fi

if [ "$INSTALL_FRESH" = true ]; then
    print_info "Downloading FixJeICT v2..."
    mkdir -p "$INSTALL_DIR"
    TMP_DIR=$(mktemp -d)
    curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/fixjeictv2.tar.gz" || { print_error "Failed to download archive. Aborting."; exit 1; }
    
    print_info "Extracting archive..."
    tar -xzf "$TMP_DIR/fixjeictv2.tar.gz" -C "$TMP_DIR" || { print_error "Failed to extract archive. Aborting."; exit 1; }
    
    # Move extracted files to install directory
    mv "$TMP_DIR/${REPO_NAME}-main/"* "$INSTALL_DIR/" 2>/dev/null || true
    mv "$TMP_DIR/${REPO_NAME}-main/".[^.]* "$INSTALL_DIR/" 2>/dev/null || true
    
    # Cleanup
    rm -rf "$TMP_DIR"
    
    print_success "FixJeICT v2 downloaded and extracted"
fi

cd "$INSTALL_DIR"

# Create virtual environment in root of install dir
print_info "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
source "$INSTALL_DIR/venv/bin/activate"

print_info "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies from root requirements.txt
print_info "Installing Python dependencies..."
pip install -r "$INSTALL_DIR/requirements.txt" --quiet

print_success "Dependencies installed"

# Interactive configuration
print_header "Configuration"

SECRET_KEY=$(openssl rand -hex 32)
print_success "Generated SECRET_KEY"

read -p "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

while true; do
    read -s -p "Admin password: " ADMIN_PASSWORD
    echo
    read -s -p "Confirm admin password: " ADMIN_PASSWORD_CONFIRM
    echo
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

read -p "App URL [https://fixjeict.nl]: " APP_URL
APP_URL=${APP_URL:-https://fixjeict.nl}

# Create .env file in root of install dir
print_info "Creating .env file..."
cat > "$INSTALL_DIR/.env" << EOF
DATABASE_URL=sqlite:////opt/fixjeictv2/fixjeict.db
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
RESEND_API_KEY=${RESEND_API_KEY}
RESEND_FROM=${RESEND_FROM}
CLOUDFLARE_API_KEY=${CLOUDFLARE_API_KEY}
CLOUDFLARE_ACCOUNT_ID=${CLOUDFLARE_ACCOUNT_ID}
CLOUDFLARE_ZONE_ID=${CLOUDFLARE_ZONE_ID}
EMAIL_DOMAIN=${EMAIL_DOMAIN}
ADMIN_USERNAME=${ADMIN_USERNAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
APP_URL=${APP_URL}
EOF

print_success ".env file created"

# Prepare scripts directory and copy utility scripts
print_info "Preparing scripts..."

mkdir -p "$INSTALL_DIR/scripts"

for script in backup.sh health-check.sh; do
    if [ -f "$INSTALL_DIR/fixjeict_app/scripts/$script" ]; then
        cp "$INSTALL_DIR/fixjeict_app/scripts/$script" "$INSTALL_DIR/scripts/$script"
        print_success "Copied $script"
    else
        print_warning "$script not found in fixjeict_app/scripts"
    fi
done

chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true

print_success "Scripts prepared"

# Initialize database from INSTALL_DIR root with correct imports
print_info "Initializing database..."
cd "$INSTALL_DIR"
"$INSTALL_DIR/venv/bin/python3" -c "
import sys
sys.path.insert(0, '$INSTALL_DIR')
from app import app
with app.app_context():
    from fixjeict_app.models import db
    db.create_all()
    print('Database tables created')
"

print_success "Database initialized"

# Create systemd services
print_info "Creating systemd services..."

cat > /etc/systemd/system/fixjeict.service << EOF
[Unit]
Description=FixJeICT Main Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin"
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --log-level info app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/fixjeict-admin.service << EOF
[Unit]
Description=FixJeICT Admin Portal
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin"
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 --log-level info admin_app:admin_app
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
    fi

    if systemctl is-active --quiet fixjeict-admin.service; then
        print_success "Admin portal service (fixjeict-admin) is running on port 5001"
    else
        print_error "Admin portal service failed to start. Check: journalctl -u fixjeict-admin -n 50"
    fi
fi

# Firewall configuration
print_info "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 5000/tcp >/dev/null 2>&1 || true
    ufw allow 5001/tcp >/dev/null 2>&1 || true
    print_warning "Admin port 5001 should be firewalled from public access"
fi

# Add cron job for daily backups
(crontab -l 2>/dev/null | grep -v "fixjeictv2/scripts/backup.sh"; echo "0 2 * * * $INSTALL_DIR/scripts/backup.sh >> /var/log/fixjeictv2-backup.log 2>&1") | crontab -

print_success "Daily backup scheduled (2 AM)"

# Summary
print_header "Installation Complete!"

echo -e "${GREEN}✓ FixJeICT v2 installed successfully!${NC}\n"

echo "Installation Directory: $INSTALL_DIR"
echo "Main App:               http://0.0.0.0:5000"
echo "Admin Portal:           http://0.0.0.0:5001"
echo ""
echo "Services:"
echo "  - fixjeict.service       (main app on port 5000)"
echo "  - fixjeict-admin.service (admin portal on port 5001)"
echo ""
echo "Utility Scripts:"
echo "  - Start:    $INSTALL_DIR/scripts/start.sh"
echo "  - Stop:     $INSTALL_DIR/scripts/stop.sh"
echo "  - Restart:  $INSTALL_DIR/scripts/restart.sh"
echo "  - Backup:   $INSTALL_DIR/scripts/backup.sh"
echo "  - Health:   $INSTALL_DIR/scripts/health-check.sh"
echo ""
echo "Useful Commands:"
echo "  - Start services:   systemctl start fixjeict fixjeict-admin"
echo "  - Stop services:    systemctl stop fixjeict fixjeict-admin"
echo "  - Restart services: systemctl restart fixjeict fixjeict-admin"
echo "  - View logs:        journalctl -u fixjeict -f"
echo ""
echo "Next Steps:"
echo "1. Configure DNS/Cloudflare to point to your server"
echo "2. Set up HTTPS (recommended: certbot)"
echo "3. Configure MX records for email routing"
echo "4. Verify Resend domain (if using email)"
echo ""
print_warning "Remember to firewall port 5001 from public access!"
print_warning "Admin credentials: $ADMIN_USERNAME / [your password]"

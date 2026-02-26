#!/bin/bash

# FixJeICT v2 - Interactive Installer
# This script installs the complete FixJeICT platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_header "FixJeICT v2 Installer"

# Get installation directory
INSTALL_DIR=${INSTALL_DIR:-/opt/fixjeictv2}
print_info "Installation directory: $INSTALL_DIR"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download or update files from GitHub if not already present
if [ ! -f "app.py" ] || [ ! -f "requirements.txt" ]; then
    print_info "Downloading files from GitHub..."
    REPO_URL="https://github.com/Ivoozz/fixjeictv2/archive/refs/heads/main.tar.gz"

    # Download and extract
    TEMP_DIR=$(mktemp -d)
    curl -fsSL "$REPO_URL" -o "$TEMP_DIR/archive.tar.gz"
    tar -xzf "$TEMP_DIR/archive.tar.gz" -C "$TEMP_DIR"
    cp -r "$TEMP_DIR"/fixjeictv2-main/* "$INSTALL_DIR"/
    rm -rf "$TEMP_DIR"

    print_success "Files downloaded"
else
    print_info "Using existing files in $INSTALL_DIR"
fi

# Check for required commands
print_info "Checking prerequisites..."

command -v python3 >/dev/null 2>&1 || { print_error "Python 3 is required but not installed. Aborting."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { print_error "pip3 is required but not installed. Aborting."; exit 1; }

print_success "Prerequisites OK"

# Interactive configuration
print_header "Configuration"

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)
print_success "Generated SECRET_KEY"

# Admin credentials
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

# Email configuration
print_info "\nEmail Configuration (Resend)"
read -p "Resend API Key [leave empty to skip]: " RESEND_API_KEY
read -p "From email [noreply@fixjeict.nl]: " RESEND_FROM
RESEND_FROM=${RESEND_FROM:-noreply@fixjeict.nl}

# Cloudflare configuration
print_info "\nCloudflare Configuration (Email Routing)"
read -p "Cloudflare API Key [leave empty to skip]: " CLOUDFLARE_API_KEY
read -p "Cloudflare Account ID [leave empty to skip]: " CLOUDFLARE_ACCOUNT_ID
read -p "Cloudflare Zone ID [leave empty to skip]: " CLOUDFLARE_ZONE_ID
read -p "Email Domain [fixjeict.nl]: " EMAIL_DOMAIN
EMAIL_DOMAIN=${EMAIL_DOMAIN:-fixjeict.nl}

# Create .env file
print_info "Creating .env file..."
cat > .env << EOF
DATABASE_URL=sqlite:///$INSTALL_DIR/fixjeict.db
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
RESEND_API_KEY=$RESEND_API_KEY
RESEND_FROM=$RESEND_FROM
CLOUDFLARE_API_KEY=$CLOUDFLARE_API_KEY
CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_ZONE_ID=$CLOUDFLARE_ZONE_ID
EMAIL_DOMAIN=$EMAIL_DOMAIN
ADMIN_USERNAME=$ADMIN_USERNAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
APP_URL=https://fixjeict.nl
EOF

print_success ".env file created"

# Create virtual environment
print_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
print_info "Installing Python dependencies..."
pip install -r requirements.txt

print_success "Dependencies installed"

# Update hardcoded paths in scripts
print_info "Updating hardcoded paths in scripts..."
find "$INSTALL_DIR" -type f -name "*.sh" -exec sed -i "s|/opt/fixjeict|$INSTALL_DIR|g" {} \;
find "$INSTALL_DIR" -type f -name "*.sh" -exec sed -i "s|/var/backups/fixjeict|/var/backups/fixjeictv2|g" {} \;
print_success "Paths updated in scripts"

# Initialize database
print_info "Initializing database..."
export FLASK_APP=app.py
flask db init 2>/dev/null || true
flask db migrate 2>/dev/null || true
flask db upgrade 2>/dev/null || true

# Create database tables
python3 -c "
from app import app
with app.app_context():
    from fixjeict_app.models import db
    db.create_all()
    print('Database initialized')
"

print_success "Database initialized"

# Create systemd services
print_info "Creating systemd services..."

# Main app service
cat > /etc/systemd/system/fixjeict.service << EOF
[Unit]
Description=FixJeICT Main Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --log-level info app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Admin app service
cat > /etc/systemd/system/fixjeict-admin.service << EOF
[Unit]
Description=FixJeICT Admin Portal
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 --log-level info admin_app:admin_app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

print_success "Systemd services created"

# Ask about enabling services
print_header "Service Configuration"

read -p "Enable and start services on boot? [Y/n]: " ENABLE_SERVICES
ENABLE_SERVICES=${ENABLE_SERVICES:-Y}

if [[ $ENABLE_SERVICES =~ ^[Yy]$ ]]; then
    print_info "Enabling and starting services..."
    systemctl enable fixjeict.service
    systemctl enable fixjeict-admin.service
    systemctl start fixjeict.service
    systemctl start fixjeict-admin.service
    print_success "Services started"
fi

# Firewall configuration
print_info "Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 5000/tcp >/dev/null 2>&1 || true
    ufw allow 5001/tcp >/dev/null 2>&1 || true
    print_warning "Admin port 5001 should be firewalled from public access"
fi

# Copy and prepare scripts
print_info "Copying utility scripts..."

# Ensure scripts directory exists
mkdir -p "$INSTALL_DIR/scripts"

# Copy backup.sh from fixjeict_app/scripts
if [ -f "$INSTALL_DIR/fixjeict_app/scripts/backup.sh" ]; then
    cp "$INSTALL_DIR/fixjeict_app/scripts/backup.sh" "$INSTALL_DIR/scripts/backup.sh"
    chmod +x "$INSTALL_DIR/scripts/backup.sh"
    print_success "Backup script copied"
else
    print_warning "backup.sh not found in fixjeict_app/scripts"
fi

# Copy health-check.sh from fixjeict_app/scripts
if [ -f "$INSTALL_DIR/fixjeict_app/scripts/health-check.sh" ]; then
    cp "$INSTALL_DIR/fixjeict_app/scripts/health-check.sh" "$INSTALL_DIR/scripts/health-check.sh"
    chmod +x "$INSTALL_DIR/scripts/health-check.sh"
    print_success "Health check script copied"
else
    print_warning "health-check.sh not found in fixjeict_app/scripts"
fi

# Ensure start.sh, stop.sh, restart.sh have execute permissions
chmod +x "$INSTALL_DIR/scripts/start.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/scripts/stop.sh" 2>/dev/null || true
chmod +x "$INSTALL_DIR/scripts/restart.sh" 2>/dev/null || true

print_success "Utility scripts prepared"

# Add cron job for daily backups
(crontab -l 2>/dev/null | grep -v "fixjeict/scripts/backup.sh"; echo "0 2 * * * $INSTALL_DIR/scripts/backup.sh >> /var/log/fixjeictv2-backup.log 2>&1") | crontab -

print_success "Daily backup scheduled (2 AM)"

# Summary
print_header "Installation Complete!"

echo -e "${GREEN}✓ FixJeICT v2 installed successfully!${NC}\n"

echo "Installation Directory: $INSTALL_DIR"
echo "Main App Port: 5000"
echo "Admin Portal Port: 5001"
echo ""
echo "Services:"
echo "  - fixjeict.service (main app)"
echo "  - fixjeict-admin.service (admin portal)"
echo ""
echo "Useful Commands:"
echo "  - Start services:   systemctl start fixjeict fixjeict-admin"
echo "  - Stop services:    systemctl stop fixjeict fixjeict-admin"
echo "  - Restart services: systemctl restart fixjeict fixjeict-admin"
echo "  - View logs:        journalctl -u fixjeict -f"
echo "  - Run backup:       $INSTALL_DIR/scripts/backup.sh"
echo ""
echo "Next Steps:"
echo "1. Configure DNS/Cloudflare to point to your server"
echo "2. Set up HTTPS (recommended: certbot)"
echo "3. Configure MX records for email routing"
echo "4. Verify Resend domain (if using email)"
echo ""
print_warning "Remember to firewall port 5001 from public access!"
print_warning "Change your admin password regularly."
echo ""

read -p "Press Enter to exit..."

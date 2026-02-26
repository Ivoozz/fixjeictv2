# FixJeICT v2 - Deployment Guide

This guide covers deployment of FixJeICT v2 in production environments.

## Prerequisites

### System Requirements

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Python**: 3.8 or higher
- **RAM**: Minimum 512MB, Recommended 1GB+
- **Disk Space**: Minimum 1GB free space
- **Network**: Public IP with DNS configured

### Required Ports

- **Port 5000**: Main application (public)
- **Port 5001**: Admin portal (should be firewalled from public access)
- **Port 22**: SSH (for server management)

### Before You Start

1. Ensure your domain DNS is pointing to your server
2. Have a valid email address ready for Let's Encrypt certificates
3. Decide on your admin credentials
4. Prepare Resend API key (if using email notifications)

## Quick Deployment

### Automated Installation

```bash
# Clone or download the repository
cd fixjeictv2

# Run the interactive installer
sudo bash install.sh
```

The installer will guide you through:
- Setting up the Python environment
- Configuring environment variables
- Creating the database
- Setting up systemd services
- Configuring automated backups

### Manual Installation

#### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv sqlite3 nginx certbot python3-certbot-nginx

# Create installation directory
sudo mkdir -p /opt/fixjeict
cd /opt/fixjeict
```

#### 2. Application Setup

```bash
# Copy application files (or clone from git)
# If from git:
# git clone https://github.com/Ivoozz/fixjeictv2.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env
```

Edit `.env` with your configuration:

```bash
DATABASE_URL=sqlite:///fixjeict.db
SECRET_KEY=$(openssl rand -hex 32)
FLASK_ENV=production
RESEND_API_KEY=your_resend_api_key
RESEND_FROM=noreply@yourdomain.com
CLOUDFLARE_API_KEY=your_cloudflare_api_key
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_ZONE_ID=your_zone_id
EMAIL_DOMAIN=yourdomain.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
APP_URL=https://yourdomain.com
```

#### 3. Database Initialization

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database
export FLASK_APP=app.py
python -c "from app import app; from fixjeict_app.models import db; app.app_context().push(); db.create_all()"
```

#### 4. Systemd Service Configuration

Create `/etc/systemd/system/fixjeict.service`:

```ini
[Unit]
Description=FixJeICT Main Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/opt/fixjeict
Environment="PATH=/opt/fixjeict/venv/bin"
EnvironmentFile=/opt/fixjeict/.env
ExecStart=/opt/fixjeict/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 --log-level info app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/fixjeict-admin.service`:

```ini
[Unit]
Description=FixJeICT Admin Portal
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/opt/fixjeict
Environment="PATH=/opt/fixjeict/venv/bin"
EnvironmentFile=/opt/fixjeict/.env
ExecStart=/opt/fixjeict/venv/bin/gunicorn -w 2 -b 127.0.0.1:5001 --timeout 120 --log-level info admin_app:admin_app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 5. Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable fixjeict.service
sudo systemctl enable fixjeict-admin.service

# Start services
sudo systemctl start fixjeict.service
sudo systemctl start fixjeict-admin.service

# Check status
sudo systemctl status fixjeict
sudo systemctl status fixjeict-admin
```

## Nginx Configuration

### Basic Nginx Setup

Create `/etc/nginx/sites-available/fixjeict`:

```nginx
# Main site (port 5000)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (optional - can be served directly)
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# Admin portal (port 5001) - INTERNAL USE ONLY
server {
    listen 80;
    server_name admin.yourdomain.com;

    # Restrict access by IP (optional but recommended)
    # allow YOUR_OFFICE_IP;
    # deny all;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/fixjeict /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

**Important**: When using Nginx as a proxy, update `ProxyFix` in `app.py` and `admin_app.py`:
```python
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)
```

## SSL/TLS Configuration

### Let's Encrypt Certificates

```bash
# Obtain certificate for main domain
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Obtain certificate for admin subdomain (if configured)
sudo certbot --nginx -d admin.yourdomain.com

# Certificates will auto-renew
sudo certbot renew --dry-run
```

## Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block admin port from public access (if running without Nginx proxy)
sudo ufw deny 5001/tcp

# Check status
sudo ufw status
```

## Cloudflare Configuration

### DNS Settings

1. Add A records pointing to your server IP:
   - `yourdomain.com` → YOUR_SERVER_IP
   - `www.yourdomain.com` → YOUR_SERVER_IP
   - `admin.yourdomain.com` → YOUR_SERVER_IP (if using subdomain)

2. Enable "Proxied" (orange cloud) for all records

### Email Routing Setup

1. **Enable Email Routing**:
   - Go to DNS > Email
   - Click "Enable Email Routing"

2. **Verify Domain**:
   - Add MX records provided by Cloudflare to your DNS

3. **API Access**:
   - Get API Token from: My Profile > API Tokens
   - Get Account ID and Zone ID from URLs in Cloudflare dashboard

4. **Update `.env`**:
   ```bash
   CLOUDFLARE_API_KEY=your_api_token
   CLOUDFLARE_ACCOUNT_ID=your_account_id
   CLOUDFLARE_ZONE_ID=your_zone_id
   EMAIL_DOMAIN=yourdomain.com
   ```

## Resend Email Setup

1. **Create Account**: Sign up at [resend.com](https://resend.com)

2. **Verify Domain**:
   - Go to Domains
   - Add your domain
   - Add DNS records provided

3. **Get API Key**:
   - Go to API Keys
   - Create new API key

4. **Update `.env`**:
   ```bash
   RESEND_API_KEY=re_xxxxx
   RESEND_FROM=noreply@yourdomain.com
   ```

## Backup Configuration

### Automated Backups

The installer sets up automated daily backups via cron:

```bash
# View cron job
crontab -l | grep fixjeict

# Backup location
ls -la /var/backups/fixjeict/

# Manual backup
/opt/fixjeict/scripts/backup.sh
```

### Backup Script Location

The backup script is at `/opt/fixjeict/scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/fixjeict"
DATE=$(date +%Y%m%d_%H%M%S)
INSTALL_DIR="/opt/fixjeict"

mkdir -p "$BACKUP_DIR"
cp "$INSTALL_DIR/fixjeict.db" "$BACKUP_DIR/fixjeict_$DATE.db"
ls -t "$BACKUP_DIR"/fixjeict_*.db | tail -n +31 | xargs -r rm
```

## Monitoring and Logging

### View Logs

```bash
# Application logs
sudo journalctl -u fixjeict -f

# Admin portal logs
sudo journalctl -u fixjeict-admin -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Check if services are running
curl http://localhost:5000/
curl http://localhost:5001/

# Check systemd status
sudo systemctl is-active fixjeict
sudo systemctl is-active fixjeict-admin
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u fixjeict -n 50 --no-pager

# Common issues:
# 1. Port already in use: sudo lsof -i :5000
# 2. Permission issues: Check file ownership
# 3. Virtual environment not activated: Ensure path is correct
```

### Database Locked

```bash
# Restart services
sudo systemctl restart fixjeict fixjeict-admin

# Check for SQLite lock files
ls -la /opt/fixjeict/*.db-wal
```

### Email Not Sending

1. Verify API keys in `.env`
2. Check domain verification status
3. Test Resend API manually:
   ```bash
   curl -X POST https://api.resend.com/emails \
     -H "Authorization: Bearer re_xxxxx" \
     -H "Content-Type: application/json" \
     -d '{
       "from": "noreply@yourdomain.com",
       "to": "test@example.com",
       "subject": "Test",
       "html": "<p>Test</p>"
     }'
   ```

### SSL Certificate Issues

```bash
# Renew manually
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Check certificate status
sudo certbot certificates
```

## Performance Tuning

### Gunicorn Workers

Adjust worker count based on available RAM:

```ini
# In systemd service file
ExecStart=/opt/fixjeict/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 app:app

# Calculation: (2 x CPU cores) + 1 for I/O bound
# Or 4 workers per 1GB RAM for memory-intensive apps
```

### Database Optimization

SQLite uses WAL mode by default for concurrency. For high traffic:
- Consider migrating to PostgreSQL
- Add connection pooling
- Implement database indexing

## Security Checklist

- [ ] Change default admin password
- [ ] Firewall admin port (5001) from public access
- [ ] Enable SSL/TLS certificates
- [ ] Keep system packages updated
- [ ] Restrict SSH access (key-based only)
- [ ] Configure fail2ban for SSH brute-force protection
- [ ] Regular backup testing
- [ ] Monitor logs for suspicious activity
- [ ] Keep API keys secure (never commit to git)
- [ ] Use strong SECRET_KEY
- [ ] Enable Cloudflare proxy
- [ ] Configure DNSSEC (optional)

## Scaling Considerations

For high-traffic deployments:

1. **Load Balancer**: Use HAProxy or nginx load balancer
2. **Multiple Workers**: Increase Gunicorn workers
3. **Database Migration**: Switch to PostgreSQL
4. **Redis**: Add for caching and session storage
5. **CDN**: Use Cloudflare CDN for static assets
6. **Monitoring**: Add Prometheus/Grafana monitoring

## Support

For deployment issues:
- Check logs: `sudo journalctl -u fixjeict -f`
- Review this guide
- Check main README.md
- Email: info@fixjeict.nl

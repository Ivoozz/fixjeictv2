# FixJeICT v2 - Complete ICT Support Platform

A modern, full-featured ICT support and ticketing system built with Flask, featuring dual-port architecture, PWA support, email integration, and a vibrant modern UI.

## Features

### Core Functionality
- **Dual-Port Architecture**: Main app on port 5000 (public), Admin portal on port 5001
- **Magic Link Authentication**: Passwordless login via email
- **Complete CRUD**: Tickets, Users, Categories, Blog, Knowledge Base, Leads, Testimonials
- **Time Tracking**: Built-in time logging for fixers
- **Internal Notes**: Private notes for team collaboration
- **Dutch Status System**: Open, In behandeling, Wacht op klant, Wacht op leverancier, Gereed, Afgemeld
- **Role-Based Access**: Client, Fixer, Admin roles with different dashboards

### Integrations
- **Resend Email**: Transactional emails with beautiful HTML templates
- **Cloudflare Email Routing**: Dynamic email forwarding setup via API
- **PWA Support**: Installable as mobile app with offline functionality

### Design & UX
- **Vibrant Modern UI**: Gradient-based design with glassmorphism effects
- **Responsive**: Works on desktop, tablet, and mobile
- **Zero Placeholder Data**: Beautiful empty states instead of fake data
- **Dutch Language**: All user-facing text in Dutch

## Installation

### Quick Install (Recommended)

```bash
# Clone or download the repository
cd fixjeictv2

# Run the interactive installer (requires sudo)
sudo bash install.sh
```

The installer will:
1. Create a Python virtual environment
2. Install all dependencies
3. Create the `.env` file with your configuration
4. Initialize the database
5. Create and enable systemd services
6. Set up automated daily backups

### Manual Install

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv sqlite3 -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit configuration

# Initialize database
export FLASK_APP=app.py
python -c "from app import app; from fixjeict_app.models import db; app.app_context().push(); db.create_all()"

# Run manually (for testing)
python app.py      # Main app on port 5000
python admin_app.py  # Admin portal on port 5001
```

### Production Deployment with Systemd

```bash
# Create systemd service for main app
sudo nano /etc/systemd/system/fixjeict.service
```

```ini
[Unit]
Description=FixJeICT Main Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/opt/fixjeictv2
Environment="PATH=/opt/fixjeictv2/venv/bin"
EnvironmentFile=/opt/fixjeictv2/.env
ExecStart=/opt/fixjeictv2/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --log-level info app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create systemd service for admin portal
sudo nano /etc/systemd/system/fixjeict-admin.service
```

```ini
[Unit]
Description=FixJeICT Admin Portal
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/opt/fixjeictv2
Environment="PATH=/opt/fixjeictv2/venv/bin"
EnvironmentFile=/opt/fixjeictv2/.env
ExecStart=/opt/fixjeictv2/venv/bin/gunicorn -w 2 -b 0.0.0.0:5001 --timeout 120 --log-level info admin_app:admin_app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable fixjeict.service fixjeict-admin.service
sudo systemctl start fixjeict.service fixjeict-admin.service
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=sqlite:///fixjeict.db

# Flask
SECRET_KEY=your-random-secret-key-here
FLASK_ENV=production

# Resend Email
RESEND_API_KEY=re_xxxxx
RESEND_FROM=noreply@yourdomain.com

# Cloudflare
CLOUDFLARE_API_KEY=your-api-key
CLOUDFLARE_ACCOUNT_ID=your-account-id
CLOUDFLARE_ZONE_ID=your-zone-id
EMAIL_DOMAIN=yourdomain.com

# Admin Portal
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password

# App URL
APP_URL=https://yourdomain.com
```

### Proxy Configuration

The apps use `ProxyFix` with `x_for=1` for Cloudflare direct connection or single nginx proxy.

**Cloudflare → Gunicorn (direct)**: `x_for=1` (default)
**Client → Nginx → Gunicorn**: Change to `x_for=2`

## Email Setup

### Resend Integration

1. Sign up at [resend.com](https://resend.com)
2. Verify your domain
3. Get your API key
4. Add to `.env`:
   ```bash
   RESEND_API_KEY=re_xxxxx
   RESEND_FROM=noreply@yourdomain.com
   ```

### Cloudflare Email Routing

1. Enable Email Routing in your Cloudflare DNS settings
2. Get your API credentials from Cloudflare dashboard
3. Add to `.env`:
   ```bash
   CLOUDFLARE_API_KEY=your-api-key
   CLOUDFLARE_ACCOUNT_ID=your-account-id
   CLOUDFLARE_ZONE_ID=your-zone-id
   EMAIL_DOMAIN=yourdomain.com
   ```

The system will automatically create email forwarding rules when needed.

## Database

The platform uses SQLite with WAL mode for concurrency.

### Backup

Automated backups are scheduled daily via cron (2 AM):

```bash
# Manual backup
/opt/fixjeictv2/scripts/backup.sh

# Backup location
/var/backups/fixjeictv2/
```

### Restore

```bash
# Stop services
sudo systemctl stop fixjeict fixjeict-admin

# Restore database
cp /var/backups/fixjeictv2/fixjeict_YYYYMMDD_HHMMSS.db /opt/fixjeictv2/fixjeict.db

# Start services
sudo systemctl start fixjeict fixjeict-admin
```

## Security

### Important Security Notes

1. **Admin Portal**: Port 5001 should be firewalled from public access
   ```bash
   sudo ufw deny 5001/tcp
   ```

2. **HTTPS**: Always use HTTPS in production
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Admin Password**: Change the default admin password immediately
4. **SECRET_KEY**: Keep your SECRET_KEY secure and unique
5. **API Keys**: Never commit API keys to version control

### Firewall

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5001/tcp   # Admin portal (block public access)
sudo ufw enable
```

## Usage

### User Roles

**Client**
- Create and view tickets
- Add messages to tickets
- View ticket status and history
- Manage profile

**Fixer**
- Claim available tickets
- Update ticket status
- Log time spent
- Add internal notes
- View all tickets

**Admin**
- Full access to all features
- Manage users and roles
- Manage categories
- Manage blog and knowledge base
- View leads and testimonials
- Complete ticket management

### Admin Portal

Access the admin portal at: `http://your-server:5001` (or via VPN/SSH tunnel)

Login with HTTP Basic Auth using credentials from `.env`.

## Monitoring

### View Logs

```bash
# Main app logs
sudo journalctl -u fixjeict -f

# Admin portal logs
sudo journalctl -u fixjeict-admin -f

# Service status
sudo systemctl status fixjeict fixjeict-admin
```

### Health Check

```bash
# Check if services are running
curl http://localhost:5000/
curl http://localhost:5001/
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :5000
sudo lsof -i :5001

# Kill the process if needed
sudo kill -9 <PID>
```

### Database Locked

```bash
# Restart services
sudo systemctl restart fixjeict fixjeict-admin
```

### Email Not Sending

1. Check Resend API key in `.env`
2. Verify domain is verified in Resend dashboard
3. Check logs for errors: `sudo journalctl -u fixjeict -n 50`

### Service Won't Start

```bash
# Check logs
sudo journalctl -u fixjeict -n 100

# Test manually
source venv/bin/activate
export $(cat .env | xargs)
python app.py
```

## Development

### Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env for development
cp .env.example .env
nano .env

# Run with Flask development server
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000

# In another terminal for admin
export FLASK_APP=admin_app.py
flask run --host=0.0.0.0 --port=5001
```

## Project Structure

```
fixjeictv2/
├── app.py                      # Main Flask application (port 5000)
├── admin_app.py                # Admin Flask application (port 5001)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── install.sh                  # Interactive installer script
├── README.md                   # This file
├── fixjeict_app/
│   ├── models.py               # SQLAlchemy database models
│   ├── email_service.py        # Resend email integration
│   ├── cloudflare_service.py   # Cloudflare API integration
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html           # Main layout
│   │   ├── base_admin.html     # Admin layout
│   │   ├── index.html          # Homepage
│   │   ├── dashboard.html     # Client dashboard
│   │   ├── dashboard_fixer.html # Fixer dashboard
│   │   ├── ticket_detail.html # Ticket page
│   │   └── ...                 # More templates
│   └── static/
│       ├── css/
│       │   └── style.css       # Vibrant design system
│       ├── js/
│       ├── images/
│       ├── manifest.json       # PWA manifest
│       └── sw.js               # Service worker
└── deploy/
    └── README.md               # Deployment guide
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For support, email: info@fixjeict.nl

## Changelog

### v2.0.0 (2024)
- Complete rewrite with Flask
- Dual-port architecture
- PWA support
- Modern vibrant UI
- Email integration (Resend)
- Cloudflare email routing
- Time tracking
- Internal notes
- Zero placeholder data policy

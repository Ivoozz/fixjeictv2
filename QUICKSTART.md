# FixJeICT v2 - Quick Start Guide

Get FixJeICT v2 running in under 5 minutes!

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Root/sudo access
- Domain name configured to point to your server

## Installation

### Option 1: One-Line Install (Recommended)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ivoozz/fixjeictv2/main/install.sh)
```

This automatically downloads all files from GitHub and installs everything.

### Option 2: Manual Install

```bash
# 1. Download the code
git clone https://github.com/Ivoozz/fixjeictv2.git
cd fixjeictv2

# 2. Run the installer
sudo bash install.sh
```

Follow the prompts to configure:
- Admin username and password (default: admin/fixjeict2026)
- Email settings (Resend API key)
- Cloudflare settings (for email routing)

### That's It!

The installer will:
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Initialize database
- ✅ Create systemd services
- ✅ Start the applications
- ✅ Set up automated backups

## Accessing Your Application

### Main Application (Public)
- **URL**: `http://your-server-ip:5000` or `https://yourdomain.com`
- **Features**: Ticket management, dashboard, knowledge base, blog

### Admin Portal (Internal)
- **URL**: `http://your-server-ip:5001`
- **Authentication**: HTTP Basic Auth with credentials you set during installation
- **Features**: Full admin control panel

## First Steps

1. **Set Up HTTPS** (recommended):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

2. **Create Initial Categories**:
   - Log in to admin portal
   - Go to Categories
   - Add ticket categories (Hardware, Software, Network, etc.)

3. **Configure Email** (optional but recommended):
   - Get API key from [resend.com](https://resend.com)
   - Add to `.env` file
   - Restart services: `sudo systemctl restart fixjeict`

4. **Set Up Cloudflare** (optional):
   - Configure Email Routing in Cloudflare DNS
   - Add API credentials to `.env`
   - Restart services

## Common Commands

### Service Management

```bash
# Start services
sudo systemctl start fixjeict fixjeict-admin

# Stop services
sudo systemctl stop fixjeict fixjeict-admin

# Restart services
sudo systemctl restart fixjeict fixjeict-admin

# Check status
sudo systemctl status fixjeict fixjeict-admin

# View logs
sudo journalctl -u fixjeict -f
```

### Database Operations

```bash
# Manual backup
/opt/fixjeictv2/scripts/backup.sh

# Check database size
ls -lh /opt/fixjeictv2/fixjeict.db

# View backups
ls -lh /var/backups/fixjeictv2/
```

### Health Check

```bash
# Run health check
/opt/fixjeictv2/scripts/health-check.sh

# Check if services respond
curl http://localhost:5000/
curl http://localhost:5001/
```

## Firewall Configuration

```bash
# Allow web traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Block admin port from public
sudo ufw deny 5001/tcp

# Enable firewall
sudo ufw enable
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u fixjeict -n 50

# Common fix: Restart services
sudo systemctl restart fixjeict fixjeict-admin
```

### Database Locked
```bash
# Restart both services
sudo systemctl restart fixjeict fixjeict-admin
```

### Port Already in Use
```bash
# Find what's using the port
sudo lsof -i :5000
sudo lsof -i :5001

# Kill if necessary
sudo kill -9 <PID>
```

## Configuration Files

### Main Configuration
- **Location**: `/opt/fixjeictv2/.env`
- **Edit**: `sudo nano /opt/fixjeictv2/.env`
- **After changes**: `sudo systemctl restart fixjeict fixjeict-admin`

### Systemd Services
- **Main app**: `/etc/systemd/system/fixjeict.service`
- **Admin**: `/etc/systemd/system/fixjeict-admin.service`

## Next Steps

1. **Customize branding**: Update `fixjeict_app/templates/base.html`
2. **Add content**: Create blog posts and knowledge base articles
3. **Set up users**: Invite team members to create accounts
4. **Configure notifications**: Test email functionality
5. **Monitor logs**: Keep an eye on system performance

## Support

- 📖 Full documentation: `README.md`
- 🚀 Deployment guide: `deploy/README.md`
- 📧 Email: info@fixjeict.nl

## Security Checklist

- [ ] Change default admin password
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Firewall port 5001 from public access
- [ ] Set up automated backups (done by installer)
- [ ] Review and rotate API keys
- [ ] Monitor logs regularly
- [ ] Keep system updated

Enjoy using FixJeICT v2! 🚀

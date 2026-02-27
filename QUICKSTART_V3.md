# FixJeICT v3 - Quick Start Guide

Get FixJeICT v3 up and running in 5 minutes.

## Option 1: One-Line Installer (Recommended)

```bash
sudo bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)
```

Follow the prompts and you're done!

## Option 2: Manual Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Ivoozz/fixjeictv2.git
cd fixjeictv2
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit as needed
```

Minimum configuration:
```env
DEBUG=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
APP_URL=http://localhost:5000
```

### 5. Initialize Database

```bash
python3 -c "from fixjeict_app.database import init_db; init_db()"
```

### 6. Run the Application

**Option A: Using the development runner**
```bash
./run.sh
```

**Option B: Running individual apps**

Terminal 1 (Main app):
```bash
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

Terminal 2 (Admin app):
```bash
uvicorn admin_app:admin_app --host 0.0.0.0 --port 5001 --reload
```

## Access the Application

- **Main App**: http://localhost:5000
- **Admin Panel**: http://localhost:5001 (HTTP Basic Auth)
- **API Documentation**: http://localhost:5000/api/docs (debug mode only)

## Admin Credentials

Default (change these in `.env`):
- Username: `admin`
- Password: `fixjeict2026`

## Testing the Application

### 1. Health Checks

```bash
# Main app
curl http://localhost:5000/health

# Admin app
curl http://localhost:5001/admin/health
```

### 2. Login Flow

1. Go to http://localhost:5000
2. Click "Inloggen"
3. Enter your email
4. Check email (simulated in logs if Resend not configured)
5. Click the magic link to login

### 3. Admin Panel

1. Go to http://localhost:5001
2. Enter admin credentials
3. Access the admin dashboard

## Production Deployment

For production deployment:

```bash
# Run the installer
sudo bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)

# Configure for production
sudo nano /opt/fixjeictv2/.env
# Set DEBUG=false
# Change admin credentials
# Set APP_URL to your domain
# Configure email settings

# Start services
sudo systemctl start fixjeict fixjeict-admin
sudo systemctl enable fixjeict fixjeict-admin

# Configure firewall
sudo ufw allow 5000/tcp
sudo ufw deny 5001/tcp
```

## Common Tasks

### Add a New Category (Admin)

1. Login to admin panel
2. Go to Categories
3. Click "New Category"
4. Fill in details and save

### Create a Ticket

1. Login as user
2. Go to Dashboard
3. Click "New Ticket"
4. Fill in details and submit

### Check Logs

```bash
# Main app logs
sudo journalctl -u fixjeict -f

# Admin app logs
sudo journalctl -u fixjeict-admin -f
```

### Backup Database

```bash
sudo /opt/fixjeictv2/scripts/backup.sh
```

### Restart Services

```bash
sudo /opt/fixjeictv2/scripts/restart.sh
```

## Troubleshooting

### Database Locked Error

Restart the services:
```bash
sudo systemctl restart fixjeict fixjeict-admin
```

### Services Won't Start

Check logs:
```bash
sudo journalctl -u fixjeict -n 50
```

### Can't Access Admin Panel

- Check firewall: `sudo ufw status`
- Check service is running: `sudo systemctl status fixjeict-admin`
- Test health: `curl http://localhost:5001/admin/health`

### Emails Not Sending

1. Check Resend API key in `.env`
2. Verify domain is verified in Resend
3. Check application logs for errors

## Next Steps

1. Read the full documentation: `README_V3.md`
2. Set up Cloudflare tunnel (see README)
3. Configure email service (Resend)
4. Set up monitoring
5. Configure automated backups

## Need Help?

- Documentation: `README_V3.md`
- Deployment Checklist: `DEPLOYMENT_CHECKLIST.md`
- GitHub Issues: https://github.com/Ivoozz/fixjeictv2/issues

## Quick Reference

| Command | Description |
|---------|-------------|
| `./run.sh` | Start in development mode |
| `./validate_structure.sh` | Validate project structure |
| `systemctl start fixjeict` | Start main service |
| `systemctl start fixjeict-admin` | Start admin service |
| `systemctl restart fixjeict` | Restart main service |
| `systemctl status fixjeict` | Check main service status |
| `journalctl -u fixjeict -f` | Follow main service logs |
| `/opt/fixjeictv2/scripts/health-check.sh` | Run health check |
| `/opt/fixjeictv2/scripts/backup.sh` | Backup database |

## Enjoy Using FixJeICT v3! 🚀

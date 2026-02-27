# FixJeICT v3 - FastAPI Rebuild

A complete rebuild of the FixJeICT IT Support Platform using FastAPI, replacing the previous Flask implementation.

## What's New in v3

### Architecture Improvements

- **Single Framework**: FastAPI replaces Flask for better performance, async support, and automatic API documentation
- **Better Database Layer**: SQLAlchemy 2.0 with proper session management and connection pooling
- **Pydantic Integration**: Type-safe configuration and data validation throughout
- **Unified Application**: Clean separation of concerns with routers, while sharing the same database
- **Robust Error Handling**: Global exception handlers and proper logging
- **Security**: Timing-safe password comparison, secure session management, and HTTPS support

### Key Features

#### Two Applications
- **Main App (port 5000)**: Public website, user dashboard, ticket system
- **Admin App (port 5001)**: Admin panel with HTTP Basic Auth (can be firewalled)

Both applications share the same SQLite database and can run independently.

#### Tech Stack
- **FastAPI**: Modern web framework with automatic OpenAPI docs
- **Uvicorn**: ASGI server for production deployment
- **SQLAlchemy 2.0**: ORM with async support
- **Pydantic Settings**: Type-safe configuration management
- **Jinja2**: Template engine (existing templates preserved)
- **Resend**: Email service for notifications
- **Cloudflare API**: Email routing integration

### Project Structure

```
fixjeictv2/
├── app.py                           # Main FastAPI application
├── admin_app.py                     # Admin FastAPI application
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── install.sh                       # One-line installer
├── fixjeict_app/
│   ├── __init__.py
│   ├── config.py                    # Pydantic settings
│   ├── database.py                  # Database setup
│   ├── models.py                    # SQLAlchemy models
│   ├── schemas.py                   # Pydantic schemas
│   ├── auth.py                      # Authentication helpers
│   ├── email_service.py             # Email service (Resend)
│   ├── cloudflare_service.py        # Cloudflare API integration
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── public.py                # Public pages (home, services, etc.)
│   │   ├── auth.py                  # Login/logout routes
│   │   ├── tickets.py               # Ticket system routes
│   │   └── admin.py                 # Admin panel routes
│   ├── services/
│   │   ├── __init__.py
│   │   └── template_service.py      # Jinja2 template service
│   ├── templates/                   # Jinja2 templates (preserved)
│   └── static/                      # CSS, JS, images (preserved)
└── scripts/
    ├── backup.sh                    # Database backup
    ├── health-check.sh              # Health check
    ├── start.sh                     # Start services
    ├── stop.sh                      # Stop services
    └── restart.sh                   # Restart services
```

## Installation

### One-Line Installer

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)
```

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/Ivoozz/fixjeictv2.git
cd fixjeictv2
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy and configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Initialize the database:
```bash
python3 -c "from fixjeict_app.database import init_db; init_db()"
```

6. Start the applications:
```bash
# Main app
uvicorn app:app --host 0.0.0.0 --port 5000 --reload

# Admin app (in another terminal)
uvicorn admin_app:admin_app --host 0.0.0.0 --port 5001 --reload
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite:////opt/fixjeictv2/data/fixjeict.db` |
| `SECRET_KEY` | Secret key for sessions | Generated automatically |
| `DEBUG` | Debug mode | `false` |
| `ADMIN_USERNAME` | Admin username | `admin` |
| `ADMIN_PASSWORD` | Admin password | `fixjeict2026` |
| `APP_URL` | Base URL for the app | `http://localhost:5000` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Main app port | `5000` |
| `ADMIN_PORT` | Admin app port | `5001` |
| `WORKERS` | Number of worker processes | `4` |
| `RESEND_API_KEY` | Resend API key | - |
| `RESEND_FROM` | From email address | `noreply@fixjeict.nl` |
| `CLOUDFLARE_API_KEY` | Cloudflare API key | - |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account ID | - |
| `CLOUDFLARE_ZONE_ID` | Cloudflare zone ID | - |
| `EMAIL_DOMAIN` | Email domain for routing | `fixjeict.nl` |

## Usage

### Starting Services

Using systemd (recommended for production):
```bash
sudo systemctl start fixjeict fixjeict-admin
sudo systemctl enable fixjeict fixjeict-admin
```

Using the helper scripts:
```bash
sudo /opt/fixjeictv2/scripts/start.sh
sudo /opt/fixjeictv2/scripts/stop.sh
sudo /opt/fixjeictv2/scripts/restart.sh
```

### Accessing the Application

- **Main App**: http://localhost:5000
- **Admin Panel**: http://localhost:5001 (HTTP Basic Auth)
- **Health Checks**:
  - Main: http://localhost:5000/health
  - Admin: http://localhost:5001/admin/health
- **API Documentation** (debug mode only):
  - Main: http://localhost:5000/api/docs
  - Admin: http://localhost:5001/admin/docs

### Cloudflare Tunnel Setup

To expose the application securely via Cloudflare Tunnel:

1. Install Cloudflare Tunnel:
```bash
sudo apt install cloudflared
```

2. Authenticate:
```bash
sudo cloudflared tunnel login
```

3. Create a tunnel:
```bash
sudo cloudflared tunnel create fixjeict
```

4. Configure routing (edit `~/.cloudflared/config.yml`):
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: fixjeict.yourdomain.com
    service: http://localhost:5000
  - hostname: admin-fixjeict.yourdomain.com
    service: http://localhost:5001
  - service: http_status:404
```

5. Start the tunnel:
```bash
sudo cloudflared tunnel run fixjeict
```

### Database Backups

Automatic daily backups are configured during installation. Manual backup:
```bash
sudo /opt/fixjeictv2/scripts/backup.sh
```

### Health Check

Run the health check script:
```bash
sudo /opt/fixjeictv2/scripts/health-check.sh
```

## Development

### Running in Development Mode

```bash
# Set DEBUG=true in .env
export DEBUG=true

# Main app
uvicorn app:app --host 0.0.0.0 --port 5000 --reload

# Admin app
uvicorn admin_app:admin_app --host 0.0.0.0 --port 5001 --reload
```

### Adding New Routes

1. Create a new router in `fixjeict_app/routers/`:
```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/new-route")
async def new_route():
    return {"message": "Hello"}
```

2. Include the router in `app.py` or `admin_app.py`:
```python
from fixjeict_app.routers import new_router
app.include_router(new_router.router, tags=["New Router"])
```

### Database Migrations

For production use with SQLite:
- Use SQLite's built-in migration support
- Backup before schema changes
- Consider using Alembic for complex migrations

## Security Considerations

1. **Firewall Port 5001**: The admin panel should be firewalled from public access:
```bash
sudo ufw deny 5001/tcp
```

2. **HTTPS**: Use HTTPS in production:
- Set `APP_URL` to `https://...`
- Configure SSL certificates (Let's Encrypt or Cloudflare)
- Enable HTTPS redirect middleware (automatic in production mode)

3. **Secret Key**: Always use a strong, random `SECRET_KEY` in production

4. **Admin Credentials**: Change default admin username and password

## Troubleshooting

### Services Won't Start

Check the logs:
```bash
sudo journalctl -u fixjeict -n 50
sudo journalctl -u fixjeict-admin -n 50
```

### Database Locked

If you get "database is locked" errors:
- Check for long-running transactions
- Restart the services
- The new version uses SQLite WAL mode for better concurrency

### Emails Not Sending

Check:
1. `RESEND_API_KEY` is set correctly
2. `RESEND_FROM` email is verified in Resend
3. Check application logs for email errors

### Cloudflare Tunnel Issues

Check:
1. Tunnel is running: `sudo systemctl status cloudflared`
2. DNS records point to the tunnel
3. Tunnel ingress configuration is correct

## Migration from v2 (Flask) to v3 (FastAPI)

### Database Migration

The database schema is compatible! Simply:
1. Backup your existing database
2. Install v3
3. Copy the old database to `/opt/fixjeictv2/data/fixjeict.db`
4. The new app will use the existing data

### Template Migration

All Jinja2 templates are preserved. However, some changes might be needed:
- Session access: Use `request.session` instead of Flask's `session`
- URL generation: Use standard URL patterns
- Flash messages: Implement custom flash message handling

## Performance

- **FastAPI**: 2-3x faster than Flask for API endpoints
- **Uvicorn Workers**: Configurable worker processes for production
- **SQLite WAL Mode**: Better concurrent access to database
- **GZip Compression**: Automatic response compression

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/Ivoozz/fixjeictv2
- Issues: https://github.com/Ivoozz/fixjeictv2/issues

## License

[Your License Here]

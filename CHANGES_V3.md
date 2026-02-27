# FixJeICT v3 - Changes from v2

## Overview
Complete framework migration from Flask to FastAPI with architecture improvements.

## Breaking Changes

### Application Structure
- **Removed**: `app.py` (Flask main app)
- **Removed**: `admin_app.py` (Flask admin app)
- **Added**: `app.py` (FastAPI main app)
- **Added**: `admin_app.py` (FastAPI admin app)
- **Changed**: Database now stored in `data/` directory instead of root

### Configuration
- **Changed**: Environment variables now use Pydantic for validation
- **Changed**: `FLASK_ENV` → `DEBUG`
- **Added**: `APP_NAME`, `APP_VERSION`
- **Added**: `HOST`, `PORT`, `ADMIN_PORT`, `WORKERS`

### Authentication
- **Changed**: Admin authentication now uses FastAPI's HTTPBasic
- **Changed**: Session management uses Starlette instead of Flask-Session
- **Changed**: Session cookies have different names and structure

### Systemd Services
- **Changed**: Gunicorn → Uvicorn
- **Changed**: `Type=notify` → `Type=simple`
- **Changed**: Service commands now use `uvicorn` directly

### Templates
- **Changed**: `session` → `request.session`
- **Changed**: Flash messages not built-in (need custom implementation)
- **Changed**: URL generation may need updates

## New Features

### FastAPI Benefits
- Automatic OpenAPI documentation at `/api/docs`
- Interactive API explorer
- Type hints and validation
- Async support
- Better performance

### Enhanced Security
- Timing-safe password comparison
- Secure session middleware
- HTTPS redirect in production
- Proper CORS configuration

### Developer Tools
- `run.sh` - Development runner
- `validate_structure.sh` - Structure validation
- Hot reload in development mode

### Health Checks
- `/health` - Main app health
- `/admin/health` - Admin app health
- Comprehensive health check script

## Upgrading from v2

### Step 1: Backup
```bash
# Backup database
cp /opt/fixjeictv2/fixjeict.db /opt/fixjeictv2/fixjeict.db.backup

# Backup configuration
cp /opt/fixjeictv2/.env /opt/fixjeictv2/.env.backup
```

### Step 2: Install v3
```bash
# Download and run installer
bash <(curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh)
```

### Step 3: Migrate Data
```bash
# Copy database to new location
cp /opt/fixjeictv2/fixjeict.db.backup /opt/fixjeictv2/data/fixjeict.db

# Restore configuration (manually update .env with old values)
```

### Step 4: Test
```bash
# Start services
systemctl start fixjeict fixjeict-admin

# Run health check
/opt/fixjeictv2/scripts/health-check.sh
```

## Compatibility Matrix

| Feature | v2 (Flask) | v3 (FastAPI) | Notes |
|---------|------------|--------------|-------|
| Database | ✅ SQLite | ✅ SQLite | Schema compatible |
| Templates | ✅ Jinja2 | ✅ Jinja2 | Minor changes needed |
| Sessions | ✅ Flask-Session | ✅ Starlette | Cookie structure changed |
| Email | ✅ Resend | ✅ Resend | Compatible |
| Cloudflare | ✅ API | ✅ API | Compatible |
| Admin Panel | ✅ HTTP Basic | ✅ HTTP Basic | Improved implementation |
| API Docs | ❌ No | ✅ Auto | New feature |
| Health Checks | ✅ Basic | ✅ Enhanced | New endpoints |

## Migration Guide for Templates

### Before (Flask)
```html
{% if session.get('user_id') %}
    <p>Welcome, {{ session.get('user_name') }}</p>
{% endif %}

<a href="{{ url_for('dashboard') }}">Dashboard</a>
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        {% for category, message in messages %}
            <div class="alert {{ category }}">{{ message }}</div>
        {% endfor %}
    {% endif %}
{% endwith %}
```

### After (FastAPI)
```html
{% if request.session.get('user_id') %}
    <p>Welcome, {{ request.session.get('user_name') }}</p>
{% endif %}

<a href="/dashboard">Dashboard</a>
<!-- Flash messages not built-in, implement custom -->
```

## Rollback Procedure

If you need to rollback to v2:

```bash
# Stop v3 services
systemctl stop fixjeict fixjeict-admin

# Restore v2 files (from backup)
cp /opt/fixjeictv2_backup/app.py /opt/fixjeictv2/
cp /opt/fixjeictv2_backup/admin_app.py /opt/fixjeictv2/
# ... other files ...

# Restore database
cp /opt/fixjeictv2/fixjeict.db.backup /opt/fixjeictv2/fixjeict.db

# Restore systemd services
cp /opt/fixjeictv2_backup/fixjeict.service /etc/systemd/system/
cp /opt/fixjeictv2_backup/fixjeict-admin.service /etc/systemd/system/
systemctl daemon-reload

# Start v2 services
systemctl start fixjeict fixjeict-admin
```

## Deprecated Features

The following features are removed in v3:

- Flask's built-in flash messages (implement custom alternative)
- Flask-Session (replaced with Starlette sessions)
- Gunicorn (replaced with Uvicorn)
- Type=notify systemd type (changed to Type=simple)

## Migration Support

If you encounter issues during migration:

1. Check logs: `journalctl -u fixjeict -n 50`
2. Run health check: `/opt/fixjeictv2/scripts/health-check.sh`
3. Validate structure: `/opt/fixjeictv2/validate_structure.sh`
4. Check GitHub issues: https://github.com/Ivoozz/fixjeictv2/issues

## Questions?

See:
- `README_V3.md` - Full documentation
- `REBUILD_SUMMARY.md` - Detailed rebuild information
- `CHANGES_SUMMARY.md` - Original v2 changes

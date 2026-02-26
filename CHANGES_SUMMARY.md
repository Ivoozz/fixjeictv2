# FixJeICT v2 - Installation Path Update Summary

## Overview
Fixed the install.sh and all related scripts to correctly install to `/opt/fixjeictv2` instead of the incorrect `/opt/fixjeict` path.

## Files Modified

### 1. install.sh
**Changes:**
- Line 47: Changed default `INSTALL_DIR` from `/opt/fixjeict` to `/opt/fixjeictv2`
- Lines 150-154: Added path update function to dynamically update hardcoded paths in all .sh scripts using sed
- Lines 245-274: Replaced inline backup.sh creation with proper script copying from `fixjeict_app/scripts/`
- Line 277: Updated cron job log path from `/var/log/fixjeict-backup.log` to `/var/log/fixjeictv2-backup.log`

**Key Features:**
- Now correctly copies backup.sh and health-check.sh from `fixjeict_app/scripts/` to `scripts/`
- Sets proper execute permissions on all scripts
- Dynamically updates paths in scripts during installation (supports custom INSTALL_DIR)
- Creates systemd services with correct paths using `$INSTALL_DIR` variable

### 2. fixjeict_app/scripts/backup.sh
**Changes:**
- Line 7: Changed `INSTALL_DIR` from `/opt/fixjeict` to `/opt/fixjeictv2`
- Line 8: Changed `BACKUP_DIR` from `/var/backups/fixjeict` to `/var/backups/fixjeictv2`

### 3. fixjeict_app/scripts/health-check.sh
**Changes:**
- Line 72: Changed `DB_PATH` from `/opt/fixjeict/fixjeict.db` to `/opt/fixjeictv2/fixjeict.db`
- Line 99: Changed `BACKUP_DIR` from `/var/backups/fixjeict` to `/var/backups/fixjeictv2`

### 4. QUICKSTART.md
**Changes:**
- Updated all `/opt/fixjeict` references to `/opt/fixjeictv2`
- Updated all `/var/backups/fixjeict` references to `/var/backups/fixjeictv2`
- Updated script paths in Database Operations section
- Updated health check script path
- Updated configuration file location

### 5. README.md
**Changes:**
- Updated systemd service examples with correct paths
- Updated backup script paths
- Updated backup and restore commands
- All paths now reference `/opt/fixjeictv2` and `/var/backups/fixjeictv2`

### 6. deploy/README.md
**Changes:**
- Updated installation directory path
- Updated systemd service configurations
- Updated backup script locations and examples
- Updated database lock file check path
- Updated Gunicorn worker path examples

## Systemd Services

### Main App Service (fixjeict.service)
- Port: 5000 (public)
- WorkingDirectory: `/opt/fixjeictv2`
- Environment PATH: `/opt/fixjeictv2/venv/bin`
- EnvironmentFile: `/opt/fixjeictv2/.env`

### Admin App Service (fixjeict-admin.service)
- Port: 5001 (admin - should be firewalled)
- WorkingDirectory: `/opt/fixjeictv2`
- Environment PATH: `/opt/fixjeictv2/venv/bin`
- EnvironmentFile: `/opt/fixjeictv2/.env`

## Scripts Location

All utility scripts are now located at `/opt/fixjeictv2/scripts/`:
- `backup.sh` - Database backup (copied from fixjeict_app/scripts/)
- `health-check.sh` - System health check (copied from fixjeict_app/scripts/)
- `start.sh` - Start both services (uses systemd)
- `stop.sh` - Stop both services (uses systemd)
- `restart.sh` - Restart both services (uses systemd)

## Backup Configuration

- Backup Directory: `/var/backups/fixjeictv2/`
- Backup Schedule: Daily at 2:00 AM via cron
- Retention: Last 30 backups
- Log File: `/var/log/fixjeictv2-backup.log`

## Installation Process

1. Downloads files from GitHub (if not present)
2. Creates virtual environment
3. Installs dependencies
4. Updates hardcoded paths in all scripts using sed
5. Initializes database
6. Creates systemd services
7. Copies utility scripts from fixjeict_app/scripts/ to scripts/
8. Sets execute permissions on all scripts
9. Configures automated backups via cron
10. Enables and starts services

## Dynamic Path Support

The installer now supports custom installation directories via the `INSTALL_DIR` environment variable:
```bash
sudo INSTALL_DIR=/custom/path bash install.sh
```

The sed commands in the installer will update all paths in scripts to match the custom installation directory.

## Testing Recommendations

After installation, verify:
1. Both services are running: `systemctl status fixjeict fixjeict-admin`
2. Apps respond on correct ports: `curl http://localhost:5000` and `curl http://localhost:5001`
3. Database exists: `ls -lh /opt/fixjeictv2/fixjeict.db`
4. Backup script works: `/opt/fixjeictv2/scripts/backup.sh`
5. Health check passes: `/opt/fixjeictv2/scripts/health-check.sh`
6. All utility scripts have execute permissions: `ls -lh /opt/fixjeictv2/scripts/`

## Notes

- Service names remain as `fixjeict.service` and `fixjeict-admin.service` (without v2 suffix) for consistency
- The installer filters out old cron jobs that reference the incorrect paths
- All scripts now use correct v2 paths by default but are updated dynamically during installation

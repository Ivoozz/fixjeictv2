# FixJeICT v3 - Deployment Checklist

Use this checklist when deploying FixJeICT v3 in production.

## Pre-Deployment

### 1. System Requirements
- [ ] Ubuntu 20.04+ or Debian 11+ recommended
- [ ] Python 3.8+ installed
- [ ] At least 2GB RAM
- [ ] At least 10GB disk space
- [ ] Root or sudo access

### 2. Prerequisites
- [ ] Install Python 3.8+ if not present
- [ ] Install pip3 if not present
- [ ] Install curl: `sudo apt install curl`
- [ ] Ensure firewall (ufw) is installed

### 3. Cloudflare Setup
- [ ] Create Cloudflare account
- [ ] Add domain to Cloudflare
- [ ] Enable Cloudflare tunnel
- [ ] Install cloudflared: `sudo apt install cloudflared`
- [ ] Create tunnel: `sudo cloudflared tunnel create fixjeict`
- [ ] Configure tunnel routing
- [ ] Set up DNS records

## Installation

### 4. Run Installer
- [ ] Download installer: `curl -fsSL https://raw.githubusercontent.com/Ivoozz/fixjeictv2/main/install.sh -o install.sh`
- [ ] Make executable: `chmod +x install.sh`
- [ ] Run installer: `sudo ./install.sh`

### 5. Configuration
- [ ] Review `.env` file: `cat /opt/fixjeictv2/.env`
- [ ] Set `DEBUG=false`
- [ ] Verify `SECRET_KEY` is strong
- [ ] Change default `ADMIN_USERNAME`
- [ ] Change default `ADMIN_PASSWORD`
- [ ] Set correct `APP_URL` (production domain)
- [ ] Configure `RESEND_API_KEY` if using email
- [ ] Configure Cloudflare settings if using email routing

### 6. Database Setup
- [ ] Verify database was created: `ls -lh /opt/fixjeictv2/data/fixjeict.db`
- [ ] Check database permissions: `ls -la /opt/fixjeictv2/data/`
- [ ] Test database access

## Services

### 7. Systemd Services
- [ ] Services installed: `ls /etc/systemd/system/fixjeict*.service`
- [ ] Enable services: `sudo systemctl enable fixjeict fixjeict-admin`
- [ ] Start services: `sudo systemctl start fixjeict fixjeict-admin`
- [ ] Check status: `sudo systemctl status fixjeict fixjeict-admin`

### 8. Service Health
- [ ] Main app running: `curl http://localhost:5000/health`
- [ ] Admin app running: `curl http://localhost:5001/admin/health`
- [ ] Main app accessible via Cloudflare tunnel
- [ ] Admin app accessible via Cloudflare tunnel

## Security

### 9. Firewall Configuration
- [ ] Install firewall: `sudo apt install ufw`
- [ ] Enable firewall: `sudo ufw enable`
- [ ] Allow SSH: `sudo ufw allow 22/tcp`
- [ ] Allow main app: `sudo ufw allow 5000/tcp`
- [ ] Deny public access to admin: `sudo ufw deny 5001/tcp`
- [ ] Allow admin only from trusted IPs (optional):
  ```bash
  sudo ufw allow from YOUR_IP to any port 5001
  ```

### 10. HTTPS/SSL
- [ ] Enable Cloudflare SSL (Full or Full Strict)
- [ ] Verify SSL certificate is working
- [ ] Test HTTP to HTTPS redirect
- [ ] Check that `DEBUG=false` in `.env`

### 11. Additional Security
- [ ] Change all default passwords
- [ ] Review admin credentials
- [ ] Enable fail2ban (recommended): `sudo apt install fail2ban`
- [ ] Configure automatic security updates
- [ ] Set up log rotation

## Email Configuration (Optional)

### 12. Resend Setup
- [ ] Create Resend account
- [ ] Verify domain in Resend
- [ ] Get API key from Resend
- [ ] Set `RESEND_API_KEY` in `.env`
- [ ] Set `RESEND_FROM` to verified email
- [ ] Test email sending

### 13. Cloudflare Email Routing (Optional)
- [ ] Enable Email Routing in Cloudflare
- [ ] Get Cloudflare API credentials
- [ ] Set `CLOUDFLARE_API_KEY` in `.env`
- [ ] Set `CLOUDFLARE_ACCOUNT_ID` in `.env`
- [ ] Set `CLOUDFLARE_ZONE_ID` in `.env`
- [ ] Set `EMAIL_DOMAIN` in `.env`
- [ ] Test email forwarding

## Monitoring & Maintenance

### 14. Backups
- [ ] Verify backup script exists: `ls -lh /opt/fixjeictv2/scripts/backup.sh`
- [ ] Verify cron job is set: `crontab -l | grep backup`
- [ ] Test manual backup: `sudo /opt/fixjeictv2/scripts/backup.sh`
- [ ] Verify backup location: `ls -lh /var/backups/fixjeictv2/`
- [ ] Test restore process

### 15. Health Checks
- [ ] Run health check: `sudo /opt/fixjeictv2/scripts/health-check.sh`
- [ ] Set up monitoring (e.g., UptimeRobot, Pingdom)
- [ ] Configure alerts for service downtime
- [ ] Monitor disk space

### 16. Logging
- [ ] View service logs: `sudo journalctl -u fixjeict -f`
- [ ] Check for errors in logs
- [ ] Set up log aggregation if needed
- [ ] Configure log rotation

## Testing

### 17. Functionality Tests
- [ ] Test homepage: `http://yourdomain.com`
- [ ] Test login flow
- [ ] Test ticket creation
- [ ] Test ticket management
- [ ] Test admin panel login
- [ ] Test admin panel features
- [ ] Test email notifications (if configured)

### 18. Performance Tests
- [ ] Test page load times
- [ ] Test concurrent users
- [ ] Check memory usage
- [ ] Check CPU usage
- [ ] Monitor response times

## Documentation

### 19. Update Documentation
- [ ] Document custom configurations
- [ ] Document any modifications
- [ ] Document deployment process
- [ ] Create runbook for common tasks

### 20. User Documentation
- [ ] Update user guide
- [ ] Create admin guide
- [ ] Document API endpoints (if used)
- [ ] Create troubleshooting guide

## Post-Deployment

### 21. Monitoring Setup
- [ ] Set uptime monitoring
- [ ] Set error tracking
- [ ] Set performance monitoring
- [ ] Configure alerts

### 22. Maintenance Tasks
- [ ] Schedule regular updates
- [ ] Schedule database backups verification
- [ ] Schedule certificate renewal (if not using Cloudflare)
- [ ] Schedule security audits

### 23. Disaster Recovery
- [ ] Test restore from backup
- [ ] Document disaster recovery procedure
- [ ] Store backups off-site
- [ ] Test recovery time

## Ongoing

### 24. Regular Tasks (Weekly/Monthly)
- [ ] Review logs for errors
- [ ] Check disk space
- [ ] Verify backups are running
- [ ] Apply security updates
- [ ] Review access logs

### 25. Security Tasks
- [ ] Review failed login attempts
- [ ] Rotate admin credentials periodically
- [ ] Review user access
- [ ] Check for security advisories

## Rollback Procedure

If you need to rollback:

1. Stop v3 services: `sudo systemctl stop fixjeict fixjeict-admin`
2. Restore from backup
3. Disable v3 services: `sudo systemctl disable fixjeict fixjeict-admin`
4. Start v2 services (if available)

## Support

For help:
- GitHub Issues: https://github.com/Ivoozz/fixjeictv2/issues
- Documentation: `README_V3.md`
- Troubleshooting guide: See documentation

## Checklist Completion

Date deployed: _______________
Deployed by: _______________
Version: _______________

[ ] All critical items completed
[ ] All recommended items completed
[ ] All optional items reviewed

Sign-off: _______________

# Upstream Production Deployment Guide

**Quick Start Guide for Safe Production Deployment**

---

## 🚀 Overview

This guide helps you safely deploy Upstream to production with all security settings properly configured.

**Estimated Time:** 2-4 hours (first deployment)

---

## 📋 Prerequisites

- [ ] Linux server (Ubuntu 22.04+ recommended)
- [ ] PostgreSQL 14+ database
- [ ] Redis 7+ server
- [ ] Domain name with DNS configured
- [ ] SSL/TLS certificate (Let's Encrypt or commercial)
- [ ] Email service account (Mailgun, SendGrid, etc.)
- [ ] (Optional) Sentry account for error tracking

---

## 🔐 Step 1: Environment Configuration

### 1.1 Copy Production Template

```bash
cp .env.production.example .env.production
chmod 600 .env.production  # Restrict to owner only
```

### 1.2 Generate Strong SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output to `SECRET_KEY` in `.env.production`

### 1.3 Generate Field Encryption Key (if handling real PHI)

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output to `FIELD_ENCRYPTION_KEY` in `.env.production`

### 1.4 Fill in Required Settings

Edit `.env.production` and set ALL required values:

**Critical Settings:**
- `SECRET_KEY` - Generated above
- `DEBUG=False` - MUST be False
- `ALLOWED_HOSTS` - Your domain(s), comma-separated
- `DATABASE_URL` - PostgreSQL connection string with SSL
- `REDIS_URL` - Redis connection string
- `EMAIL_BACKEND` - Real email service (not console)
- `DEFAULT_FROM_EMAIL` - Your sender email
- `PORTAL_BASE_URL` - Your HTTPS domain

**Security Settings:**
- `SECURE_SSL_REDIRECT=True`
- `SESSION_COOKIE_SECURE=True`
- `CSRF_COOKIE_SECURE=True`
- `SECURE_HSTS_SECONDS=31536000`

---

## ✅ Step 2: Validate Configuration

### 2.1 Run Production Validator

```bash
# Load production environment
export DJANGO_SETTINGS_MODULE=upstream.settings.prod
export $(cat .env.production | xargs)

# Run validation
python scripts/validate_production_settings.py
```

**Expected Output:**
```
✓ READY FOR PRODUCTION DEPLOYMENT
All security checks passed!
```

### 2.2 Fix Any Issues

If the validator reports errors:

**Critical Failures (Exit Code 1):**
- MUST fix before deployment
- Usually: DEBUG=True, weak SECRET_KEY, missing ALLOWED_HOSTS

**Errors (Exit Code 1):**
- Should fix before deployment
- Usually: missing HTTPS settings, email configuration

**Warnings (Exit Code 2):**
- Can proceed with caution
- Usually: optional features not configured

### 2.3 Run Django Deployment Check

```bash
python manage.py check --deploy
```

Address any warnings that appear.

---

## 🗄️ Step 3: Database Setup

### 3.1 Create PostgreSQL Database

```sql
-- On your PostgreSQL server:
CREATE DATABASE upstream;
CREATE USER upstream_user WITH PASSWORD 'secure-password-here';
GRANT ALL PRIVILEGES ON DATABASE upstream TO upstream_user;

-- Enable required extensions
\c upstream
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search
```

### 3.2 Configure DATABASE_URL

In `.env.production`:
```bash
DATABASE_URL=postgres://upstream_user:secure-password-here@db.example.com:5432/upstream?sslmode=require
```

### 3.3 Run Migrations

```bash
python manage.py migrate
```

**Expected:** All migrations run successfully

### 3.4 Verify Migrations

```bash
python manage.py showmigrations
```

**Expected:** All migrations marked [X]

---

## 👤 Step 4: Create Admin User

```bash
python manage.py createsuperuser
```

Follow prompts:
- **Username:** admin
- **Email:** admin@yourdomain.com
- **Password:** (use a strong password)

---

## 📦 Step 5: Static Files

### 5.1 Create Static Directory

```bash
sudo mkdir -p /var/www/upstream/static
sudo mkdir -p /var/www/upstream/media
sudo chown -R $USER:$USER /var/www/upstream
```

### 5.2 Collect Static Files

```bash
python manage.py collectstatic --noinput
```

**Expected:** All static files copied to `/var/www/upstream/static/`

---

## 🚦 Step 6: Application Server (Gunicorn)

### 6.1 Install Gunicorn

```bash
pip install gunicorn
```

### 6.2 Test Gunicorn

```bash
gunicorn hello_world.wsgi:application --bind 0.0.0.0:8000
```

Visit: http://your-server-ip:8000

**Expected:** Application loads (without static files yet)

### 6.3 Create Systemd Service

Create `/etc/systemd/system/upstream.service`:

```ini
[Unit]
Description=Upstream Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/upstream
EnvironmentFile=/path/to/upstream/.env.production
ExecStart=/path/to/venv/bin/gunicorn \
  --workers 4 \
  --bind unix:/run/upstream.sock \
  hello_world.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 6.4 Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start upstream
sudo systemctl enable upstream
sudo systemctl status upstream
```

**Expected:** Service running (active)

---

## 🌐 Step 7: Web Server (Nginx)

### 7.1 Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 7.2 Configure Nginx

Create `/etc/nginx/sites-available/upstream`:

```nginx
upstream upstream_app {
    server unix:/run/upstream.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /var/www/upstream/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/upstream/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Application
    location / {
        proxy_pass http://upstream_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://upstream_app;
    }
}
```

### 7.3 Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/upstream /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

---

## 🔥 Step 8: Background Tasks (Celery)

### 8.1 Create Celery Service

Create `/etc/systemd/system/celery.service`:

```ini
[Unit]
Description=Upstream Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/upstream
EnvironmentFile=/path/to/upstream/.env.production
ExecStart=/path/to/venv/bin/celery -A hello_world worker \
  --loglevel=info \
  --logfile=/var/log/celery/worker.log

[Install]
WantedBy=multi-user.target
```

### 8.2 Create Celery Beat Service (for scheduled tasks)

Create `/etc/systemd/system/celerybeat.service`:

```ini
[Unit]
Description=Upstream Celery Beat
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/upstream
EnvironmentFile=/path/to/upstream/.env.production
ExecStart=/path/to/venv/bin/celery -A hello_world beat \
  --loglevel=info \
  --logfile=/var/log/celery/beat.log

[Install]
WantedBy=multi-user.target
```

### 8.3 Start Services

```bash
sudo mkdir -p /var/log/celery
sudo chown www-data:www-data /var/log/celery

sudo systemctl daemon-reload
sudo systemctl start celery
sudo systemctl start celerybeat
sudo systemctl enable celery
sudo systemctl enable celerybeat
```

---

## ✅ Step 9: Final Verification

### 9.1 Health Check

```bash
curl https://yourdomain.com/health/
```

**Expected:** `{"status": "ok"}`

### 9.2 Admin Panel

Visit: https://yourdomain.com/admin/

**Expected:** Login page with HTTPS

### 9.3 Test User Registration

1. Visit portal
2. Register new user
3. Check email delivery
4. Verify email links use HTTPS

### 9.4 Check Logs

```bash
# Application logs
sudo journalctl -u upstream -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Celery logs
sudo tail -f /var/log/celery/worker.log
```

---

## 📊 Step 10: Monitoring Setup

### 10.1 Sentry Error Tracking

If configured in `.env.production`:

1. Visit your Sentry dashboard
2. Trigger a test error:
   ```python
   # In Django shell
   raise Exception("Test Sentry integration")
   ```
3. Verify error appears in Sentry

### 10.2 Uptime Monitoring

Set up external uptime monitoring:
- [Pingdom](https://www.pingdom.com/)
- [UptimeRobot](https://uptimerobot.com/)
- [StatusCake](https://www.statuscake.com/)

Monitor:
- `https://yourdomain.com/health/` (every 5 minutes)

### 10.3 Log Aggregation

Consider setting up:
- Papertrail, Loggly, or Datadog for log aggregation
- Prometheus + Grafana for metrics

---

## 🔄 Step 11: Backup Strategy

### 11.1 Database Backups

Create `/usr/local/bin/backup-upstream.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/upstream"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="upstream"

mkdir -p $BACKUP_DIR

# Backup database
pg_dump -h db.example.com -U upstream_user $DB_NAME | \
  gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$TIMESTAMP.tar.gz /var/www/upstream/media/

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### 11.2 Schedule Backups

```bash
sudo chmod +x /usr/local/bin/backup-upstream.sh

# Add to crontab
sudo crontab -e

# Daily backups at 2 AM
0 2 * * * /usr/local/bin/backup-upstream.sh
```

### 11.3 Test Restore

```bash
# Test database restore
gunzip -c /backups/upstream/db_TIMESTAMP.sql.gz | \
  psql -h localhost -U upstream_user upstream_test
```

---

## 🚨 Troubleshooting

### Issue: "DisallowedHost" Error

**Solution:** Add domain to ALLOWED_HOSTS in `.env.production`

### Issue: Static Files Not Loading

**Solutions:**
1. Run `python manage.py collectstatic --noinput`
2. Check Nginx static file paths
3. Verify file permissions

### Issue: 502 Bad Gateway

**Solutions:**
1. Check if Gunicorn is running: `sudo systemctl status upstream`
2. Check socket file exists: `ls -l /run/upstream.sock`
3. Check logs: `sudo journalctl -u upstream -n 50`

### Issue: Database Connection Failed

**Solutions:**
1. Verify DATABASE_URL in `.env.production`
2. Check PostgreSQL is running
3. Test connection: `psql $DATABASE_URL`
4. Check firewall rules

### Issue: Email Not Sending

**Solutions:**
1. Verify EMAIL_BACKEND is not console backend
2. Check email service credentials
3. Test manually: `python manage.py sendtestemail you@example.com`

---

## 📚 Post-Deployment Checklist

After successful deployment:

- [ ] Document server credentials in secure location
- [ ] Set up monitoring alerts
- [ ] Schedule regular backups
- [ ] Configure log rotation
- [ ] Set up SSL certificate auto-renewal
- [ ] Create runbook for common operations
- [ ] Train team on deployment process
- [ ] Set up staging environment
- [ ] Document rollback procedure
- [ ] Schedule regular security audits

---

## 🔒 Security Best Practices

1. **Credentials:**
   - Use unique passwords for each service
   - Store credentials in secure vault (1Password, Vault, AWS Secrets Manager)
   - Rotate credentials regularly

2. **Access Control:**
   - Use SSH keys (disable password auth)
   - Limit sudo access
   - Enable firewall (ufw/iptables)
   - Use VPN for database access

3. **Updates:**
   - Enable automatic security updates
   - Monitor CVE announcements
   - Test updates in staging first

4. **Monitoring:**
   - Set up intrusion detection
   - Monitor failed login attempts
   - Track unusual traffic patterns
   - Review logs regularly

---

## 📞 Support

- **Documentation:** [upstream/docs](./docs/)
- **Issues:** [GitHub Issues](https://github.com/yourorg/upstream/issues)
- **Security:** security@yourdomain.com
- **Emergency Runbook:** [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md)

---

**Next Steps:** [DEPLOYMENT_RUNBOOK.md](./DEPLOYMENT_RUNBOOK.md) - Day-to-day operations guide

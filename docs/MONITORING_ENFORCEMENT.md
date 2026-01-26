# Monitoring Enforcement & Production Validation

Comprehensive validation system to ensure monitoring and observability infrastructure is properly configured before production deployment.

## Overview

This system prevents deployment to production without proper monitoring configuration, ensuring:

- **No blind deployments**: All monitoring components validated before deployment
- **HIPAA compliance**: PHI scrubbing and audit logging enforced
- **Operational visibility**: Prometheus metrics, Sentry, logging all configured
- **Early detection**: Configuration issues caught before deployment, not after

## Components

### 1. Django System Checks (`upstream/monitoring_checks.py`)

Automated checks that run on Django startup and during `python manage.py check`:

- **Prometheus Metrics**: Verifies django-prometheus and custom metrics
- **Sentry Configuration**: Ensures error tracking in production
- **Logging Configuration**: Validates PHI scrubbing and retention
- **Celery Monitoring**: Checks background job monitoring
- **Redis Connectivity**: Verifies cache and session backend
- **Environment Variables**: Validates required production settings
- **Field Encryption**: Ensures PHI encryption when handling real data

### 2. Management Command (`validate_monitoring`)

Command-line tool for validating monitoring configuration:

```bash
# Basic validation
python manage.py validate_monitoring

# Strict mode (fail on warnings)
python manage.py validate_monitoring --strict

# Include deployment checks
python manage.py validate_monitoring --deploy
```

### 3. API Endpoint (`/api/monitoring/status/`)

Real-time monitoring status for dashboards and health checks:

```bash
curl http://localhost:8000/api/monitoring/status/
```

### 4. Pre-Deployment Script (`scripts/pre_deploy_check.sh`)

Comprehensive pre-deployment validation script:

```bash
./scripts/pre_deploy_check.sh
```

## Django System Checks

### Check Categories

All checks use the tag `monitoring` and can be run with:

```bash
python manage.py check --tag monitoring
```

### Error Codes

#### Critical Errors (E-series)

**monitoring.E001**: django-prometheus not installed
- **Impact**: No metrics collection
- **Fix**: Add 'django_prometheus' to INSTALLED_APPS

**monitoring.E002**: Custom metrics not properly registered
- **Impact**: Business metrics unavailable
- **Fix**: Ensure upstream.metrics defines Prometheus metrics

**monitoring.E003**: Cannot import custom metrics
- **Impact**: Metrics tracking broken
- **Fix**: Check upstream/metrics.py for import errors

**monitoring.E004**: Sentry SDK not installed
- **Impact**: Error tracking broken
- **Fix**: Install sentry-sdk: `pip install sentry-sdk`

**monitoring.E005**: LOGGING configuration not found
- **Impact**: No application logging
- **Fix**: Add LOGGING configuration to settings

**monitoring.E006**: PHI scrubbing filter not configured
- **Impact**: HIPAA violation risk (PHI in logs)
- **Fix**: Add 'phi_scrubber' filter to LOGGING

**monitoring.E007**: Celery enabled but no broker configured
- **Impact**: Background tasks cannot run
- **Fix**: Set CELERY_BROKER_URL in settings

**monitoring.E008**: Celery monitoring not available
- **Impact**: No task execution tracking
- **Fix**: Ensure upstream.celery_monitoring is importable

**monitoring.E009**: Redis cache not working properly
- **Impact**: Cache and sessions broken
- **Fix**: Check Redis connectivity and configuration

**monitoring.E010**: Cannot connect to Redis cache
- **Impact**: Application may be degraded
- **Fix**: Check Redis server is running

**monitoring.E011**: PORTAL_BASE_URL not configured for production
- **Impact**: Alert email links broken
- **Fix**: Set PORTAL_BASE_URL environment variable

**monitoring.E012**: ALLOWED_HOSTS not properly configured
- **Impact**: Security vulnerability
- **Fix**: Set ALLOWED_HOSTS to specific domains (not '*')

**monitoring.E013**: Field encryption not configured for real PHI data
- **Impact**: HIPAA violation (unencrypted PHI at rest)
- **Fix**: Generate FIELD_ENCRYPTION_KEY when REAL_DATA_MODE=True

#### Warnings (W-series)

**monitoring.W001**: PrometheusBeforeMiddleware not configured
- **Impact**: Incomplete request metrics
- **Fix**: Add middleware to MIDDLEWARE

**monitoring.W002**: PrometheusAfterMiddleware not configured
- **Impact**: Incomplete response metrics
- **Fix**: Add middleware to MIDDLEWARE

**monitoring.W003**: Sentry not configured in production
- **Impact**: Errors not tracked (recommended but not required)
- **Fix**: Set SENTRY_DSN environment variable

**monitoring.W004**: Sentry SDK initialized but no client configured
- **Impact**: Error tracking may not work
- **Fix**: Check Sentry initialization in settings.prod.py

**monitoring.W005**: Audit logging not configured
- **Impact**: HIPAA compliance risk (no audit trail)
- **Fix**: Add 'audit_file' handler for 7-year retention

**monitoring.W006**: Log rotation not configured
- **Impact**: Disk space issues over time
- **Fix**: Use TimedRotatingFileHandler or RotatingFileHandler

**monitoring.W007**: Not using Redis cache in production
- **Impact**: Performance degradation
- **Fix**: Use Redis for better performance

**monitoring.W008**: DEFAULT_FROM_EMAIL not properly configured
- **Impact**: Alert emails may fail
- **Fix**: Set DEFAULT_FROM_EMAIL to real email address

## Management Command Usage

### Basic Validation

```bash
$ python manage.py validate_monitoring

Monitoring Configuration Validation
============================================================

Running monitoring checks...

Summary:
  Errors:   0
  Warnings: 2
  Info:     0

Monitoring Components:
  ✓ prometheus: healthy
  ✓ sentry: healthy
  ✓ logging: healthy
  ○ celery: disabled
  ✓ redis: healthy

✓ Overall Status: HEALTHY

✓ Validation PASSED
```

### Strict Mode

Treat warnings as errors (useful for CI/CD):

```bash
$ python manage.py validate_monitoring --strict

# Exit code 2 if warnings found
# Exit code 1 if errors found
# Exit code 0 if all checks pass
```

### Deployment Checks

Include additional security and deployment checks:

```bash
$ python manage.py validate_monitoring --deploy
```

## API Endpoint

### GET /api/monitoring/status/

Returns comprehensive monitoring status.

**Response (200 OK - Healthy):**
```json
{
  "overall_status": "healthy",
  "prometheus": true,
  "sentry": true,
  "logging": true,
  "celery": true,
  "redis": true,
  "components": {
    "prometheus": {
      "healthy": true,
      "message": "Metrics are being collected"
    },
    "sentry": {
      "healthy": true,
      "message": "Error tracking is active"
    },
    "logging": {
      "healthy": true,
      "message": "Logging is configured with PHI scrubbing"
    },
    "celery": {
      "healthy": true,
      "message": "Workers are running"
    },
    "redis": {
      "healthy": true,
      "message": "Cache and session storage working"
    }
  }
}
```

**Response (503 Service Unavailable - Unhealthy):**
```json
{
  "overall_status": "unhealthy",
  "prometheus": false,
  "sentry": false,
  "logging": true,
  "celery": false,
  "redis": false,
  "components": {
    "prometheus": {
      "healthy": false,
      "message": "Metrics not available - check django-prometheus configuration"
    },
    ...
  }
}
```

### Status Values

- **healthy**: All critical components working, optional components configured
- **degraded**: Critical components working, but some optional components missing
- **unhealthy**: One or more critical components not working

### Critical vs. Optional Components

**Critical** (must work):
- Prometheus metrics
- Logging configuration
- Redis connectivity

**Optional** (recommended):
- Sentry error tracking (production only)
- Celery workers (if CELERY_ENABLED=True)

## Pre-Deployment Script

### Usage

```bash
# Run all pre-deployment checks
./scripts/pre_deploy_check.sh

# Exit codes:
#   0 = All checks passed
#   1 = Critical errors found
#   2 = Warnings found
```

### What It Checks

1. **Python Environment**
   - Python version
   - Virtual environment

2. **Environment Variables**
   - SECRET_KEY
   - ALLOWED_HOSTS
   - PORTAL_BASE_URL
   - DATABASE_URL
   - REDIS_URL
   - SENTRY_DSN (optional)

3. **Django System Checks**
   - All built-in checks
   - Security checks with --deploy flag

4. **Monitoring Configuration**
   - Runs `validate_monitoring` command
   - Verifies all monitoring components

5. **Database**
   - Connectivity test
   - Migration status

6. **Static Files**
   - Checks if collectstatic was run
   - Verifies file count

7. **Celery**
   - Worker health (if enabled)
   - Broker connectivity

8. **Metrics**
   - Import test for custom metrics
   - Verifies Prometheus integration

9. **Security**
   - DEBUG must be False
   - Custom SECRET_KEY required
   - ALLOWED_HOSTS validated

### Example Output

```bash
================================
Upstream Pre-Deployment Checks
================================

▶ Python Environment
----------------------------------------
✓ Python: Python 3.12.1

▶ Environment Variables
----------------------------------------
✓ SECRET_KEY configured
✓ ALLOWED_HOSTS: app.upstream.cx
✓ PORTAL_BASE_URL: https://app.upstream.cx
✓ DATABASE_URL configured
✓ REDIS_URL configured
✓ SENTRY_DSN configured

▶ Django System Checks
----------------------------------------
✓ Django checks passed

▶ Monitoring Configuration
----------------------------------------
✓ Monitoring configuration valid

▶ Database Connectivity
----------------------------------------
✓ Database migrations up to date

▶ Static Files
----------------------------------------
✓ Static files collected (1247 files)

▶ Celery Background Jobs
----------------------------------------
✓ Celery workers running

▶ Metrics Endpoint
----------------------------------------
✓ Prometheus metrics available

▶ Security Configuration
----------------------------------------
✓ DEBUG disabled
✓ Custom SECRET_KEY configured

================================
Summary
================================
Errors:   0
Warnings: 0

✓ All pre-deployment checks PASSED
Ready to deploy to production.
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Pre-Deployment Validation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run monitoring validation
        run: |
          python manage.py validate_monitoring --strict
        env:
          DJANGO_SETTINGS_MODULE: upstream.settings.prod
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      - name: Run pre-deployment checks
        run: |
          ./scripts/pre_deploy_check.sh
        env:
          DJANGO_SETTINGS_MODULE: upstream.settings.prod
```

### GitLab CI

```yaml
validate-monitoring:
  stage: test
  script:
    - pip install -r requirements.txt
    - python manage.py validate_monitoring --strict
    - ./scripts/pre_deploy_check.sh
  only:
    - main
    - merge_requests
```

### Docker Deployment

Add validation to Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# Run validation during build
RUN python manage.py validate_monitoring || \
    (echo "Monitoring validation failed" && exit 1)

CMD ["gunicorn", "hello_world.wsgi:application"]
```

### Kubernetes Pre-Deploy Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pre-deploy-validation
spec:
  template:
    spec:
      containers:
      - name: validator
        image: upstream:latest
        command:
          - /bin/bash
          - -c
          - |
            python manage.py validate_monitoring --strict --deploy
            ./scripts/pre_deploy_check.sh
        envFrom:
          - secretRef:
              name: upstream-secrets
      restartPolicy: Never
  backoffLimit: 1
```

## Troubleshooting

### Prometheus Metrics Not Available

**Symptom**: `monitoring.E001` or `monitoring.E002`

**Solutions**:
1. Verify django-prometheus is installed:
   ```bash
   pip list | grep django-prometheus
   ```

2. Check INSTALLED_APPS:
   ```python
   # settings.py
   INSTALLED_APPS = [
       'django_prometheus',
       ...
   ]
   ```

3. Verify middleware configuration:
   ```python
   MIDDLEWARE = [
       'django_prometheus.middleware.PrometheusBeforeMiddleware',
       ...
       'django_prometheus.middleware.PrometheusAfterMiddleware',
   ]
   ```

### Sentry Not Working

**Symptom**: `monitoring.W003` or `monitoring.E004`

**Solutions**:
1. Set SENTRY_DSN environment variable:
   ```bash
   export SENTRY_DSN="https://...@sentry.io/..."
   ```

2. Install sentry-sdk:
   ```bash
   pip install sentry-sdk
   ```

3. Verify initialization in settings.prod.py

### PHI Scrubbing Not Configured

**Symptom**: `monitoring.E006`

**Solutions**:
1. Add PHI scrubber filter to LOGGING:
   ```python
   LOGGING = {
       'filters': {
           'phi_scrubber': {
               '()': 'upstream.logging_filters.AggressivePHIScrubberFilter',
           },
       },
       'handlers': {
           'console': {
               'filters': ['phi_scrubber'],
               ...
           },
       },
   }
   ```

### Redis Connection Failed

**Symptom**: `monitoring.E009` or `monitoring.E010`

**Solutions**:
1. Check Redis is running:
   ```bash
   redis-cli ping
   ```

2. Verify REDIS_URL:
   ```bash
   echo $REDIS_URL
   ```

3. Test connection:
   ```python
   python manage.py shell
   >>> from django.core.cache import cache
   >>> cache.set('test', 'ok')
   >>> cache.get('test')
   ```

## Best Practices

1. **Run validation locally** before pushing to repository:
   ```bash
   python manage.py validate_monitoring
   ```

2. **Include in CI/CD pipeline** to catch issues early:
   ```bash
   python manage.py validate_monitoring --strict
   ```

3. **Use pre-deployment script** before production deployments:
   ```bash
   ./scripts/pre_deploy_check.sh
   ```

4. **Monitor `/api/monitoring/status/`** endpoint in production:
   - Add to monitoring dashboard
   - Set up alerts for unhealthy status

5. **Review warnings regularly** even if not blocking deployment

6. **Test after configuration changes** to ensure monitoring still works

7. **Document exceptions** if certain checks don't apply to your environment

## Related Documentation

- [Prometheus Metrics](./METRICS.md)
- [Celery Monitoring](./CELERY_MONITORING.md)
- [Log Retention](./LOG_RETENTION.md)
- [Django System Checks](https://docs.djangoproject.com/en/stable/topics/checks/)

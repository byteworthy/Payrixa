# Deployment Infrastructure: GCP Production Setup

**Document:** 06-deployment-infrastructure.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

Complete GCP deployment configuration for Upstream production environment. Infrastructure-as-code using Cloud Run, Cloud SQL, and managed services.

**Architecture:** Serverless (Cloud Run) + Managed PostgreSQL (Cloud SQL) + Redis (Memorystore)

---

## GCP Services

### Cloud Run (Application Server)

**Configuration File:** `app.yaml`

```yaml
runtime: python312
entrypoint: gunicorn -b :$PORT -w 4 -k gevent upstream.wsgi:application

automatic_scaling:
  min_instances: 2
  max_instances: 10
  target_cpu_utilization: 0.6
  target_concurrent_requests: 100

resources:
  cpu: 2
  memory: 4Gi
  startup_cpu_boost: true

env_variables:
  DJANGO_SETTINGS_MODULE: upstream.settings.production
  PYTHON_VERSION: "3.12"

vpc_access_connector:
  name: projects/upstream-prod/locations/us-central1/connectors/upstream-vpc

service_account: upstream-api@upstream-prod.iam.gserviceaccount.com
```

**Deployment Command:**
```bash
gcloud run deploy upstream-api \
  --image gcr.io/upstream-prod/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DJANGO_SETTINGS_MODULE=upstream.settings.production" \
  --service-account=upstream-api@upstream-prod.iam.gserviceaccount.com
```

---

### Cloud SQL (PostgreSQL Database)

**Instance Configuration:**

```bash
gcloud sql instances create upstream-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --backup-start-time=02:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03 \
  --enable-point-in-time-recovery \
  --retained-backups-count=30 \
  --flags=max_connections=200,shared_buffers=2GB
```

**Database Creation:**

```bash
gcloud sql databases create upstream \
  --instance=upstream-db \
  --charset=UTF8 \
  --collation=en_US.UTF8
```

**Connection Pooling (PgBouncer):**

```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
upstream = host=localhost port=5432 dbname=upstream

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

---

### Memorystore (Redis Cache)

**Instance Configuration:**

```bash
gcloud redis instances create upstream-cache \
  --tier=standard \
  --size=5 \
  --region=us-central1 \
  --redis-version=redis_6_x \
  --reserved-ip-range=10.0.0.0/29
```

**Usage:**
- Webhook idempotency keys (24-hour TTL)
- Session storage
- Celery result backend
- Rate limiting counters

---

### Secret Manager (Credentials Storage)

**Store Payer Portal Credentials:**

```bash
# Aetna credentials
echo -n '{"username":"provider@example.com","password":"***"}' | \
  gcloud secrets create aetna-portal-credentials \
  --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding aetna-portal-credentials \
  --member="serviceAccount:upstream-api@upstream-prod.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Access in Code:**

```python
from google.cloud import secretmanager

def get_payer_credentials(payer: str) -> dict:
    """Retrieve encrypted credentials from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/upstream-prod/secrets/{payer}-portal-credentials/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return json.loads(response.payload.data.decode('UTF-8'))
```

---

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD exec gunicorn -b :$PORT -w 4 -k gevent upstream.wsgi:application
```

### Build & Push

```bash
# Build image
docker build -t gcr.io/upstream-prod/api:latest .

# Push to Google Container Registry
docker push gcr.io/upstream-prod/api:latest
```

---

## Celery Workers (Cloud Run Jobs)

### Worker Configuration

```yaml
# worker.yaml
runtime: python312
entrypoint: celery -A upstream worker -l info -c 4

automatic_scaling:
  min_instances: 1
  max_instances: 5

resources:
  cpu: 2
  memory: 4Gi

env_variables:
  DJANGO_SETTINGS_MODULE: upstream.settings.production
  CELERY_BROKER_URL: redis://upstream-cache:6379/0
  CELERY_RESULT_BACKEND: redis://upstream-cache:6379/1
```

### Celery Beat (Scheduler)

```yaml
# beat.yaml
runtime: python312
entrypoint: celery -A upstream beat -l info

automatic_scaling:
  min_instances: 1
  max_instances: 1  # Single scheduler instance

resources:
  cpu: 1
  memory: 2Gi
```

### Scheduled Tasks

```python
# upstream/celery.py

app.conf.beat_schedule = {
    'check-expiring-authorizations': {
        'task': 'upstream.tasks.authorization_monitoring.check_expiring_authorizations',
        'schedule': crontab(hour=6, minute=0),  # 6 AM UTC daily
    },
    'build-risk-baselines': {
        'task': 'upstream.tasks.risk_baseline.build_risk_baselines',
        'schedule': crontab(hour=2, minute=0),  # 2 AM UTC daily
    },
    'detect-behavioral-changes': {
        'task': 'upstream.tasks.behavioral_prediction.detect_changes',
        'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
    },
}
```

---

## Monitoring & Observability

### Prometheus Metrics

**metrics.py:**

```python
from prometheus_client import Counter, Histogram, Gauge

# Webhook metrics
webhook_requests_total = Counter(
    'upstream_webhook_requests_total',
    'Total webhook requests',
    ['provider', 'customer', 'status']
)

webhook_latency_seconds = Histogram(
    'upstream_webhook_latency_seconds',
    'Webhook processing latency',
    ['provider', 'step'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

# Autonomous action metrics
autonomous_actions_total = Counter(
    'upstream_autonomous_actions_total',
    'Total autonomous actions executed',
    ['action_type', 'result']
)

rule_execution_latency_seconds = Histogram(
    'upstream_rule_execution_latency_seconds',
    'Rule execution time',
    ['action_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Database metrics
database_connections = Gauge(
    'upstream_database_connections',
    'Active database connections'
)
```

---

### Cloud Monitoring (formerly Stackdriver)

**Log-Based Alerts:**

```bash
# Alert on high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-filter='
    resource.type="cloud_run_revision" AND
    severity="ERROR"
  '
```

**Custom Dashboards:**

- Webhook processing latency (p50, p95, p99)
- Autonomous action success rate
- Database connection pool utilization
- Celery queue depth
- Portal automation success rate

---

### Error Tracking (Sentry Integration)

**Configuration:**

```python
# upstream/settings/production.py

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment='production',
    release=os.environ.get('GIT_COMMIT_SHA'),
)
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          python -m pytest
          python manage.py check

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t gcr.io/upstream-prod/api:${{ github.sha }} .
      - name: Push to GCR
        run: docker push gcr.io/upstream-prod/api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy upstream-api \
            --image gcr.io/upstream-prod/api:${{ github.sha }} \
            --platform managed \
            --region us-central1
```

---

## Backup & Disaster Recovery

### Database Backups

**Automated Backups:**
- Daily automated backups (2 AM UTC)
- Retained for 30 days
- Point-in-time recovery enabled (7-day window)

**Manual Backup:**

```bash
gcloud sql backups create \
  --instance=upstream-db \
  --description="Pre-migration backup"
```

**Restore:**

```bash
gcloud sql backups restore BACKUP_ID \
  --backup-instance=upstream-db \
  --backup-instance-project=upstream-prod
```

---

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 15 minutes

**Failover Steps:**

1. **Database Failover:** Switch to standby replica (automatic with REGIONAL tier)
2. **Application Failover:** Deploy new Cloud Run revision in secondary region
3. **DNS Update:** Update DNS to point to secondary region
4. **Verification:** Run smoke tests to verify functionality

---

## Security

### IAM Roles & Permissions

**Service Account:** `upstream-api@upstream-prod.iam.gserviceaccount.com`

**Permissions:**
- Cloud SQL Client (database access)
- Secret Manager Secret Accessor (credential access)
- Cloud Run Invoker (internal service calls)
- Cloud Logging Writer (log output)

---

### Network Security

**VPC Configuration:**

```bash
gcloud compute networks create upstream-vpc \
  --subnet-mode=auto \
  --bgp-routing-mode=regional

gcloud compute networks vpc-access connectors create upstream-vpc-connector \
  --network=upstream-vpc \
  --region=us-central1 \
  --range=10.8.0.0/28
```

**Firewall Rules:**

```bash
# Allow Cloud Run to access Cloud SQL
gcloud compute firewall-rules create allow-cloud-run-to-sql \
  --network=upstream-vpc \
  --allow=tcp:5432 \
  --source-ranges=10.8.0.0/28
```

---

### SSL/TLS Configuration

**Cloud Run SSL:** Managed by Google (automatic HTTPS)

**Custom Domain:**

```bash
gcloud run domain-mappings create \
  --service=upstream-api \
  --domain=api.upstream.app \
  --region=us-central1
```

---

## Cost Optimization

### Estimated Monthly Costs

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Cloud Run (API) | 2-10 instances, 2 vCPU, 4GB RAM | $150-300 |
| Cloud Run (Workers) | 1-5 instances, 2 vCPU, 4GB RAM | $100-200 |
| Cloud SQL | db-custom-2-8192 + backups | $280 |
| Memorystore | 5GB Redis | $45 |
| Secret Manager | 10 secrets | $0.06 |
| Cloud Logging | 50GB/month | $25 |
| **Total** | | **$600-850/month** |

### Scaling Projections

**10 customers (launch):** $600/month
**50 customers (6 months):** $1,200/month
**100 customers (12 months):** $2,000/month

---

## Health Checks

### Liveness Probe

```python
# upstream/health/views.py

@api_view(['GET'])
@authentication_classes([])
def liveness(request):
    """Kubernetes liveness probe endpoint."""
    return JsonResponse({'status': 'alive'})
```

**URL:** `GET /_health/live`

---

### Readiness Probe

```python
@api_view(['GET'])
@authentication_classes([])
def readiness(request):
    """Kubernetes readiness probe endpoint."""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JsonResponse({
        'status': 'ready' if all_healthy else 'not ready',
        'checks': checks
    }, status=status_code)
```

**URL:** `GET /_health/ready`

---

**Next:** See `07-pricing-and-go-to-market.md` for pricing strategy and market positioning.

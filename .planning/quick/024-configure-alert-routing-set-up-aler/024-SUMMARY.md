---
phase: quick-024
plan: 01
subsystem: monitoring
tags: [alerts, prometheus, email, slack, platform-health, monitoring]
requires: [quick-001, quick-005]
provides: [platform-alert-system, alert-routing, health-monitoring]
affects: []
tech-stack:
  added: []
  patterns: [alert-evaluation, notification-routing, prometheus-metrics]
key-files:
  created:
    - upstream/monitoring/alert_rules.py
    - upstream/management/commands/check_monitoring_alerts.py
  modified:
    - upstream/settings/base.py
    - .env.production.example
decisions:
  - Use Prometheus metrics for alert evaluation (queries /metrics endpoint)
  - Alert suppression with 5min cooldown prevents duplicate notifications
  - Email notifications enabled by default, Slack optional
  - Thresholds configurable via environment variables
  - Management command runs periodically via cron/Celery beat
  - Graceful error handling (exits 0) prevents cron failure notifications
metrics:
  duration: 9 minutes
  tasks_completed: 3/3
  commits: 3
  files_modified: 4
completed: 2026-01-27
---

# Quick Task 024: Configure Alert Routing - Platform Health Monitoring

**One-liner:** Platform health alert system with 4 alert rules (error rate, latency, DB pool, Celery failures), email/Slack notifications, and periodic evaluation via management command

## Overview

Implemented comprehensive platform health monitoring and alert routing system. The system queries Prometheus metrics, evaluates 4 critical alert rules against configurable thresholds, and sends notifications via email and Slack channels. Includes alert suppression to prevent duplicate notifications and a management command for periodic execution.

## What Was Built

### 1. Alert Rule Definitions (upstream/monitoring/alert_rules.py)

Created alert evaluation engine with:
- **4 Alert Rules:**
  - high_error_rate: 5xx responses > 5% of total requests (critical)
  - slow_response_time: p95 latency > 2000ms (warning)
  - db_pool_exhaustion: Active connections > 90% of pool (critical)
  - celery_task_failures: Task failure rate > 10% (warning)

- **Evaluation Logic:**
  - `evaluate_alert_rules()`: Queries Prometheus /metrics endpoint
  - Parses prometheus_client text format (regex-based extraction)
  - Compares current values against configured thresholds
  - Returns list of triggered alerts with context

- **Notification Delivery:**
  - `send_alert_notification()`: Sends to email and Slack
  - Email: Django send_mail() with formatted message
  - Slack: Webhook POST with rich attachments (severity color, fields)
  - Tracks delivery status and errors

- **Alert Suppression:**
  - `should_suppress_alert()`: Checks Django cache for recent alerts
  - 5-minute cooldown period (configurable)
  - Prevents duplicate notifications for same rule
  - Pattern follows upstream/services/alert_processing.py

### 2. Management Command (upstream/management/commands/check_monitoring_alerts.py)

Django management command for periodic alert evaluation:
- **Flags:**
  - `--dry-run`: Evaluate without sending notifications
  - `--rule NAME`: Filter to specific rule
  - `--verbose`: Enable detailed logging

- **Output:**
  - Shows [TRIGGERED] or [OK] status for each rule
  - Displays triggered alert messages
  - Reports notification delivery (email/slack counts)
  - Logs errors without breaking cron

- **Error Handling:**
  - Catches exceptions gracefully
  - Logs errors to 'upstream.monitoring.alerts' logger
  - Exits 0 even on errors (cron-friendly)

### 3. Configuration (upstream/settings/base.py + .env.production.example)

Added MONITORING_ALERTS configuration dict:
- **Structure:**
  - enabled: Global on/off switch
  - evaluation_interval: 300s (5 minutes)
  - cooldown_period: 300s
  - email: recipients list, from_email, enabled flag
  - slack: webhook_url, channel, username, icon_emoji, enabled flag
  - thresholds: error_rate, response_time_p95, db_pool_utilization, celery_failure_rate

- **Environment Variables:**
  - MONITORING_ALERTS_ENABLED (default: true)
  - ALERT_EMAIL_ENABLED (default: true)
  - ALERT_EMAIL_RECIPIENTS (comma-separated list)
  - ALERT_FROM_EMAIL
  - ALERT_SLACK_ENABLED (default: false)
  - ALERT_SLACK_WEBHOOK_URL
  - ALERT_SLACK_CHANNEL (default: #alerts)
  - ALERT_THRESHOLD_ERROR_RATE (default: 0.05)
  - ALERT_THRESHOLD_RESPONSE_TIME (default: 2000)
  - ALERT_THRESHOLD_DB_POOL (default: 0.90)
  - ALERT_THRESHOLD_CELERY_FAILURES (default: 0.10)

- **Documentation:**
  - .env.production.example includes setup instructions
  - Slack webhook creation steps (5-step guide)
  - Threshold override examples with comments

## Technical Decisions

### Decision 1: Query Prometheus via HTTP
**Context:** Need to access metrics for alert evaluation
**Options:**
1. Query Prometheus metrics via HTTP GET to /metrics
2. Use prometheus_client library directly
3. Query Prometheus server API (external)

**Choice:** Option 1 - HTTP GET to /metrics
**Rationale:**
- Simple: Single HTTP request to localhost:8000/metrics
- No dependencies: Uses existing django-prometheus metrics
- Text format parsing: Straightforward regex extraction
- Local: No external Prometheus server required

**Trade-offs:**
- Parsing: Regex-based (not as robust as client library)
- Quantiles: Requires Prometheus to be configured for histogram quantiles
- Alternative: Could use prometheus_client registry directly

### Decision 2: Alert Suppression with Django Cache
**Context:** Prevent duplicate notifications for same alert
**Options:**
1. Use Django cache (Redis/locmem) for suppression tracking
2. Store alert history in database
3. Use Prometheus Alertmanager for deduplication

**Choice:** Option 1 - Django cache
**Rationale:**
- Fast: In-memory/Redis lookup
- Automatic expiry: Cache TTL handles cooldown
- Simple: No schema changes or migrations
- Pattern: Follows upstream/services/alert_processing.py

**Trade-offs:**
- Ephemeral: Cleared on cache flush/restart
- No history: Can't query past alerts
- Alternative: Database would provide audit trail

### Decision 3: Email Enabled by Default, Slack Optional
**Context:** Choose default notification channel configuration
**Rationale:**
- Email: Universal, no external service setup
- Slack: Requires webhook creation (manual step)
- Progressive: Start simple, add Slack when ready
- Production: Most ops teams have email configured

### Decision 4: Management Command vs Celery Task
**Context:** How to run periodic alert evaluation
**Options:**
1. Management command (cron-based)
2. Celery periodic task
3. Django-Q scheduled task

**Choice:** Option 1 - Management command
**Rationale:**
- Flexibility: Can use cron OR Celery beat
- Simplicity: No Celery dependency for basic setup
- Testing: Easy to run manually with --dry-run
- Standard: Django pattern for periodic jobs

**Implementation:**
```bash
# Cron (simple)
*/5 * * * * cd /app && python manage.py check_monitoring_alerts

# Celery beat (if using Celery)
# Add to celerybeat schedule in settings
```

### Decision 5: Graceful Error Handling (Exit 0)
**Context:** Alerting system errors shouldn't break cron
**Rationale:**
- Cron emails: Exit 1 triggers cron failure emails
- Logging: Errors still logged to Sentry/logs
- Availability: Alerting issues shouldn't cascade
- Monitoring: Separate monitoring for monitoring system

## Implementation Notes

### Prometheus Metrics Parsing

The alert evaluation queries the /metrics endpoint and parses prometheus_client text format:

```python
# Example metric line:
# django_http_responses_total_by_status_total{status="500"} 42.0

for line in metrics.split("\n"):
    if line.startswith("django_http_responses_total_by_status"):
        match = re.search(r'status="(\d+)"\}\s+([\d.]+)', line)
        if match:
            status_code = match.group(1)
            count = float(match.group(2))
```

### Alert Suppression Cache Keys

Cache keys follow pattern: `monitoring_alert:{rule_name}`
- Stored value: datetime of last notification
- TTL: cooldown_period (300 seconds)
- Check: Compare elapsed time before firing

### Notification Formatting

**Email:**
- Subject: 🚨 [CRITICAL] High rate of 5xx errors detected
- Body: Plain text with rule, severity, timestamp, metric, current value, threshold

**Slack:**
- Attachment color: "danger" (red) for critical, "warning" (yellow) for warning
- Fields: Rule, Severity, Current Value, Threshold
- Footer: "Upstream Monitoring" with timestamp

## Testing

### Manual Testing

All verifications passed:

```bash
# Command registered
$ python manage.py help check_monitoring_alerts
✓ Shows usage and options

# Dry run evaluation
$ python manage.py check_monitoring_alerts --dry-run --verbose
✓ Evaluates 4 rules
✓ Shows [OK] status (no alerts triggered)
✓ No notifications sent (dry run mode)

# Rule filter
$ python manage.py check_monitoring_alerts --rule high_error_rate --dry-run
✓ Evaluates only specified rule

# Settings loaded
$ python manage.py shell -c "from django.conf import settings; print(settings.MONITORING_ALERTS['enabled'])"
✓ True

# Imports successful
$ python -c "from upstream.monitoring.alert_rules import ALERT_RULES, evaluate_alert_rules, send_alert_notification; print('OK')"
✓ OK
```

### Production Usage

**Cron setup:**
```bash
*/5 * * * * cd /app && python manage.py check_monitoring_alerts >> /var/log/monitoring_alerts.log 2>&1
```

**Celery beat setup:**
```python
# settings.py
CELERYBEAT_SCHEDULE = {
    'check-monitoring-alerts': {
        'task': 'upstream.tasks.check_monitoring_alerts',
        'schedule': crontab(minute='*/5'),
    },
}
```

**Environment variables:**
```bash
# .env.production
ALERT_EMAIL_RECIPIENTS=ops@company.com,oncall@company.com
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/XXX
ALERT_SLACK_ENABLED=true
```

## Deviations from Plan

None - plan executed exactly as written.

## Next Steps

### Immediate (Done)
- ✅ Alert rules defined and functional
- ✅ Notification channels configured
- ✅ Management command tested

### Follow-up Tasks
1. **Set up cron/Celery beat:** Schedule check_monitoring_alerts to run every 5 minutes
2. **Configure Slack webhook:** Create incoming webhook for alerts channel
3. **Tune thresholds:** Adjust thresholds based on production traffic patterns
4. **Add Prometheus Alertmanager:** (Optional) For advanced routing and silencing
5. **Create runbooks:** Document response procedures for each alert type
6. **Add more rules:** Expand to cover Redis, disk space, memory usage

### Integration Points
- **Prometheus:** Requires /metrics endpoint (provided by django-prometheus, quick-001)
- **Email:** Uses Django EMAIL_* settings (should be configured)
- **Slack:** Requires webhook URL (manual setup)
- **Flower:** (Optional) Monitor Celery beat schedule (quick-005)
- **Sentry:** Errors automatically reported via logger (quick-013)

## Files Changed

### Created
- `upstream/monitoring/alert_rules.py` (616 lines)
  - ALERT_RULES list (4 rules)
  - evaluate_alert_rules() evaluation engine
  - send_alert_notification() delivery logic
  - Alert suppression helpers
  - Prometheus metric parsing

- `upstream/management/commands/check_monitoring_alerts.py` (198 lines)
  - Django management command
  - --dry-run, --rule, --verbose flags
  - Status output ([TRIGGERED]/[OK])
  - Error handling

### Modified
- `upstream/settings/base.py` (+52 lines)
  - MONITORING_ALERTS configuration dict
  - PROMETHEUS_METRICS_PATH setting

- `.env.production.example` (+34 lines)
  - Platform Health Alerts section
  - MONITORING_ALERTS_ENABLED
  - Email configuration (ALERT_EMAIL_*)
  - Slack configuration (ALERT_SLACK_*)
  - Threshold overrides (ALERT_THRESHOLD_*)
  - Setup instructions

## Success Criteria

- [x] upstream/monitoring/alert_rules.py exists with 4 alert rules (error rate, latency, DB pool, Celery)
- [x] evaluate_alert_rules() queries Prometheus metrics and identifies threshold violations
- [x] send_alert_notification() sends formatted messages to email and Slack
- [x] Alert suppression prevents duplicate notifications within 5min cooldown
- [x] Management command check_monitoring_alerts runs without errors
- [x] MONITORING_ALERTS configuration in upstream/settings/base.py with env var overrides
- [x] .env.production.example documents all alert setup including Slack webhook creation
- [x] Dry run execution shows alert evaluation results for all rules

All success criteria met ✅

## Commits

1. **8ad4f87b** - feat(quick-024): create alert rule definitions with evaluation logic
   - Add upstream/monitoring/ package
   - Define 4 alert rules with evaluation logic
   - Implement notification delivery (email/Slack)
   - Add alert suppression with cache

2. **472fafa8** - feat(quick-024): create check_monitoring_alerts management command
   - Django management command
   - --dry-run, --rule, --verbose flags
   - Status output and error handling

3. **a4c03230** - feat(quick-024): add MONITORING_ALERTS configuration to settings
   - MONITORING_ALERTS dict in base.py
   - Email/Slack channel config
   - Threshold configuration
   - .env.production.example documentation

**Total Duration:** 9 minutes
**Lines Added:** ~900 (616 alert_rules + 198 command + 86 config/docs)

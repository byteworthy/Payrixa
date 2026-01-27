---
phase: quick-024
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - upstream/monitoring/alert_rules.py
  - upstream/monitoring/__init__.py
  - upstream/management/commands/check_monitoring_alerts.py
  - upstream/settings/base.py
  - .env.production.example
autonomous: true

user_setup:
  - service: prometheus-alertmanager
    why: "Routes monitoring alerts to notification channels"
    env_vars:
      - name: ALERTMANAGER_URL
        source: "Set to your Alertmanager endpoint (e.g., http://alertmanager:9093)"
      - name: ALERT_EMAIL_RECIPIENTS
        source: "Comma-separated list of email addresses for critical alerts"
      - name: ALERT_SLACK_WEBHOOK_URL
        source: "Slack incoming webhook URL from Slack App settings"
    dashboard_config:
      - task: "Create Slack incoming webhook"
        location: "Slack -> Apps -> Incoming Webhooks -> Add to Slack"

must_haves:
  truths:
    - "High error rate alerts fire when 5xx responses exceed threshold"
    - "Slow response time alerts fire when p95 latency exceeds 2 seconds"
    - "Database pool exhaustion alerts fire when connections hit max"
    - "Failed Celery task alerts fire when task failure rate exceeds threshold"
    - "Alerts route to configured email and Slack channels"
  artifacts:
    - path: "upstream/monitoring/alert_rules.py"
      provides: "Alert rule definitions with thresholds and conditions"
      min_lines: 200
      exports: ["ALERT_RULES", "evaluate_alert_rules", "send_alert_notification"]
    - path: "upstream/management/commands/check_monitoring_alerts.py"
      provides: "Management command to evaluate alert rules"
      contains: "BaseCommand"
    - path: "upstream/settings/base.py"
      provides: "Alert configuration settings"
      contains: "MONITORING_ALERTS"
  key_links:
    - from: "upstream/monitoring/alert_rules.py"
      to: "upstream/metrics.py"
      via: "queries Prometheus metrics for thresholds"
      pattern: "from upstream.metrics import"
    - from: "upstream/management/commands/check_monitoring_alerts.py"
      to: "upstream/monitoring/alert_rules.py"
      via: "calls evaluate_alert_rules()"
      pattern: "evaluate_alert_rules"
    - from: "upstream/monitoring/alert_rules.py"
      to: "django.core.mail.send_mail"
      via: "sends email notifications"
      pattern: "send_mail"
---

<objective>
Configure alert routing system that monitors platform health metrics (error rates, response times, database connections, Celery tasks) and sends notifications to email and Slack channels when thresholds are exceeded.

Purpose: Enable proactive incident response by alerting operators to degraded performance, errors, and resource exhaustion before they impact users.
Output: Alert rule definitions, evaluation logic, notification channels, and management command for periodic checking.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Current monitoring infrastructure:
- Prometheus metrics: upstream/metrics.py (business metrics for alerts/drift/jobs)
- django-prometheus: Request/response metrics, DB metrics, cache metrics (automatic)
- Monitoring checks: upstream/monitoring_checks.py (deployment-time validation)
- Alert processing service: upstream/services/alert_processing.py (business alerts for drift/delays)

This task creates PLATFORM monitoring alerts (different from business alerts):
- Business alerts: Notify customers about drift/delays in their data
- Platform alerts: Notify operators about system health (errors, latency, failures)

Monitoring stack:
- Prometheus metrics exposed at /metrics (django-prometheus middleware)
- Alert rules query these metrics and fire when thresholds exceeded
- Notifications sent via email (Django mail) and Slack webhooks
- Management command runs periodically (via cron or Celery beat) to evaluate rules

Pattern reference:
- Business alerts: upstream/services/alert_processing.py (evaluation/delivery logic)
- Sentry integration: quick-013 (error tracking with email notifications)
- Prometheus setup: quick-001 (metrics endpoint)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create alert rule definitions with evaluation logic</name>
  <files>
    upstream/monitoring/alert_rules.py
    upstream/monitoring/__init__.py
  </files>
  <action>
Create upstream/monitoring/ directory and alert_rules.py module defining platform monitoring alerts.

Create upstream/monitoring/alert_rules.py with:

1. Alert rule data structure defining 4 critical alert rules:
   - High error rate: 5xx responses > 5% of total requests in 5min window
   - Slow response time: p95 latency > 2000ms for 5min
   - Database pool exhaustion: Active connections > 90% of max pool size
   - Failed Celery tasks: Task failure rate > 10% in 15min window

2. Rule definition structure:
```python
ALERT_RULES = [
    {
        "name": "high_error_rate",
        "description": "High rate of 5xx errors detected",
        "severity": "critical",
        "metric": "django_http_responses_total_by_status",
        "condition": "rate > 0.05",  # 5% of requests
        "window": "5m",
        "threshold": 0.05,
        "notification_channels": ["email", "slack"],
    },
    # ... 3 more rules
]
```

3. evaluate_alert_rules() function:
   - Queries Prometheus metrics endpoint (/metrics) via HTTP
   - Parses prometheus_client text format
   - Compares current values against rule thresholds
   - Returns list of triggered alerts with context

4. send_alert_notification() function:
   - Takes alert dict with rule name, severity, current value, threshold
   - Sends email using Django send_mail() if ALERT_EMAIL_RECIPIENTS configured
   - Sends Slack message via requests.post() if ALERT_SLACK_WEBHOOK_URL configured
   - Formats message with severity emoji, metric values, timestamp
   - Logs all notifications for audit trail

5. Helper functions:
   - query_prometheus_metric(metric_name, window): Fetches metric value
   - format_alert_message(alert): Formats human-readable message
   - should_suppress_alert(alert, history): Prevents duplicate notifications (5min cooldown)

Implementation notes:
- Use requests library for Prometheus metric queries (local HTTP to /metrics)
- Parse prometheus_client text format (lines like "metric_name{labels} value timestamp")
- Store alert history in cache (django.core.cache) for suppression
- Follow pattern from upstream/services/alert_processing.py for suppression logic
- Include detailed error context in notifications (metric value, threshold, duration)

Create upstream/monitoring/__init__.py to make it a package.
  </action>
  <verify>
1. Check files created:
   ```bash
   ls upstream/monitoring/alert_rules.py upstream/monitoring/__init__.py
   ```

2. Verify rule definitions exist:
   ```bash
   python manage.py shell -c "from upstream.monitoring.alert_rules import ALERT_RULES; print(f'{len(ALERT_RULES)} rules defined')"
   ```

3. Test evaluation logic (dry run):
   ```bash
   python manage.py shell -c "from upstream.monitoring.alert_rules import evaluate_alert_rules; print(evaluate_alert_rules())"
   ```
  </verify>
  <done>
- upstream/monitoring/alert_rules.py exists with 4 alert rules defined
- ALERT_RULES list contains rules for error rate, latency, DB pool, Celery failures
- evaluate_alert_rules() function queries Prometheus and returns triggered alerts
- send_alert_notification() function sends to email and Slack channels
- Alert suppression prevents duplicate notifications within 5min cooldown
  </done>
</task>

<task type="auto">
  <name>Task 2: Create management command for periodic alert evaluation</name>
  <files>upstream/management/commands/check_monitoring_alerts.py</files>
  <action>
Create Django management command that evaluates alert rules and sends notifications when triggered.

Create upstream/management/commands/check_monitoring_alerts.py with:

1. Django BaseCommand class that:
   - Calls evaluate_alert_rules() to get triggered alerts
   - Sends notifications via send_alert_notification() for each alert
   - Logs evaluation results (alerts triggered, notifications sent)
   - Handles errors gracefully (catches exceptions, logs to Sentry if configured)

2. Command arguments:
   - --dry-run: Evaluate rules but don't send notifications (logs only)
   - --rule: Filter to specific rule name (optional)
   - --verbose: Enable detailed output

3. Output format:
   ```
   Evaluating 4 monitoring alert rules...
   [TRIGGERED] high_error_rate: 7.2% error rate (threshold: 5.0%)
   [OK] slow_response_time: p95=1234ms (threshold: 2000ms)
   [OK] db_pool_exhaustion: 45% utilization (threshold: 90%)
   [OK] celery_task_failures: 2% failure rate (threshold: 10%)

   Sent 1 notifications (1 email, 1 slack)
   ```

4. Integration points:
   - Import from upstream.monitoring.alert_rules
   - Use Django settings for configuration
   - Log to 'upstream.monitoring.alerts' logger
   - Track metrics via upstream.metrics (alert notification counters)

5. Error handling:
   - Catch prometheus query failures (metrics endpoint unavailable)
   - Catch notification failures (email/Slack service down)
   - Log errors but continue processing remaining rules
   - Exit with status code 0 even if notifications fail (alerting system issues shouldn't break cron)

Usage in production (via cron or Celery beat):
```bash
# Run every 5 minutes
*/5 * * * * cd /app && python manage.py check_monitoring_alerts
```
  </action>
  <verify>
1. Check command exists:
   ```bash
   python manage.py help check_monitoring_alerts
   ```

2. Run dry run:
   ```bash
   python manage.py check_monitoring_alerts --dry-run --verbose
   ```

3. Test with specific rule:
   ```bash
   python manage.py check_monitoring_alerts --rule high_error_rate --dry-run
   ```
  </verify>
  <done>
- Management command check_monitoring_alerts exists and is registered
- Command evaluates all 4 alert rules successfully
- --dry-run flag prevents actual notifications
- Command handles errors gracefully (metrics endpoint down, notification failures)
- Verbose output shows rule evaluation results and notification status
  </done>
</task>

<task type="auto">
  <name>Task 3: Add alert configuration to settings and document setup</name>
  <files>
    upstream/settings/base.py
    .env.production.example
  </files>
  <action>
Add monitoring alert configuration to Django settings and document environment variables for production setup.

1. Add to upstream/settings/base.py (after line 300, in Monitoring section):

```python
# =============================================================================
# MONITORING ALERTS (Platform Health)
# =============================================================================

# Alert notification channels
MONITORING_ALERTS = {
    "enabled": config("MONITORING_ALERTS_ENABLED", default=True, cast=bool),
    "evaluation_interval": 300,  # seconds (5 minutes)
    "cooldown_period": 300,  # seconds (5 minutes) - suppress duplicate alerts

    # Email notifications
    "email": {
        "enabled": config("ALERT_EMAIL_ENABLED", default=True, cast=bool),
        "recipients": config(
            "ALERT_EMAIL_RECIPIENTS",
            default="ops@example.com",
            cast=lambda v: [email.strip() for email in v.split(",") if email.strip()],
        ),
        "from_email": config("ALERT_FROM_EMAIL", default=DEFAULT_FROM_EMAIL),
    },

    # Slack notifications
    "slack": {
        "enabled": config("ALERT_SLACK_ENABLED", default=False, cast=bool),
        "webhook_url": config("ALERT_SLACK_WEBHOOK_URL", default=""),
        "channel": config("ALERT_SLACK_CHANNEL", default="#alerts"),
        "username": "Upstream Monitoring",
        "icon_emoji": ":rotating_light:",
    },

    # Alert thresholds (can be overridden via env vars)
    "thresholds": {
        "error_rate": config("ALERT_THRESHOLD_ERROR_RATE", default=0.05, cast=float),  # 5%
        "response_time_p95": config("ALERT_THRESHOLD_RESPONSE_TIME", default=2000, cast=int),  # ms
        "db_pool_utilization": config("ALERT_THRESHOLD_DB_POOL", default=0.90, cast=float),  # 90%
        "celery_failure_rate": config("ALERT_THRESHOLD_CELERY_FAILURES", default=0.10, cast=float),  # 10%
    },
}

# Prometheus metrics endpoint (for alert rule queries)
PROMETHEUS_METRICS_PATH = "/metrics"
```

2. Add to .env.production.example (after Sentry configuration):

```bash
# =============================================================================
# MONITORING ALERTS - Platform health notifications
# =============================================================================

# Enable/disable monitoring alerts
MONITORING_ALERTS_ENABLED=true

# Email notifications for critical alerts
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_RECIPIENTS=ops@your-company.com,oncall@your-company.com
ALERT_FROM_EMAIL=alerts@your-company.com

# Slack notifications (optional but recommended)
# Create webhook: https://api.slack.com/messaging/webhooks
ALERT_SLACK_ENABLED=true
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_SLACK_CHANNEL=#alerts

# Alert thresholds (optional overrides)
# ALERT_THRESHOLD_ERROR_RATE=0.05        # 5% error rate
# ALERT_THRESHOLD_RESPONSE_TIME=2000     # 2 seconds p95
# ALERT_THRESHOLD_DB_POOL=0.90           # 90% pool utilization
# ALERT_THRESHOLD_CELERY_FAILURES=0.10   # 10% task failures

# Alertmanager integration (optional - for advanced routing)
# ALERTMANAGER_URL=http://alertmanager:9093
```

3. Update imports at top of base.py if needed:
   - Ensure `from decouple import config, Csv` is present

Implementation notes:
- Follow existing settings pattern (Sentry, logging config)
- Use decouple.config() for env var parsing with defaults
- Cast ALERT_EMAIL_RECIPIENTS to list via lambda (comma-separated string)
- Set sensible defaults for development (enabled but logs only)
- Make Slack optional (some orgs use email only)
  </action>
  <verify>
1. Check settings load without errors:
   ```bash
   python manage.py shell -c "from django.conf import settings; print(settings.MONITORING_ALERTS)"
   ```

2. Verify default values:
   ```bash
   python manage.py shell -c "from django.conf import settings; print(f\"Error threshold: {settings.MONITORING_ALERTS['thresholds']['error_rate']}\")"
   ```

3. Test env var parsing:
   ```bash
   ALERT_EMAIL_RECIPIENTS="foo@test.com,bar@test.com" python manage.py shell -c "from django.conf import settings; print(settings.MONITORING_ALERTS['email']['recipients'])"
   ```
  </verify>
  <done>
- MONITORING_ALERTS configuration exists in upstream/settings/base.py
- Settings include email and Slack channel configuration with sensible defaults
- Thresholds configurable via environment variables
- .env.production.example documents all alert-related env vars with examples
- Configuration follows existing pattern (Sentry, logging)
  </done>
</task>

</tasks>

<verification>
Overall system verification:

1. Alert rule evaluation:
   ```bash
   python manage.py check_monitoring_alerts --dry-run --verbose
   ```
   Should evaluate all 4 rules and show current metric values vs thresholds.

2. Settings validation:
   ```bash
   python manage.py check --deploy
   ```
   Should pass without errors related to monitoring alerts.

3. Import verification:
   ```bash
   python -c "from upstream.monitoring.alert_rules import ALERT_RULES, evaluate_alert_rules, send_alert_notification; print('All imports successful')"
   ```

4. Management command help:
   ```bash
   python manage.py help check_monitoring_alerts
   ```
   Should show command description and arguments.
</verification>

<success_criteria>
- [ ] upstream/monitoring/alert_rules.py exists with 4 alert rules (error rate, latency, DB pool, Celery)
- [ ] evaluate_alert_rules() queries Prometheus metrics and identifies threshold violations
- [ ] send_alert_notification() sends formatted messages to email and Slack
- [ ] Alert suppression prevents duplicate notifications within 5min cooldown
- [ ] Management command check_monitoring_alerts runs without errors
- [ ] MONITORING_ALERTS configuration in upstream/settings/base.py with env var overrides
- [ ] .env.production.example documents all alert setup including Slack webhook creation
- [ ] Dry run execution shows alert evaluation results for all rules
</success_criteria>

<output>
After completion, create `.planning/quick/024-configure-alert-routing-set-up-aler/024-SUMMARY.md`
</output>

---
phase: quick-001
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - upstream/settings/base.py
  - hello_world/urls.py
  - upstream/metrics.py
autonomous: true

must_haves:
  truths:
    - "/metrics endpoint is accessible and returns Prometheus-formatted metrics"
    - "Request rate, error rate, and database query metrics are exposed"
    - "Business metrics (alerts, drift detection) are available for scraping"
  artifacts:
    - path: "hello_world/urls.py"
      provides: "Metrics endpoint registration"
      contains: "django_prometheus.urls"
    - path: "upstream/settings/base.py"
      provides: "Prometheus middleware and app configuration"
      contains: "django_prometheus"
    - path: "upstream/metrics.py"
      provides: "Custom business metrics definitions"
      min_lines: 200
  key_links:
    - from: "django_prometheus.middleware"
      to: "prometheus_client"
      via: "request/response timing and database query tracking"
      pattern: "PrometheusBeforeMiddleware.*PrometheusAfterMiddleware"
---

<objective>
Validate and document existing Prometheus metrics endpoint for production monitoring.

Purpose: Ensure the /metrics endpoint is ready for production Prometheus scraping with request rates, errors, database query metrics, and custom business metrics.

Output: Validated metrics endpoint with documentation of exposed metrics categories and verification test.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md

# Existing metrics infrastructure
@upstream/metrics.py
@upstream/monitoring_checks.py
@upstream/settings/base.py
@hello_world/urls.py

# Current configuration status
The system already has django-prometheus installed and configured:
- django-prometheus~=2.3.1 in requirements.txt
- PrometheusBeforeMiddleware and PrometheusAfterMiddleware in MIDDLEWARE
- Metrics endpoint registered at /metrics in hello_world/urls.py
- Custom business metrics defined in upstream/metrics.py
- Monitoring checks validate Prometheus configuration in upstream/monitoring_checks.py

This is a validation task - no new installation required.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Validate metrics endpoint functionality</name>
  <files>
    upstream/settings/base.py
    hello_world/urls.py
    upstream/metrics.py
  </files>
  <action>
    Verify the existing Prometheus metrics setup is working correctly:

    1. Start Django development server if not running
    2. Query the /metrics endpoint and verify response format
    3. Confirm django-prometheus default metrics are exposed:
       - django_http_requests_total_by_view_transport_method (request rates)
       - django_http_responses_total_by_status_view_method (error rates)
       - django_db_query_duration_seconds (database query metrics)
       - django_http_requests_latency_seconds_by_view_method (latency histograms)
    4. Confirm custom business metrics from upstream/metrics.py are registered:
       - upstream_alert_created_total
       - upstream_drift_event_detected_total
       - upstream_background_job_started_total
       - upstream_data_quality_score
    5. Test metric label functionality by triggering a sample metric increment

    Verify the middleware order is correct:
    - PrometheusBeforeMiddleware appears early in MIDDLEWARE stack
    - PrometheusAfterMiddleware appears at end of MIDDLEWARE stack

    Confirm django_prometheus is in INSTALLED_APPS.

    Note: This is validation only - no code changes required unless issues found.
  </action>
  <verify>
    ```bash
    # Start server if needed
    python manage.py runserver &
    SERVER_PID=$!
    sleep 3

    # Query metrics endpoint
    curl -s http://localhost:8000/metrics | head -100

    # Verify key metrics exist
    curl -s http://localhost:8000/metrics | grep -E "(django_http_requests_total|django_db_query_duration|upstream_alert_created_total|upstream_drift_event_detected_total)"

    # Check middleware configuration
    python manage.py shell -c "from django.conf import settings; import json; print(json.dumps([m for m in settings.MIDDLEWARE if 'prometheus' in m.lower()], indent=2))"

    # Stop test server
    kill $SERVER_PID 2>/dev/null || true
    ```

    Expected:
    - /metrics returns 200 OK with text/plain; version=0.0.4 content-type
    - Response contains django_http_requests_total, django_db_query_duration metrics
    - Response contains upstream_alert_created_total, upstream_drift_event_detected_total
    - PrometheusBeforeMiddleware and PrometheusAfterMiddleware present in settings
  </verify>
  <done>
    Metrics endpoint is accessible at /metrics, returns Prometheus-formatted metrics including HTTP request rates, database query durations, and custom business metrics (alerts, drift detection, background jobs).
  </done>
</task>

<task type="auto">
  <name>Task 2: Create metrics endpoint documentation</name>
  <files>
    docs/PROMETHEUS_METRICS.md
  </files>
  <action>
    Create comprehensive documentation for the Prometheus metrics endpoint:

    1. Create docs/PROMETHEUS_METRICS.md with:
       - Endpoint URL and access method
       - Prometheus scrape configuration example
       - List of default django-prometheus metrics with descriptions
       - List of custom business metrics from upstream/metrics.py
       - Example queries for common monitoring scenarios
       - Grafana dashboard recommendations

    2. Document the key metric categories:
       **HTTP Metrics (django-prometheus default):**
       - Request rates by view and method
       - Response status distributions
       - Request latency histograms
       - Response size distributions

       **Database Metrics (django-prometheus default):**
       - Query duration histograms
       - Query count by type (SELECT, INSERT, UPDATE)
       - Connection pool status

       **Business Metrics (custom):**
       - Alert creation and delivery rates
       - Drift detection events
       - Background job status
       - Data quality scores
       - Report generation metrics

    3. Include example PromQL queries:
       - Request rate: rate(django_http_requests_total[5m])
       - Error rate: rate(django_http_responses_total_by_status{status=~"5.."}[5m])
       - P95 latency: histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))
       - Alert rate by severity: rate(upstream_alert_created_total[1h])

    4. Add production scrape config example:
       ```yaml
       scrape_configs:
         - job_name: 'django-upstream'
           static_configs:
             - targets: ['app:8000']
           metrics_path: '/metrics'
           scrape_interval: 15s
       ```

    Use the existing upstream/metrics.py as source for custom metrics documentation.
  </action>
  <verify>
    ```bash
    # Verify documentation file exists
    ls -lh docs/PROMETHEUS_METRICS.md

    # Check for key sections
    grep -E "(Endpoint|Metrics|PromQL|scrape_config)" docs/PROMETHEUS_METRICS.md

    # Verify custom metrics are documented
    grep -E "(upstream_alert_created|upstream_drift_event|upstream_background_job)" docs/PROMETHEUS_METRICS.md
    ```

    Expected:
    - docs/PROMETHEUS_METRICS.md exists and is >100 lines
    - Contains endpoint URL, scrape config, and metric descriptions
    - Documents both django-prometheus defaults and custom business metrics
    - Includes example PromQL queries
  </verify>
  <done>
    Documentation created at docs/PROMETHEUS_METRICS.md describing the /metrics endpoint, available metrics categories (HTTP, database, business), and example Prometheus scrape configuration with PromQL queries.
  </done>
</task>

<task type="auto">
  <name>Task 3: Add metrics endpoint test</name>
  <files>
    upstream/tests/test_monitoring.py
  </files>
  <action>
    Create a test to validate the Prometheus metrics endpoint is working:

    1. Create or update upstream/tests/test_monitoring.py with:
       - Test that /metrics endpoint returns 200 OK
       - Test that response contains expected django-prometheus metrics
       - Test that response contains custom business metrics
       - Test that metric format is valid Prometheus exposition format
       - Test that metrics can be incremented (using a sample counter)

    2. Add test cases:
       ```python
       def test_metrics_endpoint_accessible(client):
           """Test /metrics endpoint returns valid Prometheus metrics."""
           response = client.get('/metrics')
           assert response.status_code == 200
           assert 'text/plain' in response['Content-Type']

       def test_django_prometheus_metrics_present(client):
           """Test default django-prometheus metrics are exposed."""
           response = client.get('/metrics')
           content = response.content.decode('utf-8')
           assert 'django_http_requests_total' in content
           assert 'django_db_query_duration_seconds' in content

       def test_custom_business_metrics_present(client):
           """Test custom business metrics are registered."""
           response = client.get('/metrics')
           content = response.content.decode('utf-8')
           assert 'upstream_alert_created_total' in content
           assert 'upstream_drift_event_detected_total' in content
       ```

    3. Add a test that verifies metrics can be incremented:
       ```python
       def test_metrics_can_be_incremented():
           """Test that custom metrics can be incremented."""
           from upstream.metrics import track_alert_created
           # Increment metric
           track_alert_created('DriftWatch', 'high', 1)
           # Verify metric exists (no exception)
       ```

    Use pytest conventions. Import existing metrics from upstream.metrics.
  </action>
  <verify>
    ```bash
    # Run the new monitoring tests
    pytest upstream/tests/test_monitoring.py -v -k "metrics"

    # Verify test file exists and has test functions
    grep -E "def test_.*metrics" upstream/tests/test_monitoring.py
    ```

    Expected:
    - Test file exists with 3+ test functions
    - All metrics endpoint tests pass
    - Tests verify /metrics endpoint, django-prometheus metrics, and custom metrics
  </verify>
  <done>
    Test suite created in upstream/tests/test_monitoring.py with tests validating /metrics endpoint accessibility, django-prometheus default metrics presence, custom business metrics registration, and metric increment functionality. All tests pass.
  </done>
</task>

</tasks>

<verification>
After all tasks complete, verify:

1. Metrics endpoint test suite passes:
   ```bash
   pytest upstream/tests/test_monitoring.py -v
   ```

2. Manual endpoint verification:
   ```bash
   python manage.py runserver &
   sleep 3
   curl -s http://localhost:8000/metrics | grep -E "(django_http_requests_total|upstream_alert_created_total)"
   ```

3. Documentation exists:
   ```bash
   ls -lh docs/PROMETHEUS_METRICS.md
   cat docs/PROMETHEUS_METRICS.md | grep "Endpoint"
   ```

4. Monitoring checks pass:
   ```bash
   python manage.py check --deploy 2>&1 | grep -i prometheus
   ```

Expected results:
- All tests pass
- /metrics endpoint returns valid Prometheus metrics
- Documentation describes endpoint usage and available metrics
- No deployment check errors for Prometheus configuration
</verification>

<success_criteria>
1. /metrics endpoint is accessible and returns HTTP 200
2. Response contains django-prometheus default metrics (requests, database queries, latency)
3. Response contains custom business metrics (alerts, drift events, background jobs)
4. Documentation exists at docs/PROMETHEUS_METRICS.md with endpoint details and PromQL examples
5. Test suite validates metrics endpoint functionality
6. No Prometheus-related errors in deployment checks
</success_criteria>

<output>
After completion, create `.planning/quick/001-add-prometheus-metrics-endpoint-for-pro/001-SUMMARY.md`
</output>

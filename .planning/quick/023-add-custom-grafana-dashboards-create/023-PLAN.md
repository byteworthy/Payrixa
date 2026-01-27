---
phase: quick-023
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - monitoring/grafana/dashboards/api-performance.json
  - monitoring/grafana/dashboards/database-metrics.json
  - monitoring/grafana/dashboards/celery-tasks.json
  - monitoring/grafana/dashboards/error-rates.json
  - monitoring/grafana/provisioning/dashboards/dashboard.yml
autonomous: true

must_haves:
  truths:
    - "Grafana loads 4 custom dashboards on startup"
    - "API performance dashboard shows request rates and latency by endpoint"
    - "Database dashboard shows query counts and connection pool metrics"
    - "Celery dashboard shows task execution rates, failures, and duration"
    - "Error dashboard shows 4xx/5xx rates grouped by status code"
  artifacts:
    - path: "monitoring/grafana/dashboards/api-performance.json"
      provides: "API performance metrics visualization"
      min_lines: 100
    - path: "monitoring/grafana/dashboards/database-metrics.json"
      provides: "Database query and connection metrics"
      min_lines: 80
    - path: "monitoring/grafana/dashboards/celery-tasks.json"
      provides: "Celery task monitoring dashboard"
      min_lines: 100
    - path: "monitoring/grafana/dashboards/error-rates.json"
      provides: "HTTP error rate tracking"
      min_lines: 80
    - path: "monitoring/grafana/provisioning/dashboards/dashboard.yml"
      provides: "Grafana auto-provisioning config"
      min_lines: 10
  key_links:
    - from: "monitoring/grafana/provisioning/dashboards/dashboard.yml"
      to: "monitoring/grafana/dashboards/*.json"
      via: "path reference in provisioning config"
      pattern: "path:.*dashboards"
    - from: "monitoring/grafana/dashboards/*.json"
      to: "prometheus"
      via: "Prometheus data source queries"
      pattern: "datasource.*[Pp]rometheus"
---

<objective>
Create 4 custom Grafana dashboard JSON configurations for comprehensive monitoring of the Upstream Healthcare Platform.

Purpose: Operational visibility into API performance, database health, background job execution, and error patterns. These dashboards leverage existing django-prometheus and custom upstream.metrics to provide production-ready monitoring without manual dashboard creation.

Output: Auto-provisioned Grafana dashboards loaded on container startup, querying Prometheus data sources for real-time metrics visualization.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/PROJECT.md

# Existing monitoring infrastructure
@monitoring/prometheus/prometheus.yml
@monitoring/grafana/dashboards/payrixa-dashboard.json

# Custom metrics available
@upstream/metrics.py
@upstream/celery_monitoring.py

# Stack and architecture
@.planning/codebase/STACK.md
@.planning/codebase/ARCHITECTURE.md
</context>

<tasks>

<task type="auto">
  <name>Create Grafana provisioning config and API performance dashboard</name>
  <files>
monitoring/grafana/provisioning/dashboards/dashboard.yml
monitoring/grafana/dashboards/api-performance.json
  </files>
  <action>
1. Create provisioning config at `monitoring/grafana/provisioning/dashboards/dashboard.yml`:
   - Set `apiVersion: 1`
   - Configure provider with `name: 'dashboards'`, `type: file`, `updateIntervalSeconds: 30`
   - Set `options.path: /etc/grafana/provisioning/dashboards`
   - Add `options.foldersFromFilesStructure: true` for organization
   - This enables auto-loading of all JSON dashboards in the directory

2. Create API performance dashboard at `monitoring/grafana/dashboards/api-performance.json`:
   - Title: "Upstream API Performance"
   - Tags: ["upstream", "api", "performance"]
   - Row 1: Request metrics
     - Panel 1: HTTP request rate by method (rate(django_http_requests_total_by_method_total[5m]))
     - Panel 2: Request latency p50/p95/p99 (histogram_quantile for django_http_requests_latency_seconds_by_view_method_bucket)
   - Row 2: Endpoint-specific
     - Panel 3: Top 10 slowest endpoints (topk(10, histogram_quantile(...)))
     - Panel 4: Request volume by endpoint (rate(django_http_requests_total_by_view_method_total[5m]))
   - Row 3: Custom business metrics
     - Panel 5: API rate limit hits (rate(upstream_api_rate_limit_hit_total[5m]))
     - Panel 6: Customer-specific API calls (rate(upstream_api_endpoint_calls_total[5m]) by customer_id)
   - Set refresh: "30s", time range: last 1 hour
   - Use graph panels with time series visualization
   - Datasource: "Prometheus" (default, auto-configured in docker-compose)
   - Set gridPos for 2-column layout (w: 12 for half-width panels)

Why: API dashboard consolidates request patterns, latency distribution, and rate limiting visibility in one view. Uses histogram_quantile for accurate percentile calculations from django-prometheus histograms.
  </action>
  <verify>
cat monitoring/grafana/provisioning/dashboards/dashboard.yml
cat monitoring/grafana/dashboards/api-performance.json | jq '.dashboard.panels | length'
  </verify>
  <done>
Provisioning config exists with correct path mapping. API dashboard has 6 panels covering request rates, latency percentiles, slow endpoints, volume by endpoint, rate limits, and customer segmentation.
  </done>
</task>

<task type="auto">
  <name>Create database and Celery monitoring dashboards</name>
  <files>
monitoring/grafana/dashboards/database-metrics.json
monitoring/grafana/dashboards/celery-tasks.json
  </files>
  <action>
1. Create database metrics dashboard at `monitoring/grafana/dashboards/database-metrics.json`:
   - Title: "Upstream Database Metrics"
   - Tags: ["upstream", "database", "postgresql"]
   - Row 1: Query volume
     - Panel 1: Database query rate (rate(django_db_query_total[5m]))
     - Panel 2: Query duration p95 (histogram_quantile(0.95, django_db_query_duration_seconds_bucket))
   - Row 2: Connection pool
     - Panel 3: Active connections (django_db_connections_active)
     - Panel 4: Connection errors (rate(django_db_errors_total[5m]))
   - Row 3: Custom ingestion metrics
     - Panel 5: Claim records ingested (rate(upstream_claim_records_ingested_total[5m]) by status)
     - Panel 6: Ingestion processing time p95 (histogram_quantile(0.95, upstream_ingestion_processing_seconds_bucket))
   - Set refresh: "30s", gridPos 2-column layout

2. Create Celery tasks dashboard at `monitoring/grafana/dashboards/celery-tasks.json`:
   - Title: "Upstream Celery Task Monitoring"
   - Tags: ["upstream", "celery", "background-jobs"]
   - Row 1: Task execution rates
     - Panel 1: Tasks started (rate(upstream_background_job_started_total[5m]) by job_type)
     - Panel 2: Tasks completed vs failed (rate(upstream_background_job_completed_total[5m]) vs rate(upstream_background_job_failed_total[5m]))
   - Row 2: Task duration and patterns
     - Panel 3: Task duration p95 by job_type (histogram_quantile(0.95, upstream_background_job_duration_seconds_bucket))
     - Panel 4: Error types distribution (rate(upstream_background_job_failed_total[5m]) by error_type)
   - Row 3: Business-specific tasks
     - Panel 5: Alert delivery rates (rate(upstream_alert_delivered_total[5m]) by channel_type)
     - Panel 6: Report generation time (histogram_quantile(0.95, upstream_report_generation_seconds_bucket))
   - Row 4: Task health
     - Panel 7: Task success rate (100 * rate(completed) / (rate(started) + 0.001)) - shows percentage
     - Panel 8: Alert failures by type (rate(upstream_alert_failed_total[5m]) by error_type)
   - Set refresh: "30s", gridPos 2-column layout

Why database: Connection pool monitoring prevents exhaustion issues. Ingestion metrics from upstream.metrics show domain-specific load patterns.

Why Celery: 8-panel layout provides comprehensive view of background job health. Success rate calculation prevents division by zero with +0.001 offset. Alert and report panels surface business-critical task patterns.
  </action>
  <verify>
cat monitoring/grafana/dashboards/database-metrics.json | jq '.dashboard.title'
cat monitoring/grafana/dashboards/celery-tasks.json | jq '.dashboard.panels | length'
  </verify>
  <done>
Database dashboard has 6 panels covering query rates, duration, connections, errors, and ingestion metrics. Celery dashboard has 8 panels showing task execution, duration, errors, alerts, reports, and success rates.
  </done>
</task>

<task type="auto">
  <name>Create error rates dashboard and update docker-compose</name>
  <files>
monitoring/grafana/dashboards/error-rates.json
docker-compose.yml
  </files>
  <action>
1. Create error rates dashboard at `monitoring/grafana/dashboards/error-rates.json`:
   - Title: "Upstream Error Rates"
   - Tags: ["upstream", "errors", "reliability"]
   - Row 1: HTTP errors
     - Panel 1: 4xx error rate (rate(django_http_responses_total_by_status_total{status=~"4.."}[5m]) by status)
     - Panel 2: 5xx error rate (rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]) by status)
   - Row 2: Error ratio and trends
     - Panel 3: Overall error percentage (100 * sum(rate(4xx+5xx)) / sum(rate(all_responses)))
     - Panel 4: Error rate heatmap (heatmap visualization showing error density over time)
   - Row 3: Business errors
     - Panel 5: Data quality check failures (rate(upstream_data_quality_check_failed_total[5m]) by check_type)
     - Panel 6: Alert failures (rate(upstream_alert_failed_total[5m]) by channel_type)
   - Row 4: Error details
     - Panel 7: Top error endpoints (topk(10, rate(django_http_responses_total_by_view_status_total{status=~"[45].."}[5m])))
     - Panel 8: Customer-specific errors (rate(upstream_data_quality_check_failed_total[5m]) by customer_id)
   - Set refresh: "30s", gridPos 2-column layout
   - Add alert thresholds: red line at 5% error rate (SLO threshold from Phase 5)

2. Update docker-compose.yml to mount provisioning directory:
   - Find `grafana.volumes` section
   - Add new volume mount: `./monitoring/grafana/provisioning:/etc/grafana/provisioning`
   - Ensure existing dashboards volume remains: `./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards`
   - Add environment variable: `GF_PATHS_PROVISIONING=/etc/grafana/provisioning`
   - This enables auto-loading on container startup

Why error dashboard: 8-panel comprehensive view surfaces reliability issues. Error percentage calculation uses PromQL sum() for accurate ratios. Heatmap shows temporal patterns (e.g., deploy-time spikes). Customer segmentation isolates problematic tenants.

Why docker-compose update: Grafana requires provisioning directory in specific path for auto-discovery. Explicit GF_PATHS_PROVISIONING ensures dashboards load even if Grafana changes defaults.
  </action>
  <verify>
cat monitoring/grafana/dashboards/error-rates.json | jq '.dashboard.panels | length'
grep -A 5 "grafana:" docker-compose.yml | grep "provisioning"
docker-compose config --quiet && echo "docker-compose.yml valid" || echo "YAML syntax error"
  </verify>
  <done>
Error dashboard has 8 panels covering HTTP errors, error ratios, heatmaps, quality failures, alerts, top error endpoints, and customer segmentation. docker-compose.yml mounts provisioning directory to /etc/grafana/provisioning. YAML syntax validates.
  </done>
</task>

</tasks>

<verification>
1. **Auto-provisioning works:**
   ```bash
   docker-compose up -d grafana
   sleep 10
   curl -s http://localhost:3000/api/dashboards/tags | jq '.'
   # Should show "upstream" tag with 4 dashboards
   ```

2. **Dashboard queries return data:**
   ```bash
   # Check Prometheus has django-prometheus metrics
   curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep django_http

   # Check custom upstream metrics available
   curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep upstream_
   ```

3. **Dashboard structure validation:**
   ```bash
   # Each dashboard should have valid Grafana schema
   for dash in monitoring/grafana/dashboards/*.json; do
     jq -e '.dashboard.title' "$dash" > /dev/null && echo "$dash: valid"
   done
   ```

4. **Provisioning config correct:**
   ```bash
   cat monitoring/grafana/provisioning/dashboards/dashboard.yml
   # Should have apiVersion: 1 and path to dashboards directory
   ```
</verification>

<success_criteria>
- [ ] 4 dashboard JSON files created (api-performance, database-metrics, celery-tasks, error-rates)
- [ ] Grafana provisioning config exists at monitoring/grafana/provisioning/dashboards/dashboard.yml
- [ ] docker-compose.yml mounts provisioning directory
- [ ] All dashboards use Prometheus datasource with valid PromQL queries
- [ ] API dashboard: 6 panels (request rates, latency, slow endpoints, volume, rate limits, customer calls)
- [ ] Database dashboard: 6 panels (query rate/duration, connections/errors, ingestion metrics)
- [ ] Celery dashboard: 8 panels (execution rates, duration, errors, alerts, reports, success rate)
- [ ] Error dashboard: 8 panels (4xx/5xx rates, error %, heatmap, quality checks, top endpoints, customer errors)
- [ ] Each dashboard uses histogram_quantile for p95/p99 calculations from histogram buckets
- [ ] docker-compose.yml syntax validates with `docker-compose config --quiet`
</success_criteria>

<output>
After completion, create `.planning/quick/023-add-custom-grafana-dashboards-create/023-SUMMARY.md`
</output>

# Prometheus Metrics Documentation

## Overview

The Upstream Healthcare platform exposes Prometheus-formatted metrics at the `/metrics` endpoint for comprehensive operational monitoring. This includes HTTP request metrics, database performance, and custom business metrics for healthcare operations.

## Endpoint Access

**URL:** `http://your-domain.com/metrics`

**Method:** GET

**Authentication:** Public (configure firewall rules to restrict access to Prometheus servers only)

**Content-Type:** `text/plain; version=0.0.4` (Prometheus exposition format)

## Prometheus Scrape Configuration

Add this configuration to your `prometheus.yml` file:

```yaml
scrape_configs:
  - job_name: 'django-upstream'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s
```

For Kubernetes deployments:

```yaml
scrape_configs:
  - job_name: 'upstream-production'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - upstream
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: upstream-api
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Metric Categories

### 1. HTTP Request Metrics (django-prometheus)

Django-prometheus automatically tracks all HTTP requests and responses.

#### Request Rates

**`django_http_requests_total_by_method_total`**
- Description: Total count of HTTP requests by method
- Type: Counter
- Labels: `method` (GET, POST, PUT, DELETE, PATCH)

**`django_http_requests_total_by_transport_total`**
- Description: Total count of HTTP requests by transport protocol
- Type: Counter
- Labels: `transport` (http, https)

**`django_http_requests_total_by_view_transport_method`**
- Description: Total count of HTTP requests by view, transport, and method
- Type: Counter
- Labels: `view`, `transport`, `method`

#### Response Status

**`django_http_responses_total_by_status_view_method`**
- Description: Total count of HTTP responses by status code, view, and method
- Type: Counter
- Labels: `status` (200, 201, 400, 401, 403, 404, 500, etc.), `view`, `method`

**`django_http_responses_total_by_status`**
- Description: Total count of HTTP responses by status code
- Type: Counter
- Labels: `status`

#### Latency

**`django_http_requests_latency_seconds_by_view_method`**
- Description: Histogram of request processing time by view and method
- Type: Histogram
- Labels: `view`, `method`
- Buckets: 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 25.0, 50.0, 75.0, +Inf

**`django_http_requests_latency_including_middlewares_seconds`**
- Description: Histogram of total request processing time including middleware
- Type: Histogram
- Buckets: Same as above

### 2. Database Metrics (django-prometheus)

#### Query Performance

**`django_db_query_duration_seconds`**
- Description: Histogram of database query execution time
- Type: Histogram
- Labels: `database` (default), `query_type` (SELECT, INSERT, UPDATE, DELETE)
- Buckets: 0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0

**`django_db_query_count_total`**
- Description: Total count of database queries executed
- Type: Counter
- Labels: `database`, `query_type`

#### Connection Pool

**`django_db_connections_total`**
- Description: Total number of database connections opened
- Type: Counter
- Labels: `database`

**`django_db_connections_active`**
- Description: Current number of active database connections
- Type: Gauge
- Labels: `database`

#### Model Operations

**`django_model_inserts_total`**
- Description: Total count of model insert operations
- Type: Counter
- Labels: `model`

**`django_model_updates_total`**
- Description: Total count of model update operations
- Type: Counter
- Labels: `model`

**`django_model_deletes_total`**
- Description: Total count of model delete operations
- Type: Counter
- Labels: `model`

### 3. Custom Business Metrics

#### Alert Metrics

**`upstream_alert_created_total`**
- Description: Total number of alert events created
- Type: Counter
- Labels: `product` (DriftWatch, DelayGuard, DenialScope), `severity` (low, medium, high, critical), `customer_id`

**`upstream_alert_delivered_total`**
- Description: Total number of alert notifications successfully delivered
- Type: Counter
- Labels: `product`, `channel_type` (email, slack, webhook), `customer_id`

**`upstream_alert_failed_total`**
- Description: Total number of alert notification failures
- Type: Counter
- Labels: `product`, `channel_type`, `error_type`, `customer_id`

**`upstream_alert_processing_seconds`**
- Description: Time spent processing and sending alerts
- Type: Histogram
- Labels: `product`
- Buckets: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0

**`upstream_alert_suppressed_total`**
- Description: Total number of alerts suppressed due to cooldown or noise patterns
- Type: Counter
- Labels: `product`, `reason` (cooldown, noise_pattern, duplicate), `customer_id`

#### Drift Detection Metrics

**`upstream_drift_event_detected_total`**
- Description: Total number of drift events detected across all customers
- Type: Counter
- Labels: `product`, `drift_type` (payment_delay, denial_rate, ar_aging), `severity_level` (low, medium, high), `customer_id`

**`upstream_drift_computation_seconds`**
- Description: Time spent computing drift detection algorithms
- Type: Histogram
- Labels: `product`
- Buckets: 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0

**`upstream_payment_delay_signal_total`**
- Description: Total number of payment delay signals created
- Type: Counter
- Labels: `severity` (low, medium, high), `customer_id`

**`upstream_denial_signal_total`**
- Description: Total number of denial signals created
- Type: Counter
- Labels: `signal_type` (rate_change, pattern_shift), `customer_id`

#### Data Quality Metrics

**`upstream_data_quality_score`**
- Description: Current data quality score (0.0-1.0) for each customer
- Type: Gauge
- Labels: `customer_id`, `metric_type` (completeness, accuracy, timeliness)

**`upstream_data_quality_check_failed_total`**
- Description: Total number of failed data quality checks
- Type: Counter
- Labels: `check_type` (missing_fields, invalid_values, duplicate_records), `severity` (warning, error, critical), `customer_id`

**`upstream_claim_records_ingested_total`**
- Description: Total number of claim records ingested from CSV uploads
- Type: Counter
- Labels: `customer_id`, `status` (success, failed, partial)

**`upstream_ingestion_processing_seconds`**
- Description: Time spent processing CSV ingestion batches
- Type: Histogram
- Labels: `customer_id`
- Buckets: 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0

#### Background Job Metrics

**`upstream_background_job_started_total`**
- Description: Total number of Celery background jobs started
- Type: Counter
- Labels: `job_type` (drift_detection, report_generation, data_sync), `customer_id`

**`upstream_background_job_completed_total`**
- Description: Total number of background jobs completed successfully
- Type: Counter
- Labels: `job_type`, `customer_id`

**`upstream_background_job_failed_total`**
- Description: Total number of background jobs that failed
- Type: Counter
- Labels: `job_type`, `error_type`, `customer_id`

**`upstream_background_job_duration_seconds`**
- Description: Duration of background job execution
- Type: Histogram
- Labels: `job_type`
- Buckets: 1.0, 5.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0

#### Report Generation Metrics

**`upstream_report_generated_total`**
- Description: Total number of reports generated
- Type: Counter
- Labels: `report_type` (drift_summary, payer_analysis, ar_aging, quality_report), `customer_id`

**`upstream_report_generation_seconds`**
- Description: Time spent generating reports
- Type: Histogram
- Labels: `report_type`
- Buckets: 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0

**`upstream_report_generation_failed_total`**
- Description: Total number of report generation failures
- Type: Counter
- Labels: `report_type`, `error_type`, `customer_id`

#### API Metrics

**`upstream_api_endpoint_calls_total`**
- Description: Custom tracking of specific API endpoints (supplementing django-prometheus)
- Type: Counter
- Labels: `endpoint`, `method`, `customer_id`

**`upstream_api_rate_limit_hit_total`**
- Description: Number of times API rate limits were hit
- Type: Counter
- Labels: `endpoint`, `throttle_class`, `customer_id`

#### Cache Metrics

**`upstream_cache_hit_total`**
- Description: Total number of cache hits
- Type: Counter
- Labels: `cache_key_prefix`

**`upstream_cache_miss_total`**
- Description: Total number of cache misses
- Type: Counter
- Labels: `cache_key_prefix`

## Example PromQL Queries

### Request Rate Monitoring

```promql
# Overall request rate (requests per second)
rate(django_http_requests_total_by_method_total[5m])

# Request rate by endpoint
rate(django_http_requests_total_by_view_transport_method[5m])

# Requests per minute (RPM) by method
sum(rate(django_http_requests_total_by_method_total[1m])) by (method) * 60
```

### Error Rate Monitoring

```promql
# 5xx error rate
rate(django_http_responses_total_by_status{status=~"5.."}[5m])

# 4xx error rate
rate(django_http_responses_total_by_status{status=~"4.."}[5m])

# Error percentage (5xx / total)
sum(rate(django_http_responses_total_by_status{status=~"5.."}[5m]))
/
sum(rate(django_http_responses_total_by_status[5m])) * 100
```

### Latency Monitoring

```promql
# P50 latency by view
histogram_quantile(0.50, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m]))

# P95 latency by view
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m]))

# P99 latency by view
histogram_quantile(0.99, rate(django_http_requests_latency_seconds_by_view_method_bucket[5m]))

# Average latency
rate(django_http_requests_latency_seconds_by_view_method_sum[5m])
/
rate(django_http_requests_latency_seconds_by_view_method_count[5m])
```

### Database Performance

```promql
# Average query duration by type
rate(django_db_query_duration_seconds_sum[5m])
/
rate(django_db_query_duration_seconds_count[5m])

# Slow query rate (> 1 second)
sum(rate(django_db_query_duration_seconds_bucket{le="1.0"}[5m]))

# Query rate by type
rate(django_db_query_count_total[5m])
```

### Business Metrics

```promql
# Alert creation rate by severity
rate(upstream_alert_created_total[1h]) by (severity)

# Drift detection events by product
rate(upstream_drift_event_detected_total[1h]) by (product)

# Data quality score per customer
upstream_data_quality_score by (customer_id, metric_type)

# Background job success rate
sum(rate(upstream_background_job_completed_total[5m])) by (job_type)
/
sum(rate(upstream_background_job_started_total[5m])) by (job_type) * 100

# Report generation P95 latency
histogram_quantile(0.95, rate(upstream_report_generation_seconds_bucket[5m])) by (report_type)

# Cache hit rate
sum(rate(upstream_cache_hit_total[5m]))
/
(sum(rate(upstream_cache_hit_total[5m])) + sum(rate(upstream_cache_miss_total[5m]))) * 100
```

## Grafana Dashboard Recommendations

### Dashboard 1: Application Health

**Panels:**
1. Request Rate (RPM) - Time series graph
2. Error Rate (%) - Time series graph with alerting threshold
3. P95 Latency - Time series graph by endpoint
4. Active Database Connections - Gauge
5. Error Count by Status Code - Bar chart
6. Top 10 Slowest Endpoints - Table

### Dashboard 2: Business Operations

**Panels:**
1. Alert Creation Rate - Time series by product and severity
2. Drift Events Detected - Counter with rate calculation
3. Data Quality Scores - Gauge per customer
4. Background Job Success Rate - Stat panel with sparkline
5. Report Generation Latency - Heatmap
6. Claims Ingested (24h) - Counter with daily rate

### Dashboard 3: Database Performance

**Panels:**
1. Query Duration P95 - Time series by query type
2. Query Rate - Time series by operation (SELECT/INSERT/UPDATE/DELETE)
3. Slow Queries (>1s) - Counter with rate
4. Database Connection Pool - Time series (active vs total)
5. Model Operations - Stacked area chart

### Dashboard 4: Customer Insights

**Panels:**
1. Alerts per Customer - Bar chart (top 10)
2. Data Quality by Customer - Table
3. API Usage per Customer - Time series
4. Drift Events per Customer - Heatmap
5. Background Jobs per Customer - Time series

## Alerting Rules

Example Prometheus alerting rules for production monitoring:

```yaml
groups:
  - name: upstream_critical
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(django_http_responses_total_by_status{status=~"5.."}[5m]))
          /
          sum(rate(django_http_responses_total_by_status[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High 5xx error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # High P95 latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(django_http_requests_latency_seconds_by_view_method_bucket[5m])
          ) > 2.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency detected"
          description: "P95 latency is {{ $value }}s for {{ $labels.view }}"

      # Slow database queries
      - alert: SlowDatabaseQueries
        expr: |
          histogram_quantile(0.95,
            rate(django_db_query_duration_seconds_bucket[5m])
          ) > 1.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "P95 query duration is {{ $value }}s"

      # Background job failures
      - alert: BackgroundJobFailures
        expr: |
          sum(rate(upstream_background_job_failed_total[15m])) by (job_type) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Background job failures detected"
          description: "{{ $labels.job_type }} failing at {{ $value }} jobs/sec"

      # Low data quality score
      - alert: LowDataQuality
        expr: |
          upstream_data_quality_score < 0.7
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Low data quality score"
          description: "Customer {{ $labels.customer_id }} quality score is {{ $value }}"

      # Cache degradation
      - alert: LowCacheHitRate
        expr: |
          sum(rate(upstream_cache_hit_total[10m]))
          /
          (sum(rate(upstream_cache_hit_total[10m])) + sum(rate(upstream_cache_miss_total[10m])))
          < 0.5
        for: 15m
        labels:
          severity: info
        annotations:
          summary: "Cache hit rate below 50%"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

## Security Considerations

1. **Firewall Rules**: Restrict `/metrics` endpoint to Prometheus server IPs only
2. **No Authentication Required**: The endpoint is public by design for Prometheus scraping
3. **PII/PHI Protection**: No personally identifiable information is exposed in metrics
4. **Customer Isolation**: Customer data is separated via `customer_id` labels only
5. **Rate Limiting**: Consider adding rate limiting if exposed to public networks

## Troubleshooting

### Metrics Not Appearing

1. Verify django-prometheus is installed:
   ```bash
   pip show django-prometheus
   ```

2. Check middleware configuration:
   ```python
   python manage.py shell -c "from django.conf import settings; print([m for m in settings.MIDDLEWARE if 'prometheus' in m.lower()])"
   ```

3. Verify endpoint is accessible:
   ```bash
   curl http://localhost:8000/metrics
   ```

### Custom Metrics Not Incrementing

1. Check metric is imported and called:
   ```python
   from upstream.metrics import track_alert_created
   track_alert_created('DriftWatch', 'high', customer_id=1)
   ```

2. Verify no exceptions in logs:
   ```bash
   grep "Failed to track.*metric" logs/app.log
   ```

### High Memory Usage

Django-prometheus stores metrics in memory. For high-traffic applications:

1. Use shorter scrape intervals (15s recommended)
2. Limit label cardinality (avoid unique identifiers as labels)
3. Monitor memory usage with process metrics

## References

- [django-prometheus Documentation](https://github.com/korfuri/django-prometheus)
- [Prometheus Exposition Formats](https://prometheus.io/docs/instrumenting/exposition_formats/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)

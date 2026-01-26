# Prometheus Metrics Documentation

## Overview

The Upstream Healthcare Revenue Intelligence platform exposes comprehensive metrics at the `/metrics` endpoint in Prometheus exposition format. These metrics provide visibility into application performance, database operations, and critical business operations for healthcare claims processing.

## Endpoint Access

**URL:** `http://<your-host>:8000/metrics`

**Method:** `GET`

**Authentication:** None (configure firewall rules to restrict access to Prometheus server only)

**Content-Type:** `text/plain; version=0.0.4` (Prometheus exposition format)

**Response Format:** Prometheus text-based exposition format with metric families, types, and labels

## Prometheus Scrape Configuration

Add this configuration to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'django-upstream'
    static_configs:
      - targets: ['app:8000']  # Adjust hostname/port for your deployment
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

    # Optional: Add labels for multi-environment monitoring
    # labels:
    #   environment: 'production'
    #   service: 'upstream-api'
```

For Kubernetes deployments, use ServiceMonitor or PodMonitor:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: upstream-metrics
spec:
  selector:
    matchLabels:
      app: upstream
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

## Metric Categories

### 1. HTTP Request Metrics (django-prometheus)

These metrics track all HTTP requests handled by Django:

#### `django_http_requests_total_by_view_transport_method_total`
- **Type:** Counter
- **Labels:** `view`, `transport`, `method`
- **Description:** Total count of HTTP requests grouped by Django view, transport protocol, and HTTP method
- **Example:** `django_http_requests_total_by_view_transport_method_total{method="GET",transport="http",view="upstream.api.views.ClaimViewSet"}`

#### `django_http_responses_total_by_status_view_method_total`
- **Type:** Counter
- **Labels:** `status`, `view`, `method`
- **Description:** Total count of HTTP responses grouped by status code, view, and method
- **Use Case:** Error rate monitoring (track 4xx and 5xx responses)
- **Example:** `django_http_responses_total_by_status_view_method_total{method="POST",status="400",view="upstream.api.views.ClaimViewSet"}`

#### `django_http_requests_latency_seconds_by_view_method`
- **Type:** Histogram
- **Labels:** `view`, `method`
- **Buckets:** [0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, +Inf]
- **Description:** Request latency distribution (time to process requests)
- **Use Case:** Performance monitoring, P95/P99 latency tracking
- **Example:** `histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))`

#### `django_http_requests_body_total_bytes`
- **Type:** Counter
- **Labels:** None
- **Description:** Total bytes received in HTTP request bodies
- **Use Case:** Network traffic monitoring

#### `django_http_responses_body_total_bytes`
- **Type:** Counter
- **Labels:** None
- **Description:** Total bytes sent in HTTP response bodies
- **Use Case:** Network bandwidth monitoring

### 2. Database Query Metrics (django-prometheus)

These metrics provide visibility into database operations:

#### `django_db_query_duration_seconds`
- **Type:** Histogram
- **Labels:** `vendor` (postgresql, sqlite, etc.)
- **Buckets:** [0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, +Inf]
- **Description:** Database query execution time distribution
- **Use Case:** Identify slow queries, optimize database performance
- **Example:** `histogram_quantile(0.99, rate(django_db_query_duration_seconds_bucket[10m]))`

#### `django_db_execute_total`
- **Type:** Counter
- **Labels:** `vendor`
- **Description:** Total number of database queries executed
- **Use Case:** Query volume tracking, N+1 query detection

#### `django_db_execute_many_total`
- **Type:** Counter
- **Labels:** `vendor`
- **Description:** Total number of bulk database operations (executemany)
- **Use Case:** Batch operation monitoring

### 3. Django Model Metrics (django-prometheus)

Track model-level operations:

#### `django_model_inserts_total`
- **Type:** Counter
- **Labels:** `model`
- **Description:** Total number of INSERT operations by model
- **Example:** `django_model_inserts_total{model="upstream.Claim"}`

#### `django_model_updates_total`
- **Type:** Counter
- **Labels:** `model`
- **Description:** Total number of UPDATE operations by model

#### `django_model_deletes_total`
- **Type:** Counter
- **Labels:** `model`
- **Description:** Total number of DELETE operations by model

### 4. Custom Business Metrics (upstream)

#### Alert Metrics

##### `upstream_alert_created_total`
- **Type:** Counter
- **Labels:** `product`, `severity`, `customer_id`
- **Description:** Total number of alert events created
- **Products:** `DriftWatch`, `DelayGuard`, `DenialScope`
- **Severities:** `low`, `medium`, `high`, `critical`
- **Example:** `rate(upstream_alert_created_total{product="DriftWatch",severity="high"}[1h])`

##### `upstream_alert_delivered_total`
- **Type:** Counter
- **Labels:** `product`, `channel_type`, `customer_id`
- **Description:** Total number of alert notifications successfully delivered
- **Channels:** `email`, `slack`, `webhook`

##### `upstream_alert_failed_total`
- **Type:** Counter
- **Labels:** `product`, `channel_type`, `error_type`, `customer_id`
- **Description:** Total number of alert notification failures
- **Use Case:** Monitor alert delivery reliability

##### `upstream_alert_processing_seconds`
- **Type:** Histogram
- **Labels:** `product`
- **Buckets:** [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, +Inf]
- **Description:** Time spent processing and sending alerts
- **Use Case:** Alert latency monitoring

##### `upstream_alert_suppressed_total`
- **Type:** Counter
- **Labels:** `product`, `reason`, `customer_id`
- **Description:** Alerts suppressed due to cooldown or noise patterns
- **Reasons:** `cooldown`, `duplicate`, `noise_threshold`

#### Drift Detection Metrics

##### `upstream_drift_event_detected_total`
- **Type:** Counter
- **Labels:** `product`, `drift_type`, `severity_level`, `customer_id`
- **Description:** Total number of payer drift events detected
- **Drift Types:** `payment_delay`, `denial_rate`, `adjustment_pattern`, `code_mapping_change`
- **Severity Levels:** `low` (0.0-0.4), `medium` (0.4-0.7), `high` (0.7-1.0)

##### `upstream_drift_computation_seconds`
- **Type:** Histogram
- **Labels:** `product`
- **Buckets:** [1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, +Inf]
- **Description:** Time spent computing drift signals
- **Use Case:** Monitor drift detection job performance

##### `upstream_payment_delay_signal_total`
- **Type:** Counter
- **Labels:** `severity`, `customer_id`
- **Description:** Payment delay signals created (part of DelayGuard product)

##### `upstream_denial_signal_total`
- **Type:** Counter
- **Labels:** `signal_type`, `customer_id`
- **Description:** Denial pattern signals created (part of DenialScope product)

#### Data Quality Metrics

##### `upstream_data_quality_score`
- **Type:** Gauge
- **Labels:** `customer_id`, `metric_type`
- **Description:** Current data quality score (0.0-1.0)
- **Metric Types:** `completeness`, `accuracy`, `timeliness`, `consistency`
- **Use Case:** Real-time data quality monitoring
- **Example:** `upstream_data_quality_score{customer_id="123",metric_type="completeness"}`

##### `upstream_data_quality_check_failed_total`
- **Type:** Counter
- **Labels:** `check_type`, `severity`, `customer_id`
- **Description:** Failed data quality checks
- **Check Types:** `missing_required_field`, `invalid_format`, `out_of_range`, `referential_integrity`

##### `upstream_claim_records_ingested_total`
- **Type:** Counter
- **Labels:** `customer_id`, `status`
- **Description:** Total number of claim records ingested
- **Statuses:** `success`, `failed`, `partial`
- **Use Case:** Monitor ingestion throughput and success rate

##### `upstream_ingestion_processing_seconds`
- **Type:** Histogram
- **Labels:** `customer_id`
- **Buckets:** [0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, +Inf]
- **Description:** Time spent processing claim data ingestion batches

#### Background Job Metrics

##### `upstream_background_job_started_total`
- **Type:** Counter
- **Labels:** `job_type`, `customer_id`
- **Description:** Background jobs started (Celery tasks)
- **Job Types:** `drift_detection`, `report_generation`, `data_export`, `alert_processing`

##### `upstream_background_job_completed_total`
- **Type:** Counter
- **Labels:** `job_type`, `customer_id`
- **Description:** Background jobs completed successfully

##### `upstream_background_job_failed_total`
- **Type:** Counter
- **Labels:** `job_type`, `error_type`, `customer_id`
- **Description:** Background jobs that failed
- **Use Case:** Monitor Celery task reliability

##### `upstream_background_job_duration_seconds`
- **Type:** Histogram
- **Labels:** `job_type`
- **Buckets:** [1.0, 5.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0, +Inf]
- **Description:** Duration of background job execution
- **Use Case:** Track long-running jobs, identify performance issues

#### Report Generation Metrics

##### `upstream_report_generated_total`
- **Type:** Counter
- **Labels:** `report_type`, `customer_id`
- **Description:** Reports generated successfully
- **Report Types:** `drift_summary`, `payment_analysis`, `denial_analysis`, `quality_dashboard`

##### `upstream_report_generation_seconds`
- **Type:** Histogram
- **Labels:** `report_type`
- **Buckets:** [1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, +Inf]
- **Description:** Time spent generating reports

##### `upstream_report_generation_failed_total`
- **Type:** Counter
- **Labels:** `report_type`, `error_type`, `customer_id`
- **Description:** Report generation failures

#### API & Cache Metrics

##### `upstream_api_endpoint_calls_total`
- **Type:** Counter
- **Labels:** `endpoint`, `method`, `customer_id`
- **Description:** Custom tracking of specific API endpoints (supplementing django-prometheus)

##### `upstream_api_rate_limit_hit_total`
- **Type:** Counter
- **Labels:** `endpoint`, `throttle_class`, `customer_id`
- **Description:** API rate limit violations
- **Use Case:** Monitor API abuse, adjust rate limits

##### `upstream_cache_hit_total`
- **Type:** Counter
- **Labels:** `cache_key_prefix`
- **Description:** Redis cache hits

##### `upstream_cache_miss_total`
- **Type:** Counter
- **Labels:** `cache_key_prefix`
- **Description:** Redis cache misses
- **Use Case:** Cache effectiveness monitoring, hit rate calculation

### 5. Python & Process Metrics (prometheus_client)

Standard Python runtime metrics:

- `python_gc_objects_collected_total` - Garbage collection statistics
- `python_gc_collections_total` - GC invocation counts
- `process_virtual_memory_bytes` - Virtual memory usage
- `process_resident_memory_bytes` - RSS memory usage
- `process_cpu_seconds_total` - CPU time consumed
- `process_open_fds` - Open file descriptors
- `process_start_time_seconds` - Process start time (Unix timestamp)

## Example PromQL Queries

### Request Rate & Errors

```promql
# Overall request rate (requests per second)
rate(django_http_requests_total_by_method_total[5m])

# Request rate by endpoint
rate(django_http_requests_total_by_view_transport_method_total[5m])

# Error rate (5xx responses per second)
rate(django_http_responses_total_by_status_view_method_total{status=~"5.."}[5m])

# Error percentage
sum(rate(django_http_responses_total_by_status_view_method_total{status=~"5.."}[5m]))
/
sum(rate(django_http_responses_total_by_status_view_method_total[5m]))
* 100

# 4xx client error rate
rate(django_http_responses_total_by_status_view_method_total{status=~"4.."}[5m])
```

### Latency & Performance

```promql
# P50 (median) latency
histogram_quantile(0.50, rate(django_http_requests_latency_seconds_bucket[5m]))

# P95 latency (95th percentile)
histogram_quantile(0.95, rate(django_http_requests_latency_seconds_bucket[5m]))

# P99 latency (worst 1% of requests)
histogram_quantile(0.99, rate(django_http_requests_latency_seconds_bucket[5m]))

# Average request latency
rate(django_http_requests_latency_seconds_sum[5m])
/
rate(django_http_requests_latency_seconds_count[5m])

# Slow endpoint identification (P99 > 2s)
histogram_quantile(0.99,
  rate(django_http_requests_latency_seconds_bucket{view=~"upstream.*"}[5m])
) > 2
```

### Database Performance

```promql
# Database query rate
rate(django_db_execute_total[5m])

# P99 database query latency
histogram_quantile(0.99, rate(django_db_query_duration_seconds_bucket[10m]))

# Slow queries (P95 > 100ms)
histogram_quantile(0.95, rate(django_db_query_duration_seconds_bucket[10m])) > 0.1

# Average queries per request
rate(django_db_execute_total[5m])
/
rate(django_http_requests_total_by_method_total[5m])
```

### Alert Metrics

```promql
# Alert creation rate by severity
rate(upstream_alert_created_total[1h])

# High-severity alert rate
rate(upstream_alert_created_total{severity="high"}[1h])

# Alert delivery success rate
sum(rate(upstream_alert_delivered_total[1h]))
/
sum(rate(upstream_alert_created_total[1h]))
* 100

# Alert processing latency (P95)
histogram_quantile(0.95, rate(upstream_alert_processing_seconds_bucket[10m]))

# Failed alert deliveries by channel
rate(upstream_alert_failed_total[1h])
```

### Drift Detection

```promql
# Drift events per hour
rate(upstream_drift_event_detected_total[1h]) * 3600

# High-severity drift events
rate(upstream_drift_event_detected_total{severity_level="high"}[1h])

# Drift detection by type
sum by (drift_type) (rate(upstream_drift_event_detected_total[1h]))

# Drift computation time (P95)
histogram_quantile(0.95, rate(upstream_drift_computation_seconds_bucket[10m]))
```

### Data Quality

```promql
# Current data quality score (by customer)
upstream_data_quality_score

# Data quality trend (average over 24h)
avg_over_time(upstream_data_quality_score[24h])

# Ingestion throughput (records per second)
rate(upstream_claim_records_ingested_total[5m])

# Ingestion success rate
sum(rate(upstream_claim_records_ingested_total{status="success"}[5m]))
/
sum(rate(upstream_claim_records_ingested_total[5m]))
* 100

# Failed quality checks by type
sum by (check_type) (rate(upstream_data_quality_check_failed_total[1h]))
```

### Background Jobs (Celery)

```promql
# Job execution rate
rate(upstream_background_job_started_total[5m])

# Job success rate
sum(rate(upstream_background_job_completed_total[5m]))
/
sum(rate(upstream_background_job_started_total[5m]))
* 100

# Failed jobs by type
sum by (job_type) (rate(upstream_background_job_failed_total[1h]))

# Job duration (P95)
histogram_quantile(0.95, rate(upstream_background_job_duration_seconds_bucket[10m]))

# Long-running jobs (>30 minutes)
histogram_quantile(0.99, rate(upstream_background_job_duration_seconds_bucket[1h])) > 1800
```

### Cache Performance

```promql
# Cache hit rate
sum(rate(upstream_cache_hit_total[5m]))
/
sum(rate(upstream_cache_hit_total[5m]) + rate(upstream_cache_miss_total[5m]))
* 100

# Cache effectiveness by key prefix
sum by (cache_key_prefix) (
  rate(upstream_cache_hit_total[5m])
  /
  (rate(upstream_cache_hit_total[5m]) + rate(upstream_cache_miss_total[5m]))
)
```

### Resource Utilization

```promql
# Memory usage (MB)
process_resident_memory_bytes / 1024 / 1024

# CPU usage
rate(process_cpu_seconds_total[1m])

# Open file descriptors
process_open_fds

# File descriptor usage percentage
(process_open_fds / process_max_fds) * 100
```

## Alerting Rules

Example Prometheus alerting rules for critical conditions:

```yaml
groups:
  - name: upstream_api
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(django_http_responses_total_by_status_view_method_total{status=~"5.."}[5m]))
          /
          sum(rate(django_http_responses_total_by_status_view_method_total[5m]))
          * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(django_http_requests_latency_seconds_bucket[5m])
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "API latency is high"
          description: "P95 latency is {{ $value }}s (threshold: 2s)"

      # Database slow queries
      - alert: SlowDatabaseQueries
        expr: |
          histogram_quantile(0.95,
            rate(django_db_query_duration_seconds_bucket[10m])
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Database queries are slow"
          description: "P95 query duration is {{ $value }}s (threshold: 500ms)"

      # Alert delivery failures
      - alert: AlertDeliveryFailures
        expr: |
          sum(rate(upstream_alert_failed_total[5m])) > 0.1
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Alert delivery failures detected"
          description: "{{ $value }} alert delivery failures per second"

      # Data quality degradation
      - alert: DataQualityDegraded
        expr: |
          upstream_data_quality_score < 0.8
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Data quality score below threshold"
          description: "Quality score: {{ $value }} (threshold: 0.8)"

      # Background job failures
      - alert: BackgroundJobFailures
        expr: |
          sum(rate(upstream_background_job_failed_total[5m])) > 0.05
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Background job failures detected"
          description: "{{ $value }} job failures per second"

      # Memory usage high
      - alert: HighMemoryUsage
        expr: |
          process_resident_memory_bytes / 1024 / 1024 / 1024 > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Process using {{ $value }}GB of memory"
```

## Grafana Dashboard Recommendations

### Dashboard 1: API Overview
- Request rate (QPS)
- Error rate (5xx, 4xx)
- Latency percentiles (P50, P95, P99)
- Top endpoints by traffic
- Top endpoints by latency
- Top endpoints by errors

### Dashboard 2: Database Performance
- Query rate
- Query latency distribution
- Slow query identification
- Queries per request
- Connection pool usage
- Model operation rates (inserts/updates/deletes)

### Dashboard 3: Business Metrics
- Alert creation rate by product
- Alert delivery success rate
- Drift event detection rate
- Data quality scores
- Ingestion throughput
- Report generation rates

### Dashboard 4: Background Jobs
- Job execution rate by type
- Job success rate
- Job duration trends
- Failed job breakdown
- Queue depth (if using Celery monitoring)

### Dashboard 5: System Resources
- Memory usage trend
- CPU utilization
- File descriptor usage
- Garbage collection frequency
- Python interpreter metrics

## Instrumentation Code Examples

### Tracking Alert Creation

```python
from upstream.metrics import track_alert_created

# In alert creation logic
track_alert_created(
    product='DriftWatch',
    severity='high',
    customer_id=customer.id
)
```

### Tracking Drift Events

```python
from upstream.metrics import track_drift_event

# In drift detection logic
track_drift_event(
    product='DriftWatch',
    drift_type='payment_delay',
    severity=0.85,  # Will be categorized as 'high'
    customer_id=customer.id
)
```

### Tracking Data Quality

```python
from upstream.metrics import track_data_quality_score

# After data quality checks
track_data_quality_score(
    customer_id=customer.id,
    metric_type='completeness',
    score=0.94
)
```

### Timing Operations

```python
from upstream.metrics import alert_processing_time

# Time alert processing
with alert_processing_time.labels(product='DriftWatch').time():
    process_and_send_alert(alert)
```

### Tracking Ingestion

```python
from upstream.metrics import track_ingestion

# After claim data ingestion
track_ingestion(
    customer_id=customer.id,
    record_count=1500,
    status='success'
)
```

## Production Deployment Checklist

- [ ] Prometheus server configured to scrape `/metrics` endpoint
- [ ] Firewall rules restrict `/metrics` access to Prometheus server only
- [ ] Alerting rules configured in Prometheus for critical conditions
- [ ] Grafana dashboards created for visualization
- [ ] Alert notification channels configured (PagerDuty, Slack, email)
- [ ] Metric retention policy configured (recommend 30+ days for trends)
- [ ] High-cardinality labels avoided (don't use unbounded dimensions like request ID)
- [ ] Custom business metrics instrumented in application code
- [ ] Monitoring infrastructure health checks validated

## Troubleshooting

### Metrics Endpoint Returns 404
- Verify `django_prometheus.urls` is included in `urlpatterns`
- Check that django-prometheus is in `INSTALLED_APPS`
- Ensure middleware is correctly configured

### Missing Custom Metrics
- Verify `upstream.metrics` module is importable
- Check that metrics are registered at module load time
- Ensure instrumentation code is being executed

### High Cardinality Warnings
- Avoid using unbounded labels (IDs, timestamps, email addresses)
- Use label values with known, limited set of values
- Consider aggregating high-cardinality data before exporting

### Metrics Endpoint Slow to Respond
- Reduce scrape frequency (increase `scrape_interval`)
- Use federation to reduce load on application servers
- Consider using prometheus-aggregator for high-traffic deployments

## Security Considerations

1. **Firewall Rules**: Restrict `/metrics` endpoint to Prometheus server IPs only
2. **No Authentication Required**: The endpoint is public by design for Prometheus scraping
3. **PII/PHI Protection**: No personally identifiable information is exposed in metrics
4. **Customer Isolation**: Customer data is separated via `customer_id` labels only
5. **Rate Limiting**: Consider adding rate limiting if exposed to public networks

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [django-prometheus GitHub](https://github.com/korfuri/django-prometheus)
- [Prometheus Exposition Format](https://prometheus.io/docs/instrumenting/exposition_formats/)
- [PromQL Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/)

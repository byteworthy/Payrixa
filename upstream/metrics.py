"""
Custom Prometheus metrics for Upstream Healthcare Platform.

Provides business-level metrics for operational visibility:
- Alert creation and delivery rates
- Drift detection and signal generation
- Data quality scores
- Background job processing

Usage:
    from upstream.metrics import alert_created, drift_event_detected

    # Increment counter
    alert_created.labels(product='DriftWatch', severity='high').inc()

    # Set gauge value
    data_quality_score.labels(customer='Acme Corp').set(0.95)

    # Time operations
    with alert_processing_time.labels(product='DelayGuard').time():
        process_alert(...)

Related to DEVOPS-MEDIUM: Custom business metrics for operational visibility.
"""

from prometheus_client import Counter, Gauge, Histogram
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Alert Metrics
# =============================================================================

alert_created = Counter(
    "upstream_alert_created_total",
    "Total number of alert events created",
    ["product", "severity", "customer_id"],
)

alert_delivered = Counter(
    "upstream_alert_delivered_total",
    "Total number of alert notifications delivered",
    ["product", "channel_type", "customer_id"],
)

alert_failed = Counter(
    "upstream_alert_failed_total",
    "Total number of alert notification failures",
    ["product", "channel_type", "error_type", "customer_id"],
)

alert_processing_time = Histogram(
    "upstream_alert_processing_seconds",
    "Time spent processing and sending alerts",
    ["product"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

alert_suppressed = Counter(
    "upstream_alert_suppressed_total",
    "Total number of alerts suppressed due to cooldown or noise patterns",
    ["product", "reason", "customer_id"],
)

# =============================================================================
# Drift Detection Metrics
# =============================================================================

drift_event_detected = Counter(
    "upstream_drift_event_detected_total",
    "Total number of drift events detected",
    ["product", "drift_type", "severity_level", "customer_id"],
)

drift_computation_time = Histogram(
    "upstream_drift_computation_seconds",
    "Time spent computing drift signals",
    ["product"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

payment_delay_signal_created = Counter(
    "upstream_payment_delay_signal_total",
    "Total number of payment delay signals created",
    ["severity", "customer_id"],
)

denial_signal_created = Counter(
    "upstream_denial_signal_total",
    "Total number of denial signals created",
    ["signal_type", "customer_id"],
)

# =============================================================================
# Data Quality Metrics
# =============================================================================

data_quality_score = Gauge(
    "upstream_data_quality_score",
    "Current data quality score (0.0-1.0)",
    ["customer_id", "metric_type"],
)

data_quality_check_failed = Counter(
    "upstream_data_quality_check_failed_total",
    "Total number of failed data quality checks",
    ["check_type", "severity", "customer_id"],
)

claim_records_ingested = Counter(
    "upstream_claim_records_ingested_total",
    "Total number of claim records ingested",
    ["customer_id", "status"],
)

ingestion_processing_time = Histogram(
    "upstream_ingestion_processing_seconds",
    "Time spent processing ingestion batches",
    ["customer_id"],
    buckets=(0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# =============================================================================
# Background Job Metrics
# =============================================================================

background_job_started = Counter(
    "upstream_background_job_started_total",
    "Total number of background jobs started",
    ["job_type", "customer_id"],
)

background_job_completed = Counter(
    "upstream_background_job_completed_total",
    "Total number of background jobs completed successfully",
    ["job_type", "customer_id"],
)

background_job_failed = Counter(
    "upstream_background_job_failed_total",
    "Total number of background jobs that failed",
    ["job_type", "error_type", "customer_id"],
)

background_job_duration = Histogram(
    "upstream_background_job_duration_seconds",
    "Duration of background job execution",
    ["job_type"],
    buckets=(1.0, 5.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0),
)

# =============================================================================
# Report Generation Metrics
# =============================================================================

report_generated = Counter(
    "upstream_report_generated_total",
    "Total number of reports generated",
    ["report_type", "customer_id"],
)

report_generation_time = Histogram(
    "upstream_report_generation_seconds",
    "Time spent generating reports",
    ["report_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

report_generation_failed = Counter(
    "upstream_report_generation_failed_total",
    "Total number of report generation failures",
    ["report_type", "error_type", "customer_id"],
)

# =============================================================================
# API Metrics (Supplementing django-prometheus)
# =============================================================================

api_endpoint_custom_metric = Counter(
    "upstream_api_endpoint_calls_total",
    "Custom tracking of specific API endpoints",
    ["endpoint", "method", "customer_id"],
)

api_rate_limit_hit = Counter(
    "upstream_api_rate_limit_hit_total",
    "Number of times API rate limits were hit",
    ["endpoint", "throttle_class", "customer_id"],
)

# =============================================================================
# Cache Metrics
# =============================================================================

cache_hit = Counter(
    "upstream_cache_hit_total", "Total number of cache hits", ["cache_key_prefix"]
)

cache_miss = Counter(
    "upstream_cache_miss_total", "Total number of cache misses", ["cache_key_prefix"]
)

# =============================================================================
# Utility Functions
# =============================================================================


def track_alert_created(product: str, severity: str, customer_id: int):
    """
    Track alert creation event.

    Args:
        product: Product name (DriftWatch, DelayGuard, DenialScope)
        severity: Alert severity level
        customer_id: Customer ID
    """
    try:
        alert_created.labels(
            product=product, severity=severity, customer_id=str(customer_id)
        ).inc()
    except Exception as e:
        logger.warning(f"Failed to track alert_created metric: {e}")


def track_alert_delivered(product: str, channel_type: str, customer_id: int):
    """
    Track successful alert delivery.

    Args:
        product: Product name
        channel_type: Notification channel (email, slack, webhook)
        customer_id: Customer ID
    """
    try:
        alert_delivered.labels(
            product=product, channel_type=channel_type, customer_id=str(customer_id)
        ).inc()
    except Exception as e:
        logger.warning(f"Failed to track alert_delivered metric: {e}")


def track_drift_event(product: str, drift_type: str, severity: float, customer_id: int):
    """
    Track drift event detection.

    Args:
        product: Product name
        drift_type: Type of drift detected
        severity: Severity value (0.0-1.0)
        customer_id: Customer ID
    """
    try:
        # Categorize severity
        if severity >= 0.7:
            severity_level = "high"
        elif severity >= 0.4:
            severity_level = "medium"
        else:
            severity_level = "low"

        drift_event_detected.labels(
            product=product,
            drift_type=drift_type,
            severity_level=severity_level,
            customer_id=str(customer_id),
        ).inc()
    except Exception as e:
        logger.warning(f"Failed to track drift_event_detected metric: {e}")


def track_data_quality_score(customer_id: int, metric_type: str, score: float):
    """
    Set current data quality score.

    Args:
        customer_id: Customer ID
        metric_type: Type of quality metric (completeness, accuracy, timeliness)
        score: Quality score (0.0-1.0)
    """
    try:
        data_quality_score.labels(
            customer_id=str(customer_id), metric_type=metric_type
        ).set(score)
    except Exception as e:
        logger.warning(f"Failed to track data_quality_score metric: {e}")


def track_ingestion(customer_id: int, record_count: int, status: str = "success"):
    """
    Track claim record ingestion.

    Args:
        customer_id: Customer ID
        record_count: Number of records ingested
        status: Ingestion status (success, failed, partial)
    """
    try:
        claim_records_ingested.labels(customer_id=str(customer_id), status=status).inc(
            record_count
        )
    except Exception as e:
        logger.warning(f"Failed to track claim_records_ingested metric: {e}")

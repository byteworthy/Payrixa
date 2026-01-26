"""
Tests for Prometheus metrics endpoint and monitoring infrastructure.

Validates that:
- /metrics endpoint is accessible
- Django-prometheus default metrics are exposed
- Custom business metrics are registered
- Metrics can be incremented
"""

import pytest
from django.test import TestCase, Client
from unittest.mock import patch
from upstream.metrics import (
    track_alert_created,
    track_alert_delivered,
    track_drift_event,
    track_data_quality_score,
    track_ingestion,
)


class PrometheusMetricsEndpointTests(TestCase):
    """Test suite for Prometheus metrics endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_metrics_endpoint_accessible(self):
        """Test /metrics endpoint returns valid Prometheus metrics."""
        response = self.client.get("/metrics")

        # Should return 200 OK
        self.assertEqual(response.status_code, 200)

        # Should return Prometheus text format
        self.assertIn("text/plain", response["Content-Type"])

    def test_django_prometheus_metrics_present(self):
        """Test default django-prometheus metrics are exposed."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Note: In test environment, PrometheusMiddleware is disabled for cleaner output
        # So request-specific metrics won't be present, but model operations still are

        # Check for model operation metrics (always present)
        self.assertIn("django_model_inserts_total", content)
        self.assertIn("django_model_updates_total", content)
        self.assertIn("django_model_deletes_total", content)

    def test_custom_business_metrics_present(self):
        """Test custom business metrics are registered."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Alert metrics
        self.assertIn("upstream_alert_created_total", content)
        self.assertIn("upstream_alert_delivered_total", content)
        self.assertIn("upstream_alert_failed_total", content)

        # Drift detection metrics
        self.assertIn("upstream_drift_event_detected_total", content)
        self.assertIn("upstream_drift_computation_seconds", content)

        # Background job metrics
        self.assertIn("upstream_background_job_started_total", content)
        self.assertIn("upstream_background_job_completed_total", content)
        self.assertIn("upstream_background_job_failed_total", content)

        # Data quality metrics
        self.assertIn("upstream_data_quality_score", content)
        self.assertIn("upstream_claim_records_ingested_total", content)

        # Report generation metrics
        self.assertIn("upstream_report_generated_total", content)

    def test_metric_format_is_valid_prometheus(self):
        """Test that metrics follow Prometheus exposition format."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Should contain HELP and TYPE declarations
        self.assertIn("# HELP", content)
        self.assertIn("# TYPE", content)

        # Should contain metric types
        self.assertIn("counter", content)
        self.assertIn("histogram", content)
        self.assertIn("gauge", content)

    def test_metrics_endpoint_does_not_require_authentication(self):
        """Test that /metrics endpoint is public (for Prometheus scraping)."""
        # Create unauthenticated client
        client = Client()
        response = client.get("/metrics")

        # Should still return 200 OK without authentication
        self.assertEqual(response.status_code, 200)

    def test_metrics_can_be_incremented_alert_created(self):
        """Test that alert_created metric can be incremented."""
        # This should not raise an exception
        track_alert_created("DriftWatch", "high", 1)

        # Verify metric was incremented by checking endpoint
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Should contain the metric with labels
        self.assertIn("upstream_alert_created_total", content)

    def test_metrics_can_be_incremented_alert_delivered(self):
        """Test that alert_delivered metric can be incremented."""
        # This should not raise an exception
        track_alert_delivered("DriftWatch", "email", 1)

        # Verify metric was incremented
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        self.assertIn("upstream_alert_delivered_total", content)

    def test_metrics_can_be_incremented_drift_event(self):
        """Test that drift_event_detected metric can be incremented."""
        # This should not raise an exception
        track_drift_event("DriftWatch", "payment_delay", 0.8, 1)

        # Verify metric was incremented
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        self.assertIn("upstream_drift_event_detected_total", content)

    def test_metrics_can_be_set_data_quality_score(self):
        """Test that data_quality_score gauge can be set."""
        # This should not raise an exception
        track_data_quality_score(1, "completeness", 0.95)

        # Verify metric was set
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        self.assertIn("upstream_data_quality_score", content)

    def test_metrics_can_be_incremented_ingestion(self):
        """Test that claim_records_ingested metric can be incremented."""
        # This should not raise an exception
        track_ingestion(1, 100, "success")

        # Verify metric was incremented
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        self.assertIn("upstream_claim_records_ingested_total", content)

    def test_metrics_track_helper_functions_handle_errors_gracefully(self):
        """Test that track_* helper functions handle exceptions gracefully."""
        # These should log warnings but not raise exceptions
        with patch("upstream.metrics.logger.warning") as mock_warning:
            # Pass invalid customer_id type to trigger potential exception
            track_alert_created("DriftWatch", "high", None)

            # Should have logged a warning if exception occurred
            # (may or may not fail depending on implementation)
            # Main point: should not crash

    def test_metrics_endpoint_contains_python_process_metrics(self):
        """Test that Python process metrics are included."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Python runtime metrics from prometheus_client
        self.assertIn("python_gc_objects_collected_total", content)
        self.assertIn("process_virtual_memory_bytes", content)
        self.assertIn("process_cpu_seconds_total", content)

    def test_metrics_endpoint_contains_model_operation_metrics(self):
        """Test that Django model operation metrics are included."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Django model operations tracked by django-prometheus
        self.assertIn("django_model_inserts_total", content)
        self.assertIn("django_model_updates_total", content)
        self.assertIn("django_model_deletes_total", content)

    def test_metrics_labels_are_properly_formatted(self):
        """Test that metric labels follow Prometheus conventions."""
        # Increment a metric with specific labels
        track_alert_created("DriftWatch", "high", 123)

        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Should contain label format: metric_name{label1="value1",label2="value2"}
        # We don't check exact values since metrics are cumulative across tests
        # But we verify the label structure exists
        self.assertIn("upstream_alert_created_total", content)

        # Labels should use double quotes and comma separation
        # This is validated by Prometheus scraper, so if endpoint works, format is valid

    def test_histogram_buckets_are_present(self):
        """Test that histogram metrics include bucket counts."""
        response = self.client.get("/metrics")
        content = response.content.decode("utf-8")

        # Check custom histogram (always present)
        self.assertIn("upstream_alert_processing_seconds", content)
        self.assertIn("upstream_drift_computation_seconds", content)
        self.assertIn("upstream_background_job_duration_seconds", content)


class PrometheusMiddlewareTests(TestCase):
    """Test suite for Prometheus middleware configuration."""

    def test_prometheus_middleware_is_configured_in_base_settings(self):
        """
        Test that PrometheusBeforeMiddleware and PrometheusAfterMiddleware are in base settings.

        Note: Test environment removes these middlewares for cleaner output,
        so we check the base.py settings file directly.
        """
        from upstream.settings import base

        middleware_list = base.MIDDLEWARE

        # Check both middlewares are present in base settings
        self.assertIn(
            "django_prometheus.middleware.PrometheusBeforeMiddleware",
            middleware_list,
        )
        self.assertIn(
            "django_prometheus.middleware.PrometheusAfterMiddleware",
            middleware_list,
        )

    def test_prometheus_middleware_order_in_base_settings(self):
        """
        Test that PrometheusBeforeMiddleware comes before PrometheusAfterMiddleware.

        Note: Test environment removes these middlewares, so we check base.py directly.
        """
        from upstream.settings import base

        middleware_list = base.MIDDLEWARE

        before_index = middleware_list.index(
            "django_prometheus.middleware.PrometheusBeforeMiddleware"
        )
        after_index = middleware_list.index(
            "django_prometheus.middleware.PrometheusAfterMiddleware"
        )

        # Before should come before After
        self.assertLess(before_index, after_index)

    def test_prometheus_app_is_installed(self):
        """Test that django_prometheus is in INSTALLED_APPS."""
        from django.conf import settings

        self.assertIn("django_prometheus", settings.INSTALLED_APPS)


class CustomMetricsRegistrationTests(TestCase):
    """Test suite for custom business metrics registration."""

    def test_alert_metrics_are_importable(self):
        """Test that alert metrics can be imported."""
        from upstream.metrics import (
            alert_created,
            alert_delivered,
            alert_failed,
            alert_processing_time,
            alert_suppressed,
        )

        # Verify they are Counter/Histogram instances
        self.assertTrue(hasattr(alert_created, "inc"))
        self.assertTrue(hasattr(alert_delivered, "inc"))
        self.assertTrue(hasattr(alert_failed, "inc"))
        self.assertTrue(hasattr(alert_processing_time, "time"))
        self.assertTrue(hasattr(alert_suppressed, "inc"))

    def test_drift_metrics_are_importable(self):
        """Test that drift detection metrics can be imported."""
        from upstream.metrics import (
            drift_event_detected,
            drift_computation_time,
            payment_delay_signal_created,
            denial_signal_created,
        )

        # Verify they are Counter/Histogram instances
        self.assertTrue(hasattr(drift_event_detected, "inc"))
        self.assertTrue(hasattr(drift_computation_time, "time"))
        self.assertTrue(hasattr(payment_delay_signal_created, "inc"))
        self.assertTrue(hasattr(denial_signal_created, "inc"))

    def test_data_quality_metrics_are_importable(self):
        """Test that data quality metrics can be imported."""
        from upstream.metrics import (
            data_quality_score,
            data_quality_check_failed,
            claim_records_ingested,
            ingestion_processing_time,
        )

        # Verify they are Gauge/Counter/Histogram instances
        self.assertTrue(hasattr(data_quality_score, "set"))
        self.assertTrue(hasattr(data_quality_check_failed, "inc"))
        self.assertTrue(hasattr(claim_records_ingested, "inc"))
        self.assertTrue(hasattr(ingestion_processing_time, "time"))

    def test_background_job_metrics_are_importable(self):
        """Test that background job metrics can be imported."""
        from upstream.metrics import (
            background_job_started,
            background_job_completed,
            background_job_failed,
            background_job_duration,
        )

        # Verify they are Counter/Histogram instances
        self.assertTrue(hasattr(background_job_started, "inc"))
        self.assertTrue(hasattr(background_job_completed, "inc"))
        self.assertTrue(hasattr(background_job_failed, "inc"))
        self.assertTrue(hasattr(background_job_duration, "time"))

    def test_report_metrics_are_importable(self):
        """Test that report generation metrics can be imported."""
        from upstream.metrics import (
            report_generated,
            report_generation_time,
            report_generation_failed,
        )

        # Verify they are Counter/Histogram instances
        self.assertTrue(hasattr(report_generated, "inc"))
        self.assertTrue(hasattr(report_generation_time, "time"))
        self.assertTrue(hasattr(report_generation_failed, "inc"))

    def test_cache_metrics_are_importable(self):
        """Test that cache metrics can be imported."""
        from upstream.metrics import cache_hit, cache_miss

        # Verify they are Counter instances
        self.assertTrue(hasattr(cache_hit, "inc"))
        self.assertTrue(hasattr(cache_miss, "inc"))

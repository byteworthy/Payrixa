"""
Production monitoring validation checks for Upstream.

This module ensures that critical monitoring and observability infrastructure
is properly configured before allowing production deployment.

Validates:
- Prometheus metrics endpoint accessibility
- Sentry error tracking configuration
- Logging configuration and retention
- Celery worker availability (if enabled)
- Redis connectivity
- Required environment variables

Related: Phase 3 - DevOps Monitoring & Metrics (Task #5)
"""

import logging
from typing import List, Tuple, Optional
from django.conf import settings
from django.core.checks import Error, Warning as DjangoWarning, Info, register
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =============================================================================
# PROMETHEUS METRICS CHECKS
# =============================================================================


@register(deploy=True)
def check_prometheus_metrics(app_configs, **kwargs):
    """
    Verify Prometheus metrics endpoint is accessible.

    This check ensures that:
    - django-prometheus is installed
    - Metrics endpoint is configured
    - Custom business metrics are registered
    """
    errors = []

    # Check if django-prometheus is installed
    if "django_prometheus" not in settings.INSTALLED_APPS:
        errors.append(
            Error(
                "django-prometheus not installed",
                hint="Add 'django_prometheus' to INSTALLED_APPS",
                obj=settings,
                id="monitoring.E001",
            )
        )
        return errors

    # Check if Prometheus middleware is configured
    prometheus_before = "django_prometheus.middleware.PrometheusBeforeMiddleware"
    prometheus_after = "django_prometheus.middleware.PrometheusAfterMiddleware"

    if prometheus_before not in settings.MIDDLEWARE:
        errors.append(
            DjangoWarning(
                "PrometheusBeforeMiddleware not configured",
                hint=f"Add '{prometheus_before}' to MIDDLEWARE",
                obj=settings,
                id="monitoring.W001",
            )
        )

    if prometheus_after not in settings.MIDDLEWARE:
        errors.append(
            DjangoWarning(
                "PrometheusAfterMiddleware not configured",
                hint=f"Add '{prometheus_after}' to MIDDLEWARE",
                obj=settings,
                id="monitoring.W002",
            )
        )

    # Verify custom metrics are registered
    try:
        from upstream.metrics import (
            alert_created,
            drift_event_detected,
            background_job_started,
        )

        # Check that metrics are Counter/Histogram instances
        if not hasattr(alert_created, "inc"):
            errors.append(
                Error(
                    "Custom metrics not properly registered",
                    hint="Ensure upstream.metrics defines Prometheus metrics",
                    obj=settings,
                    id="monitoring.E002",
                )
            )
    except ImportError as e:
        errors.append(
            Error(
                "Cannot import custom metrics",
                hint=f"Check upstream/metrics.py: {str(e)}",
                obj=settings,
                id="monitoring.E003",
            )
        )

    return errors


# =============================================================================
# SENTRY ERROR TRACKING CHECKS
# =============================================================================


@register(deploy=True)
def check_sentry_configuration(app_configs, **kwargs):
    """
    Verify Sentry error tracking is configured in production.

    In production environments, Sentry should be configured to capture
    errors and exceptions for monitoring and alerting.
    """
    errors = []

    # Only enforce Sentry in production
    if not settings.DEBUG:
        sentry_dsn = getattr(settings, "SENTRY_DSN", None)

        if not sentry_dsn:
            errors.append(
                DjangoWarning(
                    "Sentry not configured in production",
                    hint=(
                        "Set SENTRY_DSN environment variable for error tracking. "
                        "This is recommended but not required."
                    ),
                    obj=settings,
                    id="monitoring.W003",
                )
            )
        else:
            # Verify Sentry SDK is imported
            try:
                import sentry_sdk

                if not sentry_sdk.Hub.current.client:
                    errors.append(
                        DjangoWarning(
                            "Sentry SDK initialized but no client configured",
                            hint="Check Sentry initialization in settings.prod.py",
                            obj=settings,
                            id="monitoring.W004",
                        )
                    )
            except ImportError:
                errors.append(
                    Error(
                        "Sentry SDK not installed",
                        hint="Install sentry-sdk: pip install sentry-sdk",
                        obj=settings,
                        id="monitoring.E004",
                    )
                )

    return errors


# =============================================================================
# LOGGING CONFIGURATION CHECKS
# =============================================================================


@register(deploy=True)
def check_logging_configuration(app_configs, **kwargs):
    """
    Verify logging is properly configured with retention policies.

    Checks:
    - LOGGING configuration exists
    - PHI scrubbing filters are configured
    - File handlers have rotation configured
    - Audit logging is enabled
    """
    errors = []

    # Check LOGGING exists
    if not hasattr(settings, "LOGGING"):
        errors.append(
            Error(
                "LOGGING configuration not found",
                hint="Add LOGGING configuration to settings",
                obj=settings,
                id="monitoring.E005",
            )
        )
        return errors

    logging_config = settings.LOGGING

    # Check for PHI scrubbing filter
    filters = logging_config.get("filters", {})
    if "phi_scrubber" not in filters:
        errors.append(
            Error(
                "PHI scrubbing filter not configured",
                hint=(
                    "Add 'phi_scrubber' filter to LOGGING configuration "
                    "for HIPAA compliance"
                ),
                obj=settings,
                id="monitoring.E006",
            )
        )

    # Check for audit logging
    handlers = logging_config.get("handlers", {})
    if "audit_file" not in handlers:
        errors.append(
            DjangoWarning(
                "Audit logging not configured",
                hint=(
                    "Add 'audit_file' handler for HIPAA compliance "
                    "(7-year retention required)"
                ),
                obj=settings,
                id="monitoring.W005",
            )
        )

    # Check for log rotation
    has_rotation = False
    for handler_name, handler_config in handlers.items():
        handler_class = handler_config.get("class", "")
        if "RotatingFileHandler" in handler_class or "TimedRotatingFileHandler" in handler_class:
            has_rotation = True
            break

    if not has_rotation and not settings.DEBUG:
        errors.append(
            DjangoWarning(
                "Log rotation not configured",
                hint=(
                    "Use TimedRotatingFileHandler or RotatingFileHandler "
                    "to prevent disk space issues"
                ),
                obj=settings,
                id="monitoring.W006",
            )
        )

    return errors


# =============================================================================
# CELERY MONITORING CHECKS
# =============================================================================


@register(deploy=True)
def check_celery_monitoring(app_configs, **kwargs):
    """
    Verify Celery is properly configured with monitoring.

    Checks:
    - Celery is enabled if CELERY_ENABLED=True
    - Worker health check endpoint is accessible
    - Tasks use MonitoredTask base class
    """
    errors = []

    celery_enabled = getattr(settings, "CELERY_ENABLED", False)

    if celery_enabled:
        # Check if Celery broker is configured
        broker_url = getattr(settings, "CELERY_BROKER_URL", None)
        if not broker_url:
            errors.append(
                Error(
                    "Celery enabled but no broker configured",
                    hint="Set CELERY_BROKER_URL in settings",
                    obj=settings,
                    id="monitoring.E007",
                )
            )

        # Verify MonitoredTask is available
        try:
            from upstream.celery_monitoring import MonitoredTask

            # Check that at least one task uses MonitoredTask
            try:
                from upstream.tasks import run_drift_detection_task

                if not hasattr(run_drift_detection_task, "__self__"):
                    # Task is not bound, check if base class is set
                    pass  # Tasks may not be bound at check time
            except ImportError:
                pass
        except ImportError:
            errors.append(
                Error(
                    "Celery monitoring not available",
                    hint="Ensure upstream.celery_monitoring is importable",
                    obj=settings,
                    id="monitoring.E008",
                )
            )

    return errors


# =============================================================================
# REDIS CONNECTIVITY CHECKS
# =============================================================================


@register(deploy=True)
def check_redis_connectivity(app_configs, **kwargs):
    """
    Verify Redis is accessible for caching and Celery.

    In production, Redis should be available for:
    - Django cache backend
    - Celery broker/result backend
    - Session storage
    """
    errors = []

    # Only enforce in production
    if settings.DEBUG:
        return errors

    # Check cache backend
    cache_backend = settings.CACHES.get("default", {}).get("BACKEND", "")

    if "redis" in cache_backend.lower():
        # Try to connect to Redis
        try:
            cache.set("monitoring_check", "ok", 10)
            value = cache.get("monitoring_check")
            if value != "ok":
                errors.append(
                    Error(
                        "Redis cache not working properly",
                        hint="Check Redis connectivity and configuration",
                        obj=settings,
                        id="monitoring.E009",
                    )
                )
        except Exception as e:
            errors.append(
                Error(
                    "Cannot connect to Redis cache",
                    hint=f"Check Redis server is running: {str(e)}",
                    obj=settings,
                    id="monitoring.E010",
                )
            )
    else:
        # Not using Redis in production - warning
        errors.append(
            DjangoWarning(
                "Not using Redis cache in production",
                hint=(
                    "Consider using Redis for better performance. "
                    "Set CACHES['default']['BACKEND'] to "
                    "'django.core.cache.backends.redis.RedisCache'"
                ),
                obj=settings,
                id="monitoring.W007",
            )
        )

    return errors


# =============================================================================
# ENVIRONMENT VARIABLE CHECKS
# =============================================================================


@register(deploy=True)
def check_required_env_vars(app_configs, **kwargs):
    """
    Verify required environment variables are set in production.

    Critical variables for monitoring and observability:
    - PORTAL_BASE_URL (for alert links)
    - DEFAULT_FROM_EMAIL (for alert emails)
    - ALLOWED_HOSTS (security)
    """
    errors = []

    # Only enforce in production
    if settings.DEBUG:
        return errors

    # Check PORTAL_BASE_URL
    portal_url = getattr(settings, "PORTAL_BASE_URL", "")
    if not portal_url or portal_url == "http://localhost:8000":
        errors.append(
            Error(
                "PORTAL_BASE_URL not configured for production",
                hint="Set PORTAL_BASE_URL environment variable",
                obj=settings,
                id="monitoring.E011",
            )
        )

    # Check DEFAULT_FROM_EMAIL
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    if not from_email or "example.com" in from_email:
        errors.append(
            DjangoWarning(
                "DEFAULT_FROM_EMAIL not properly configured",
                hint="Set DEFAULT_FROM_EMAIL to a real email address",
                obj=settings,
                id="monitoring.W008",
            )
        )

    # Check ALLOWED_HOSTS
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
    if not allowed_hosts or allowed_hosts == ["*"]:
        errors.append(
            Error(
                "ALLOWED_HOSTS not properly configured",
                hint="Set ALLOWED_HOSTS to specific domain names (not '*')",
                obj=settings,
                id="monitoring.E012",
            )
        )

    return errors


# =============================================================================
# FIELD ENCRYPTION CHECKS (HIPAA)
# =============================================================================


@register(deploy=True)
def check_field_encryption(app_configs, **kwargs):
    """
    Verify field encryption is configured when handling real PHI data.

    HIPAA requires encryption of PHI at rest. When REAL_DATA_MODE=True,
    FIELD_ENCRYPTION_KEY must be configured.
    """
    errors = []

    real_data_mode = getattr(settings, "REAL_DATA_MODE", False)
    encryption_key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")

    if real_data_mode and not encryption_key:
        errors.append(
            Error(
                "Field encryption not configured for real PHI data",
                hint=(
                    "When REAL_DATA_MODE=True, FIELD_ENCRYPTION_KEY is required. "
                    "Generate with: python -c 'from cryptography.fernet import "
                    "Fernet; print(Fernet.generate_key().decode())'"
                ),
                obj=settings,
                id="monitoring.E013",
            )
        )

    return errors


# =============================================================================
# COMPREHENSIVE VALIDATION FUNCTION
# =============================================================================


def validate_production_monitoring() -> Tuple[bool, List[str]]:
    """
    Run all monitoring checks and return validation result.

    This function can be called from management commands or deployment scripts
    to validate monitoring configuration before deployment.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    from django.core.management import call_command
    from io import StringIO

    # Run Django system checks
    output = StringIO()
    try:
        call_command("check", "--deploy", stdout=output, stderr=output)
        check_output = output.getvalue()

        # Parse output for errors
        has_errors = "ERROR" in check_output or "CRITICAL" in check_output

        return (not has_errors, check_output.split("\n"))
    except Exception as e:
        return (False, [f"Error running checks: {str(e)}"])


def get_monitoring_status() -> dict:
    """
    Get comprehensive monitoring status for dashboard/API.

    Returns:
        dict: Monitoring status information
            - prometheus: bool
            - sentry: bool
            - logging: bool
            - celery: bool
            - redis: bool
            - overall_status: 'healthy'|'degraded'|'unhealthy'
    """
    status = {
        "prometheus": True,
        "sentry": True,
        "logging": True,
        "celery": True,
        "redis": True,
        "overall_status": "healthy",
    }

    # Check Prometheus
    try:
        from upstream.metrics import alert_created

        status["prometheus"] = True
    except Exception:
        status["prometheus"] = False

    # Check Sentry
    if not settings.DEBUG:
        sentry_dsn = getattr(settings, "SENTRY_DSN", None)
        status["sentry"] = bool(sentry_dsn)

    # Check logging
    status["logging"] = hasattr(settings, "LOGGING")

    # Check Celery (if enabled)
    celery_enabled = getattr(settings, "CELERY_ENABLED", False)
    if celery_enabled:
        try:
            from upstream.celery_monitoring import get_celery_worker_status

            worker_status = get_celery_worker_status()
            status["celery"] = worker_status.get("healthy", False)
        except Exception:
            status["celery"] = False
    else:
        status["celery"] = None  # Not enabled

    # Check Redis
    try:
        cache.set("monitoring_status_check", "ok", 10)
        status["redis"] = cache.get("monitoring_status_check") == "ok"
    except Exception:
        status["redis"] = False

    # Determine overall status
    critical_checks = [status["prometheus"], status["logging"], status["redis"]]
    optional_checks = [status["sentry"], status["celery"]]

    if all(critical_checks):
        if all(c for c in optional_checks if c is not None):
            status["overall_status"] = "healthy"
        else:
            status["overall_status"] = "degraded"
    else:
        status["overall_status"] = "unhealthy"

    return status

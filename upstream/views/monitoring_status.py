"""
Monitoring status API endpoint for observability dashboard.

Provides comprehensive monitoring status for:
- Prometheus metrics
- Sentry error tracking
- Logging configuration
- Celery workers
- Redis connectivity

Related: Phase 3 - DevOps Monitoring & Metrics (Task #5)
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from upstream.monitoring_checks import get_monitoring_status


@require_http_methods(["GET"])
@csrf_exempt
def monitoring_status(request):
    """
    Get comprehensive monitoring status.

    GET /api/monitoring/status/

    Returns:
        200: Monitoring status (healthy or degraded)
        503: Monitoring is unhealthy

    Response:
        {
            "overall_status": "healthy|degraded|unhealthy",
            "prometheus": true,
            "sentry": true,
            "logging": true,
            "celery": true,
            "redis": true,
            "components": {
                "prometheus": {
                    "healthy": true,
                    "message": "Metrics are being collected"
                },
                "sentry": {
                    "healthy": true,
                    "message": "Error tracking is active"
                },
                ...
            }
        }
    """
    status = get_monitoring_status()

    # Add detailed component information
    components = {}

    # Prometheus
    if status["prometheus"]:
        components["prometheus"] = {
            "healthy": True,
            "message": "Metrics are being collected",
        }
    else:
        components["prometheus"] = {
            "healthy": False,
            "message": "Metrics not available - check django-prometheus configuration",
        }

    # Sentry
    if status["sentry"] is None:
        components["sentry"] = {
            "healthy": None,
            "message": "Not configured (development mode)",
        }
    elif status["sentry"]:
        components["sentry"] = {
            "healthy": True,
            "message": "Error tracking is active",
        }
    else:
        components["sentry"] = {
            "healthy": False,
            "message": "Sentry not configured - errors will not be tracked",
        }

    # Logging
    if status["logging"]:
        components["logging"] = {
            "healthy": True,
            "message": "Logging is configured with PHI scrubbing",
        }
    else:
        components["logging"] = {
            "healthy": False,
            "message": "Logging not configured",
        }

    # Celery
    if status["celery"] is None:
        components["celery"] = {
            "healthy": None,
            "message": "Not enabled (CELERY_ENABLED=False)",
        }
    elif status["celery"]:
        components["celery"] = {
            "healthy": True,
            "message": "Workers are running",
        }
    else:
        components["celery"] = {
            "healthy": False,
            "message": "Workers are not running - background tasks will fail",
        }

    # Redis
    if status["redis"]:
        components["redis"] = {
            "healthy": True,
            "message": "Cache and session storage working",
        }
    else:
        components["redis"] = {
            "healthy": False,
            "message": "Redis not available - cache and sessions will fail",
        }

    # Build response
    response = {
        "overall_status": status["overall_status"],
        "prometheus": status["prometheus"],
        "sentry": status["sentry"],
        "logging": status["logging"],
        "celery": status["celery"],
        "redis": status["redis"],
        "components": components,
    }

    # Determine HTTP status code
    if status["overall_status"] == "unhealthy":
        status_code = 503
    else:
        status_code = 200

    return JsonResponse(response, status=status_code)

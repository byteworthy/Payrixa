# Stack Research

**Domain:** Django Technical Debt Remediation - Transaction Isolation, API Improvements, Testing
**Researched:** 2026-01-26
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Django | 5.2.2 | Web framework | Already in use. Django 5.2 includes native support for psycopg3, improved constraint operations (AlterConstraint), and mature transaction isolation configuration. [Official Docs](https://docs.djangoproject.com/en/5.2/) |
| Django REST Framework | 3.15.0 | API framework | Already in use. Current stable version with mature pagination, filtering, and OpenAPI support. DRF 3.15+ has enhanced custom action support and improved serializer performance. [Official Docs](https://www.django-rest-framework.org/) |
| PostgreSQL | 15 | Database | Already in use. PostgreSQL 15 supports all four standard SQL isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable) with proven Django integration. [PostgreSQL 15 Docs](https://www.postgresql.org/docs/15/transaction-iso.html) |
| Python | 3.12.1 | Runtime | Already in use. Python 3.12 offers performance improvements and is fully compatible with Django 5.2 and all recommended libraries. |

### Database Transaction Management

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| psycopg2-binary | 2.9.9 | PostgreSQL adapter | Currently in use. **RECOMMENDED FOR HIPAA PRODUCTION**: Stable, battle-tested, and widely deployed. While psycopg3 is the future, psycopg2 remains fully supported in Django 5.2 and avoids migration risk. Zero-downtime requirement makes "if it's not broken" approach safer. [Django Forum Discussion](https://forum.djangoproject.com/t/is-psycopg2-still-supported-in-django-5-2/41032) |
| django.db.transaction | Built-in | Transaction control | Django's built-in transaction.atomic() decorator and context manager with isolation level support via IsolationLevel enum. Mature, well-documented, HIPAA-compliant. [Django 5.2 Transaction Docs](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) |

**Alternative to Consider for Future:**
- **psycopg3** (3.3.x): The next-generation PostgreSQL adapter with native async support, connection pooling, and modern Python features. Django 5.2 prioritizes psycopg3 when both are installed. However, for HIPAA production systems with zero-downtime requirements, defer migration until post-remediation phase. [Psycopg3 Migration Guide](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html)

### API Pagination & Filtering

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| djangorestframework | 3.15.0 | Built-in pagination | **PRIMARY**: DRF's PageNumberPagination, LimitOffsetPagination, and CursorPagination work on custom actions via manual paginator invocation. Use for all list endpoints. [DRF Pagination Docs](https://www.django-rest-framework.org/api-guide/pagination/) |
| django-filter | 25.2 | Advanced filtering | **REQUIRED**: Provides DjangoFilterBackend for complex field filtering and SearchFilter for text search. Current CalVer release supports Django 5.2 and 6.0. Essential for implementing filterset_fields and search_fields on custom actions. [PyPI django-filter 25.2](https://pypi.org/project/django-filter/) |

### OpenAPI Documentation

| Library | Version | Purpose | Why Recommended |
|---------|---------|---------|-----------------|
| drf-spectacular | 0.29.0 | OpenAPI 3 schema generation | **STRONGLY RECOMMENDED**: Already in requirements.txt. Industry standard for DRF OpenAPI 3.0 schemas in 2025. Superior to drf-yasg (OpenAPI 2.0 only, unmaintained). Excellent @extend_schema decorator support for custom actions. Native SwaggerUI and Redoc integration. [PyPI drf-spectacular 0.29.0](https://pypi.org/project/drf-spectacular/) |

**What NOT to Use:**
- **drf-yasg**: Only supports OpenAPI 2.0 (obsolete Swagger spec), unlikely to get OpenAPI 3.0 support. drf-spectacular is the community-recommended migration path. [drf-spectacular Migration Guide](https://drf-spectacular.readthedocs.io/en/latest/drf_yasg.html)

### Testing Framework

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| pytest | 8.3.3 | Test runner | Already in use. Industry standard for Python testing with superior fixture management and parametrization vs unittest. |
| pytest-django | 4.11.1 | Django integration | Already in use. Essential for Django-aware fixtures (django_db, transactional_db, settings). Latest version (April 2025) includes database reuse optimizations. [PyPI pytest-django 4.11.1](https://pypi.org/project/pytest-django/) |
| pytest-xdist | 3.8.0 | Parallel testing | **RECOMMENDED**: Distributes tests across multiple CPUs with -n auto flag. Each worker gets isolated test database (gw0, gw1, etc.). Critical for large test suites. Version 3.8.0 (July 2025) supports Python 3.9-3.13. [PyPI pytest-xdist](https://pypi.org/project/pytest-xdist/) |
| pytest-randomly | Latest | Test randomization | **RECOMMENDED**: Randomizes test order to detect hidden inter-test dependencies. Works seamlessly with pytest-xdist. Helps ensure transaction isolation is working correctly. [pytest-randomly on PyPI](https://pypi.org/project/pytest-randomly/) |
| pytest-cov | 6.0.0 | Coverage reporting | Already in use. Essential for tracking test coverage of transaction-critical code paths. |

### Webhook Integration Testing

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| responses | 0.25.8 | HTTP mocking | **PRIMARY CHOICE**: Mock HTTP requests without hitting real servers. Version 0.25.8 (Aug 2025) includes matchers for JSON/form bodies, query params, headers, and custom validators. Excellent for webhook payload validation. [PyPI responses 0.25.8](https://pypi.org/project/responses/) |
| vcrpy | Latest | HTTP cassettes | **ALTERNATIVE**: Records real HTTP interactions and replays them in subsequent runs. More realistic than responses but requires initial live call. Better for complex OAuth flows. [VCR.py on GitHub](https://github.com/kevin1024/vcrpy) |
| factory-boy | Latest | Test data generation | **RECOMMENDED**: DjangoModelFactory integration for creating test fixtures. Combines with Faker for realistic data. pytest-factoryboy adds fixture registration for cleaner tests. [factory_boy Docs](https://factoryboy.readthedocs.io/) |
| pytest-factoryboy | Latest | Factory fixtures | **COMPANION TO FACTORY-BOY**: Registers factories as pytest fixtures automatically, reducing boilerplate in webhook payload tests. [pytest-factoryboy on PyPI](https://pypi.org/project/pytest-factoryboy/) |

### Performance Testing

| Tool | Version | Purpose | Why Recommended |
|------|---------|---------|-----------------|
| locust | 2.43.1 | Load testing | Already in use. Version 2.43.1 (Jan 2026) is the latest stable release. Write load tests in plain Python using HttpUser class. Real-time web UI for monitoring. Supports distributed testing for simulating thousands of concurrent users against Django endpoints. **NOT A REPLACEMENT FOR pytest** - use for load/performance testing, not unit tests. [PyPI locust 2.43.1](https://pypi.org/project/locust/) |
| django-debug-toolbar | Latest | Development profiling | **RECOMMENDED FOR DEV**: SQL query analysis, template rendering, cache hits. Essential for identifying N+1 queries and transaction bottlenecks during development. |
| django-silk | Latest | Production profiling | **ALTERNATIVE**: Request profiling in production-like environments. More heavyweight than debug toolbar but captures real-world performance data. |

## Installation

```bash
# Transaction Management (already installed)
pip install psycopg2-binary~=2.9.9

# API Filtering & Documentation
pip install django-filter~=25.2
pip install drf-spectacular~=0.29.0

# Testing Framework Enhancements
pip install pytest-xdist~=3.8.0
pip install pytest-randomly

# Webhook Testing
pip install responses~=0.25.8
pip install factory-boy
pip install pytest-factoryboy

# Performance Testing (already installed)
pip install locust~=2.43.1

# Development Tools (optional)
pip install django-debug-toolbar
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| drf-spectacular | drf-yasg | **NEVER** - drf-yasg is OpenAPI 2.0 only and unmaintained. No valid use case in 2025. |
| responses | vcrpy | Use vcrpy when you need to test against actual third-party API responses (e.g., OAuth flows). responses is better for controlled webhook scenarios. |
| pytest-django | unittest | Only if you have a massive existing unittest test suite. pytest-django can run unittest-based tests, so migration is incremental. |
| psycopg2 | psycopg3 | Use psycopg3 for new greenfield projects starting in 2025. For production HIPAA systems, wait until after technical debt remediation to minimize migration risk. |
| locust | pytest-benchmark | Use pytest-benchmark for microbenchmarks of individual functions. locust is for full system load testing. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| drf-yasg | OpenAPI 2.0 only (obsolete). No OpenAPI 3.0 support planned. Community has migrated to drf-spectacular. | drf-spectacular |
| unique_together | Deprecated in favor of UniqueConstraint. Less functionality, no conditional constraints, no covering indexes. | models.UniqueConstraint in Meta.constraints |
| Django's TestCase.client | Less flexible than pytest fixtures. No parallel test support without complexity. | pytest-django with APIClient |
| Manual transaction.set_isolation_level() | Deprecated and removed in psycopg3. Non-portable across database backends. | IsolationLevel enum in DATABASES['OPTIONS']['isolation_level'] |
| ATOMIC_REQUESTS = True | Global transaction wrapping is inefficient at scale. Increases lock contention and transaction overhead on every view. Poor fit for HIPAA compliance auditing. | Explicit @transaction.atomic() decorators on views/functions that need transactions |

## Stack Patterns by Use Case

### Transaction Isolation for Drift Detection

**Pattern:**
```python
# settings.py
from django.db.backends.postgresql.psycopg_any import IsolationLevel

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'isolation_level': IsolationLevel.SERIALIZABLE,
        },
    }
}

# views.py
from django.db import transaction

@transaction.atomic
def detect_drift(request):
    # SERIALIZABLE isolation ensures consistent snapshot
    # Raises serialization error if concurrent modification detected
    pass
```

**Why:** PostgreSQL SERIALIZABLE isolation prevents phantom reads and write skew anomalies in concurrent drift detection. Django 5.2 uses IsolationLevel enum for type-safe configuration. Must handle serialization exceptions (HINT: retry logic with exponential backoff).

**Source:** [Django 5.2 Database Configuration](https://docs.djangoproject.com/en/5.2/ref/databases/)

### DRF Pagination on Custom Actions

**Pattern:**
```python
from rest_framework.decorators import action
from rest_framework.response import Response

class MyViewSet(viewsets.ModelViewSet):
    pagination_class = PageNumberPagination

    @action(detail=False, methods=['get'])
    def custom_list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        # Fallback if pagination disabled
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

**Why:** DRF's automatic pagination only works on list() methods. Custom actions require manual paginator invocation via self.paginate_queryset(). Always include fallback for non-paginated case.

**Source:** [DRF Pagination Documentation](https://www.django-rest-framework.org/api-guide/pagination/)

### SearchFilter + DjangoFilterBackend

**Pattern:**
```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'in_stock']  # Exact match filters
    search_fields = ['name', 'description']  # Full-text search
```

**Why:** DjangoFilterBackend provides exact-match filtering on specified fields. SearchFilter adds case-insensitive partial matching on search_fields. Both work together seamlessly and respect custom pagination on actions.

**Source:** [DRF Filtering Documentation](https://www.django-rest-framework.org/api-guide/filtering/)

### OpenAPI Documentation with drf-spectacular

**Pattern:**
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class MyViewSet(viewsets.ModelViewSet):
    @extend_schema(
        summary="Custom drift detection endpoint",
        description="Detects configuration drift with SERIALIZABLE isolation",
        parameters=[
            OpenApiParameter(name='severity', type=str, enum=['low', 'medium', 'high']),
        ],
        responses={200: DriftSerializer(many=True)},
    )
    @action(detail=False, methods=['get'])
    def detect_drift(self, request):
        pass
```

**Why:** @extend_schema decorator provides fine-grained control over OpenAPI schema generation. Essential for documenting custom actions, query parameters, and response formats. Auto-generates Swagger UI and Redoc documentation.

**Source:** [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)

### Webhook Testing with responses

**Pattern:**
```python
import responses
import pytest

@responses.activate
def test_webhook_success():
    responses.post(
        'https://external-service.com/webhook',
        json={'status': 'success'},
        status=200,
        match=[
            responses.matchers.json_params_matcher({'event': 'drift_detected'}),
            responses.matchers.header_matcher({'X-API-Key': 'secret'}),
        ]
    )

    result = send_drift_webhook({'event': 'drift_detected'})
    assert result['status'] == 'success'
```

**Why:** responses library mocks HTTP requests without network calls. Matchers validate webhook payload structure and headers. Version 0.25.8 includes comprehensive matcher library for body, params, and headers.

**Source:** [responses on PyPI](https://pypi.org/project/responses/)

### Performance Testing with locust

**Pattern:**
```python
from locust import HttpUser, task, between

class DriftDetectionUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def detect_drift(self):
        with self.client.get(
            "/api/v1/drift/detect/",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 409:  # Serialization error
                response.failure("Serialization conflict")
```

**Why:** locust simulates concurrent users to test SERIALIZABLE transaction behavior under load. Real-time web UI shows response times, throughput, and error rates. Distributed mode can simulate thousands of concurrent drift detection requests.

**Source:** [locust Documentation](https://locust.io/)

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Django 5.2.2 | Python 3.10-3.13 | Python 3.12 recommended for performance |
| djangorestframework 3.15.0 | Django 4.2-5.2 | Full Django 5.2 support confirmed |
| drf-spectacular 0.29.0 | Django 2.2-5.2, DRF 3.10.3+ | Production/Stable maturity |
| django-filter 25.2 | Django 5.2, 6.0 | CalVer versioning (YY.MINOR) |
| pytest-django 4.11.1 | Django 4.2-5.2, pytest 7.0+ | April 2025 release with database reuse improvements |
| pytest-xdist 3.8.0 | pytest 7.4.0+, Python 3.9-3.13 | July 2025 release |
| responses 0.25.8 | requests >= 2.30.0, Python 3.8+ | August 2025 release |
| locust 2.43.1 | Python 3.9+ | January 2026 release (latest stable) |
| psycopg2-binary 2.9.9 | PostgreSQL 9.6-16, Django 4.2-5.2 | Fully supported in Django 5.2, no migration needed |

**Critical Compatibility Note:**
- **Django 5.2 + PostgreSQL 15 + psycopg2 2.9.9**: This combination is production-proven and HIPAA-compliant. While Django 5.2 prioritizes psycopg3, psycopg2 remains fully supported and is safer for zero-downtime migration requirements.

## Configuration Recommendations

### Transaction Isolation Levels

**For Drift Detection (Concurrent Read/Write):**
```python
# settings.py
from django.db.backends.postgresql.psycopg_any import IsolationLevel

DATABASES = {
    'default': {
        'OPTIONS': {
            'isolation_level': IsolationLevel.SERIALIZABLE,
        }
    }
}
```

**Trade-offs:**
- **READ COMMITTED** (default): Best performance, lowest lock contention. Sufficient for most use cases. Allows phantom reads.
- **REPEATABLE READ**: Prevents non-repeatable reads, maintains consistent snapshot. Moderate performance impact.
- **SERIALIZABLE**: Strongest guarantees, prevents all anomalies. Highest performance impact, requires retry logic for serialization errors.

**Recommendation:** Start with READ COMMITTED (default) for general endpoints. Use SERIALIZABLE isolation selectively via per-view @transaction.atomic(isolation=IsolationLevel.SERIALIZABLE) for drift detection. Global SERIALIZABLE causes performance degradation.

**Source:** [PostgreSQL 15 Isolation Levels](https://www.postgresql.org/docs/15/transaction-iso.html)

### DRF Pagination Configuration

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

**Why:** PageNumberPagination is the most common pattern (page=1, page=2). PAGE_SIZE=100 balances payload size vs. HTTP requests. DjangoFilterBackend + SearchFilter + OrderingFilter cover 95% of API filtering needs.

### drf-spectacular Configuration

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API',
    'DESCRIPTION': 'API for drift detection and HIPAA-compliant operations',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Don't expose /schema/ in production
    'COMPONENT_SPLIT_REQUEST': True,  # Separate request/response schemas
}

# urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

**Why:** COMPONENT_SPLIT_REQUEST generates cleaner schemas. SERVE_INCLUDE_SCHEMA=False prevents schema exposure in production (use env-based config).

### pytest Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = your_project.settings_test
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts =
    --reuse-db
    --nomigrations
    --cov=your_app
    --cov-report=html
    --cov-report=term-missing
    --randomly-seed=last
    -n auto
    --maxfail=5

markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    transaction: marks tests requiring SERIALIZABLE isolation
```

**Why:**
- `--reuse-db`: Speeds up test runs by reusing test database
- `--nomigrations`: Use --testsetup-database instead for faster initial setup
- `-n auto`: Parallel execution with pytest-xdist
- `--randomly-seed=last`: Reproducible random order (use same seed on failure)
- `--maxfail=5`: Fail fast if multiple tests break

## Sources

### HIGH Confidence (Official Documentation & Context7)

- [Django 5.2 Database Configuration](https://docs.djangoproject.com/en/5.2/ref/databases/) - Transaction isolation configuration
- [Django 5.2 Transaction Documentation](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) - transaction.atomic() usage
- [PostgreSQL 15 Transaction Isolation](https://www.postgresql.org/docs/15/transaction-iso.html) - Isolation level semantics
- [Django 5.2 Constraints Reference](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) - UniqueConstraint vs unique_together
- [Django REST Framework Pagination](https://www.django-rest-framework.org/api-guide/pagination/) - Custom action pagination
- [Django REST Framework Filtering](https://www.django-rest-framework.org/api-guide/filtering/) - DjangoFilterBackend and SearchFilter
- [drf-spectacular PyPI 0.29.0](https://pypi.org/project/drf-spectacular/) - Latest version verification
- [django-filter PyPI 25.2](https://pypi.org/project/django-filter/) - Version and Django 5.2 compatibility
- [pytest-django PyPI 4.11.1](https://pypi.org/project/pytest-django/) - Latest version and features
- [pytest-xdist PyPI 3.8.0](https://pypi.org/project/pytest-xdist/) - Parallel testing capabilities
- [responses PyPI 0.25.8](https://pypi.org/project/responses/) - HTTP mocking for webhooks
- [locust PyPI 2.43.1](https://pypi.org/project/locust/) - Performance testing

### MEDIUM Confidence (Community Consensus & Recent Articles)

- [drf-spectacular Migration from drf-yasg](https://drf-spectacular.readthedocs.io/en/latest/drf_yasg.html) - Migration path
- [Django Forum: psycopg2 vs psycopg3 in Django 5.2](https://forum.djangoproject.com/t/is-psycopg2-still-supported-in-django-5-2/41032) - Support status
- [Medium: Mastering API Versioning in DRF (2025)](https://medium.com/@anas-issath/mastering-api-versioning-in-django-rest-framework-drf-b9e5f365a5a2)
- [Medium: Database Isolation Levels in Django](https://medium.com/buserbrasil/database-isolation-levels-anomalies-and-how-to-handle-them-with-django-992889d233d5)
- [pytest-factoryboy Documentation](https://pytest-factoryboy.readthedocs.io/) - Factory fixture integration
- [factory_boy Documentation](https://factoryboy.readthedocs.io/) - DjangoModelFactory usage
- [VCR.py on GitHub](https://github.com/kevin1024/vcrpy) - HTTP cassette testing

### Testing & Load Testing Patterns

- [Comprehensive Guide to Testing Django REST APIs with Pytest](https://pytest-with-eric.com/pytest-advanced/pytest-django-restapi-testing/)
- [Django Tests Cheatsheet 2025](https://medium.com/@jonathan.hoffman91/django-tests-cheatsheet-2025-4fae3d32c3c5)
- [Locust Documentation](https://locust.io/) - Official load testing guide
- [BrowserStack: Python Performance Testing](https://www.browserstack.com/guide/python-performance-testing)

---

*Stack research for: Django Technical Debt Remediation*
*Researched: 2026-01-26*
*Confidence: HIGH (all versions verified with official sources as of January 2026)*

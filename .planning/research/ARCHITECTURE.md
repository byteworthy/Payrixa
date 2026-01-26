# Architecture Research

**Domain:** Django Database and API Patterns
**Researched:** 2026-01-26
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (DRF ViewSets)                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Filters │  │  Paging │  │ Ordering│  │ OpenAPI │        │
│  │ Backend │  │ Classes │  │ Filters │  │ Schema  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                  Service Layer (Business Logic)              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Transaction Management (@atomic)             │    │
│  │  - Isolation Level Control                           │    │
│  │  - select_for_update() for row locking               │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer (Django ORM)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ Models   │  │ Managers │  │ QuerySet │                   │
│  │ +Indexes │  │ +Tenant  │  │ +Locking │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
├─────────────────────────────────────────────────────────────┤
│                   PostgreSQL Database                        │
│  - Transaction Isolation (Read Committed default)            │
│  - Row-level locking (SELECT FOR UPDATE)                     │
│  - Database constraints (CHECK, UNIQUE, FK)                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **ViewSet** | HTTP request/response handling, pagination, filtering | DRF ModelViewSet with filter_backends, pagination_class |
| **Filter Backends** | Query parameter parsing and queryset filtering | SearchFilter, OrderingFilter, DjangoFilterBackend |
| **Pagination Classes** | Result set chunking and response formatting | PageNumberPagination with custom page_size |
| **Service Layer** | Business logic, transaction boundaries, concurrent access control | Python classes with @transaction.atomic methods |
| **Manager/QuerySet** | Data access patterns, tenant isolation | CustomerScopedManager with auto-filtering |
| **Models** | Data structure, validation, database schema | Django Model with db_index, constraints, CHECK constraints |
| **OpenAPI Schema** | API documentation generation | drf-spectacular with @extend_schema decorators |

## Recommended Project Structure

```
upstream/
├── api/                   # API layer
│   ├── views.py          # ViewSets with pagination/filtering
│   ├── serializers.py    # Data transformation + @extend_schema_field
│   ├── urls.py           # URL routing
│   ├── throttling.py     # Rate limiting
│   └── permissions.py    # Authorization
├── services/             # Business logic layer
│   ├── base_drift_detection.py  # Transaction management patterns
│   └── payer_drift.py    # Concrete service implementations
├── core/                 # Core infrastructure
│   ├── tenant.py         # Multi-tenant manager and middleware
│   └── validation_models.py  # Validation rules and quality metrics
├── models.py             # Data models with indexes and constraints
├── middleware.py         # Request processing (timing, metrics, tenant)
└── tests_*.py           # Test suites (unit, integration, API)
```

### Structure Rationale

- **api/**: Clean separation of HTTP concerns (serialization, throttling, permissions) from business logic
- **services/**: Transaction boundaries and business logic live here, not in views or models
- **core/**: Infrastructure patterns (tenant isolation, validation) that cut across features
- **models.py**: Single source of truth for data structure, with indexes and constraints close to schema
- **tests_*.py**: Co-located with implementation for discoverability

## Architectural Patterns

### Pattern 1: Transaction Isolation for Concurrent Aggregations

**What:** Use database transactions with explicit isolation levels and row locking to prevent race conditions during aggregate computations (e.g., drift detection that reads recent data and computes statistics).

**When to use:**
- Computing aggregates from recent data that may be modified concurrently
- Detecting drift/anomalies where consistency across multiple queries matters
- Preventing "phantom reads" where new rows appear mid-computation

**Trade-offs:**
- ✅ Guarantees consistency across multiple queries in a computation
- ✅ Prevents lost updates and race conditions
- ❌ Increases transaction duration (hold locks longer)
- ❌ Can cause deadlocks if not designed carefully
- ❌ Reduces concurrency (other transactions may wait)

**Example:**
```python
from django.db import transaction

class BaseDriftDetectionService:
    def compute(self):
        # Default isolation level: READ COMMITTED
        with transaction.atomic():
            # Step 1: Lock relevant rows to prevent concurrent modifications
            baseline_data = (
                ClaimRecord.objects
                .filter(customer=self.customer, date__gte=baseline_start)
                .select_for_update()  # SELECT ... FOR UPDATE (row lock)
            )

            # Step 2: Compute aggregates (no phantom reads)
            aggregates = self._compute_aggregates(baseline_data)

            # Step 3: Detect signals based on consistent snapshot
            signals = self._detect_signals(aggregates)

            # All operations see consistent data
            # Locks released at transaction commit

# For higher isolation when needed:
from django.db import transaction
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE

# Option 1: Using django-pgtransaction (third-party)
from pgtransaction import transaction as pg_transaction

@pg_transaction(isolation_level=pg_transaction.SERIALIZABLE)
def critical_computation():
    # Strongest isolation - prevents all anomalies
    pass

# Option 2: Manual isolation level setting (settings.py)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
        }
    }
}
```

### Pattern 2: Pagination on Custom ViewSet Actions

**What:** Apply DRF's pagination to custom @action methods (not just list/retrieve) by manually invoking pagination methods.

**When to use:**
- Custom endpoints that return large querysets (e.g., /uploads/{id}/statistics/)
- Actions that aggregate or filter data in non-standard ways
- Maintaining consistent pagination format across all list endpoints

**Trade-offs:**
- ✅ Consistent pagination across all endpoints (standard DRF response format)
- ✅ Prevents loading entire querysets into memory
- ✅ Client can control page size with ?page=N&page_size=M
- ❌ Requires manual pagination in each custom action
- ❌ Adds boilerplate (paginate_queryset + get_paginated_response)

**Example:**
```python
from rest_framework.decorators import action
from rest_framework.response import Response

class UploadViewSet(CustomerFilterMixin, viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    pagination_class = PageNumberPagination  # Default: 50 items/page

    @action(detail=False, methods=['get'])
    def recent_with_errors(self, request):
        """Custom action: Recent uploads with errors (paginated)."""
        queryset = (
            Upload.objects
            .filter(status='failed')
            .order_by('-uploaded_at')
        )

        # Manual pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback if pagination disabled
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def claim_records(self, request, pk=None):
        """Paginated list of claims for a specific upload."""
        upload = self.get_object()
        queryset = upload.claim_records.all().order_by('claim_number')

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ClaimRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ClaimRecordSerializer(queryset, many=True)
        return Response(serializer.data)
```

### Pattern 3: Search, Filter, and Ordering Backends

**What:** Use DRF's filter backend system to declaratively add search, filtering, and ordering to ViewSets without custom query parameter parsing.

**When to use:**
- Any list endpoint where users need to search text fields
- Filtering by specific field values (status, date ranges, foreign keys)
- Ordering results by different columns
- Standard CRUD APIs that follow REST conventions

**Trade-offs:**
- ✅ Zero boilerplate - just declare fields
- ✅ Automatic query parameter handling (?search=term&ordering=-date)
- ✅ Consistent API conventions across all endpoints
- ✅ DjangoFilterBackend supports complex filters (ranges, lookups)
- ❌ Limited to simple query patterns (not suitable for complex aggregations)
- ❌ Requires django-filter package for DjangoFilterBackend

**Example:**
```python
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

class ClaimRecordViewSet(CustomerFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ClaimRecord.objects.all()
    serializer_class = ClaimRecordSerializer

    # Enable all three filter backends
    filter_backends = [
        DjangoFilterBackend,  # Field-based filtering
        filters.SearchFilter,  # Full-text search
        filters.OrderingFilter,  # Column ordering
    ]

    # Search across multiple text fields
    search_fields = ['claim_number', 'payer_name', 'cpt_code']
    # Example: GET /api/claims/?search=Aetna

    # Exact filtering by specific fields
    filterset_fields = ['status', 'payer_name', 'service_date']
    # Example: GET /api/claims/?status=denied&payer_name=Aetna

    # Allow ordering by these fields
    ordering_fields = ['service_date', 'billed_amount', 'created_at']
    ordering = ['-service_date']  # Default ordering
    # Example: GET /api/claims/?ordering=-billed_amount,service_date

# Advanced filtering with django-filter
from django_filters import rest_framework as filters

class ClaimRecordFilter(filters.FilterSet):
    """Custom filter for complex queries."""
    min_amount = filters.NumberFilter(field_name='billed_amount', lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name='billed_amount', lookup_expr='lte')
    date_after = filters.DateFilter(field_name='service_date', lookup_expr='gte')
    date_before = filters.DateFilter(field_name='service_date', lookup_expr='lte')

    class Meta:
        model = ClaimRecord
        fields = ['status', 'payer_name']

class ClaimRecordViewSet(CustomerFilterMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ClaimRecord.objects.all()
    serializer_class = ClaimRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ClaimRecordFilter  # Use custom filter
    search_fields = ['claim_number']
    # Example: GET /api/claims/?min_amount=1000&max_amount=5000&date_after=2024-01-01
```

### Pattern 4: OpenAPI Schema Generation with drf-spectacular

**What:** Use `@extend_schema` decorator to generate accurate, complete OpenAPI documentation for custom actions, including request/response schemas, parameters, and examples.

**When to use:**
- Custom @action methods that need documentation
- Complex request/response structures (nested serializers, polymorphic responses)
- Adding query parameters not captured by serializers
- Providing examples for client code generation

**Trade-offs:**
- ✅ Auto-generates interactive API documentation (Swagger UI, ReDoc)
- ✅ Enables client SDK generation (TypeScript, Python, etc.)
- ✅ Validates that documentation matches implementation
- ✅ Explicit schema control for edge cases
- ❌ Requires decorating all custom actions (boilerplate)
- ❌ Schema generation can be slow for large APIs

**Example:**
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

class UploadViewSet(CustomerFilterMixin, viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer

    @extend_schema(
        summary="Get upload statistics",
        description="Returns aggregate statistics for uploads within a date range.",
        parameters=[
            OpenApiParameter(
                name='start_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter start date (YYYY-MM-DD)',
                required=False,
                examples=[
                    OpenApiExample('Recent', value='2024-01-01'),
                ],
            ),
            OpenApiParameter(
                name='end_date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Filter end date (YYYY-MM-DD)',
                required=False,
            ),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'total_uploads': {'type': 'integer'},
                    'success_count': {'type': 'integer'},
                    'failed_count': {'type': 'integer'},
                    'avg_processing_time': {'type': 'number'},
                },
            },
        },
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get upload statistics (documented with @extend_schema)."""
        # Implementation...
        return Response({
            'total_uploads': 150,
            'success_count': 140,
            'failed_count': 10,
            'avg_processing_time': 12.5,
        })

    @extend_schema(
        summary="List claims for a specific upload",
        description="Returns paginated list of claim records associated with this upload.",
        responses={200: ClaimRecordSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def claim_records(self, request, pk=None):
        """List claims (schema automatically includes pagination)."""
        upload = self.get_object()
        queryset = upload.claim_records.all()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ClaimRecordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ClaimRecordSerializer(queryset, many=True)
        return Response(serializer.data)

# Customize serializer fields for OpenAPI
from drf_spectacular.utils import extend_schema_field

class UploadSerializer(serializers.ModelSerializer):
    processing_time = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_processing_time(self, obj):
        """Calculate processing time in seconds (documented for OpenAPI)."""
        if obj.processing_completed_at and obj.processing_started_at:
            delta = obj.processing_completed_at - obj.processing_started_at
            return delta.total_seconds()
        return None

    class Meta:
        model = Upload
        fields = ['id', 'filename', 'status', 'processing_time']
```

## Data Flow

### Request Flow (API with Pagination and Filtering)

```
Client Request: GET /api/v1/uploads/?status=failed&ordering=-uploaded_at&page=2
    ↓
[DRF ViewSet] → filter_backends process query params
    ↓ (1. DjangoFilterBackend: status=failed)
    ↓ (2. OrderingFilter: ordering=-uploaded_at)
    ↓ (3. paginate_queryset: page=2, page_size=50)
[CustomerScopedManager] → auto-apply tenant filter
    ↓
[PostgreSQL Query]
    SELECT * FROM uploads
    WHERE customer_id = 123
      AND status = 'failed'
    ORDER BY uploaded_at DESC
    LIMIT 50 OFFSET 50;  -- page 2
    ↓
[Serializer] → transform queryset to JSON
    ↓
[Pagination Response] → wrap in {count, next, previous, results}
    ↓
Response: {
  "count": 150,
  "next": "...?page=3",
  "previous": "...?page=1",
  "results": [...]
}
```

### Transaction Flow (Service Layer with Isolation)

```
[API Endpoint] → calls service method
    ↓
[Service Layer]
    with transaction.atomic():  # BEGIN transaction (READ COMMITTED)
        ↓
        [select_for_update()] → SELECT ... FOR UPDATE (lock rows)
            ↓ (1. Acquire row locks)
            ↓ (2. Block concurrent updates)
        [Business Logic] → compute aggregates
            ↓ (3. Consistent snapshot - no phantom reads)
        [Create/Update Models] → INSERT/UPDATE
            ↓ (4. Changes visible within transaction)
        ↓
    # END transaction (COMMIT) → release locks
    ↓
[Publish Events] → notify other systems (outside transaction)
    ↓
[Return Result]
```

### Key Data Flows

1. **Tenant Isolation Flow:** Middleware sets current customer → Manager auto-filters queries → All data scoped to customer
2. **API Documentation Flow:** ViewSet defined → drf-spectacular introspects → OpenAPI schema generated → Swagger UI rendered
3. **Test Flow:** TestCase creates fixtures → API client makes request → Assert response status/data → Database rolled back

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-1k users** | Default settings work fine. Use READ COMMITTED isolation, basic pagination (50 items/page), no special optimization needed. |
| **1k-100k users** | Optimize queries: add indexes (done in Phase 3), use `select_related()` / `prefetch_related()` to prevent N+1 queries, enable query caching for expensive aggregations. Consider read replicas for reporting workload. |
| **100k+ users** | Split read/write workload: route reads to replicas, use connection pooling (PgBouncer in transaction mode), implement result caching (Redis), consider partitioning large tables by date/customer, monitor transaction lock contention. |

### Scaling Priorities

1. **First bottleneck:** N+1 queries from API endpoints → Fix with `select_related()` / `prefetch_related()` and add missing indexes
2. **Second bottleneck:** Long-running transactions causing lock contention → Reduce transaction scope, move expensive operations (like emailing) outside transactions, consider row-level locking with `select_for_update(nowait=True)` to fail fast
3. **Third bottleneck:** Database connection exhaustion → Add PgBouncer connection pooler (already configured in prod settings), tune `default_pool_size`

## Anti-Patterns

### Anti-Pattern 1: Transaction-per-Request for Read Operations

**What people do:** Wrap every API endpoint in `@transaction.atomic()` even for simple reads.

**Why it's wrong:**
- Holds database connections longer than necessary
- Increases connection pool pressure
- No benefit for read-only operations (Django's autocommit is fine)
- Can cause lock contention on high-traffic endpoints

**Do this instead:** Only use `@transaction.atomic()` for operations that span multiple writes or need consistency across multiple queries. Let Django's autocommit mode handle simple reads.

```python
# BAD: Unnecessary transaction for read
@transaction.atomic()
def list(self, request):
    uploads = Upload.objects.all()
    serializer = UploadSerializer(uploads, many=True)
    return Response(serializer.data)

# GOOD: Let Django handle autocommit
def list(self, request):
    uploads = Upload.objects.all()
    serializer = UploadSerializer(uploads, many=True)
    return Response(serializer.data)

# GOOD: Transaction only when needed
@transaction.atomic()
def complex_update(self, request):
    upload = Upload.objects.get(id=request.data['id'])
    upload.status = 'processing'
    upload.save()

    # Multiple writes need consistency
    for claim in upload.claim_records.all():
        claim.reprocess()
        claim.save()

    return Response({'status': 'ok'})
```

### Anti-Pattern 2: Forgetting Pagination on Custom Actions

**What people do:** Add custom `@action` methods that return querysets without calling `paginate_queryset()`, causing entire result set to load into memory.

**Why it's wrong:**
- Can return thousands of objects in a single response (memory exhaustion)
- Breaks client expectations (no pagination metadata)
- Inconsistent API behavior (some endpoints paginated, some not)
- Performance degrades as data grows

**Do this instead:** Always paginate custom actions that return collections. Use `self.paginate_queryset()` and `self.get_paginated_response()`.

```python
# BAD: No pagination on custom action
@action(detail=False, methods=['get'])
def recent_errors(self, request):
    uploads = Upload.objects.filter(status='failed')
    serializer = self.get_serializer(uploads, many=True)
    return Response(serializer.data)  # Could be 10,000+ objects!

# GOOD: Properly paginated custom action
@action(detail=False, methods=['get'])
def recent_errors(self, request):
    uploads = Upload.objects.filter(status='failed').order_by('-uploaded_at')

    # Apply pagination (respects ?page=N&page_size=M)
    page = self.paginate_queryset(uploads)
    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    # Fallback if pagination disabled
    serializer = self.get_serializer(uploads, many=True)
    return Response(serializer.data)
```

### Anti-Pattern 3: Using SERIALIZABLE Isolation by Default

**What people do:** Set `ISOLATION_LEVEL_SERIALIZABLE` globally or use it for all service methods to "be safe."

**Why it's wrong:**
- Massive performance impact (serializable causes more transaction retries)
- Increases deadlock likelihood
- Overkill for most operations (READ COMMITTED + select_for_update handles 95% of cases)
- Can cause unexpected transaction failures that need retry logic

**Do this instead:** Use READ COMMITTED (Django default) + `select_for_update()` for row locking. Only elevate to REPEATABLE READ or SERIALIZABLE for specific critical operations where you've verified it's necessary.

```python
# BAD: Global serializable isolation
DATABASES = {
    'default': {
        'OPTIONS': {
            'isolation_level': ISOLATION_LEVEL_SERIALIZABLE,  # Too strict!
        }
    }
}

# GOOD: Default READ COMMITTED, selective locking
class DriftDetectionService:
    @transaction.atomic()  # READ COMMITTED is fine
    def compute(self):
        # Lock only the rows we're updating
        baseline_data = (
            ClaimRecord.objects
            .filter(customer=self.customer, date__gte=start)
            .select_for_update()  # Row-level lock
        )

        aggregates = self._compute_aggregates(baseline_data)
        signals = self._detect_signals(aggregates)
        return signals

# ACCEPTABLE: SERIALIZABLE only for critical financial operations
from pgtransaction import transaction as pg_transaction

@pg_transaction(isolation_level=pg_transaction.SERIALIZABLE)
def process_payment_settlement():
    # Financial reconciliation that must be 100% consistent
    # Worth the performance cost
    pass
```

### Anti-Pattern 4: Missing @extend_schema on Custom Actions

**What people do:** Add custom `@action` methods without `@extend_schema` decorator, relying on automatic introspection.

**Why it's wrong:**
- OpenAPI schema missing query parameters
- Response structure not documented
- Clients can't generate accurate SDKs
- Manual API testing required (no Swagger UI for these endpoints)

**Do this instead:** Always decorate custom actions with `@extend_schema`, documenting parameters, responses, and examples.

```python
# BAD: No schema documentation
@action(detail=True, methods=['get'])
def export_claims(self, request, pk=None):
    upload = self.get_object()
    format = request.query_params.get('format', 'csv')
    # ...implementation
    return Response(data)

# GOOD: Complete schema documentation
@extend_schema(
    summary="Export claims to file",
    description="Export all claims for this upload in the specified format.",
    parameters=[
        OpenApiParameter(
            name='format',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Export format',
            enum=['csv', 'json', 'excel'],
            default='csv',
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'download_url': {'type': 'string'},
                'expires_at': {'type': 'string', 'format': 'date-time'},
            },
        },
    },
)
@action(detail=True, methods=['get'])
def export_claims(self, request, pk=None):
    upload = self.get_object()
    format = request.query_params.get('format', 'csv')
    # ...implementation
    return Response(data)
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| PostgreSQL | Django ORM with connection pooling (PgBouncer) | Use `transaction.atomic()` + `select_for_update()` for concurrency control |
| Redis | Django cache backend for query caching | Cache expensive aggregations, invalidate on data changes |
| Celery | Async task queue for background processing | Move expensive operations (email, reports) outside request cycle |
| OpenAPI/Swagger | drf-spectacular schema generation | Auto-generates from ViewSet introspection + `@extend_schema` |
| Monitoring | Django-Prometheus metrics export | Instrument custom metrics (drift computation time, API latency) |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| API ↔ Service | Direct method calls | ViewSets call service methods, pass customer from request.user |
| Service ↔ ORM | Django QuerySet API | Services use transaction.atomic() boundaries, never raw SQL |
| Middleware ↔ View | Request/response pipeline | Middleware sets tenant context, views inherit filtering |
| Tests ↔ API | Django TestClient or APIClient | Integration tests use client.post/get, assert response status/data |

## Testing Architecture

### Testing Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Integration Tests                         │
│  - Full request/response cycle (APIClient)                   │
│  - Tests pagination, filtering, ordering                     │
│  - Verifies tenant isolation                                 │
│  - Example: tests_api.py                                     │
├─────────────────────────────────────────────────────────────┤
│                      Service Tests                           │
│  - Transaction behavior                                      │
│  - Concurrent access patterns (select_for_update)            │
│  - Business logic correctness                                │
│  - Example: tests_celery.py, tests_tenant_isolation.py      │
├─────────────────────────────────────────────────────────────┤
│                       Unit Tests                             │
│  - Model validation                                          │
│  - Serializer transformation                                 │
│  - Utility functions                                         │
│  - Example: tests.py (model tests)                           │
└─────────────────────────────────────────────────────────────┘
```

### Test Patterns

**Integration Tests (API Endpoints):**
```python
class UploadViewSetTests(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name='Test Co')
        self.user = User.objects.create_user(username='test')
        UserProfile.objects.create(user=self.user, customer=self.customer)
        self.client.force_authenticate(user=self.user)

    def test_list_uploads_pagination(self):
        # Create 75 uploads
        for i in range(75):
            Upload.objects.create(customer=self.customer, filename=f'file{i}.csv')

        # Test first page
        response = self.client.get('/api/v1/uploads/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 50)  # PAGE_SIZE
        self.assertIsNotNone(response.data['next'])

        # Test second page
        response = self.client.get('/api/v1/uploads/?page=2')
        self.assertEqual(len(response.data['results']), 25)

    def test_search_filter_ordering(self):
        Upload.objects.create(customer=self.customer, filename='report.csv')
        Upload.objects.create(customer=self.customer, filename='data.csv')

        # Test search
        response = self.client.get('/api/v1/uploads/?search=report')
        self.assertEqual(len(response.data['results']), 1)

        # Test ordering
        response = self.client.get('/api/v1/uploads/?ordering=filename')
        self.assertEqual(response.data['results'][0]['filename'], 'data.csv')
```

**Transaction Isolation Tests:**
```python
from django.test import TransactionTestCase
from threading import Thread

class ConcurrencyTests(TransactionTestCase):
    def test_select_for_update_prevents_race_condition(self):
        upload = Upload.objects.create(customer=self.customer, status='processing')

        results = []

        def worker():
            with transaction.atomic():
                # Lock the row
                locked_upload = Upload.objects.select_for_update().get(id=upload.id)
                locked_upload.row_count = (locked_upload.row_count or 0) + 1
                locked_upload.save()
                results.append(locked_upload.row_count)

        # Run 10 concurrent updates
        threads = [Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should be sequential (1, 2, 3, ..., 10), not race conditions
        upload.refresh_from_db()
        self.assertEqual(upload.row_count, 10)
```

**Performance Tests:**
```python
import time

class PerformanceTests(APITestCase):
    def test_api_response_time_under_threshold(self):
        # Create realistic dataset
        for i in range(1000):
            Upload.objects.create(customer=self.customer, filename=f'file{i}.csv')

        start = time.time()
        response = self.client.get('/api/v1/uploads/?page=1')
        elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 0.5)  # < 500ms

    def test_n_plus_one_queries_prevented(self):
        # Create uploads with related data
        for i in range(50):
            upload = Upload.objects.create(customer=self.customer, filename=f'file{i}.csv')
            for j in range(10):
                ClaimRecord.objects.create(upload=upload, claim_number=f'{i}-{j}')

        with self.assertNumQueries(3):  # Expect: 1 upload query + 1 prefetch + 1 count
            response = self.client.get('/api/v1/uploads/')
```

## Build Order Implications

### Suggested Build Order (Dependencies)

**Phase 1: Transaction Isolation (Foundation)**
- Implement transaction boundaries in service layer
- Add `select_for_update()` to drift detection services
- Write concurrency tests to verify isolation
- **Why first:** Other features depend on correct concurrent access control

**Phase 2: Pagination on Custom Actions (API Enhancement)**
- Add `paginate_queryset()` to custom @action methods
- Test pagination with query params (?page=N)
- **Depends on:** Phase 1 (services need to return querysets, not full lists)

**Phase 3: Search/Filter/Ordering (API Enhancement)**
- Add `filter_backends` to ViewSets
- Define `search_fields`, `filterset_fields`, `ordering_fields`
- Test combinations (?search=X&status=Y&ordering=Z)
- **Depends on:** Phase 2 (pagination must work with filtering)

**Phase 4: OpenAPI Schema Generation (Documentation)**
- Add `@extend_schema` to custom actions
- Document query parameters, responses, examples
- Generate schema and test in Swagger UI
- **Depends on:** Phases 2-3 (document what exists)

**Phase 5: Integration and Performance Tests (Quality Assurance)**
- Write tests for pagination + filtering combinations
- Test transaction isolation under load (TransactionTestCase)
- Benchmark API response times
- **Depends on:** All previous phases (tests validate completed features)

### Dependency Diagram

```
Phase 1: Transaction Isolation
    ↓
Phase 2: Pagination (uses querysets from services)
    ↓
Phase 3: Filtering (applies before pagination)
    ↓
Phase 4: OpenAPI Schema (documents phases 2-3)
    ↓
Phase 5: Tests (validates all phases)
```

## Sources

**Transaction Isolation & Concurrency:**
- [Database transactions | Django documentation](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)
- [Exploring Database Isolation Levels in PostgreSQL and Django ORM](https://joseph-fox.co.uk/tech/understanding-postgresql-isolation-levels)
- [Django and Isolation | The Startup](https://medium.com/swlh/django-and-isolation-40d28f469aa)
- [Managing concurrency in Django using select_for_update](https://www.sankalpjonna.com/learn-django/managing-concurrency-in-django-using-select-for-update)
- [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [GitHub - django-pgtransaction](https://github.com/Opus10/django-pgtransaction)

**DRF Pagination:**
- [Pagination - Django REST framework](https://www.django-rest-framework.org/api-guide/pagination/)
- [Viewsets - Django REST framework](https://www.django-rest-framework.org/api-guide/viewsets/)
- [Pagination made easy with Django Rest Framework](https://www.sankalpjonna.com/learn-django/pagination-made-easy-with-django-rest-framework)

**DRF Filtering:**
- [Filtering - Django REST framework](https://www.django-rest-framework.org/api-guide/filtering/)
- [Filter data in Django Rest Framework - GeeksforGeeks](https://www.geeksforgeeks.org/python/filter-data-in-django-rest-framework/)
- [Implementing Search Functionality in Django Rest Framework](https://dev.to/theresa_okoro/implementing-search-functionality-in-django-rest-framework-drf-2fp0)

**OpenAPI Schema:**
- [GitHub - drf-spectacular](https://github.com/tfranzel/drf-spectacular)
- [drf-spectacular documentation](https://drf-spectacular.readthedocs.io/)
- [Schemas - Django REST framework](https://www.django-rest-framework.org/api-guide/schemas/)

**Testing:**
- [Writing and running tests | Django documentation](https://docs.djangoproject.com/en/6.0/topics/testing/overview/)
- [11 Tips for Lightning-Fast Tests in Django](https://gauravvjn.medium.com/11-tips-for-lightning-fast-tests-in-django-effa87383040)
- [A Guide to Performance Testing and Optimization With Python and Django](https://www.toptal.com/python/performance-optimization-testing-django)
- [Automating Performance Testing in Django](https://testdriven.io/blog/django-performance-testing/)

---
*Architecture research for: Django Database and API Patterns*
*Researched: 2026-01-26*

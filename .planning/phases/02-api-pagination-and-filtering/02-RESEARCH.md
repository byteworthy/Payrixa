# Phase 2: API Pagination & Filtering - Research

**Researched:** 2026-01-26
**Domain:** Django REST Framework pagination and filtering
**Confidence:** HIGH

## Summary

Django REST Framework 3.15 provides built-in pagination classes (PageNumberPagination, LimitOffsetPagination, CursorPagination) and filter backends (SearchFilter, OrderingFilter, DjangoFilterBackend). The project already has PageNumberPagination configured globally with PAGE_SIZE=50. The main task is to apply pagination to custom ViewSet actions (feedback, payer_summary, active, dashboard) and add search/filter capabilities to existing list endpoints.

The standard approach is:
1. Install django-filter 25.2 for DjangoFilterBackend (already supports Django 5.2)
2. Apply SearchFilter and DjangoFilterBackend to ViewSets via filter_backends
3. Define search_fields and filterset_fields on each ViewSet
4. For custom actions, call self.paginate_queryset() and self.get_paginated_response()
5. drf-spectacular automatically documents filters and pagination in OpenAPI schema

**Primary recommendation:** Use DjangoFilterBackend for complex filtering (status, severity, date ranges), SearchFilter for text search (claim numbers, payer names), and apply the standard paginate_queryset/get_paginated_response pattern to all custom actions.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| djangorestframework | 3.15.0 | REST API framework | Already installed; provides pagination, filters, ViewSets |
| django-filter | 25.2 | Advanced filtering | De facto standard for DRF filtering; supports Django 5.2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| drf-spectacular | 0.27.0 | OpenAPI schema generation | Already installed; auto-documents filters and pagination |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PageNumberPagination | CursorPagination | Cursor is better for very large datasets (millions+) but more complex; project has <100k claims per customer |
| DjangoFilterBackend | Hand-rolled filter logic | Custom logic is more work and lacks browsable API controls; DjangoFilterBackend is battle-tested |

**Installation:**
```bash
pip install django-filter~=25.2
```

## Architecture Patterns

### Recommended Project Structure
```
upstream/api/
├── views.py              # ViewSets with filter_backends and search_fields
├── filters.py            # Custom FilterSet classes (create if needed)
├── serializers.py        # Existing serializers
└── permissions.py        # Existing permissions
```

### Pattern 1: Apply Pagination to Custom Actions
**What:** Custom @action methods must manually call pagination methods
**When to use:** Any custom action that returns a list of items
**Example:**
```python
# Source: https://www.django-rest-framework.org/api-guide/pagination/
from rest_framework.decorators import action
from rest_framework.response import Response

@action(detail=False, methods=['get'])
def custom_list_action(self, request):
    queryset = self.filter_queryset(self.get_queryset())
    page = self.paginate_queryset(queryset)

    if page is not None:
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    serializer = self.get_serializer(queryset, many=True)
    return Response(serializer.data)
```

### Pattern 2: Add SearchFilter for Text Search
**What:** Use SearchFilter for simple text-based searches across multiple fields
**When to use:** When users need to search by text (payer names, claim numbers)
**Example:**
```python
# Source: https://www.django-rest-framework.org/api-guide/filtering/
from rest_framework import filters

class ClaimRecordViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['claim_number', 'payer', 'cpt_code']  # icontains by default
    # Use ^ prefix for startswith: search_fields = ['^claim_number']
    # Use = prefix for exact: search_fields = ['=payer']
    ordering_fields = ['decided_date', 'submitted_date']
```

### Pattern 3: Add DjangoFilterBackend for Complex Filtering
**What:** Use DjangoFilterBackend for field-level filtering with operators (gte, lte, in, range)
**When to use:** When users need to filter by specific field values or ranges
**Example:**
```python
# Source: https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html
from django_filters import rest_framework as filters

class ClaimRecordFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="allowed_amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="allowed_amount", lookup_expr='lte')
    start_date = filters.DateFilter(field_name="decided_date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="decided_date", lookup_expr='lte')

    class Meta:
        model = ClaimRecord
        fields = {
            'payer': ['exact', 'icontains'],
            'outcome': ['exact'],
            'status': ['exact'],
        }

class ClaimRecordViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [
        filters.DjangoFilterBackend,
        rest_framework_filters.SearchFilter,
        rest_framework_filters.OrderingFilter
    ]
    filterset_class = ClaimRecordFilter
```

### Pattern 4: Simple Filtering with filterset_fields
**What:** Quick filtering without creating a FilterSet class
**When to use:** Simple exact-match filtering on model fields
**Example:**
```python
# Source: https://www.django-rest-framework.org/api-guide/filtering/
from django_filters.rest_framework import DjangoFilterBackend

class DriftEventViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['payer', 'drift_type', 'severity']
    # Generates ?payer=Aetna&drift_type=DENIAL_RATE&severity=0.85
```

### Anti-Patterns to Avoid
- **Forgetting to check page is not None:** In custom actions, always check if pagination returned None (when pagination is disabled)
- **Using filterset_fields and filterset_class together:** These are mutually exclusive; use one or the other
- **Exposing all fields to filtering:** Only expose fields that are safe to filter on; avoid sensitive fields
- **Hand-rolling pagination logic:** Use self.paginate_queryset() and self.get_paginated_response() instead of custom logic
- **Not calling filter_queryset before paginating:** Always filter first, then paginate

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Paginated API responses | Custom page calculation, offset/limit logic | PageNumberPagination, self.paginate_queryset() | DRF handles edge cases (last page, invalid page numbers, empty querysets) |
| Filter query parameters | Manual request.query_params parsing | DjangoFilterBackend with filterset_fields | Handles type conversion, validation, multiple filters, browsable API controls |
| Text search across fields | Manual Q() object construction | SearchFilter with search_fields | Handles quoted phrases, multiple terms, related field lookups |
| Date range filtering | Custom date parsing and validation | DateFilter with gte/lte lookup_expr | Handles date format validation, timezone conversion, invalid dates |
| Enum/choice filtering | Manual string comparison | ChoiceFilter or filterset_fields | Validates choices, provides dropdown in browsable API |

**Key insight:** DRF and django-filter have solved edge cases like empty lists with __in lookups, invalid page numbers, malformed date strings, and SQL injection via filter parameters. Custom solutions miss these edge cases.

## Common Pitfalls

### Pitfall 1: Custom Actions Don't Automatically Paginate
**What goes wrong:** Custom @action methods return unpaginated results even when pagination_class is set on the ViewSet
**Why it happens:** DRF's automatic pagination only applies to list() and retrieve() methods, not custom actions
**How to avoid:** Manually call self.paginate_queryset() and self.get_paginated_response() in every custom action that returns a list
**Warning signs:** Custom action returns huge JSON payloads; frontend crashes on large datasets; API response time degrades with data growth

### Pitfall 2: Wrong Import for DjangoFilterBackend
**What goes wrong:** DjangoFilterBackend doesn't work; browsable API doesn't show filter controls
**Why it happens:** Importing from wrong package (rest_framework.filters vs django_filters.rest_framework)
**How to avoid:** Always import DjangoFilterBackend from django_filters.rest_framework, not rest_framework.filters
**Warning signs:** ImportError, filter_backends configured but filters not applied, missing filter UI in browsable API

### Pitfall 3: Forgetting to Add 'django_filters' to INSTALLED_APPS
**What goes wrong:** DjangoFilterBackend silently fails; no error but filters don't work
**Why it happens:** django-filter requires 'django_filters' in INSTALLED_APPS to register templates and extensions
**How to avoid:** Add 'django_filters' to INSTALLED_APPS after installing package
**Warning signs:** Filters work in shell but not in API; drf-spectacular doesn't document filters; no filter form in browsable API

### Pitfall 4: Using Default Lookup for Text Fields
**What goes wrong:** Search for "foo" doesn't find "foobar"; users complain search is too strict
**Why it happens:** Default lookup for CharField is exact, not icontains
**How to avoid:** For SearchFilter, omit prefix for icontains (default). For DjangoFilterBackend with filterset_fields, use Meta.fields dict: {'payer': ['exact', 'icontains']}
**Warning signs:** Users report search is "broken"; exact matches work but partial matches don't

### Pitfall 5: Exposing Sensitive Fields to Filtering
**What goes wrong:** Users can filter by fields that leak data (e.g., customer_id, internal status codes)
**Why it happens:** Using filterset_fields = '__all__' or not thinking about access control
**How to avoid:** Explicitly list filterable fields; never use '__all__'. Review each field for data leakage.
**Warning signs:** Security audit finds data leakage; users can enumerate other customers' data via filters

### Pitfall 6: Not Filtering Before Paginating
**What goes wrong:** Pagination returns wrong results; filter parameters ignored
**Why it happens:** Calling self.paginate_queryset(self.get_queryset()) instead of self.paginate_queryset(self.filter_queryset(self.get_queryset()))
**How to avoid:** Always call self.filter_queryset() before self.paginate_queryset()
**Warning signs:** Filters work on list() but not on custom actions; search parameter ignored in custom actions

### Pitfall 7: Empty List with __in Filter
**What goes wrong:** Filtering with ?status__in= (empty list) returns all results instead of empty queryset
**Why it happens:** django-filter doesn't treat empty list as "no results"; it treats it as "no filter"
**How to avoid:** Validate filter inputs; handle empty lists explicitly in custom FilterSet
**Warning signs:** Users report unexpected results when clearing multi-select filters

## Code Examples

Verified patterns from official sources:

### Basic ViewSet with Search and Filters
```python
# Source: https://www.django-rest-framework.org/api-guide/filtering/
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

class ClaimRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClaimRecord.objects.all()
    serializer_class = ClaimRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Simple filtering - exact match only
    filterset_fields = ['payer', 'outcome', 'status']

    # Text search - icontains by default
    search_fields = ['claim_number', 'payer']

    # Ordering control
    ordering_fields = ['decided_date', 'submitted_date', 'allowed_amount']
    ordering = ['-decided_date']  # default ordering
```

### Custom Action with Pagination
```python
# Source: https://www.django-rest-framework.org/api-guide/pagination/
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

class AlertEventViewSet(viewsets.ReadOnlyModelViewSet):

    @extend_schema(
        summary="Get operator feedback summary",
        responses={200: OperatorFeedbackSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def feedback(self, request):
        """Return all feedback with pagination."""
        queryset = OperatorJudgment.objects.filter(
            customer=get_user_customer(request.user)
        ).select_related('alert_event', 'operator')

        # Apply any filter backends
        queryset = self.filter_queryset(queryset)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = OperatorFeedbackSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Fallback if pagination is disabled
        serializer = OperatorFeedbackSerializer(queryset, many=True)
        return Response(serializer.data)
```

### Advanced FilterSet with Date Ranges
```python
# Source: https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html
from django_filters import rest_framework as filters
from django.db.models import Q

class DriftEventFilter(filters.FilterSet):
    # Custom filters for range queries
    min_severity = filters.NumberFilter(field_name='severity', lookup_expr='gte')
    max_severity = filters.NumberFilter(field_name='severity', lookup_expr='lte')

    # Date range filters
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')

    # Multiple lookup expressions for same field
    payer = filters.CharFilter(field_name='payer', lookup_expr='icontains')

    class Meta:
        model = DriftEvent
        fields = {
            'drift_type': ['exact'],  # Exact match only
            'status': ['exact', 'in'],  # Exact or multiple values
            'report_run': ['exact'],  # FK relationship
        }

class DriftEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DriftEvent.objects.all()
    serializer_class = DriftEventSerializer
    filter_backends = [filters.DjangoFilterBackend, rest_framework_filters.SearchFilter]
    filterset_class = DriftEventFilter
    search_fields = ['payer', 'cpt_code']
```

### SearchFilter with Field Prefixes
```python
# Source: https://www.django-rest-framework.org/api-guide/filtering/
from rest_framework import viewsets, filters

class UploadViewSet(viewsets.ModelViewSet):
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    # Field prefixes control search behavior:
    # ^ = istartswith (starts with)
    # = = iexact (exact match)
    # @ = search (PostgreSQL full-text search)
    # $ = iregex (regex match)
    # (no prefix) = icontains (contains substring, default)
    search_fields = [
        '^filename',  # Search filename from start
        'status',     # Search status by substring (icontains)
        'customer__name',  # Search related field
    ]

    ordering_fields = ['uploaded_at', 'row_count', 'status']
    ordering = ['-uploaded_at']
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual pagination in views | GenericAPIView.paginate_queryset() | DRF 3.0 (2014) | Standardized pagination across ViewSets |
| django-filter 1.x | django-filter 2.0+ | 2019 | Better DRF integration, cleaner imports |
| Hand-coded filter logic | DjangoFilterBackend | DRF 3.0 (2014) | Declarative filtering, browsable API support |
| Custom OpenAPI filter docs | drf-spectacular auto-detection | drf-spectacular 0.20+ | Filters auto-documented in schema |
| SearchFilter null-character bug | SearchFilter validates input | DRF 3.15 (2024) | Security fix for null-character injection |
| SearchFilter space-separated only | Quoted phrase support | DRF 3.15 (2024) | Better search UX with multi-word terms |

**Deprecated/outdated:**
- **drf-spectacular.contrib.django_filters.DjangoFilterBackend**: Removed after deprecation; use django_filters.rest_framework.DjangoFilterBackend instead
- **rest_framework.filters.DjangoFilterBackend**: Never existed; common mistake is trying to import from here

## Open Questions

Things that couldn't be fully resolved:

1. **Custom action pagination in drf-spectacular**
   - What we know: drf-spectacular auto-detects pagination on list/retrieve, but custom actions may need manual @extend_schema annotations
   - What's unclear: Whether pagination_class parameter on @action decorator is automatically reflected in OpenAPI schema
   - Recommendation: Test with drf-spectacular; add manual schema annotations if needed

2. **Performance impact of multiple filter backends**
   - What we know: Each filter backend in filter_backends list is applied in sequence
   - What's unclear: Whether combining DjangoFilterBackend + SearchFilter + OrderingFilter causes measurable overhead
   - Recommendation: Profile API response times before/after adding filters; customer data size (<100k claims) likely makes this negligible

3. **Cursor pagination for large datasets**
   - What we know: CursorPagination is recommended for very large datasets (millions+)
   - What's unclear: At what dataset size does switching from PageNumberPagination to CursorPagination become necessary
   - Recommendation: Stick with PageNumberPagination; current customer data size doesn't warrant cursor pagination complexity

## Sources

### Primary (HIGH confidence)
- [Django REST Framework Pagination Guide](https://www.django-rest-framework.org/api-guide/pagination/) - Official DRF docs, verified 2026-01-26
- [Django REST Framework Filtering Guide](https://www.django-rest-framework.org/api-guide/filtering/) - Official DRF docs, verified 2026-01-26
- [django-filter DRF Integration](https://django-filter.readthedocs.io/en/stable/guide/rest_framework.html) - Official django-filter docs, verified 2026-01-26
- [django-filter Installation Guide](https://django-filter.readthedocs.io/en/stable/guide/install.html) - Official installation docs, verified 2026-01-26

### Secondary (MEDIUM confidence)
- [DRF 3.15 Announcement](https://www.django-rest-framework.org/community/3.15-announcement/) - Official release notes for SearchFilter improvements
- [django-filter 25.2 Release](https://github.com/carltongibson/django-filter/releases) - Official GitHub releases showing Django 5.2 support
- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/en/latest/customization.html) - Official docs on filter backend documentation

### Tertiary (LOW confidence)
- [WebSearch: DRF pagination best practices 2026] - Community discussions on pagination patterns
- [WebSearch: django-filter common pitfalls 2026] - Community-reported issues with DjangoFilterBackend

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official DRF docs and django-filter docs verified; versions confirmed compatible
- Architecture: HIGH - Patterns verified from official DRF documentation and source code
- Pitfalls: HIGH - Common pitfalls verified from django-filter GitHub issues and official documentation

**Research date:** 2026-01-26
**Valid until:** 2026-02-26 (30 days - stable domain, slow-moving ecosystem)

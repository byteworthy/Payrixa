# Upstream Healthcare Platform - Agent Memory

This file captures codebase patterns, conventions, and gotchas discovered during development.

## Django REST Framework Patterns

### API Endpoint Structure

Standard pattern for creating REST endpoints:

1. **Model** (`models.py`) - Define data structure
2. **Serializer** (`serializers.py`) - Handle JSON <-> Model conversion
3. **ViewSet** (`views.py`) - Implement business logic
4. **Router** (`urls.py`) - Register endpoint

### Test Organization

Tests are organized by feature in separate files:
- `tests_api.py` - API endpoint tests
- `tests_<feature>.py` - Feature-specific tests
- Use fixtures from `test_fixtures.py`

### Quality Gates

Before committing, ensure these pass:
```bash
pytest                                    # Tests with 25% coverage minimum
python manage.py check                    # Django system check
python manage.py makemigrations --check   # No missing migrations
```

## Filtering and Pagination

This project uses:
- `django_filters.FilterSet` for complex filtering
- `rest_framework.filters.SearchFilter` for search
- Standard DRF pagination (PageNumberPagination)

Example:
```python
from django_filters import rest_framework as filters

class MyModelFilter(filters.FilterSet):
    class Meta:
        model = MyModel
        fields = ['field1', 'field2']

class MyViewSet(viewsets.ModelViewSet):
    filterset_class = MyModelFilter
    search_fields = ['name', 'description']
```

## Authentication & Permissions

- JWT authentication via `rest_framework_simplejwt`
- Always set permission classes on viewsets
- Default to `IsAuthenticated` for protected endpoints
- Use `AllowAny` only for public endpoints

## Migrations

- Always generate migrations: `python manage.py makemigrations`
- Review generated migrations before committing
- Migrations run sequentially - never skip or reorder
- Test migrations in isolation before committing

## Testing Best Practices

1. Use `APITestCase` for API endpoint tests
2. Leverage existing fixtures from `test_fixtures.py`
3. Test both success and error cases
4. Use `APIClient` for API requests
5. Assert status codes and response data structure

## Settings Organization

Multiple settings files:
- `settings/base.py` - Shared settings
- `settings/development.py` - Development overrides
- `settings/test.py` - Test environment settings

Never modify test settings unless explicitly required by the story.

## Discovered Patterns

(Ralph will append new patterns discovered during autonomous iterations)

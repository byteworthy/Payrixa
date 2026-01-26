# Feature Research: Django/DRF API Production Features

**Domain:** Django REST Framework Healthcare SaaS API (Phase 3 Technical Debt)
**Researched:** 2026-01-26
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or unprofessional.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Pagination on all list endpoints** | Industry standard for APIs with large datasets; prevents performance issues and timeouts | LOW | DRF has built-in `PageNumberPagination`, `LimitOffsetPagination`, `CursorPagination`. Custom actions currently lack pagination. |
| **Search and filtering** | Users need to find specific records without downloading everything; basic usability requirement | LOW-MEDIUM | `SearchFilter` and `DjangoFilterBackend` are standard DRF patterns. Missing on current ViewSets. |
| **Consistent error responses** | API consumers need predictable error formats to build robust clients; inconsistent errors = broken integrations | LOW | DRF has built-in exception handling, but customization needed for standardized format across all 4xx/5xx responses. |
| **OpenAPI/Swagger documentation** | Developers expect interactive docs to explore APIs; lack of docs = poor developer experience | LOW | `drf-spectacular` is installed but not fully configured. Missing endpoint descriptions, parameter docs. |
| **Basic transaction safety** | Data integrity in concurrent operations; race conditions = data corruption | MEDIUM | Django supports `transaction.atomic()` and `select_for_update()`. Currently missing for drift detection. |
| **Unique constraints on business logic** | Prevent duplicate data (e.g., same alert rule name per customer); duplicates = data quality issues | LOW | Django supports `UniqueConstraint` with multi-field combinations. Missing on several models. |
| **Rate limiting on expensive operations** | Prevent system overload from report generation, bulk uploads; missing = DDoS vulnerability | LOW | Already implemented with custom throttle classes. **Already complete.** |
| **Multi-tenant data isolation** | SaaS requirement; data leaks = HIPAA violation and breach of trust | MEDIUM | Already implemented with `CustomerScopedManager`. **Already complete.** |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued and drive competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Comprehensive test coverage (85%+)** | Demonstrates reliability and quality; reduces production bugs; enables confident refactoring | MEDIUM | Current: ~80%. Need webhook tests, performance tests, RBAC cross-role tests. |
| **Webhook delivery with retry logic** | Reliable integrations with exponential backoff; most competitors have flaky webhooks | MEDIUM | Tests needed for delivery, retry, signature verification. Implementation exists but lacks test coverage. |
| **Performance test suite** | Proactively identify bottlenecks before production; demonstrates scalability commitment | MEDIUM | Load testing key endpoints (dashboard, payer_summary, drift detection). |
| **Detailed API parameter validation** | Clear, helpful error messages guide developers; reduces support burden | LOW | Already good (date format validation in views.py). Can enhance with OpenAPI schema validation. |
| **Role-based access control (RBAC) testing** | Ensures security guarantees hold across user roles; prevents privilege escalation | MEDIUM | Need cross-role tests: superuser vs customer admin vs regular user. |
| **Cursor-based pagination** | Best for infinite scroll, real-time data feeds; better UX than page numbers for large datasets | LOW | Available in DRF but not configured. Consider for drift events feed. |
| **Query optimization with covering indexes** | 50-70% faster aggregate queries; demonstrates performance investment | MEDIUM | **Phase 3 Task #2 complete.** Competitive advantage achieved. |
| **Database-level data integrity** | CHECK constraints prevent invalid data at DB level; harder than app-level validation but more reliable | MEDIUM | **Phase 3 Task #3 complete.** 27 constraints across 7 models. Differentiator achieved. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems. Deliberately NOT building these.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **No pagination on custom actions** | "Just return everything, we'll filter client-side" | OOM errors with large result sets; slow response times; poor mobile experience | **Always paginate custom actions** like `feedback`, `active` endpoints. Use `self.paginate_queryset()`. |
| **GraphQL instead of REST** | "More flexible queries, avoid N+1" | Adds complexity; harder to cache; exposes full data model; performance unpredictable | **Stick with REST + optimize queries**. DRF has `select_related`/`prefetch_related` for N+1. |
| **Real-time everything (WebSockets)** | "Users want live updates" | Increases infrastructure complexity; hard to scale; most use cases work fine with polling | **Polling with cache** (current approach with 5-min dashboard cache is correct). |
| **Unfiltered SELECT FOR UPDATE** | "Lock all rows to prevent conflicts" | Database deadlocks; performance degradation; blocks concurrent reads unnecessarily | **Selective locking** with specific WHERE clauses. Only lock rows being modified. |
| **Custom pagination on every endpoint** | "Our frontend needs a different format" | Maintenance burden; inconsistent API; breaks tooling | **Use DRF standard pagination**. Clients can adapt to standard format. |
| **Automatic retry on ALL failed webhooks** | "Never lose a webhook" | Infinite retries on permanent failures; fills queue with poison messages | **Max 5 retries with exponential backoff**, then dead-letter queue. |
| **SERIALIZABLE isolation everywhere** | "Maximum consistency" | Performance penalty; high lock contention; not needed for most operations | **Use READ COMMITTED default**, SELECT FOR UPDATE for specific conflicts. |
| **Exposing all ORM filter lookups** | "Let users build any query" | Security risk; allows expensive queries; can leak data through timing attacks | **Whitelist specific filters** with `filterset_fields` or custom FilterSet. |

## Feature Dependencies

```
Database Optimization (Foundation)
    ├──> Transaction Isolation (DB-01)
    │       ├── Required for: Concurrent drift detection
    │       └── Enables: Safe multi-user report generation
    │
    └──> Unique Constraints (DB-02)
            ├── Required for: Data integrity guarantees
            └── Enables: Reliable RBAC testing

API Improvements (Build on DB Foundation)
    ├──> Pagination (API-01)
    │       ├── Depends on: Stable query patterns (from DB optimization)
    │       └── Enables: Performance testing with realistic data volumes
    │
    ├──> Search/Filter (API-02)
    │       ├── Depends on: Indexes (Phase 3 Tasks #1-3 complete)
    │       └── Enables: User-friendly data exploration
    │
    ├──> Error Standardization (API-03)
    │       ├── Independent: Can be done anytime
    │       └── Enhances: OpenAPI documentation quality
    │
    └──> OpenAPI Docs (API-04)
            ├── Depends on: Error standardization (for accurate responses)
            └── Enables: Better developer experience, client generation

Testing (Validates Everything)
    ├──> Webhook Tests (TEST-01)
    │       ├── Depends on: Error handling (API-03)
    │       └── Tests: Retry logic, signature verification, delivery
    │
    ├──> Performance Tests (TEST-02)
    │       ├── Depends on: Pagination (API-01), Filters (API-02)
    │       └── Validates: Query optimization gains
    │
    ├──> Rollback Test Fix (TEST-03)
    │       ├── Independent: Deployment workflow issue
    │       └── Critical for: Zero-downtime migrations
    │
    └──> RBAC Tests (TEST-04)
            ├── Depends on: Unique constraints (DB-02)
            └── Tests: Superuser, admin, regular user isolation
```

### Dependency Notes

- **DB-01 (Transaction Isolation) → API-01 (Pagination)**: Pagination queries must work correctly under concurrent access. Need transaction safety first.
- **DB-02 (Unique Constraints) → TEST-04 (RBAC Tests)**: RBAC tests require predictable data state. Unique constraints prevent test data conflicts.
- **API-01 (Pagination) → TEST-02 (Performance Tests)**: Can't load test endpoints that return unbounded result sets. Pagination must be implemented first.
- **API-03 (Error Standardization) → API-04 (OpenAPI Docs)**: OpenAPI schema should document standardized error format, not legacy DRF default.
- **TEST-01 (Webhook Tests) enhances API-03**: Webhook error handling is part of API error standardization.

## MVP Definition (Phase 3 Scope)

### Launch With (Phase 3 Complete)

Minimum features to call Phase 3 "done" and move to Phase 4.

- [x] **Database indexes** (Phase 3 Tasks #1-3) — Foundation for query performance
- [x] **Covering indexes** — 50-70% faster aggregates (competitive advantage)
- [x] **CHECK constraints** — Data integrity at DB level (27 constraints)
- [ ] **Transaction isolation (DB-01)** — Safe concurrent drift detection
- [ ] **Unique constraints (DB-02)** — Prevent duplicate business entities
- [ ] **Pagination on custom actions (API-01)** — Table stakes for production API
- [ ] **Search/filter capabilities (API-02)** — Basic usability requirement
- [ ] **Error response standardization (API-03)** — Predictable API client behavior
- [ ] **Complete OpenAPI docs (API-04)** — Developer experience baseline
- [ ] **Webhook tests (TEST-01)** — Validate integration reliability
- [ ] **Performance tests (TEST-02)** — Prove optimization gains
- [ ] **Fix rollback test (TEST-03)** — Zero-downtime deployment confidence
- [ ] **RBAC cross-role tests (TEST-04)** — Security guarantee validation

### Defer to Phase 4+ (Out of Scope)

Features explicitly deferred to maintain focus on technical debt.

- [ ] **Password reset flow** — Phase 4 polish item
- [ ] **HATEOAS links** — Phase 4 API enhancement
- [ ] **Structured logging** — Phase 4 observability improvement
- [ ] **GraphQL endpoint** — Anti-feature; not building
- [ ] **WebSocket real-time updates** — Anti-feature; polling sufficient
- [ ] **Cursor pagination** — Nice-to-have; page numbers sufficient for now
- [ ] **Advanced FilterSet classes** — Simple filtering sufficient for MVP
- [ ] **Request/response middleware logging** — Phase 4 observability

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Rationale |
|---------|------------|---------------------|----------|-----------|
| **DB-01: Transaction Isolation** | HIGH | MEDIUM | P1 | Race conditions = data corruption in production |
| **DB-02: Unique Constraints** | HIGH | LOW | P1 | Data integrity is foundation for testing |
| **API-01: Pagination** | HIGH | LOW | P1 | Missing on custom actions; OOM risk |
| **API-02: Search/Filter** | HIGH | MEDIUM | P1 | Table stakes for production API |
| **API-03: Error Standardization** | MEDIUM | LOW | P1 | Improves API-04 quality; low cost |
| **API-04: OpenAPI Docs** | MEDIUM | LOW | P1 | drf-spectacular installed; just needs config |
| **TEST-01: Webhook Tests** | HIGH | MEDIUM | P1 | Integration reliability is critical |
| **TEST-02: Performance Tests** | MEDIUM | MEDIUM | P2 | Validates optimization work; proves value |
| **TEST-03: Rollback Test** | HIGH | LOW | P1 | Blocks zero-downtime migrations |
| **TEST-04: RBAC Tests** | HIGH | MEDIUM | P2 | Security is critical, but auth already works |
| **Cursor pagination** | LOW | LOW | P3 | Nice-to-have; page numbers work fine |
| **Advanced filtering** | MEDIUM | MEDIUM | P3 | Simple filtering covers 80% of use cases |

**Priority key:**
- **P1: Must have for Phase 3 completion** — Blocks Phase 4 or creates production risk
- **P2: Should have, add when possible** — Valuable but not blocking
- **P3: Nice to have, future consideration** — Defer to Phase 4+

## Competitor Feature Analysis

| Feature | Typical SaaS API | Healthcare Compliance API | Upstream Current State | Gap Analysis |
|---------|------------------|---------------------------|------------------------|--------------|
| **Pagination** | ✅ Standard (page/offset) | ✅ Required for HIPAA audit logs | ⚠️ Partial (missing on custom actions) | **Need: API-01** |
| **Search/Filter** | ✅ Basic text search | ✅ Required for claim lookup | ⚠️ Manual query params only | **Need: API-02** |
| **Error Responses** | ⚠️ Often inconsistent | ✅ Standardized for compliance | ⚠️ DRF default (inconsistent) | **Need: API-03** |
| **OpenAPI Docs** | ✅ Standard (Swagger/Redoc) | ✅ Required for integration partners | ⚠️ Partial (drf-spectacular installed, not configured) | **Need: API-04** |
| **Rate Limiting** | ✅ Basic throttling | ✅ Required for API security | ✅ **Granular throttle classes** | ✅ **Competitive advantage** |
| **Transaction Safety** | ⚠️ Basic atomic() | ✅ SELECT FOR UPDATE required | ❌ Missing for drift detection | **Need: DB-01** |
| **Unique Constraints** | ✅ Database-level | ✅ Required for data integrity | ❌ App-level only | **Need: DB-02** |
| **Test Coverage** | ⚠️ 60-70% typical | ✅ 85%+ for compliance | ⚠️ 80% (missing webhook, perf, RBAC) | **Need: TEST-01,02,04** |
| **Webhook Reliability** | ⚠️ Best-effort delivery | ✅ Retries with audit trail | ⚠️ Implemented but untested | **Need: TEST-01** |
| **RBAC Testing** | ⚠️ Basic auth tests | ✅ Cross-role security tests | ⚠️ Basic tests, no cross-role | **Need: TEST-04** |
| **Performance Testing** | ❌ Rare in SaaS | ✅ Required for scale proof | ❌ No performance test suite | **Need: TEST-02** |
| **Zero-downtime Deploy** | ⚠️ Manual rollbacks | ✅ Automated rollback tests | ⚠️ Test disabled (broken) | **Need: TEST-03** |

**Legend:**
- ✅ **Implemented and working** — Meets or exceeds standard
- ⚠️ **Partial implementation** — Works but incomplete or not production-ready
- ❌ **Missing** — Not implemented; gap vs competitors

### Competitive Position

**Strengths (Table Stakes Already Met):**
- Rate limiting (granular throttle classes)
- Multi-tenant isolation (CustomerScopedManager)
- Database indexes (Phase 3 Tasks #1-3 complete)
- Covering indexes (50-70% performance gain)
- CHECK constraints (27 constraints across 7 models)

**Gaps (Table Stakes Missing):**
- Pagination on custom actions
- Search/filter capabilities
- Error standardization
- Complete OpenAPI docs
- Transaction isolation
- Unique constraints
- Webhook tests
- Performance tests
- RBAC cross-role tests

**Differentiators to Maintain:**
- Comprehensive test coverage (80% → 85% target)
- Query optimization (covering indexes)
- Database-level integrity (CHECK constraints)
- Granular rate limiting (report generation, bulk operations, read-only)

## Complexity Breakdown

### Low Complexity (1-2 days each)

- **DB-02**: Unique constraints — Add `UniqueConstraint` to models
- **API-01**: Pagination — Use `self.paginate_queryset()` in custom actions
- **API-03**: Error standardization — Custom exception handler or `drf-standardized-errors`
- **API-04**: OpenAPI docs — Configure `drf-spectacular` with `@extend_schema`
- **TEST-03**: Fix rollback test — Debug deployment workflow test

### Medium Complexity (3-5 days each)

- **DB-01**: Transaction isolation — Add `transaction.atomic()` + `select_for_update()`
- **API-02**: Search/Filter — Add `DjangoFilterBackend` + `SearchFilter` to ViewSets
- **TEST-01**: Webhook tests — Mock webhook delivery, test retry logic, signature verification
- **TEST-02**: Performance tests — Locust/pytest-benchmark for dashboard, payer_summary endpoints
- **TEST-04**: RBAC tests — Cross-role tests for superuser, customer admin, regular user

### High Complexity (Not in Phase 3 Scope)

- GraphQL endpoint (anti-feature, not building)
- Real-time WebSocket updates (anti-feature, not building)
- Advanced cursor pagination (deferred to Phase 4+)
- Structured logging with ELK stack (Phase 4 observability)

## Sources

### Official Documentation (HIGH Confidence)

- [DRF Pagination Guide](https://www.django-rest-framework.org/api-guide/pagination/)
- [DRF Filtering Guide](https://www.django-rest-framework.org/api-guide/filtering/)
- [DRF Exception Handling](https://www.django-rest-framework.org/api-guide/exceptions/)
- [Django Database Transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)
- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [django-filter DRF Integration](https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html)

### Best Practices & Patterns (MEDIUM Confidence)

- [DRF Testing Best Practices](https://www.django-rest-framework.org/api-guide/testing/)
- [Django Multi-Tenant Unique Constraints](https://medium.com/django-journal/building-a-multi-tenant-saas-in-django-complete-2026-architecture-e956e9f5086a)
- [DRF RBAC Implementation](https://www.permit.io/blog/how-to-implement-role-based-access-control-rbac-into-a-django-application)
- [Django Webhook Best Practices](https://dev.to/aakas/webhooks-in-django-a-comprehensive-guide-44jp)
- [Standardized Error Responses in DRF](https://rednafi.com/python/uniform-error-response-in-drf/)
- [Django Transaction Isolation Levels](https://joseph-fox.co.uk/tech/understanding-postgresql-isolation-levels)

### Community Articles (MEDIUM Confidence, 2023-2025)

- [DRF Performance Optimization](https://medium.com/@alirezazarei51/optimizing-performance-in-django-rest-framework-drf-c33e00a6fb0a)
- [Integration Testing with DRF](https://python.plainenglish.io/how-to-write-integration-tests-for-django-rest-framework-apis-b3627f35a75d)
- [DRF-Spectacular with Postman](https://medium.com/@anindya.lokeswara/efficient-api-development-in-django-rest-framework-drf-spectacular-and-postman-workspace-4dd6f860d14d)
- [Webhook Retry Patterns](https://www.svix.com/guides/receiving/receive-webhooks-with-python-django/)

---

*Feature research for Phase 3 Technical Debt Remediation*
*Researched: 2026-01-26*
*Confidence: HIGH (Django 5.2, DRF 3.x official docs + current codebase analysis)*

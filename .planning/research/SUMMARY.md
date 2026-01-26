# Project Research Summary

**Project:** Django Technical Debt Remediation - Phase 3 API & Database Improvements
**Domain:** Healthcare SaaS with HIPAA Compliance (Django/DRF)
**Researched:** 2026-01-26
**Confidence:** HIGH

## Executive Summary

This is a Phase 3 technical debt remediation project for a production Django REST Framework healthcare SaaS platform with HIPAA requirements and zero-downtime deployment constraints. The research reveals a well-architected system (existing covering indexes, CHECK constraints, and granular rate limiting) that needs critical fixes in three areas: transaction isolation for concurrent drift detection, API standardization (pagination/filtering/documentation), and comprehensive testing (webhooks, performance, RBAC).

The recommended approach prioritizes database-level correctness first (transaction isolation and unique constraints), then builds API improvements on that foundation, and validates everything through integration and performance testing. The existing Django 5.2 + PostgreSQL 15 + DRF 3.15 stack is production-proven and should not be changed. The critical risk is race conditions in drift detection causing duplicate alerts, which must be addressed with `select_for_update()` locking before scaling.

The roadmap must enforce multi-phase migrations for unique constraints (to maintain zero-downtime deployments) and include realistic load testing with Pareto-distributed data. Quality indicators already in place (covering indexes, CHECK constraints, multi-tenant isolation) demonstrate strong foundation; the focus should be on concurrency correctness and API completeness.

## Key Findings

### Recommended Stack

**Stay on existing stack** — Django 5.2.2, PostgreSQL 15, DRF 3.15, Python 3.12.1 are production-proven for HIPAA workloads and have excellent transaction isolation support. The research recommends keeping psycopg2 (2.9.9) rather than migrating to psycopg3 to minimize migration risk during technical debt remediation.

**Core technologies:**
- **Django 5.2.2**: Web framework — native support for transaction isolation via IsolationLevel enum, mature constraint operations
- **Django REST Framework 3.15.0**: API framework — built-in pagination, filtering, and OpenAPI support (already in use)
- **PostgreSQL 15**: Database — supports all four SQL isolation levels (Read Committed default is correct; SERIALIZABLE for specific cases only)
- **drf-spectacular 0.29.0**: OpenAPI 3 schema generation — already installed, industry standard, just needs configuration with @extend_schema decorators
- **django-filter 25.2**: Advanced filtering — required for DjangoFilterBackend on custom actions
- **pytest-xdist 3.8.0**: Parallel testing — distribute tests across multiple CPUs, essential for large test suites
- **responses 0.25.8**: HTTP mocking — mock webhook delivery without network calls, includes comprehensive matchers for validation
- **locust 2.43.1**: Load testing — already installed, simulate concurrent users to test transaction isolation under load

**What NOT to use:**
- **drf-yasg** — OpenAPI 2.0 only (obsolete), no OpenAPI 3.0 support
- **ATOMIC_REQUESTS = True** — global transaction wrapping is inefficient at scale, use explicit @transaction.atomic() decorators
- **SERIALIZABLE isolation everywhere** — massive performance impact, only use selectively for critical operations
- **psycopg3 migration now** — defer until post-remediation to minimize risk in HIPAA production

### Expected Features

**Must have (table stakes):**
- **Pagination on all list endpoints** — Currently missing on custom actions (OOM risk with large result sets)
- **Search and filtering** — Users need to find specific records (basic usability requirement)
- **OpenAPI/Swagger documentation** — drf-spectacular installed but not configured, missing endpoint descriptions
- **Transaction safety** — Race conditions in drift detection = data corruption (critical for concurrent access)
- **Unique constraints** — Prevent duplicate business entities at database level (data integrity requirement)

**Already complete (competitive advantages):**
- **Rate limiting** — Granular throttle classes (report generation, bulk operations, read-only)
- **Multi-tenant data isolation** — CustomerScopedManager with auto-filtering
- **Covering indexes** — 50-70% faster aggregate queries (Phase 3 Tasks #1-3 complete)
- **CHECK constraints** — 27 constraints across 7 models for database-level integrity

**Defer (v2+):**
- **GraphQL endpoint** — Anti-feature, adds complexity without benefit (REST + query optimization sufficient)
- **Real-time WebSockets** — Polling with 5-min cache is correct for this use case
- **Cursor pagination** — Page numbers work fine for MVP
- **HATEOAS links** — Phase 4 API enhancement

### Architecture Approach

**Three-layer architecture with explicit transaction boundaries:** API layer (ViewSets with filter backends and pagination) → Service layer (business logic with @transaction.atomic() boundaries) → Data layer (Django ORM with CustomerScopedManager and select_for_update() locking). Transaction isolation is handled at the service layer, not in views or models.

**Major components:**
1. **ViewSet (API Layer)** — HTTP request/response handling, pagination via self.paginate_queryset(), filtering via filter_backends (DjangoFilterBackend, SearchFilter), OpenAPI schema via @extend_schema decorators
2. **Service Layer** — Business logic with transaction.atomic() boundaries, select_for_update() for row locking, consistent lock ordering to prevent deadlocks (Customer → DriftEvent → AlertRule → AlertEvent)
3. **Manager/QuerySet (Data Layer)** — CustomerScopedManager auto-filters queries by tenant, querysets use select_related()/prefetch_related() to prevent N+1
4. **Filter Backends** — DjangoFilterBackend (exact-match field filtering), SearchFilter (text search), OrderingFilter (column sorting)
5. **Pagination Classes** — PageNumberPagination (standard page=1,2,3 pattern), manual invocation required on custom actions

**Key patterns:**
- **READ COMMITTED isolation (default) + select_for_update()** — Handles 95% of concurrency cases without SERIALIZABLE performance penalty
- **Multi-phase migrations** — Add nullable fields first, populate in code, make required later (zero-downtime requirement)
- **Manual pagination on custom actions** — DRF only auto-paginates list() methods, custom @action methods need self.paginate_queryset()
- **Consistent lock ordering** — Always lock by ascending primary key within model, lock models in defined order across codebase

### Critical Pitfalls

1. **Missing select_for_update() causes race conditions in drift detection** — Django's @transaction.atomic() provides rollback but NOT concurrency control. Two workers can both check for existing alerts and both create one (duplicate alerts). Must lock DriftEvent row with select_for_update() before check-then-create pattern. Establish consistent lock ordering (Customer → DriftEvent → AlertRule → AlertEvent) to prevent deadlocks.

2. **Backwards incompatible migrations break rolling deployments** — Adding unique constraints or dropping columns in single migration causes IntegrityError during deployment when old code is still running. MUST use 3-phase migrations: (1) Add nullable constraint + index CONCURRENTLY, (2) Deploy code that prevents violations, (3) Make constraint required. Use django-migration-linter in CI to detect breaking migrations.

3. **N+1 query explosion in paginated API endpoints** — Adding pagination without select_related()/prefetch_related() causes 1 query + N queries per result. For 100 alert events with related drift_events/alert_rules/customers, becomes 301 queries instead of 4. Must add assertNumQueries() tests to prevent regression.

4. **False sense of security from high test coverage without integration tests** — 85% coverage doesn't guarantee correct behavior when tests mock database/webhooks/Celery. Critical scenarios like "does transaction rollback cleanup alert state?" are never tested. Need 30% integration tests with real PostgreSQL, 10% E2E tests with real Celery tasks, not just mocked unit tests.

5. **Webhook retry without idempotency causes duplicate processing** — HTTP is not transactional. Webhook POST might succeed server-side but response lost in transit, causing retry. Recipient processes alert twice. MUST include X-Idempotency-Key header, track WebhookDeliveryAttempt records, only retry on 5xx (not 4xx), max 5 attempts with exponential backoff.

## Implications for Roadmap

Based on research, suggested phase structure follows dependency chain: database correctness → API improvements → testing validation.

### Phase 1: Transaction Isolation & Unique Constraints (DB Foundation)
**Rationale:** All other features depend on correct concurrent access control and data integrity. Race conditions in drift detection are critical bugs that corrupt production data. Must be fixed before scaling API usage.

**Delivers:**
- Transaction boundaries in service layer with @transaction.atomic()
- select_for_update() locking in drift detection (BaseDriftDetectionService, evaluate_drift_event)
- Unique constraints on business entities (customer+payer+cpt_group+drift_type, customer+alert_rule_name)
- Concurrency tests verifying no duplicates under parallel access

**Addresses:**
- DB-01: Transaction isolation for concurrent drift detection
- DB-02: Unique constraints to prevent duplicate business entities

**Avoids:**
- Pitfall #1: Race conditions from missing select_for_update()
- Pitfall #2: Backwards incompatible migrations (use 3-phase approach)
- Pitfall #3: Deadlocks (establish lock ordering conventions)

**Critical requirement:** Multi-phase migration strategy for unique constraints (3 deployments to maintain zero-downtime).

### Phase 2: API Pagination & Filtering (Usability Foundation)
**Rationale:** Pagination must work before adding filters (filters apply before pagination). Custom actions currently return unbounded result sets (OOM risk). Builds on Phase 1's stable query patterns.

**Delivers:**
- Pagination on custom actions via self.paginate_queryset() (feedback, dashboard, active endpoints)
- DjangoFilterBackend + SearchFilter on ViewSets
- Query optimization with select_related()/prefetch_related() to prevent N+1

**Addresses:**
- API-01: Add pagination to custom ViewSet actions
- API-02: Implement search/filter capabilities

**Avoids:**
- Pitfall #4: N+1 query explosion (add assertNumQueries() tests)

**Uses:** DRF's built-in PageNumberPagination, django-filter 25.2 for DjangoFilterBackend

### Phase 3: OpenAPI Documentation & Error Standardization (Developer Experience)
**Rationale:** Documents what exists from Phases 1-2. Error standardization improves OpenAPI schema quality. drf-spectacular already installed, just needs configuration.

**Delivers:**
- @extend_schema decorators on custom actions documenting parameters, responses, examples
- Standardized error response format (consistent 4xx/5xx structure)
- SwaggerUI and Redoc documentation generated from schema

**Addresses:**
- API-03: Error response standardization
- API-04: Complete OpenAPI documentation

**Uses:** drf-spectacular 0.29.0 with @extend_schema, OpenApiParameter for query params

### Phase 4: Webhook & RBAC Testing (Integration Quality)
**Rationale:** Validates reliability of existing webhook implementation and security guarantees. Depends on error handling from Phase 3.

**Delivers:**
- Webhook delivery tests (success, retry, signature verification, idempotency)
- RBAC cross-role tests (superuser, customer admin, regular user isolation)
- Integration tests with real database (not mocked)

**Addresses:**
- TEST-01: Webhook integration tests
- TEST-04: RBAC cross-role security tests

**Avoids:**
- Pitfall #5: Webhook retry without idempotency (test duplicate delivery scenario)
- Pitfall #6: False security from mocked tests (require real database integration tests)

**Uses:** responses 0.25.8 for HTTP mocking, pytest-django 4.11.1 with real test database

### Phase 5: Performance Testing & Rollback Fix (Production Readiness)
**Rationale:** Validates optimization gains from Phases 1-2. Load tests need pagination and filtering implemented first. Rollback test fix is standalone but critical for deployments.

**Delivers:**
- Load tests with Locust (dashboard, payer_summary, drift detection endpoints)
- Realistic data distributions (Pareto 80/20 customer load pattern)
- Fix rollback test (deployment workflow test currently disabled)
- Performance regression tests (assertNumQueries baselines)

**Addresses:**
- TEST-02: Performance test suite
- TEST-03: Fix rollback test for zero-downtime deployments

**Avoids:**
- Pitfall #7: Unrealistic load testing (model production patterns, not uniform distribution)

**Uses:** locust 2.43.1 for concurrent user simulation, pytest-django assertNumQueries() for regression prevention

### Phase Ordering Rationale

- **Database first (Phase 1):** Transaction safety and unique constraints are foundation for all other work. Race conditions corrupt production data.
- **API second (Phases 2-3):** Pagination prevents OOM errors on large datasets, filtering enables usability, documentation improves developer experience. Builds on stable queries from Phase 1.
- **Testing last (Phases 4-5):** Validates completed features. Integration tests need error handling (Phase 3). Performance tests need pagination (Phase 2).
- **Multi-phase migrations in Phase 1:** Zero-downtime requirement forces 3-deployment strategy for unique constraints. Cannot rush this.
- **Query optimization in Phase 2:** N+1 prevention must happen when adding pagination, not as separate phase.

### Research Flags

**Phases needing deeper research during planning:**
- **None** — All phases follow well-documented Django/DRF patterns. Official docs and high-quality community articles exist for all features.

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Django transaction isolation and select_for_update() are well-documented official features
- **Phase 2:** DRF pagination and filtering are core framework features with extensive docs
- **Phase 3:** drf-spectacular is industry standard with comprehensive documentation
- **Phase 4:** Webhook testing patterns and RBAC testing are well-established in Django community
- **Phase 5:** Locust load testing and pytest performance testing have mature ecosystems

**Research adequacy:** The 4 research files provide HIGH confidence guidance for all 5 suggested phases. No gaps requiring additional research.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified with official sources (Django 5.2 docs, PyPI package pages). Stack already in production use. |
| Features | HIGH | Feature analysis based on existing codebase inspection + official DRF docs. Clear distinction between table stakes and differentiators. |
| Architecture | HIGH | Patterns documented in official Django/DRF docs. Service layer architecture is standard Django best practice. |
| Pitfalls | HIGH | Critical pitfalls sourced from DjangoCon talks, official docs, and production incident reports. Multi-phase migration requirement verified. |

**Overall confidence:** HIGH

All recommended technologies are mature, production-proven, and well-documented. The existing codebase already demonstrates good architectural decisions (covering indexes, CHECK constraints, CustomerScopedManager). The research identifies specific gaps (transaction isolation, pagination on custom actions) with clear solutions.

### Gaps to Address

**No major gaps.** Minor validation items during implementation:

- **Lock ordering conventions:** Document the specific lock order (Customer → DriftEvent → AlertRule → AlertEvent) in CONVENTIONS.md during Phase 1 implementation. Research provides pattern but team must establish project-specific conventions.

- **Idempotency key format:** Research recommends `alert-event-{id}-{timestamp}` pattern. Validate this works with webhook recipient systems during TEST-01.

- **Load test data distribution:** Research provides Pareto 80/20 pattern. Validate this matches actual production customer distribution during TEST-02 by analyzing production metrics.

- **Migration linter configuration:** Add django-migration-linter to CI during Phase 1. Research identifies tool but team must configure rules for project-specific constraints.

These are implementation details, not research gaps. All can be resolved during phase execution without additional research.

## Sources

### Primary (HIGH confidence)
- [Django 5.2 Database Configuration](https://docs.djangoproject.com/en/5.2/ref/databases/) — Transaction isolation, IsolationLevel enum
- [Django 5.2 Transaction Documentation](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) — transaction.atomic(), select_for_update() patterns
- [PostgreSQL 15 Transaction Isolation](https://www.postgresql.org/docs/15/transaction-iso.html) — Isolation level semantics
- [DRF Pagination Documentation](https://www.django-rest-framework.org/api-guide/pagination/) — Custom action pagination
- [DRF Filtering Documentation](https://www.django-rest-framework.org/api-guide/filtering/) — DjangoFilterBackend, SearchFilter
- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/) — @extend_schema decorator usage
- [django-filter DRF Integration](https://django-filter.readthedocs.io/en/latest/guide/rest_framework.html) — FilterSet patterns
- PyPI package verification (drf-spectacular 0.29.0, django-filter 25.2, pytest-xdist 3.8.0, responses 0.25.8, locust 2.43.1)

### Secondary (MEDIUM confidence)
- [Django Migrations: Pitfalls and Solutions (DjangoCon US 2022)](https://2022.djangocon.us/talks/django-migrations-pitfalls-and-solutions/) — Zero-downtime migration strategies
- [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter) — Backwards compatibility detection
- [Handling Deadlocks in Django Applications](https://wawaziphil.medium.com/handling-deadlocks-in-django-applications-a-comprehensive-guide-03d8a7fd31a3) — Lock ordering patterns
- [Django @atomic Doesn't Prevent Race Conditions](https://medium.com/@anas-issath/djangos-atomic-decorator-didn-t-prevent-my-race-condition-and-the-docs-never-warned-me-58a98177cb9e) — select_for_update() requirement
- [Understanding Webhook Retry Logic | CodeHook](https://www.codehook.dev/blog/understanding-webhook-retry-logic-what-you-need-to-implement) — Idempotency patterns
- [Automating Performance Testing in Django | TestDriven.io](https://testdriven.io/blog/django-performance-testing/) — Locust integration

### Context7 Libraries Referenced
- Django 5.2 official documentation (transaction isolation, constraints, migrations)
- Django REST Framework official guides (pagination, filtering, schemas)
- PostgreSQL 15 official documentation (isolation levels, locking)

---
*Research completed: 2026-01-26*
*Ready for roadmap: YES*

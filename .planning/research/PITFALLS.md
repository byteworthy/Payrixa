# Pitfalls Research

**Domain:** Django Database Optimization and API Improvements (Healthcare SaaS with HIPAA)
**Researched:** 2026-01-26
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Missing select_for_update Causes Race Conditions in Concurrent Drift Detection

**What goes wrong:**
Multiple workers processing drift events simultaneously can create duplicate AlertEvent records, corrupt aggregate calculations, or produce inconsistent alert states. The `evaluate_drift_event()` function checks for existing alerts but the check-then-create pattern creates a race window where two workers can both find no existing alert and both create one.

**Why it happens:**
Django's `@transaction.atomic()` provides rollback (atomicity) but NOT concurrency control. Developers commonly believe that wrapping code in `transaction.atomic()` prevents race conditions, but it only ensures all-or-nothing execution. Without explicit row locking via `select_for_update()`, concurrent transactions can read the same data and make conflicting decisions.

**How to avoid:**
```python
# BAD - Race condition
with transaction.atomic():
    existing = AlertEvent.objects.filter(drift_event=drift_event, alert_rule=rule).first()
    if not existing:
        alert = AlertEvent.objects.create(...)  # Two workers can both reach here

# GOOD - Proper locking
with transaction.atomic():
    # Lock the drift_event row to prevent concurrent processing
    drift_event = DriftEvent.objects.select_for_update().get(pk=drift_event.pk)
    existing = AlertEvent.objects.filter(drift_event=drift_event, alert_rule=rule).first()
    if not existing:
        alert = AlertEvent.objects.create(...)  # Only one worker proceeds
```

Always use consistent lock ordering to prevent deadlocks: lock DriftEvent before AlertRule, lock by primary key in ascending order when locking multiple records.

**Warning signs:**
- Duplicate alert notifications sent to users
- Database unique constraint violations (if unique constraints added later)
- Audit logs showing multiple AlertEvent records for the same drift_event + rule combination
- Customer complaints about "seeing the same alert twice"
- Intermittent IntegrityError exceptions under load

**Phase to address:**
Phase 3 - Database Optimization (DB-01: Fix transaction isolation for concurrent drift detection)

**Sources:**
- [Django @atomic Doesn't Prevent Race Conditions](https://medium.com/@anas-issath/djangos-atomic-decorator-didn-t-prevent-my-race-condition-and-the-docs-never-warned-me-58a98177cb9e)
- [How to avoid Race Conditions and Deadlocks in Django](https://www.kubeblogs.com/avoid-race-conditions-and-deadlocks-in-django-step-by-step-guide/)

---

### Pitfall 2: Backwards Incompatible Migrations Break Rolling Deployments

**What goes wrong:**
Adding unique constraints, dropping columns, or renaming fields in a single migration causes crashes when old code versions are still running during deployment. The classic scenario: migration adds `UniqueConstraint` on `(customer, payer, cpt_group, drift_type)`, but old code doesn't check for duplicates before creating records, causing IntegrityError exceptions mid-deployment.

**Why it happens:**
In production systems with rolling deployments (blue-green, canary), you cannot deploy database and application servers simultaneously. There's always a window where new schema runs with old code OR old schema runs with new code. Operations like `DROP COLUMN` immediately break old code still querying that column.

**How to avoid:**
Use multi-phase migrations for any breaking changes:

**Phase 1 (Deploy): Add column/constraint with null=True**
```python
# Migration 0042
operations = [
    migrations.AddField('MyModel', 'new_field', null=True),  # Old code ignores it
]
```

**Phase 2 (Deploy): Update code to populate new field**
- Old code still running: ignores new field
- New code deployed: writes to new field

**Phase 3 (Deploy after all old code gone): Make field required**
```python
# Migration 0043 (only after Phase 2 fully deployed)
operations = [
    migrations.AlterField('MyModel', 'new_field', null=False),  # Now safe
]
```

For unique constraints on Phase 3 work (DB-02):
1. First migration: Add database index with CONCURRENTLY (doesn't lock table)
2. Second deployment: Update code to check duplicates before insert
3. Third migration: Add UniqueConstraint (now safe because code prevents violations)

**Warning signs:**
- IntegrityError exceptions appearing during deployments
- Application crashes with "column does not exist" errors
- Migration rollback failures requiring manual database fixes
- Long-running migrations that lock tables for minutes
- Customer-facing errors during deployment windows

**Phase to address:**
Phase 3 - Database Optimization (DB-02: Implement unique constraints) - MUST use multi-phase approach

**Sources:**
- [Django Migrations: Pitfalls and Solutions (DjangoCon US 2022)](https://2022.djangocon.us/talks/django-migrations-pitfalls-and-solutions/)
- [django-migration-linter: Detect backward incompatible migrations](https://github.com/3YOURMIND/django-migration-linter)
- [Zero Downtime Django Deployments with Multistep Database Changes](https://johnnymetz.com/posts/multistep-database-changes/)

---

### Pitfall 3: Deadlocks from Inconsistent Lock Ordering with select_for_update

**What goes wrong:**
Two concurrent transactions create a circular wait: Transaction A locks DriftEvent #1 then tries to lock AlertRule #5, while Transaction B locks AlertRule #5 then tries to lock DriftEvent #1. Both wait forever until PostgreSQL detects the deadlock and kills one transaction with `psycopg2.errors.DeadlockDetected`. Lost work, failed background jobs, and unpredictable errors.

**Why it happens:**
When using `select_for_update()` to prevent race conditions, developers often lock records in different orders across different code paths. Drift detection might lock payer records alphabetically, while alert evaluation locks them by severity. This creates circular dependencies.

**How to avoid:**
Establish and enforce consistent lock ordering conventions across the codebase:

```python
# GOOD - Consistent ordering convention
LOCK_ORDER = {
    'Customer': 1,
    'DriftEvent': 2,
    'AlertRule': 3,
    'AlertEvent': 4,
}

# Always lock in this order: Customer → DriftEvent → AlertRule → AlertEvent
with transaction.atomic():
    # 1. Lock customer context (if needed)
    customer = Customer.objects.select_for_update().get(pk=customer_id)

    # 2. Lock drift events (always by ascending PK)
    drift_events = DriftEvent.objects.select_for_update().filter(
        customer=customer
    ).order_by('pk')  # CRITICAL: ascending PK order

    # 3. Lock alert rules (always by ascending PK)
    rules = AlertRule.objects.select_for_update().filter(
        customer=customer
    ).order_by('pk')

    # 4. Create alert events (lowest priority in lock order)
    for event in drift_events:
        for rule in rules:
            if rule.evaluate(event):
                AlertEvent.objects.create(...)
```

Additional deadlock prevention strategies:
- Keep transactions as short as possible (< 1 second)
- Use `select_for_update(nowait=True)` to fail fast instead of blocking
- Implement retry logic with exponential backoff for deadlock errors
- Use `select_for_update(skip_locked=True)` for work queue patterns

**Warning signs:**
- `OperationalError: deadlock detected` in production logs
- Background jobs randomly failing and requiring retry
- Database locks timing out under high concurrency
- Prometheus metrics showing spikes in transaction retry counts
- Performance degradation under load (workers waiting on locks)

**Phase to address:**
Phase 3 - Database Optimization (DB-01: Fix transaction isolation) - Must establish lock ordering conventions

**Sources:**
- [Handling Deadlocks in Django Applications: A Comprehensive Guide](https://wawaziphil.medium.com/handling-deadlocks-in-django-applications-a-comprehensive-guide-03d8a7fd31a3)
- [Solving Django race conditions with select_for_update](https://www.youssefm.com/posts/solving-django-race-conditions)

---

### Pitfall 4: N+1 Query Explosion in Paginated API Endpoints

**What goes wrong:**
Adding pagination to custom actions (`@action` decorated methods) without proper `select_related()` or `prefetch_related()` causes the API to make 1 query for the page, then N additional queries for related objects (one per result). For a page of 100 alert events with related drift_events, alert_rules, and customers, this becomes 301 queries instead of 4.

**Why it happens:**
DRF's generic pagination automatically handles serialization but doesn't know about your model relationships. Custom action methods (`def feedback(self, request)`, `def dashboard(self, request)`) bypass the ViewSet's optimized `get_queryset()` method, losing any prefetch optimization. The CustomerScopedManager's query filtering also bypasses some ORM optimizations.

**How to avoid:**
Always optimize querysets before pagination in custom actions:

```python
# BAD - N+1 queries
@action(detail=False, methods=['get'])
def dashboard(self, request):
    # Each alert accesses alert_rule and drift_event → N queries
    alerts = AlertEvent.objects.filter(status='pending')
    paginator = self.pagination_class()
    page = paginator.paginate_queryset(alerts, request)
    serializer = AlertEventSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)

# GOOD - Optimized with prefetch
@action(detail=False, methods=['get'])
def dashboard(self, request):
    alerts = AlertEvent.objects.select_related(
        'alert_rule',
        'drift_event',
        'drift_event__customer',  # If serializer includes customer name
        'payment_delay_signal',
    ).prefetch_related(
        'drift_event__report_run',  # If serializer includes report details
    ).filter(status='pending')

    paginator = self.pagination_class()
    page = paginator.paginate_queryset(alerts, request)
    serializer = AlertEventSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)
```

Create a test that fails on N+1 queries:
```python
def test_dashboard_no_n_plus_1_queries(self):
    """Verify dashboard endpoint uses select_related to avoid N+1."""
    # Create 20 alerts
    for _ in range(20):
        create_alert_event(...)

    with self.assertNumQueries(5):  # Allow only 5 queries max
        response = self.client.get('/api/v1/alert-events/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)
```

**Warning signs:**
- API response times increase linearly with page size
- Database query logs showing hundreds of nearly identical queries
- `django-debug-toolbar` showing 50+ duplicate queries on a single page
- API timeouts under load during high-traffic periods
- Database CPU usage spikes when paginating through large result sets

**Phase to address:**
Phase 3 - API Improvements (API-01: Add pagination to custom actions) - Must include query optimization

**Sources:**
- [Database access optimization - Django docs](https://docs.djangoproject.com/en/6.0/topics/db/optimization/)
- [A Few Django ORM Mistakes](https://kevinmahoney.co.uk/articles/django-orm-mistakes/)

---

### Pitfall 5: False Sense of Security from High Test Coverage Without Integration Tests

**What goes wrong:**
Achieving 85% code coverage doesn't guarantee correct behavior. Tests mock the database, external webhooks, and Celery tasks, leading to passing tests while production breaks on race conditions, transaction rollbacks, webhook delivery failures, or tenant isolation violations. Coverage measures "lines executed" not "behaviors verified."

**Why it happens:**
Developers optimize for coverage percentage instead of meaningful test scenarios. Mocking is faster than integration testing, so tests mock everything: `@patch('AlertEvent.objects.create')` passes without ever touching the database. Critical scenarios like "what happens when webhook POST returns 500?" or "does transaction rollback cleanup alert state?" are never tested.

**How to avoid:**
Balance unit tests (mocked, fast) with integration tests (real database, slow):

**Unit Tests (60% of tests):**
- Test business logic with mocked database
- Fast feedback during development
- Test edge cases and error paths

**Integration Tests (30% of tests):**
- Test with real PostgreSQL (test database)
- Verify transaction boundaries and rollbacks
- Test multi-model interactions (DriftEvent + AlertEvent + AlertRule)
- Verify CustomerScopedManager tenant isolation

**E2E Tests (10% of tests):**
- Test full workflows end-to-end
- Real Celery tasks (use `task.apply()` instead of `.apply_async()`)
- Real webhook HTTP calls (use test server, not mocks)
- Test production-like scenarios: concurrent requests, large uploads, error recovery

Example critical integration tests for Phase 3:
```python
class TransactionIsolationIntegrationTest(TestCase):
    """Test race conditions with real database."""

    def test_concurrent_alert_creation_no_duplicates(self):
        """Verify select_for_update prevents duplicate alerts."""
        drift_event = create_drift_event()
        rule = create_alert_rule()

        # Simulate two workers evaluating the same drift_event
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(evaluate_drift_event, drift_event),
                executor.submit(evaluate_drift_event, drift_event),
            ]
            results = [f.result() for f in futures]

        # Verify only 1 alert created despite concurrent evaluation
        alert_count = AlertEvent.objects.filter(
            drift_event=drift_event, alert_rule=rule
        ).count()
        self.assertEqual(alert_count, 1, "Race condition created duplicate alerts")
```

Don't mock these critical components:
- Django ORM operations (test real database behavior)
- Transaction boundaries (`transaction.atomic()` behavior)
- Model validation and constraints
- Tenant isolation (`CustomerScopedManager` filtering)
- Multi-table queries (JOIN performance, prefetch correctness)

**Warning signs:**
- "Tests pass locally but fail in production"
- Production errors never caught by test suite
- Coverage report shows 85% but bugs slip through regularly
- Tests run in 10 seconds (too fast = everything mocked)
- Integration test suite doesn't exist or is marked `@pytest.mark.skip`
- Database migrations cause production errors despite passing tests

**Phase to address:**
Phase 3 - Testing (TEST-01 through TEST-04) - Must include integration tests, not just mocked unit tests

**Sources:**
- [Getting a Django Application to 100% Test Coverage](https://adamj.eu/tech/2019/04/30/getting-a-django-application-to-100-percent-coverage/)
- [Pytest + Coverage: How to Use Them Properly](https://python.plainenglish.io/pytest-coverage-how-to-use-them-properly-a0cea834b313)

---

### Pitfall 6: Load Testing with Unrealistic Data Distributions

**What goes wrong:**
Performance tests create uniform data (same number of claims per customer, even distribution of payers, no variance in upload sizes), missing real-world patterns where 90% of load comes from 10% of customers. Tests show acceptable performance at 100 req/s, but production degrades at 50 req/s because one customer uploads 50MB CSVs while others upload 1MB files.

**Why it happens:**
Load testing tools (Locust, JMeter) default to uniform distributions. Developers create `users = [user1, user2, ..., user100]` and round-robin through them, missing hotspot behavior. Test data uses synthetic uploads (100 rows each), not production-like uploads (ranging from 10 to 100,000 rows).

**How to avoid:**
Model realistic data distributions in performance tests:

```python
# BAD - Uniform distribution
def create_test_uploads():
    """Creates 100 uploads of exactly 100 rows each."""
    for i in range(100):
        Upload.objects.create(customer=customers[i % 10], row_count=100)

# GOOD - Realistic distribution
def create_test_uploads_realistic():
    """Creates uploads following production patterns."""
    # Model Pareto distribution (80/20 rule)
    # 20% of customers generate 80% of uploads
    heavy_customers = random.sample(customers, k=2)  # 2 out of 10
    light_customers = [c for c in customers if c not in heavy_customers]

    # Heavy customers: large uploads, frequent
    for customer in heavy_customers:
        for _ in range(40):  # 80 uploads from 2 customers
            row_count = random.randint(5000, 100000)  # Production sizes
            Upload.objects.create(customer=customer, row_count=row_count)

    # Light customers: small uploads, infrequent
    for customer in light_customers:
        for _ in range(2):  # 20 uploads from 8 customers
            row_count = random.randint(10, 500)
            Upload.objects.create(customer=customer, row_count=row_count)
```

Production-like load test characteristics:
- **Hotspot patterns**: 80% of load from 20% of customers
- **Realistic data sizes**: Min 10 rows, max 100k rows, median 500 rows
- **Concurrent access**: Multiple workers processing same customer's data
- **Mixed operations**: 80% reads, 15% writes, 5% heavy analytics
- **Time-based patterns**: Simulate morning upload spike (8-10am)
- **Cache behavior**: Cold cache at start, then warm cache (more realistic)

**Warning signs:**
- Load tests pass but production performance degrades unexpectedly
- Performance issues only appear with specific customers (large ones)
- Database slow query logs show queries not covered by load tests
- Memory usage in production much higher than load test environment
- Cache hit rates in load tests (90%) don't match production (60%)
- Load test results show linear scaling but production has step-function degradation

**Phase to address:**
Phase 3 - Testing (TEST-02: Add performance tests) - Must model production data distributions

**Sources:**
- [Automating Performance Testing in Django | TestDriven.io](https://testdriven.io/blog/django-performance-testing/)
- [Load Testing Django APIs with Locust](https://damisola.hashnode.dev/load-testing-django-apis-with-locust-a-quick-guide)

---

### Pitfall 7: Webhook Retry Logic Without Idempotency Causes Duplicate Processing

**What goes wrong:**
Webhook delivery fails (network timeout, 503 response), retry logic sends the webhook again, but the recipient processes the alert twice—sending duplicate notifications, creating duplicate tickets in external systems, or double-charging customers. Without idempotency keys, retries become duplicates.

**Why it happens:**
HTTP is not transactional. A webhook POST might succeed on the server side (alert recorded) but the response gets lost in transit, causing the client to retry. The recipient sees two identical requests and has no way to know they're the same logical event. Django's Celery retry mechanism (`task.retry()`) makes this worse by automatically retrying failed tasks.

**How to avoid:**
Implement idempotency for all webhook deliveries:

```python
# Phase 3 TEST-01 implementation
def send_webhook_with_idempotency(alert_event, webhook_url):
    """Send webhook with idempotency key to prevent duplicate processing."""
    # Use alert_event.id as idempotency key (unique, immutable)
    idempotency_key = f"alert-event-{alert_event.id}-{alert_event.triggered_at.timestamp()}"

    headers = {
        'Content-Type': 'application/json',
        'X-Idempotency-Key': idempotency_key,  # Recipient uses this to dedupe
        'X-Webhook-Signature': generate_signature(alert_event, webhook_secret),
    }

    payload = {
        'event_id': str(alert_event.id),
        'event_type': 'alert.triggered',
        'idempotency_key': idempotency_key,  # Also in body for logging
        'timestamp': alert_event.triggered_at.isoformat(),
        'data': alert_event.payload,
    }

    # Track delivery attempts
    attempt = WebhookDeliveryAttempt.objects.create(
        alert_event=alert_event,
        url=webhook_url,
        idempotency_key=idempotency_key,
        status='pending',
    )

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=10,  # Don't wait forever
        )

        # Record attempt regardless of status code
        attempt.status = 'delivered' if response.status_code < 500 else 'failed'
        attempt.response_code = response.status_code
        attempt.response_body = response.text[:1000]  # Truncate for storage
        attempt.save()

        # Only retry on 5xx (server errors), not 4xx (client errors)
        if response.status_code >= 500:
            raise Exception(f"Webhook delivery failed: {response.status_code}")

        return response

    except Exception as e:
        attempt.status = 'failed'
        attempt.error_message = str(e)
        attempt.save()
        raise
```

Recipient side must implement idempotency checking:
```python
# Webhook receiver (customer's system)
@csrf_exempt
def receive_alert_webhook(request):
    idempotency_key = request.headers.get('X-Idempotency-Key')

    # Check if we've already processed this event
    if ProcessedWebhook.objects.filter(idempotency_key=idempotency_key).exists():
        logger.info(f"Skipping duplicate webhook: {idempotency_key}")
        return JsonResponse({'status': 'duplicate', 'message': 'Already processed'})

    # Process webhook
    alert_data = json.loads(request.body)
    process_alert(alert_data)

    # Record that we processed it
    ProcessedWebhook.objects.create(
        idempotency_key=idempotency_key,
        processed_at=timezone.now(),
    )

    return JsonResponse({'status': 'success'})
```

**Warning signs:**
- Customer reports receiving duplicate alert notifications
- External ticketing systems (Jira, ServiceNow) show duplicate tickets
- Webhook logs show multiple successful deliveries for same alert
- Customer complaints about "getting spammed" by alerts
- Database has multiple WebhookDeliveryAttempt records with status='delivered' for same alert

**Phase to address:**
Phase 3 - Testing (TEST-01: Create webhook integration tests) - Must include retry and idempotency testing

**Sources:**
- [Understanding Webhook Retry Logic: What You Need to Implement | CodeHook](https://www.codehook.dev/blog/understanding-webhook-retry-logic-what-you-need-to-implement)
- [10 Best Practices for Webhook Implementation](https://www.codehook.dev/blog/10-best-practices-for-webhook-implementation-in-2023)

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip `select_for_update()` in evaluate_drift_event | Simpler code, no deadlock risk | Race conditions create duplicate alerts under load | **Never** - concurrent access is guaranteed in production |
| Single-phase migration for unique constraints | Faster deployment (1 step vs 3) | Rolling deployment crashes, requires emergency rollback | **Never** - zero-downtime requirement is absolute |
| Mock all database operations in tests | Tests run in <1 second | Integration bugs slip to production, false confidence | Only for pure business logic tests; 70% of tests should use real DB |
| Uniform test data distributions | Easy to generate (loop 1..100) | Load tests don't catch real performance issues | Only for unit tests; performance tests need production-like distributions |
| Omit idempotency keys from webhooks | Simpler implementation (no tracking table) | Duplicate processing, customer complaints, support burden | **Never** - webhooks will retry, duplicates are guaranteed |
| Use `get_or_create()` instead of `select_for_update()` | Django handles existence check | Race condition window between get and create | Only in single-threaded contexts (management commands with --single-worker) |
| Skip prefetch_related on paginated endpoints | Works fine in dev (10 records) | N+1 explosion in production (1000+ records) | **Never** - pagination is specifically for large datasets |
| Test only happy paths | 100% coverage faster | Error handling bugs slip through | Only during rapid prototyping; production code needs error path tests |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Webhook delivery | Fire-and-forget without tracking attempts | Store WebhookDeliveryAttempt records with status, response_code, retries |
| Webhook retry | Retry indefinitely until success | Exponential backoff with max 5 attempts, then dead-letter queue |
| Webhook signatures | Skip signature verification in staging | Always verify signatures (use test keys in staging, prod keys in prod) |
| Email alerts | Assume SMTP send() success means delivered | Track delivery status with bounce handling, log Message-ID for debugging |
| Celery task retry | Use default `autoretry_for=(Exception,)` | Only retry on specific exceptions (ConnectionError, OperationalError), not ValidationError |
| External API calls | No timeout specified | Always set timeout (10s for webhooks, 30s for reports, 5s for health checks) |
| Redis cache | Assume cache.get() never fails | Wrap in try/except, degrade gracefully if cache unavailable |
| PostgreSQL replication | Write to replica for better performance | Always write to primary, only read from replicas (avoid replication lag bugs) |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Missing `select_related()` in paginated APIs | Response time increases with page size; 100+ queries per request | Add `select_related()` for ForeignKey, `prefetch_related()` for ManyToMany | >10 results per page with 2+ levels of relationships |
| Validation loads all rules per row | CSV upload processing time linear with rules × rows | Filter rules by context (payer, CPT) before applying | >50 active validation rules and >1000 row uploads |
| CustomerScopedManager filtering at Python level | Queries slow down as customer count grows | Add explicit `customer_id` indexes, consider partitioning | >5000 customers or >1M records per table |
| Memory cache in multi-process deployment | Cache misses in prod despite hits in dev | Require Redis for all multi-worker deployments | >1 Gunicorn worker (immediate) |
| Transaction holding locks during external API call | Lock timeouts under load, deadlocks increase | Complete external I/O before `transaction.atomic()` or after | >10 concurrent workers hitting same customer's data |
| Synchronous webhook delivery in request cycle | API timeout when webhook endpoint slow | Use Celery task for webhook delivery (async) | Webhook recipient has >5s response time |
| No connection pooling (default CONN_MAX_AGE=0) | Connection overhead dominates at scale | Set CONN_MAX_AGE=60 for web workers, use PgBouncer | >100 requests/minute per worker |
| Drift detection without CONCURRENTLY index | Exclusive lock blocks writes during index creation | Use `CREATE INDEX CONCURRENTLY` in migrations | Tables with >100k rows |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Tenant isolation bypass via `.unscoped()` without audit | PHI data leak between customers (HIPAA violation, $50k+ fine) | Always log unscoped queries with caller context, require explicit customer_id parameter |
| Webhook signature verification disabled "temporarily" | Attacker sends fake alerts, triggers false notifications, reputation damage | Never deploy with signature verification disabled, use test keys in non-prod |
| Database dumps include PHI in plaintext | Data breach if backup stolen, compliance violation | Encrypt backups at rest, store encryption keys separately, test restore process |
| Background tasks inherit superuser context incorrectly | Cross-customer data contamination if customer context not set | Always use `with customer_context(customer):` in Celery tasks, never rely on thread-local leakage |
| Error messages leak sensitive query parameters | PHI exposed in logs, Sentry reports, customer emails | Scrub PHI from exception messages, use error codes instead of raw SQL |
| Missing row-level encryption for demo vs real data | Production PHI stored in plaintext if `REAL_DATA_MODE=True` but encryption not configured | Enforce `FIELD_ENCRYPTION_KEY` required when `REAL_DATA_MODE=True`, add startup validation |
| Unique constraints without partial index | Patient identifiers in unique constraint exposed in constraint violation errors | Use partial unique indexes: `UniqueConstraint(fields=['patient_id'], condition=Q(deleted=False))` |
| Celery task arguments include PHI | PHI logged in Celery broker (Redis), visible in Flower monitoring | Pass only record IDs in task arguments, fetch PHI inside task with encryption |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Transaction isolation fixes:** Often missing deadlock retry logic — verify exponential backoff with max 3 attempts
- [ ] **Unique constraints:** Often missing backwards-compatible migration plan — verify 3-phase deployment strategy documented
- [ ] **API pagination:** Often missing `select_related()` optimization — verify `assertNumQueries()` test exists
- [ ] **Webhook tests:** Often missing retry and idempotency scenarios — verify duplicate delivery test exists
- [ ] **Performance tests:** Often missing realistic data distributions — verify Pareto distribution (80/20) modeled
- [ ] **Integration tests:** Often missing transaction rollback verification — verify concurrent access test exists
- [ ] **Load tests:** Often missing cold-start scenarios — verify cache warmup test exists
- [ ] **Error handling:** Often missing client vs server error distinction (4xx vs 5xx) — verify retry only on 5xx
- [ ] **Tenant isolation:** Often missing background task context verification — verify Celery task sets customer_context()
- [ ] **Database migrations:** Often missing CONCURRENTLY for index creation — verify no exclusive locks on large tables
- [ ] **Audit logging:** Often missing unscoped query tracking — verify `.unscoped()` calls are logged with caller
- [ ] **RBAC tests:** Often missing cross-role boundary verification — verify superuser cannot access arbitrary customer data without context

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Race condition created duplicate alerts | MEDIUM | 1) Add `select_for_update()` 2) Run deduplication script: `AlertEvent.objects.filter(drift_event=X).order_by('created_at')[1:].delete()` 3) Deploy unique constraint to prevent recurrence |
| Backwards incompatible migration deployed | HIGH | 1) Immediate rollback of app deployment (keep DB migrated) 2) Deploy backwards-compatible code version 3) Schedule forward migration after all old code removed 4) Post-incident: add migration linter to CI |
| Deadlock causing background job failures | LOW | 1) Automatic retry usually succeeds 2) Add consistent lock ordering 3) Reduce transaction scope 4) Add deadlock monitoring alerts |
| N+1 query causing API timeouts | MEDIUM | 1) Add read replica to offload reads 2) Deploy `select_related()` fix 3) Add `assertNumQueries()` test to prevent regression 4) Monitor query counts in APM |
| Webhook duplicates processed | MEDIUM | 1) Add idempotency key checking on receiver side 2) Run deduplication script on recipient's data 3) Re-send corrected webhooks if needed 4) Add idempotency to sender side |
| Load test missed performance issue | LOW | 1) Immediate: add caching or rate limiting 2) Create production-like load test 3) Run load test against staging before production deployment 4) Add performance regression tests to CI |
| Test coverage hiding integration bugs | MEDIUM | 1) Write integration test reproducing the bug 2) Fix the bug 3) Add integration test category to CI 4) Review existing tests for excessive mocking |
| Unique constraint violation in production | HIGH | 1) Add unique index with CONCURRENTLY (no lock) 2) Run cleanup script to resolve duplicates 3) Update code to prevent duplicates 4) Deploy unique constraint migration 5) Post-incident: require 3-phase migration review |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Race conditions from missing `select_for_update()` | Phase 3 - DB-01 | Integration test with `ThreadPoolExecutor` creating concurrent transactions, asserting no duplicates |
| Backwards incompatible migrations | Phase 3 - DB-02 | Add `django-migration-linter` to CI pipeline, require 3-phase migration plan in PR template |
| Deadlocks from inconsistent lock ordering | Phase 3 - DB-01 | Document lock ordering in CONVENTIONS.md, add lock ordering test helper, monitor deadlock metrics |
| N+1 queries in paginated endpoints | Phase 3 - API-01 | Add `pytest-django` `assertNumQueries()` test for each paginated endpoint, fail if >10 queries |
| False sense of security from coverage | Phase 3 - TEST-01 through TEST-04 | Require integration tests (real DB) for 30% of test suite, add pytest markers for test types |
| Unrealistic load testing | Phase 3 - TEST-02 | Model Pareto distribution in test data, require 80/20 customer load pattern, test cold start |
| Webhook retry without idempotency | Phase 3 - TEST-01 | Add `WebhookDeliveryAttempt` model tracking retries, test duplicate delivery scenario, verify deduplication |
| Tenant isolation bypass | Phase 3 - TEST-04 | Add RBAC cross-role tests, verify background tasks set customer_context(), audit log unscoped queries |

## Sources

**Django Transaction Isolation & Deadlocks:**
- [Database transactions | Django documentation](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)
- [Handling Deadlocks in Django Applications: A Comprehensive Guide](https://wawaziphil.medium.com/handling-deadlocks-in-django-applications-a-comprehensive-guide-03d8a7fd31a3)
- [Django's transaction.atomic() - Not as atomic as you may think](https://charemza.name/blog/posts/django/postgres/transactions/not-as-atomic-as-you-may-think/)
- [How to avoid Race Conditions and Deadlocks in Django](https://www.kubeblogs.com/avoid-race-conditions-and-deadlocks-in-django-step-by-step-guide/)

**Zero-Downtime Migrations:**
- [django-pg-zero-downtime-migrations](https://github.com/tbicr/django-pg-zero-downtime-migrations)
- [Zero Downtime Django Deployments with Multistep Database Changes](https://johnnymetz.com/posts/multistep-database-changes/)
- [Django zero downtime deployment: best practices](https://www.vintasoftware.com/blog/django-zero-downtime-guide)
- [Django Migrations: Pitfalls and Solutions (DjangoCon US 2022)](https://2022.djangocon.us/talks/django-migrations-pitfalls-and-solutions/)
- [django-migration-linter](https://github.com/3YOURMIND/django-migration-linter)

**select_for_update Race Conditions:**
- [Django @atomic Doesn't Prevent Race Conditions](https://medium.com/@anas-issath/djangos-atomic-decorator-didn-t-prevent-my-race-condition-and-the-docs-never-warned-me-58a98177cb9e)
- [Solving Django race conditions with select_for_update](https://www.youssefm.com/posts/solving-django-race-conditions)
- [Django's select_for_update with Examples and Tests](https://medium.com/@alexandre.laplante/djangos-select-for-update-with-examples-and-tests-caff09414766)

**Database Optimization & Concurrency:**
- [Database access optimization | Django documentation](https://docs.djangoproject.com/en/6.0/topics/db/optimization/)
- [A Few Django ORM Mistakes](https://kevinmahoney.co.uk/articles/django-orm-mistakes/)
- [Database Integrity in Django: Safely Handling Critical Data](https://pirate.github.io/django-concurrency-talk/)
- [Handling Concurrency Without Locks | Haki Benita](https://hakibenita.com/django-concurrency)

**Performance Testing:**
- [Automating Performance Testing in Django | TestDriven.io](https://testdriven.io/blog/django-performance-testing/)
- [Load Testing Django APIs with Locust](https://damisola.hashnode.dev/load-testing-django-apis-with-locust-a-quick-guide)
- [Django Performance Optimization Tips | TestDriven.io](https://testdriven.io/blog/django-performance-optimization-tips/)

**DRF Pagination & Filtering:**
- [Pagination - Django REST framework](https://www.django-rest-framework.org/api-guide/pagination/)
- [Filtering - Django REST framework](https://www.django-rest-framework.org/api-guide/filtering/)

**Testing Best Practices:**
- [Getting a Django Application to 100% Test Coverage](https://adamj.eu/tech/2019/04/30/getting-a-django-application-to-100-percent-coverage/)
- [Pytest + Coverage: How to Use Them Properly](https://python.plainenglish.io/pytest-coverage-how-to-use-them-properly-a0cea834b313)

**Webhook Implementation:**
- [Understanding Webhook Retry Logic | CodeHook](https://www.codehook.dev/blog/understanding-webhook-retry-logic-what-you-need-to-implement)
- [10 Best Practices for Webhook Implementation](https://www.codehook.dev/blog/10-best-practices-for-webhook-implementation-in-2023)
- [How to Build a Webhook Receiver in Django](https://adamj.eu/tech/2021/05/09/how-to-build-a-webhook-receiver-in-django/)

---
*Pitfalls research for: Django database optimization, API improvements, and testing (Healthcare SaaS with HIPAA compliance)*
*Researched: 2026-01-26*

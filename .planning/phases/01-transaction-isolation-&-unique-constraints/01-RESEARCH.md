# Phase 1: Transaction Isolation & Unique Constraints - Research

**Researched:** 2026-01-26
**Domain:** Django/PostgreSQL database integrity and concurrency
**Confidence:** HIGH

## Summary

This research investigates how to prevent race conditions in concurrent drift detection operations and implement unique constraints without downtime in a production Django 5.2 + PostgreSQL 15 HIPAA system. The phase addresses two critical database integrity requirements: (1) preventing duplicate alert creation when multiple Celery workers process the same customer data concurrently, and (2) enforcing unique constraints on key business fields to prevent duplicate records.

The standard Django approach uses `transaction.atomic()` with `select_for_update()` for row-level locking to prevent race conditions. For unique constraints, PostgreSQL's `CREATE UNIQUE INDEX CONCURRENTLY` combined with Django's `SeparateDatabaseAndState` migration operation enables zero-downtime deployments through a three-phase migration strategy.

Key findings reveal that Django's default READ COMMITTED isolation level allows phantom reads between queries in the same transaction, requiring explicit locking via `select_for_update()`. The research also confirms that `get_or_create()` is inherently racy under READ COMMITTED and requires IntegrityError handling or unique database constraints for safety.

**Primary recommendation:** Use `transaction.atomic()` with `select_for_update()` for drift computation locking, implement unique constraints via three-phase migrations with concurrent index creation, and add IntegrityError retry logic for `get_or_create()` patterns.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django ORM | 5.2 | Transaction management & migrations | Built-in transaction isolation, migration framework with PostgreSQL-specific operations |
| PostgreSQL | 15+ | Database with MVCC | Industry standard for ACID compliance, concurrent index creation, multiple isolation levels |
| psycopg2 | 2.9+ | PostgreSQL adapter | Official Django-recommended driver, supports PostgreSQL-specific features |
| django-pgtransaction | 2.x | Transaction isolation control | Extends Django's atomic() with per-transaction isolation level control (REPEATABLE_READ, SERIALIZABLE) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-pg-zero-downtime-migrations | Latest | Migration safety checks | Optional: Warns about unsafe migration operations (useful for large production databases) |
| django-postgres-extra | 2.x | PostgreSQL helpers | Optional: Provides additional PostgreSQL-specific model fields and query operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| select_for_update() | SERIALIZABLE isolation | SERIALIZABLE prevents all race conditions but requires retry logic for serialization failures; select_for_update() is more targeted and performant |
| Three-phase migrations | Downtime during migration | Downtime acceptable for non-production; three-phase required for 24/7 HIPAA systems |
| Manual SQL | Django ORM operations | Manual SQL gives more control but loses migration reversibility and database portability |

**Installation:**
```bash
# Core (already installed)
pip install Django>=5.2 psycopg2-binary>=2.9

# Optional: For granular transaction isolation control
pip install django-pgtransaction>=2.0

# Optional: For migration safety checks
pip install django-pg-zero-downtime-migrations
```

## Architecture Patterns

### Recommended Locking Strategy

**Pattern 1: Prevent Concurrent Drift Computation**
```python
from django.db import transaction
from django.db.models import F

class BaseDriftDetectionService:
    def compute(self, start_date=None, end_date=None, **kwargs):
        # Use select_for_update to lock customer row during computation
        with transaction.atomic():
            # Lock the customer record to prevent concurrent drift computations
            customer = Customer.objects.select_for_update().get(id=self.customer.id)

            # Alternative: Lock on a dedicated coordination record
            # computation_lock, _ = DriftComputationLock.objects.select_for_update().get_or_create(
            #     customer=customer,
            #     defaults={'last_computed_at': timezone.now()}
            # )

            # Compute aggregates
            aggregates = self._compute_aggregates(start_date, end_date, **kwargs)

            # Detect signals (creates DriftEvent records)
            signals = self._detect_signals(baseline_window, current_window, **kwargs)

            return ComputationResult(...)
```

**Pattern 2: Idempotent Alert Creation with Unique Constraints**
```python
from django.db import IntegrityError, transaction

def create_alert_from_drift_event(drift_event):
    """Create alert with idempotent retry on race condition."""
    try:
        with transaction.atomic():
            alert = AlertEvent.objects.create(
                customer=drift_event.customer,
                drift_event=drift_event,
                severity=drift_event.severity,
                # ... other fields
            )
            return alert, True  # created=True
    except IntegrityError:
        # Race condition: another worker created the alert
        # Fetch and return existing alert
        alert = AlertEvent.objects.get(
            customer=drift_event.customer,
            drift_event=drift_event
        )
        return alert, False  # created=False
```

**Pattern 3: Batch Operations with FOR UPDATE SKIP LOCKED**
```python
def process_pending_tasks_distributed():
    """Multiple workers can safely process different tasks concurrently."""
    with transaction.atomic():
        # Each worker grabs different unlocked tasks
        tasks = (
            Task.objects
            .select_for_update(skip_locked=True)
            .filter(status='pending')[:10]
        )

        for task in tasks:
            task.status = 'processing'
            task.save()
            process_task(task)
```

### Three-Phase Migration Pattern

**Phase 1: Add index concurrently (no constraint yet)**
```python
# migrations/0001_add_unique_index_phase1.py
from django.db import migrations
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import models

class Migration(migrations.Migration):
    atomic = False  # Required for CONCURRENTLY operations

    dependencies = [
        ('upstream', '0000_previous_migration'),
    ]

    operations = [
        # Create unique index concurrently (no table lock)
        AddIndexConcurrently(
            model_name='driftevent',
            index=models.Index(
                fields=['customer', 'report_run', 'payer', 'cpt_group', 'drift_type'],
                name='driftevent_unique_idx',
            ),
        ),
    ]
```

**Phase 2: Add constraint using existing index**
```python
# migrations/0002_add_unique_constraint_phase2.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('upstream', '0001_add_unique_index_phase1'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Update Django's internal state
                migrations.AddConstraint(
                    model_name='driftevent',
                    constraint=models.UniqueConstraint(
                        fields=['customer', 'report_run', 'payer', 'cpt_group', 'drift_type'],
                        name='driftevent_unique_signal',
                    ),
                ),
            ],
            database_operations=[
                # Use existing index to create constraint (fast operation)
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE upstream_driftevent
                        ADD CONSTRAINT driftevent_unique_signal
                        UNIQUE USING INDEX driftevent_unique_idx;
                    """,
                    reverse_sql="""
                        ALTER TABLE upstream_driftevent
                        DROP CONSTRAINT driftevent_unique_signal;
                    """,
                ),
            ],
        ),
    ]
```

**Phase 3: Validate constraint (optional validation pass)**
```python
# migrations/0003_validate_constraint_phase3.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('upstream', '0002_add_unique_constraint_phase2'),
    ]

    operations = [
        # Validate no duplicates exist
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op, constraint already enforced
            reverse_sql="SELECT 1;",
        ),
    ]
```

### Anti-Patterns to Avoid

- **Don't rely on application-level uniqueness checks**: Race conditions between check and insert make them unreliable. Always enforce uniqueness with database constraints.

- **Don't use ATOMIC_REQUESTS globally**: Wrapping every request in a transaction adds overhead for read-only operations and causes issues with async tasks and streaming responses. Use selective `@transaction.atomic` decorators instead.

- **Don't assume transaction.atomic prevents all race conditions**: Django's default READ COMMITTED isolation allows concurrent transactions to see each other's commits between queries. Use `select_for_update()` for row-level locking.

- **Don't create unique constraints synchronously in production**: `AddConstraint` without concurrent index creation locks the table during migration. Always use the three-phase pattern for large tables.

- **Don't ignore IntegrityError on get_or_create**: The method is inherently racy. Always catch `IntegrityError` and retry or use unique constraints to make duplicate creation harmless.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Transaction isolation control | Custom connection management | `django-pgtransaction` with `pgtransaction.atomic(isolation_level=...)` | Handles edge cases (nested transactions, savepoints, connection pooling) |
| Distributed locking | Redis-based locks | `select_for_update()` with database rows | Database locks are ACID-compliant, survive crashes, and integrate with transactions |
| Retry logic for serialization failures | Custom retry decorators | Django's built-in transaction hooks + `django-pgtransaction` with `retry=True` | Handles partial commits, nested transactions, and idempotency correctly |
| Zero-downtime index creation | Application-level coordination | PostgreSQL `CREATE INDEX CONCURRENTLY` | Database-level operation prevents table locks and integrates with MVCC |
| Migration safety checks | Manual review | `django-pg-zero-downtime-migrations` | Automatically detects 20+ unsafe migration patterns |

**Key insight:** Database-level mechanisms (constraints, locks, transactions) are always more reliable than application-level implementations because they're atomic, crash-resistant, and don't require distributed coordination.

## Common Pitfalls

### Pitfall 1: Concurrent get_or_create() Creates Duplicates

**What goes wrong:** Two Celery workers call `get_or_create()` simultaneously. Both check for existence, find nothing, and both try to create the record. One succeeds, the other gets `IntegrityError`.

**Why it happens:** READ COMMITTED isolation means the second transaction's GET query doesn't see the first transaction's uncommitted INSERT.

**How to avoid:**
```python
# BAD: Unhandled race condition
signal, created = DriftEvent.objects.get_or_create(
    customer=customer,
    report_run=report_run,
    payer=payer,
    cpt_group=cpt_group,
    drift_type='DENIAL_RATE',
    defaults={'severity': 0.8, ...}
)

# GOOD: Handle race condition with IntegrityError
from django.db import IntegrityError, transaction

try:
    with transaction.atomic():
        signal, created = DriftEvent.objects.get_or_create(
            customer=customer,
            report_run=report_run,
            payer=payer,
            cpt_group=cpt_group,
            drift_type='DENIAL_RATE',
            defaults={'severity': 0.8, ...}
        )
except IntegrityError:
    # Race condition occurred, fetch existing record
    signal = DriftEvent.objects.get(
        customer=customer,
        report_run=report_run,
        payer=payer,
        cpt_group=cpt_group,
        drift_type='DENIAL_RATE'
    )
    created = False
```

**Warning signs:**
- IntegrityError in production logs with "duplicate key value violates unique constraint"
- Intermittent test failures on concurrent operations
- Duplicate records in database despite "unique" business logic

### Pitfall 2: AddConstraint Locks Table During Migration

**What goes wrong:** Running `migrations.AddConstraint()` on a large table locks it for minutes/hours, causing request timeouts and downtime.

**Why it happens:** PostgreSQL creates unique constraints by building a unique index synchronously, which requires an ACCESS EXCLUSIVE lock preventing all reads and writes.

**How to avoid:** Use the three-phase migration pattern (documented above):
1. Create unique index concurrently (no lock)
2. Create constraint using existing index (fast)
3. Validate (optional)

**Warning signs:**
- Migration takes >30 seconds on tables with >1M rows
- "Lock wait timeout" errors in application logs during migration
- Database monitoring shows blocked queries during migration

### Pitfall 3: Forgetting atomic=False for Concurrent Index Creation

**What goes wrong:** Migration fails with error: "CREATE INDEX CONCURRENTLY cannot run inside a transaction block"

**Why it happens:** Django wraps migrations in transactions by default, but PostgreSQL's CONCURRENTLY option requires running outside a transaction.

**How to avoid:**
```python
class Migration(migrations.Migration):
    atomic = False  # REQUIRED for AddIndexConcurrently

    operations = [
        AddIndexConcurrently(...),
    ]
```

**Warning signs:**
- Migration fails with PostgreSQL error about transaction blocks
- Migration succeeds in dev (small tables) but fails in production (large tables need CONCURRENTLY)

### Pitfall 4: select_for_update() Without transaction.atomic()

**What goes wrong:** Locks are not acquired or are released immediately, causing race conditions.

**Why it happens:** `select_for_update()` requires an active transaction to hold locks until COMMIT. Outside a transaction, locks are released after the query.

**How to avoid:**
```python
# BAD: Lock released immediately
customer = Customer.objects.select_for_update().get(id=1)
# ... compute drift (not locked anymore)

# GOOD: Lock held until transaction commits
with transaction.atomic():
    customer = Customer.objects.select_for_update().get(id=1)
    # ... compute drift (still locked)
    # Lock released after this block
```

**Warning signs:**
- Race conditions persist despite using `select_for_update()`
- Database logs show no lock waits when concurrent operations occur

### Pitfall 5: Nullable ForeignKey with select_for_update()

**What goes wrong:** Django raises `NotSupportedError: FOR UPDATE cannot be applied to nullable relations`

**Why it happens:** PostgreSQL can't lock rows that might not exist (NULL foreign keys). Django explicitly prevents this to avoid silent failures.

**How to avoid:**
```python
# BAD: Nullable relation
Person.objects.select_related('hometown').select_for_update()

# GOOD: Filter out nulls first
Person.objects.select_related('hometown').select_for_update().exclude(hometown=None)

# BETTER: Lock only specific relations
Person.objects.select_related('hometown').select_for_update(of=('self',))
```

**Warning signs:**
- NotSupportedError in production logs
- SELECT FOR UPDATE queries fail on models with nullable foreign keys

## Code Examples

Verified patterns from official sources:

### Transaction Isolation with select_for_update()

```python
# Source: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
from django.db import transaction

# Basic row-level locking
with transaction.atomic():
    # Locks all matched rows until transaction commits
    entries = Entry.objects.select_for_update().filter(author=request.user)
    for entry in entries:
        entry.status = 'processing'
        entry.save()
```

### Non-Blocking Lock Acquisition

```python
# Source: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
from django.db import DatabaseError, transaction

# Fail fast if lock unavailable
try:
    with transaction.atomic():
        obj = Model.objects.select_for_update(nowait=True).get(pk=1)
        # Process object
except DatabaseError:
    # Lock unavailable, handle gracefully
    pass

# Skip locked rows (work queue pattern)
with transaction.atomic():
    tasks = Task.objects.select_for_update(skip_locked=True).filter(status='pending')[:10]
    for task in tasks:
        process(task)
```

### Unique Constraint with Partial Index

```python
# Source: https://docs.djangoproject.com/en/5.2/ref/models/constraints/
from django.db import models
from django.db.models import Q

class Booking(models.Model):
    room = models.CharField(max_length=100)
    date = models.DateField()
    status = models.CharField(max_length=20)

    class Meta:
        constraints = [
            # Only active bookings must be unique
            models.UniqueConstraint(
                fields=['room', 'date'],
                condition=Q(status='active'),
                name='unique_active_booking',
            ),
        ]
```

### IntegrityError Retry Pattern

```python
# Source: Django ticket #24009, community best practice
from django.db import IntegrityError, transaction

def create_or_get_signal(customer, report_run, payer, cpt_group, drift_type, **defaults):
    """Idempotent signal creation with race condition handling."""
    try:
        with transaction.atomic():
            signal, created = DriftEvent.objects.get_or_create(
                customer=customer,
                report_run=report_run,
                payer=payer,
                cpt_group=cpt_group,
                drift_type=drift_type,
                defaults=defaults,
            )
            return signal, created
    except IntegrityError:
        # Race condition: another worker created it first
        signal = DriftEvent.objects.get(
            customer=customer,
            report_run=report_run,
            payer=payer,
            cpt_group=cpt_group,
            drift_type=drift_type,
        )
        return signal, False
```

### Concurrent Index Creation

```python
# Source: https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/operations/
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False  # Required for CONCURRENTLY

    operations = [
        AddIndexConcurrently(
            model_name='driftevent',
            index=models.Index(
                fields=['customer', 'payer', 'drift_type'],
                name='drift_lookup_idx',
            ),
        ),
    ]
```

### Three-Phase Unique Constraint Migration

```python
# Source: https://johnnymetz.com/posts/multistep-database-changes/
# Phase 1: Create index concurrently
class Migration(migrations.Migration):
    atomic = False
    operations = [
        AddIndexConcurrently(
            model_name='driftevent',
            index=models.Index(fields=[...], name='temp_unique_idx'),
        ),
    ]

# Phase 2: Use index to create constraint
class Migration(migrations.Migration):
    dependencies = [('upstream', '0001_phase1')]
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddConstraint(
                    model_name='driftevent',
                    constraint=models.UniqueConstraint(fields=[...], name='unique_signal'),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE upstream_driftevent ADD CONSTRAINT unique_signal UNIQUE USING INDEX temp_unique_idx;",
                    reverse_sql="ALTER TABLE upstream_driftevent DROP CONSTRAINT unique_signal;",
                ),
            ],
        ),
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `unique_together` in Meta | `UniqueConstraint` in Meta.constraints | Django 2.2+ | UniqueConstraint supports partial constraints (condition=Q(...)) and functional indexes (Lower('name')) |
| Manual retry logic for race conditions | IntegrityError + database constraints | Django 1.x → 2.x+ | Database enforces uniqueness; application handles retry gracefully |
| Synchronous index creation | `AddIndexConcurrently` | Django 3.0+ | Zero-downtime migrations on large tables |
| Global isolation level in DATABASES | Per-transaction isolation with django-pgtransaction | Django 1.x → modern | Granular control: use SERIALIZABLE only where needed |
| Manual SQL for unique index + constraint | `SeparateDatabaseAndState` pattern | Django 1.7+ | Keeps Django state in sync with database while running custom SQL |

**Deprecated/outdated:**
- `unique_together`: Replaced by `UniqueConstraint` (more flexible, supports partial/functional constraints)
- Setting isolation level in `DATABASES['OPTIONS']`: Global setting affects all queries; use per-transaction control instead
- Ignoring IntegrityError from `get_or_create()`: Race conditions are real in production; always handle gracefully

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal locking granularity for drift detection**
   - What we know: Can lock customer row, or create dedicated DriftComputationLock table
   - What's unclear: Performance impact of locking customer row (high contention) vs separate lock table (additional query)
   - Recommendation: Start with customer row locking (simpler); add dedicated lock table only if profiling shows contention issues

2. **SERIALIZABLE vs select_for_update for drift computation**
   - What we know: SERIALIZABLE prevents all anomalies but requires retry logic; select_for_update is more targeted
   - What's unclear: Whether complex drift computation queries have read/write dependencies requiring SERIALIZABLE
   - Recommendation: Use select_for_update initially; upgrade to SERIALIZABLE only if race conditions persist

3. **Uniqueness scope for DriftEvent records**
   - What we know: Should be unique per (customer, report_run, payer, cpt_group, drift_type)
   - What's unclear: Whether report_run should be included (prevents historical comparison) or excluded (allows duplicate detection across runs)
   - Recommendation: Include report_run in unique constraint to allow historical trend analysis; prevents duplicates within a single computation

4. **Handling historical duplicate data**
   - What we know: Adding unique constraints may fail if existing duplicates exist
   - What's unclear: Best strategy for deduplicating production data before constraint migration
   - Recommendation: Add data cleanup migration before unique constraint; keep most recent record, delete older duplicates

## Sources

### Primary (HIGH confidence)
- [Django Documentation: select_for_update()](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update) - Official querysets reference
- [Django Documentation: UniqueConstraint](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) - Official constraints reference
- [PostgreSQL Documentation: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) - Official PostgreSQL isolation levels
- [Django Documentation: PostgreSQL Operations](https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/operations/) - AddIndexConcurrently reference
- [Django Documentation: Database Transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) - Official transaction management guide

### Secondary (MEDIUM confidence)
- [Michal Charemza: Django's transaction.atomic()](https://charemza.name/blog/posts/django/postgres/transactions/not-as-atomic-as-you-may-think/) - Read Committed limitations
- [Johnny Metz: Zero Downtime Django Deployments](https://johnnymetz.com/posts/multistep-database-changes/) - Multistep migration pattern
- [Joseph Fox: PostgreSQL Isolation Levels in Django](https://joseph-fox.co.uk/tech/understanding-postgresql-isolation-levels) - Isolation level comparison
- [Medium: Database Isolation Levels in Django](https://medium.com/buserbrasil/database-isolation-levels-anomalies-and-how-to-handle-them-with-django-992889d233d5) - Anomalies explanation
- [django-pgtransaction GitHub](https://github.com/Opus10/django-pgtransaction) - Transaction isolation library
- [Medium: How to add UniqueConstraint concurrently](https://medium.com/@timmerop/how-to-add-a-uniqueconstraint-concurrently-in-django-2043c4752ee6) - Practical guide

### Tertiary (LOW confidence)
- [Django Forum: Any problems with SERIALIZABLE](https://forum.djangoproject.com/t/any-problems-using-django-with-postgresql-serializable-transaction-isolation/27550) - Community discussion
- [Django Forum: Zero-downtime migrations discussion](https://forum.djangoproject.com/t/lets-talk-zero-downtime-migrations/28388) - Community patterns
- [Django Ticket #24009](https://code.djangoproject.com/ticket/24009) - get_or_create race condition discussion
- [Django Ticket #21039](https://code.djangoproject.com/ticket/21039) - CREATE INDEX CONCURRENTLY support

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Django/PostgreSQL features, well-documented
- Architecture: HIGH - Patterns verified in official documentation and production use
- Pitfalls: HIGH - Documented in Django tickets, official docs, and consistent across multiple sources

**Research date:** 2026-01-26
**Valid until:** 2026-03-26 (60 days - Django/PostgreSQL are stable; migration patterns unlikely to change)

**Project-specific context:**
- Django 5.2 + DRF + Celery + PostgreSQL 15 + Redis
- Multi-tenant with CustomerScopedManager
- HIPAA compliance requires zero-downtime migrations
- Concurrent Celery workers processing drift detection
- Existing models: Customer, ReportRun, DriftEvent, AlertEvent
- Current issue: DriftEvent.objects.create() in concurrent tasks creates duplicates

# Database Performance Optimizer Agent

**Agent Type**: db_performance
**Purpose**: Analyze Django ORM queries for N+1 problems, missing indexes, slow queries
**Trigger Points**: on-demand, pre-deploy (optional)

---

## What This Agent Does

1. **N+1 Query Detection**: Finds queries that trigger multiple DB roundtrips
2. **Missing Index Suggestions**: Analyzes query patterns and suggests indexes
3. **Slow Query Analysis**: Identifies queries taking >100ms
4. **Query Optimization**: Proposes select_related() and prefetch_related() improvements

---

## Critical Issues Detected

### 1. N+1 Query Problem

```python
# ❌ N+1 Problem (1 + N queries)
customers = Customer.objects.all()
for customer in customers:
    print(customer.claims.count())  # Queries DB each iteration!

# ✅ Optimized (2 queries)
customers = Customer.objects.annotate(claims_count=Count('claims'))
for customer in customers:
    print(customer.claims_count)
```

### 2. Missing Index

```python
# Query pattern detected:
ClaimRecord.objects.filter(customer=1, service_date__gte='2024-01-01')

# ⚠️ No index exists for (customer, service_date)
#
# Recommendation: Add index
class Meta:
    indexes = [
        models.Index(fields=['customer', 'service_date']),
    ]
```

### 3. Unoptimized Foreign Key Access

```python
# ❌ Unoptimized (N+1 queries)
claims = ClaimRecord.objects.filter(customer=customer)
for claim in claims:
    print(claim.payer.name)  # Queries payer table each time

# ✅ Optimized (2 queries)
claims = ClaimRecord.objects.filter(customer=customer).select_related('payer')
for claim in claims:
    print(claim.payer.name)
```

---

## Usage

```bash
# Analyze entire codebase
python manage.py optimize_database

# Analyze specific app
python manage.py optimize_database --app upstream

# Generate migration with suggested indexes
python manage.py optimize_database --create-migration

# Run with query logging
python manage.py optimize_database --log-queries
```

---

## Output

```
🔍 Database Performance Optimizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing ORM usage across 89 files...

❌ N+1 QUERIES (4)
  upstream/views.py:156 - Customer loop accessing claims
  upstream/api/views.py:89 - DriftEvent loop accessing payer

⚠️  MISSING INDEXES (7)
  ClaimRecord(customer, service_date) - Used in 12 queries
  DriftEvent(customer, event_type, event_date) - Used in 8 queries

📊 SLOW QUERIES (3)
  upstream/services/payer_drift.py:245 - 340ms average
  upstream/views.py:78 - 215ms average

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendations: 11 optimizations possible
Estimated speedup: 2-3x
```

---

## Integration

**Pre-Deploy Check** (optional, can be slow):
```bash
git push
# Triggers: python manage.py optimize_database --fail-on-critical
```

**On-Demand**:
```bash
python manage.py optimize_database
```

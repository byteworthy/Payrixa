# Database Schema: Complete Migrations

**Document:** 04-database-schema.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

This document consolidates all database migrations for the Upstream platform. Migrations are organized by phase and include index strategies for performance.

**Technology:** PostgreSQL 15 (production), SQLite (dev)

---

## Phase 1 Migrations (Weeks 1-4)

### Migration 1: RiskBaseline Model

**Purpose:** Store historical denial rate baselines for risk scoring

**File:** `upstream/migrations/0XXX_add_risk_baseline.py`

```python
from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiskBaseline',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='risk_baselines',
                    to='upstream.customer'
                )),
                ('payer', models.CharField(max_length=255, db_index=True)),
                ('cpt', models.CharField(max_length=20, db_index=True)),
                ('denial_rate', models.FloatField(
                    help_text='Historical denial rate: denied / total'
                )),
                ('sample_size', models.IntegerField()),
                ('confidence_score', models.FloatField(
                    help_text='Statistical confidence: min(sample_size / 100, 1.0)'
                )),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'upstream_risk_baseline',
                'verbose_name': 'Risk Baseline',
                'verbose_name_plural': 'Risk Baselines',
            },
        ),
        migrations.AddConstraint(
            model_name='riskbaseline',
            constraint=models.UniqueConstraint(
                fields=['customer', 'payer', 'cpt'],
                name='risk_baseline_unique_key'
            ),
        ),
        migrations.AddConstraint(
            model_name='riskbaseline',
            constraint=models.CheckConstraint(
                check=Q(confidence_score__gte=0.0) & Q(confidence_score__lte=1.0),
                name='risk_baseline_confidence_range'
            ),
        ),
        migrations.AddIndex(
            model_name='riskbaseline',
            index=models.Index(
                fields=['customer', 'payer', 'cpt'],
                name='risk_baseline_lookup_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='riskbaseline',
            index=models.Index(
                fields=['customer', '-confidence_score'],
                name='risk_baseline_confidence_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_risk_baseline
python manage.py migrate
```

---

### Migration 2: AutomationRule Model

**Purpose:** Store pre-approved automation rules for autonomous execution

**File:** `upstream/migrations/0XXX_add_automation_rule.py`

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_risk_baseline'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationRule',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='automation_rules',
                    to='upstream.customer'
                )),
                ('name', models.CharField(max_length=255)),
                ('rule_type', models.CharField(
                    max_length=50,
                    choices=[
                        ('THRESHOLD', 'Threshold-based'),
                        ('PATTERN', 'Pattern detection'),
                        ('SCHEDULE', 'Calendar-based'),
                        ('CHAIN', 'Chained action'),
                    ]
                )),
                ('trigger_event', models.CharField(max_length=100, db_index=True)),
                ('conditions', models.JSONField(default=dict)),
                ('action_type', models.CharField(max_length=100)),
                ('action_params', models.JSONField(default=dict)),
                ('enabled', models.BooleanField(default=True, db_index=True)),
                ('escalate_on_error', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'upstream_automation_rule',
                'verbose_name': 'Automation Rule',
                'verbose_name_plural': 'Automation Rules',
            },
        ),
        migrations.AddIndex(
            model_name='automationrule',
            index=models.Index(
                fields=['customer', 'enabled', 'trigger_event'],
                name='automation_rule_lookup_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_automation_rule
python manage.py migrate
```

---

### Migration 3: ExecutionLog Model

**Purpose:** Audit trail for all autonomous actions

**File:** `upstream/migrations/0XXX_add_execution_log.py`

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_automation_rule'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExecutionLog',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='execution_logs',
                    to='upstream.customer'
                )),
                ('rule', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    null=True,
                    blank=True,
                    to='upstream.automationrule'
                )),
                ('trigger_event', models.JSONField()),
                ('action_taken', models.CharField(max_length=100)),
                ('result', models.CharField(
                    max_length=20,
                    choices=[
                        ('SUCCESS', 'Success'),
                        ('FAILED', 'Failed'),
                        ('ESCALATED', 'Escalated to human'),
                    ],
                    db_index=True
                )),
                ('details', models.JSONField(default=dict)),
                ('execution_time_ms', models.IntegerField()),
                ('executed_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'upstream_execution_log',
                'verbose_name': 'Execution Log',
                'verbose_name_plural': 'Execution Logs',
                'ordering': ['-executed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='executionlog',
            index=models.Index(
                fields=['customer', '-executed_at'],
                name='execution_log_customer_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='executionlog',
            index=models.Index(
                fields=['rule', 'result'],
                name='execution_log_rule_result_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_execution_log
python manage.py migrate
```

---

### Migration 4: Enhance ClaimRecord for Multi-Source Ingestion

**Purpose:** Track ingestion source (CSV, EHR webhook, API, batch)

**File:** `upstream/migrations/0XXX_add_claim_submitted_via.py`

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_execution_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='claimrecord',
            name='submitted_via',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('csv_upload', 'CSV Upload'),
                    ('ehr_webhook', 'EHR Webhook'),
                    ('api', 'API'),
                    ('batch_import', 'Batch Import'),
                ],
                default='csv_upload',
                db_index=True,
                help_text='Ingestion source for analytics'
            ),
        ),
        migrations.AddIndex(
            model_name='claimrecord',
            index=models.Index(
                fields=['customer', 'submitted_via', 'decided_date'],
                name='claim_source_analytics_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_claim_submitted_via
python manage.py migrate
```

---

### Migration 5: Authorization Model

**Purpose:** Track authorizations with 30-day expiration alerts

**File:** `upstream/migrations/0XXX_add_authorization.py`

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_claim_submitted_via'),
    ]

    operations = [
        migrations.CreateModel(
            name='Authorization',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='authorizations',
                    to='upstream.customer'
                )),
                ('auth_number', models.CharField(max_length=100, unique=True)),
                ('patient_identifier', models.CharField(
                    max_length=100,
                    help_text='De-identified patient ID'
                )),
                ('payer', models.CharField(max_length=255, db_index=True)),
                ('service_type', models.CharField(max_length=100)),
                ('cpt_codes', models.JSONField(default=list)),
                ('auth_start_date', models.DateField()),
                ('auth_expiration_date', models.DateField(db_index=True)),
                ('units_authorized', models.IntegerField()),
                ('units_used', models.IntegerField(default=0)),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('ACTIVE', 'Active'),
                        ('EXPIRING_SOON', 'Expiring Soon'),
                        ('EXPIRED', 'Expired'),
                        ('RENEWED', 'Renewed'),
                    ],
                    default='ACTIVE',
                    db_index=True
                )),
                ('reauth_lead_time_days', models.IntegerField(
                    default=21,
                    help_text='Payer-specific reauth lead time (Blue Cross: 21, Aetna: 30, UHC: 14)'
                )),
                ('auto_reauth_enabled', models.BooleanField(
                    default=False,
                    help_text='If true, auto-submit reauth without approval'
                )),
                ('last_alert_sent', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'upstream_authorization',
                'verbose_name': 'Authorization',
                'verbose_name_plural': 'Authorizations',
            },
        ),
        migrations.AddIndex(
            model_name='authorization',
            index=models.Index(
                fields=['customer', 'status', 'auth_expiration_date'],
                name='auth_expiration_check_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='authorization',
            index=models.Index(
                fields=['customer', 'payer', 'status'],
                name='auth_payer_status_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_authorization
python manage.py migrate
```

---

## Phase 2 Migrations (Weeks 5-8)

### Migration 6: ModifierRequirement Model

**Purpose:** Payer-specific modifier requirements for risk scoring

**File:** `upstream/migrations/0XXX_add_modifier_requirement.py`

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_authorization'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModifierRequirement',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('payer', models.CharField(max_length=255, db_index=True)),
                ('cpt', models.CharField(max_length=20, db_index=True)),
                ('required_modifier', models.CharField(max_length=10)),
                ('condition', models.TextField(
                    help_text='When this modifier is required'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'upstream_modifier_requirement',
                'verbose_name': 'Modifier Requirement',
                'verbose_name_plural': 'Modifier Requirements',
            },
        ),
        migrations.AddConstraint(
            model_name='modifierrequirement',
            constraint=models.UniqueConstraint(
                fields=['payer', 'cpt', 'required_modifier'],
                name='modifier_requirement_unique'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_modifier_requirement
python manage.py migrate
```

---

### Migration 7: DiagnosisCPTRule Model

**Purpose:** Valid diagnosis-CPT combinations for medical necessity validation

**File:** `upstream/migrations/0XXX_add_diagnosis_cpt_rule.py`

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_modifier_requirement'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosisCPTRule',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('cpt', models.CharField(max_length=20, db_index=True)),
                ('diagnosis_category', models.CharField(max_length=100)),
                ('icd10_codes', models.JSONField(default=list)),
                ('payer', models.CharField(
                    max_length=255,
                    null=True,
                    blank=True,
                    help_text='null = all payers'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'upstream_diagnosis_cpt_rule',
                'verbose_name': 'Diagnosis-CPT Rule',
                'verbose_name_plural': 'Diagnosis-CPT Rules',
            },
        ),
        migrations.AddIndex(
            model_name='diagnosiscptrule',
            index=models.Index(
                fields=['cpt', 'payer'],
                name='diagnosis_cpt_lookup_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_diagnosis_cpt_rule
python manage.py migrate
```

---

### Migration 8: RiskScore Model

**Purpose:** Store calculated risk scores for claims

**File:** `upstream/migrations/0XXX_add_risk_score.py`

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_diagnosis_cpt_rule'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiskScore',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('claim', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='risk_scores',
                    to='upstream.claimrecord'
                )),
                ('score', models.IntegerField(help_text='Risk score 0-100')),
                ('confidence', models.FloatField(help_text='Confidence 0-1')),
                ('factors', models.JSONField(
                    default=list,
                    help_text='List of risk factors with contributions'
                )),
                ('recommendation', models.TextField()),
                ('auto_fix_actions', models.JSONField(
                    default=list,
                    help_text='Actions that can be auto-executed'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'upstream_risk_score',
                'verbose_name': 'Risk Score',
                'verbose_name_plural': 'Risk Scores',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='riskscore',
            index=models.Index(
                fields=['claim', '-created_at'],
                name='risk_score_claim_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_risk_score
python manage.py migrate
```

---

### Migration 9: AppealOutcome Model

**Purpose:** Track appeal outcomes to optimize future appeals

**File:** `upstream/migrations/0XXX_add_appeal_outcome.py`

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('upstream', '0XXX_add_risk_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppealOutcome',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('appeal_id', models.CharField(max_length=100, unique=True)),
                ('customer', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='appeal_outcomes',
                    to='upstream.customer'
                )),
                ('payer', models.CharField(max_length=255, db_index=True)),
                ('denial_reason', models.CharField(max_length=255, db_index=True)),
                ('claim_count', models.IntegerField()),
                ('total_amount', models.DecimalField(max_digits=12, decimal_places=2)),

                # Outcome
                ('decision', models.CharField(
                    max_length=20,
                    choices=[
                        ('APPROVED', 'Approved'),
                        ('DENIED', 'Denied'),
                        ('PARTIAL', 'Partial Approval'),
                        ('PENDING', 'Pending'),
                    ],
                    db_index=True
                )),
                ('amount_recovered', models.DecimalField(
                    max_digits=12,
                    decimal_places=2,
                    default=0
                )),
                ('decision_date', models.DateField(null=True, blank=True)),

                # Appeal strategy used
                ('template_used', models.CharField(max_length=100)),
                ('arguments_used', models.JSONField(default=list)),

                # Learning
                ('days_to_decision', models.IntegerField(null=True, blank=True)),

                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'upstream_appeal_outcome',
                'verbose_name': 'Appeal Outcome',
                'verbose_name_plural': 'Appeal Outcomes',
            },
        ),
        migrations.AddIndex(
            model_name='appealoutcome',
            index=models.Index(
                fields=['payer', 'denial_reason', 'decision'],
                name='appeal_outcome_learning_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='appealoutcome',
            index=models.Index(
                fields=['customer', '-decision_date'],
                name='appeal_outcome_customer_idx'
            ),
        ),
    ]
```

**Migration Command:**
```bash
python manage.py makemigrations upstream -n add_appeal_outcome
python manage.py migrate
```

---

## Index Strategy

### Composite Indexes

**Purpose:** Optimize common query patterns

**RiskBaseline Lookups:**
```sql
CREATE INDEX risk_baseline_lookup_idx
ON upstream_risk_baseline (customer_id, payer, cpt);
```

**Authorization Expiration Checks:**
```sql
CREATE INDEX auth_expiration_check_idx
ON upstream_authorization (customer_id, status, auth_expiration_date);
```

**Execution Log Audits:**
```sql
CREATE INDEX execution_log_customer_idx
ON upstream_execution_log (customer_id, executed_at DESC);
```

### Partial Indexes

**Purpose:** Index only relevant subset of data

**Active Authorizations Only:**
```sql
CREATE INDEX auth_active_only_idx
ON upstream_authorization (customer_id, auth_expiration_date)
WHERE status = 'ACTIVE';
```

**Enabled Automation Rules Only:**
```sql
CREATE INDEX automation_rule_enabled_idx
ON upstream_automation_rule (customer_id, trigger_event)
WHERE enabled = TRUE;
```

### Covering Indexes

**Purpose:** Satisfy queries without touching heap

**Risk Score Lookup with Confidence:**
```sql
CREATE INDEX risk_baseline_covering_idx
ON upstream_risk_baseline (customer_id, payer, cpt)
INCLUDE (denial_rate, confidence_score);
```

---

## Performance Considerations

### Query Optimization

**Bad Query (No Index):**
```python
# Sequential scan - SLOW
auths = Authorization.objects.filter(
    auth_expiration_date__lte=today + timedelta(days=30)
)
```

**Good Query (Uses Index):**
```python
# Index scan - FAST
auths = Authorization.objects.filter(
    customer=customer,
    status='ACTIVE',
    auth_expiration_date__lte=today + timedelta(days=30)
)
```

### Connection Pooling

**Configure PgBouncer:**
```ini
[databases]
upstream = host=localhost dbname=upstream

[pgbouncer]
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

### Monitoring

**Track Slow Queries:**
```sql
-- PostgreSQL slow query log
ALTER DATABASE upstream SET log_min_duration_statement = 1000; -- 1 second
```

**Monitor Index Usage:**
```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC
LIMIT 10;
```

---

## Migration Checklist

**Pre-Migration:**
- [ ] Backup database
- [ ] Test migration on staging
- [ ] Review rollback plan
- [ ] Notify team of downtime (if any)

**Migration:**
- [ ] Run `python manage.py migrate --plan` to review
- [ ] Run `python manage.py migrate`
- [ ] Verify migration success in Django admin
- [ ] Run smoke tests

**Post-Migration:**
- [ ] Verify indexes created: `\d+ table_name` in psql
- [ ] Run `ANALYZE` to update statistics
- [ ] Monitor query performance
- [ ] Update documentation

---

**Next:** See `05-api-specifications.md` for webhook and internal API details.

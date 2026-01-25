# Migration Safety Checker Agent

**Agent Type**: migration_safety
**Purpose**: Validate migrations before running, detect data loss risks
**Trigger Points**: pre-commit (for new migrations), pre-deploy

---

## What This Agent Does

1. **Risk Assessment**: Categorizes migrations as Safe/Caution/High Risk/Destructive
2. **Data Loss Detection**: Identifies operations that could lose data
3. **Rollback Analysis**: Determines if migration is reversible
4. **Performance Impact**: Estimates migration execution time

---

## Risk Levels

### ✅ Safe
- Adding models
- Adding nullable fields
- Adding indexes (with `concurrent=True`)
- Creating tables

### ⚠️ Caution
- Renaming fields (requires data migration)
- Changing field types (might truncate data)
- Adding constraints

### 🔥 High Risk
- Dropping fields (data loss)
- Dropping models (table deletion)
- Removing constraints (might break app)

### ☢️ Destructive
- `RunSQL` with DROP statements
- `RemoveField` on production data
- `DeleteModel` operations

---

## Usage

```bash
# Check all pending migrations
python manage.py check_migrations

# Check specific migration
python manage.py check_migrations upstream 0015

# Generate rollback plan
python manage.py check_migrations --rollback-plan
```

---

## Output

```
🔍 Migration Safety Checker
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzing 3 pending migrations...

✅ 0012_add_database_indexes - SAFE
   └─ AddIndex: 12 new indexes
   └─ Rollback: Possible
   └─ Duration: ~2 minutes

⚠️  0013_alter_claim_status - CAUTION
   └─ AlterField: Changes varchar(20) → varchar(50)
   └─ Rollback: Possible (may truncate)
   └─ Duration: ~30 seconds

🔥 0014_remove_old_field - HIGH RISK
   └─ RemoveField: Deletes claim.old_status
   └─ ⚠️  DATA LOSS: 15,234 records affected
   └─ Rollback: NOT POSSIBLE
   └─ Recommendation: Backup data first!

━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ DEPLOYMENT BLOCKED
Fix high-risk migrations before deploying
```

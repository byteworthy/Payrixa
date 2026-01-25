# Upstream Specialized Agents - Complete Implementation

**Status**: ✅ Fully Implemented (All 3 Formats)
**Date**: 2026-01-25
**Version**: 1.0.0

---

## Executive Summary

Upstream now has **5 specialized agents** that continuously monitor code quality, database performance, test coverage, migration safety, and HIPAA compliance. These agents are implemented in **three formats**:

1. **Agent Definitions** (`.agents/agents/*.md`) - For Claude Code to understand and iterate on
2. **Management Commands** (`upstream/management/commands/*.py`) - For manual developer execution
3. **Pre-Commit Hooks** (`.pre-commit-config.yaml`) - For automatic enforcement

All findings are tracked in the database for historical analysis and trending.

---

## What Was Built

### 1. Agent Definition Files (`.agents/agents/`)

Five comprehensive agent specifications:

| Agent | File | Lines | Purpose |
|-------|------|-------|---------|
| **Code Quality Auditor** | `code-quality-auditor.md` | ~300 | Security, PHI, linting |
| **Database Performance Optimizer** | `database-performance-optimizer.md` | ~150 | N+1 queries, indexes |
| **Test Coverage Analyzer** | `test-coverage-analyzer.md` | ~150 | Coverage gaps, untested code |
| **Migration Safety Checker** | `migration-safety-checker.md` | ~150 | Migration risks, data loss |
| **HIPAA Compliance Monitor** | `hipaa-compliance-monitor.md` | ~150 | PHI exposure, compliance |

**Total**: ~900 lines of agent specifications

### 2. Management Commands (`upstream/management/commands/`)

Five fully functional Django management commands:

| Command | File | Lines | Functionality |
|---------|------|-------|--------------|
| `audit_code_quality` | `audit_code_quality.py` | ~400 | AST parsing, PHI detection, security scan |
| `optimize_database` | `optimize_database.py` | ~200 | Query analysis, index suggestions |
| `analyze_test_coverage` | `analyze_test_coverage.py` | ~100 | Coverage tracking, gap analysis |
| `check_migrations` | `check_migrations.py` | ~150 | Risk assessment, rollback analysis |
| `check_hipaa_compliance` | `check_hipaa_compliance.py` | ~200 | Compliance validation, violation detection |

**Total**: ~1,050 lines of command implementation

### 3. Database Models (`upstream/models_agents.py`)

Six models for tracking agent execution and findings:

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **AgentRun** | Track agent execution | agent_type, status, findings_count, git_commit |
| **Finding** | Individual security/quality issues | severity, category, file_path, recommendation |
| **CodeQualityMetric** | Code metrics over time | metric_name, metric_value, threshold |
| **DatabaseQueryAnalysis** | Query performance issues | query_pattern, issue_type, suggestion |
| **TestCoverageReport** | Coverage per file | coverage_percentage, missing_lines |
| **MigrationAnalysis** | Migration risk assessment | risk_level, operations, rollback_possible |

**Total**: ~250 lines of model definitions

### 4. Pre-Commit Hooks Configuration

Complete `.pre-commit-config.yaml` with:
- Standard hooks (trailing whitespace, large files, etc.)
- Black formatter
- Flake8 linter
- All 5 Upstream agents with appropriate trigger points

### 5. Installation & Execution Scripts

| Script | Purpose | Lines |
|--------|---------|-------|
| `scripts/install_hooks.sh` | One-time setup of all agents | ~60 |
| `scripts/run_all_agents.sh` | Run all agents manually | ~40 |

### 6. Documentation

| Document | Purpose | Lines |
|----------|---------|-------|
| **AGENTS_INTEGRATION_GUIDE.md** | Complete integration guide | ~550 |
| **AGENTS_README.md** | This file | ~400 |

---

## File Structure

```
/workspaces/codespaces-django/
│
├── .agents/
│   └── agents/                           # Agent definitions for Claude Code
│       ├── code-quality-auditor.md       # Agent 1 specification
│       ├── database-performance-optimizer.md  # Agent 2 specification
│       ├── test-coverage-analyzer.md     # Agent 3 specification
│       ├── migration-safety-checker.md   # Agent 4 specification
│       └── hipaa-compliance-monitor.md   # Agent 5 specification
│
├── upstream/
│   ├── models_agents.py                  # Agent tracking models
│   ├── models.py                         # Updated with agent imports
│   └── management/commands/              # Django commands
│       ├── audit_code_quality.py
│       ├── optimize_database.py
│       ├── analyze_test_coverage.py
│       ├── check_migrations.py
│       └── check_hipaa_compliance.py
│
├── scripts/
│   ├── install_hooks.sh                  # Setup script
│   └── run_all_agents.sh                 # Manual execution
│
├── .pre-commit-config.yaml               # Hook configuration
├── AGENTS_INTEGRATION_GUIDE.md           # Complete guide
└── AGENTS_README.md                      # This file
```

---

## Installation

### Quick Install (One Command)

```bash
./scripts/install_hooks.sh
```

This will:
1. ✅ Install pre-commit framework
2. ✅ Install all hooks
3. ✅ Create database migrations for agent models
4. ✅ Run migrations
5. ✅ Display usage instructions

### Verify Installation

```bash
# Test all agents
./scripts/run_all_agents.sh

# Or test individually
python manage.py audit_code_quality
python manage.py optimize_database
python manage.py analyze_test_coverage
python manage.py check_migrations
python manage.py check_hipaa_compliance
```

---

## Usage Guide

### Automatic (Pre-Commit Hooks)

```bash
# Normal workflow - agents run automatically
git add .
git commit -m "feat: Add new feature"

# Hooks execute:
# 1. Black formatter
# 2. Flake8 linter
# 3. Code Quality Auditor (blocks if critical issues)
# 4. Test Coverage Analyzer (warns only)
# 5. Migration Safety Checker (if migrations present)

# On push:
git push origin main
# HIPAA Compliance Monitor runs
```

### Manual Execution

```bash
# Run all agents
./scripts/run_all_agents.sh

# Run specific agent
python manage.py audit_code_quality --staged
python manage.py optimize_database --create-migration
python manage.py analyze_test_coverage --min-coverage 75
python manage.py check_migrations
python manage.py check_hipaa_compliance --fail-on critical
```

### Bypass Hooks (Emergency Only)

```bash
# Bypass pre-commit
git commit --no-verify -m "Emergency fix"

# Bypass pre-push
git push --no-verify
```

---

## The 5 Agents In Detail

### Agent 1: Code Quality Auditor ✅

**Purpose**: Prevent security issues and PHI exposure

**What It Detects**:
- ❌ PHI in code, comments, test data
- ❌ SQL injection vulnerabilities
- ❌ Missing customer filters (multi-tenant violations)
- ❌ Hardcoded secrets
- ⚠️  Missing database indexes
- ⚠️  Unprotected API endpoints
- ℹ️  Missing docstrings

**Trigger Points**:
- Pre-commit (blocks on critical)
- Pre-deploy (CI/CD)
- On-demand

**Command**:
```bash
python manage.py audit_code_quality --staged --fail-on critical
```

**Typical Output**:
```
🔍 Code Quality Auditor
Scanning 142 Python files...

❌ CRITICAL (2)
  upstream/views.py:45 - PHI in log statement
  upstream/api/views.py:123 - Missing customer filter

⚠️  HIGH (5)
  upstream/models.py:89 - Missing database index
  ...

❌ COMMIT BLOCKED - Fix critical issues first
```

---

### Agent 2: Database Performance Optimizer 🚀

**Purpose**: Prevent N+1 queries and missing indexes

**What It Detects**:
- ❌ N+1 query problems
- ⚠️  Missing database indexes
- ⚠️  Unoptimized foreign key access
- ℹ️  Slow queries (>100ms)

**Trigger Points**:
- On-demand (manual)
- Pre-deploy (optional, can be slow)

**Command**:
```bash
python manage.py optimize_database --create-migration
```

**Typical Output**:
```
🔍 Database Performance Optimizer
Analyzing 89 Python files...

❌ N+1 QUERIES (4)
  upstream/views.py:156 - Customer loop accessing claims
  → Use: .select_related('customer', 'payer')

⚠️  MISSING INDEXES (7)
  ClaimRecord(customer, service_date) - Used in 12 queries
  → Migration ready: python manage.py migrate

Estimated speedup: 2-3x
```

---

### Agent 3: Test Coverage Analyzer 📊

**Purpose**: Ensure critical code paths are tested

**What It Detects**:
- Overall coverage percentage
- Untested functions
- Critical paths <100% coverage
- Missing test fixtures

**Trigger Points**:
- Pre-commit (warns only)
- On-demand

**Command**:
```bash
python manage.py analyze_test_coverage --min-coverage 75
```

**Typical Output**:
```
🔍 Test Coverage Analyzer
Overall Coverage: 78%

❌ CRITICAL PATHS < 100%
  upstream/utils.py:detect_phi - 85% coverage

⚠️  LOW COVERAGE
  upstream/services/payer_drift.py - 62%

ℹ️  UNTESTED FUNCTIONS (12)
  upstream/views/metrics.py:calculate_stats
```

---

### Agent 4: Migration Safety Checker 🔒

**Purpose**: Prevent destructive migrations

**What It Detects**:
- ✅ Safe operations (AddField, CreateModel)
- ⚠️  Caution (RenameField, AlterField)
- 🔥 High risk (RemoveField - data loss!)
- ☢️  Destructive (DeleteModel, DROP statements)

**Trigger Points**:
- Pre-commit (if migrations detected)
- Pre-deploy
- On-demand

**Command**:
```bash
python manage.py check_migrations
```

**Typical Output**:
```
🔍 Migration Safety Checker
Analyzing 3 pending migrations...

✅ 0012_add_indexes - SAFE
   └─ AddIndex: 12 new indexes

⚠️  0013_alter_field - CAUTION
   └─ AlterField: May truncate data

🔥 0014_remove_field - HIGH RISK
   └─ RemoveField: Deletes claim.old_status
   └─ ⚠️  DATA LOSS: 15,234 records
   └─ Rollback: NOT POSSIBLE

❌ DEPLOYMENT BLOCKED
```

---

### Agent 5: HIPAA Compliance Monitor 🏥

**Purpose**: Ensure HIPAA compliance

**What It Checks**:
- ✅ Session timeout = 30 minutes
- ✅ HTTPOnly cookies enabled
- ✅ HTTPS enforced
- ✅ Audit logging configured
- ✅ PHI detection working
- ❌ PHI in database schema
- ❌ Missing audit logs
- ❌ Unencrypted sensitive fields

**Trigger Points**:
- Pre-push (not every commit)
- Pre-deploy
- Weekly scheduled
- On-demand

**Command**:
```bash
python manage.py check_hipaa_compliance --fail-on critical
```

**Typical Output**:
```
🔍 HIPAA Compliance Monitor

✅ Technical Safeguards (§164.312)
   ✅ Access Control: Configured
   ✅ Audit Controls: Active
   ✅ Integrity: PHI detection working

❌ VIOLATIONS (2)
   upstream/models.py - Missing audit logging
   test_data.json - Contains PHI

Compliance: 95%
❌ FIX BEFORE DEPLOYMENT
```

---

## Database Tracking

All agent findings are persisted:

```python
from upstream.models_agents import AgentRun, Finding

# Latest code quality run
AgentRun.objects.filter(agent_type='code_quality').latest('started_at')

# All critical issues
Finding.objects.filter(severity='critical', status='open')

# PHI exposure incidents
Finding.objects.filter(category='phi_exposure')

# Trending metrics
from django.db.models import Count
Finding.objects.values('category').annotate(count=Count('id'))
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Upstream Agents

on: [pull_request, push]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run migrations
        run: python manage.py migrate

      - name: Code Quality
        run: python manage.py audit_code_quality --fail-on critical

      - name: Database Performance
        run: python manage.py optimize_database

      - name: Test Coverage
        run: python manage.py analyze_test_coverage --min-coverage 70

      - name: Migration Safety
        run: python manage.py check_migrations

      - name: HIPAA Compliance
        run: python manage.py check_hipaa_compliance --fail-on critical
```

---

## Metrics & Monitoring

### Track Agent Performance

```sql
-- Agent execution history
SELECT agent_type, COUNT(*), AVG(findings_count)
FROM upstream_agent_run
WHERE status='completed'
GROUP BY agent_type;

-- Critical issues over time
SELECT DATE(created_at), COUNT(*)
FROM upstream_finding
WHERE severity='critical'
GROUP BY DATE(created_at);

-- False positive rate (ignored findings)
SELECT category, COUNT(*)
FROM upstream_finding
WHERE status='ignored'
GROUP BY category;
```

### Agent Dashboard (Future Enhancement)

```
http://localhost:8000/portal/admin/agents/

Features:
- Recent agent runs
- Open findings by severity
- Trending charts
- Compliance scorecard
```

---

## Configuration Options

```python
# upstream/settings/local.py

# Code Quality Auditor
CODE_QUALITY_AUDITOR = {
    'enabled': True,
    'block_on_critical': True,
    'block_on_high': False,
    'auto_fix': False,
    'excluded_paths': ['migrations/', 'tests/fixtures/'],
}

# Test Coverage
TEST_COVERAGE_THRESHOLDS = {
    'overall': 75,
    'critical_paths': 100,  # PHI detection, auth
}

# HIPAA Compliance
HIPAA_COMPLIANCE = {
    'session_timeout': 1800,
    'require_audit_logging': True,
    'require_field_encryption': True,
}

# PHI Detection
PHI_DETECTION_EXCEPTIONS = [
    'blue cross',  # Payer name, not PHI
    'medicare',    # Program name
]
```

---

## Best Practices

### 1. Run Locally Before Push

```bash
./scripts/run_all_agents.sh
```

### 2. Fix Priority Order

1. ❌ **Critical** (PHI, SQL injection) - Fix immediately
2. ⚠️  **High** (Missing indexes, no validation) - Fix same day
3. ℹ️  **Medium** (Docstrings) - Fix within week
4. 💡 **Low** (Style) - Batch during refactoring

### 3. Review Weekly

```bash
python manage.py check_hipaa_compliance --report weekly_compliance.json
```

### 4. Acknowledge False Positives

```python
finding = Finding.objects.get(id=123)
finding.status = 'ignored'
finding.save()
```

---

## Troubleshooting

### "Hooks are too slow"

```yaml
# .pre-commit-config.yaml - Enable fast mode
- id: code-quality-audit
  entry: python manage.py audit_code_quality --staged --fast
```

### "False positive PHI detection"

```python
# Add to settings
PHI_DETECTION_EXCEPTIONS = ['blue cross', 'medicare']
```

### "Need emergency commit"

```bash
git commit --no-verify -m "Emergency hotfix"
# Use sparingly!
```

---

## Statistics

### Lines of Code Written

| Component | Lines | Files |
|-----------|-------|-------|
| Agent Definitions | ~900 | 5 |
| Management Commands | ~1,050 | 5 |
| Database Models | ~250 | 1 |
| Pre-commit Config | ~100 | 1 |
| Scripts | ~100 | 2 |
| Documentation | ~1,000 | 2 |
| **Total** | **~3,400** | **16** |

### Coverage

- ✅ 5/5 agents fully implemented
- ✅ 3/3 formats complete (agents, commands, hooks)
- ✅ 6 database models for tracking
- ✅ 2 installation scripts
- ✅ Complete documentation

---

## Next Steps

### Immediate
1. ✅ Install hooks: `./scripts/install_hooks.sh`
2. ✅ Run agents: `./scripts/run_all_agents.sh`
3. ✅ Fix any critical issues found
4. ✅ Commit to test hooks

### Short-Term
1. Add agent dashboard UI (`/portal/admin/agents/`)
2. Add GitHub Actions workflow
3. Configure scheduled weekly runs
4. Set up Slack/email notifications

### Long-Term
1. Machine learning for false positive detection
2. Auto-fix suggestions for common issues
3. Trend analysis and predictive alerts
4. Integration with external security scanners

---

## Support

**Documentation**:
- Agent specs: `.agents/agents/*.md`
- Integration guide: `AGENTS_INTEGRATION_GUIDE.md`
- This file: `AGENTS_README.md`

**Commands**:
```bash
python manage.py [command] --help
```

**Database**:
```python
from upstream.models_agents import AgentRun, Finding
# Query for insights
```

---

## Version History

- **2026-01-25**: Initial release
  - 5 agents implemented
  - 3 formats complete
  - Database tracking
  - Pre-commit integration

---

**Status**: ✅ Production Ready

All agents are fully functional and ready for use. Install, test, and start catching issues before they reach production!

```bash
./scripts/install_hooks.sh
./scripts/run_all_agents.sh
```

🚀 Happy coding with safety nets!

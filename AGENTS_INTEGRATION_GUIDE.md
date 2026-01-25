# Upstream Agents Integration Guide

**Version**: 1.0.0
**Last Updated**: 2026-01-25

---

## Overview

Upstream now includes 5 specialized agents that analyze code quality, database performance, test coverage, migration safety, and HIPAA compliance. These agents run automatically via pre-commit hooks and can be executed manually via management commands.

---

## Quick Start

### 1. Install Pre-Commit Hooks

```bash
# One-time setup
./scripts/install_hooks.sh

# This installs:
# - Pre-commit framework
# - All 5 Upstream agents
# - Database models for tracking findings
```

### 2. Test Installation

```bash
# Run all agents manually
./scripts/run_all_agents.sh

# Or run individually
python manage.py audit_code_quality
python manage.py optimize_database
python manage.py analyze_test_coverage
python manage.py check_migrations
python manage.py check_hipaa_compliance
```

### 3. Make a Commit

```bash
git add .
git commit -m "feat: Add new feature"

# Agents automatically run:
# ✓ Code Quality Auditor (blocks if critical issues)
# ✓ Test Coverage Analyzer (warns if coverage drops)
# ✓ Migration Safety Checker (blocks if unsafe migrations)
```

---

## The 5 Agents

### Agent 1: Code Quality Auditor

**Purpose**: Scan for security issues, PHI exposure, linting problems

**Triggers**:
- ✅ Pre-commit (automatic)
- ✅ Pre-deploy (CI/CD)
- ✅ On-demand (manual)

**Command**:
```bash
python manage.py audit_code_quality

# Options:
--staged            # Scan only staged files (faster)
--fail-on critical  # Exit with error on critical issues
--report FILE       # Save JSON report to file
```

**What It Checks**:
- ❌ PHI in code, comments, test data
- ❌ SQL injection risks
- ❌ Missing customer filters
- ❌ Hardcoded secrets
- ⚠️  Missing indexes
- ⚠️  No PHI validation on inputs
- ⚠️  Unprotected API endpoints

**Blocks Commit**: Yes (if critical issues)

---

### Agent 2: Database Performance Optimizer

**Purpose**: Detect N+1 queries, missing indexes, slow queries

**Triggers**:
- ✅ On-demand (manual)
- ⚠️  Pre-deploy (optional, can be slow)

**Command**:
```bash
python manage.py optimize_database

# Options:
--app upstream                 # Analyze specific app
--create-migration            # Generate migration with indexes
--log-queries                 # Log all queries during analysis
```

**What It Checks**:
- ❌ N+1 query problems
- ⚠️  Missing database indexes
- ⚠️  Unoptimized foreign key access
- ℹ️  Slow queries (>100ms)

**Blocks Commit**: No (informational only)

---

### Agent 3: Test Coverage Analyzer

**Purpose**: Identify untested code and coverage gaps

**Triggers**:
- ✅ Pre-commit (warns only, doesn't block)
- ✅ On-demand (manual)

**Command**:
```bash
python manage.py analyze_test_coverage

# Options:
--min-coverage 75             # Minimum acceptable coverage %
--html                        # Generate HTML report
--module upstream.services    # Check specific module
```

**What It Checks**:
- Overall test coverage percentage
- Critical paths requiring 100% coverage
- Untested functions
- Missing test fixtures

**Blocks Commit**: No (warns only)

---

### Agent 4: Migration Safety Checker

**Purpose**: Validate migrations before running, detect data loss

**Triggers**:
- ✅ Pre-commit (if migrations detected)
- ✅ Pre-deploy (CI/CD)
- ✅ On-demand (manual)

**Command**:
```bash
python manage.py check_migrations

# Options:
--rollback-plan               # Generate rollback instructions
```

**What It Checks**:
- ✅ Safe operations (AddField, CreateModel)
- ⚠️  Caution operations (RenameField, AlterField)
- 🔥 High risk operations (RemoveField)
- ☢️  Destructive operations (DeleteModel, DROP statements)

**Risk Levels**:
- **Safe**: No data loss, reversible
- **Caution**: Possible data truncation, check carefully
- **High Risk**: Will lose data, backup first
- **Destructive**: Irreversible, extreme caution

**Blocks Commit**: Yes (if high risk or destructive)

---

### Agent 5: HIPAA Compliance Monitor

**Purpose**: Ensure HIPAA compliance, detect PHI exposure

**Triggers**:
- ✅ Pre-push (not every commit, just before push)
- ✅ Pre-deploy (CI/CD)
- ✅ Weekly scheduled check
- ✅ On-demand (manual)

**Command**:
```bash
python manage.py check_hipaa_compliance

# Options:
--fail-on critical            # Exit with error on violations
--check phi-exposure          # Check specific area only
--report FILE                 # Generate compliance report
```

**What It Checks**:
- ✅ Session timeout = 30 minutes
- ✅ HTTPOnly cookies enabled
- ✅ HTTPS enforced
- ✅ Audit logging configured
- ✅ PHI detection working
- ✅ Field encryption configured
- ❌ PHI in database schema
- ❌ Missing audit logs on models
- ❌ Unencrypted sensitive fields

**Blocks Push**: Yes (if critical violations)

---

## Database Models

All agent findings are stored in the database for tracking:

### Models Created

```python
# Core agent execution tracking
AgentRun  # Records each agent execution
Finding   # Individual findings from agents

# Specialized tracking
CodeQualityMetric         # Code quality metrics over time
DatabaseQueryAnalysis     # Query performance issues
TestCoverageReport        # Coverage data per file
MigrationAnalysis         # Migration risk assessments
```

### Querying Findings

```python
from upstream.models_agents import AgentRun, Finding

# Get latest code quality run
latest_run = AgentRun.objects.filter(
    agent_type='code_quality'
).order_by('-started_at').first()

# Get all open critical issues
critical_issues = Finding.objects.filter(
    severity='critical',
    status='open'
).order_by('-created_at')

# Get findings by category
phi_issues = Finding.objects.filter(
    category='phi_exposure',
    status='open'
)
```

### Admin Dashboard (Coming Soon)

```
http://localhost:8000/portal/admin/agents/

View:
- Recent agent runs
- Open findings by severity
- Trending metrics
- Compliance status
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/quality.yml
name: Code Quality & Compliance

on: [pull_request, push]

jobs:
  agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run migrations
        run: python manage.py migrate

      - name: Code Quality Audit
        run: python manage.py audit_code_quality --fail-on critical

      - name: Database Performance Check
        run: python manage.py optimize_database

      - name: Test Coverage
        run: python manage.py analyze_test_coverage --min-coverage 70

      - name: Migration Safety
        run: python manage.py check_migrations

      - name: HIPAA Compliance
        run: python manage.py check_hipaa_compliance --fail-on critical

      - name: Upload Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: agent-reports
          path: reports/
```

---

## Bypassing Hooks

**Use sparingly!** Only for emergency commits.

```bash
# Bypass all pre-commit hooks
git commit --no-verify -m "Emergency fix"

# Bypass all pre-push hooks
git push --no-verify
```

**When to bypass**:
- ✅ Emergency production hotfix
- ✅ Non-code commits (README updates)
- ❌ "I'll fix it later" (don't do this!)
- ❌ Convenience (hooks exist for a reason!)

---

## Configuration

### Customize Agent Behavior

```python
# upstream/settings/local.py

# Code Quality Auditor
CODE_QUALITY_AUDITOR = {
    'enabled': True,
    'block_on_critical': True,
    'excluded_paths': ['migrations/', 'tests/fixtures/'],
}

# Test Coverage Analyzer
TEST_COVERAGE_THRESHOLDS = {
    'overall': 75,
    'critical_paths': 100,  # PHI detection, auth, etc.
}

# HIPAA Compliance
HIPAA_COMPLIANCE_CHECKS = {
    'session_timeout': 1800,  # 30 minutes
    'require_audit_logging': True,
    'require_field_encryption': True,
}
```

---

## Troubleshooting

### "Hooks are too slow"

Enable fast mode for code quality auditor:

```bash
# .pre-commit-config.yaml
- id: code-quality-audit
  entry: python manage.py audit_code_quality --staged --fast
```

### "False positive PHI detection"

Add exceptions:

```python
# upstream/settings/local.py
PHI_DETECTION_EXCEPTIONS = [
    'blue cross',  # Payer name
    'medicare',    # Program name
]
```

### "Migration check blocking valid migration"

Review the risk assessment and add migration notes:

```python
# In migration file
class Migration(migrations.Migration):
    # SAFETY: Data backed up, rollback plan documented
    # TESTED: Staging database migration successful
```

### "Need to update agent logic"

Agents are in two places:
1. **Agent definitions**: `.agents/agents/*.md` (for Claude to understand)
2. **Command implementations**: `upstream/management/commands/*.py` (actual code)

Modify the command file to change behavior.

---

## Monitoring Agent Performance

### View Agent History

```bash
# SQL query
sqlite3 db.sqlite3 "SELECT agent_type, COUNT(*), AVG(findings_count)
FROM upstream_agent_run
WHERE status='completed'
GROUP BY agent_type;"
```

### Track False Positives

Mark findings as "ignored" if they're false positives:

```python
finding = Finding.objects.get(id=123)
finding.status = 'ignored'
finding.save()
```

### Agent Metrics

```python
# Average findings per agent type
from django.db.models import Avg
from upstream.models_agents import AgentRun

AgentRun.objects.values('agent_type').annotate(
    avg_findings=Avg('findings_count'),
    avg_critical=Avg('critical_count')
)
```

---

## Best Practices

### 1. Run Agents Locally Before Pushing

```bash
# Full check before important commits
./scripts/run_all_agents.sh
```

### 2. Fix Critical Issues First

Priority order:
1. ❌ Critical (PHI exposure, SQL injection) - Fix immediately
2. ⚠️  High (Missing indexes, no validation) - Fix same day
3. ℹ️  Medium (Missing docstrings) - Fix within week
4. 💡 Low (Style issues) - Batch fix during refactoring

### 3. Review Agent Reports Weekly

```bash
# Generate weekly compliance report
python manage.py check_hipaa_compliance --report reports/weekly_compliance.json
```

### 4. Update Agents as Codebase Grows

Agents learn from your patterns. Update detection rules as you discover new anti-patterns.

---

## Uninstalling

If you need to remove the agents:

```bash
# Remove pre-commit hooks
pre-commit uninstall
pre-commit uninstall --hook-type pre-push

# Remove agent database tables (optional)
# This will delete all agent history
# python manage.py migrate upstream zero
```

---

## Support

### Logs

Agent execution logs:
- Console output during execution
- Database: `AgentRun` records
- Files: `reports/` directory (if `--report` used)

### Common Issues

See troubleshooting section above or check:
- `.agents/agents/*.md` - Agent documentation
- `upstream/management/commands/*.py` - Implementation details

---

## Version History

- **2026-01-25**: Initial release with 5 agents
- Pre-commit integration
- Database tracking
- CI/CD examples

---

**Questions?** Check individual agent documentation in `.agents/agents/` or run:

```bash
python manage.py [agent_command] --help
```

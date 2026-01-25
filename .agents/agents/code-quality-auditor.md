# Code Quality Auditor Agent

**Agent Type**: code_quality
**Purpose**: Scan Django/React code for security issues, PHI exposure, linting failures
**Trigger Points**: pre-commit, pre-deploy, on-demand

---

## What This Agent Does

1. **PHI Detection**: Scans code, comments, test data for protected health information
2. **Security Issues**: Detects SQL injection risks, XSS vulnerabilities, insecure patterns
3. **Linting**: Runs Black, Flake8, and Django system checks
4. **Type Validation**: Checks for type errors and missing type hints (if using mypy)

---

## Scan Targets

### Python Files
- `upstream/**/*.py` - All Django app code
- `tests/**/*.py` - Test files
- `scripts/**/*.py` - Utility scripts

### JavaScript/React Files (when implemented)
- `frontend/**/*.{js,jsx,ts,tsx}`
- `upstream/static/**/*.js`

### Configuration Files
- `upstream/settings/**/*.py`
- `.env.example` (never `.env` - that's gitignored)

---

## Critical Issues (Block Commit)

These issues **must** be fixed before commit is allowed:

### 1. PHI in Code or Comments

```python
# ❌ CRITICAL
patient_name = "John Smith"  # Contains PHI
logger.info(f"Processing claim for {patient.name}")

# ✅ SAFE
claim_id = "CLM-001"
logger.info(f"Processing claim {claim_id} for customer {customer.id}")
```

### 2. SQL Injection Risk

```python
# ❌ CRITICAL
cursor.execute(f"SELECT * FROM claims WHERE payer = '{payer_name}'")

# ✅ SAFE
ClaimRecord.objects.filter(payer=payer_name)
```

### 3. Missing Customer Filter

```python
# ❌ CRITICAL - exposes all customers' data
claims = ClaimRecord.objects.all()

# ✅ SAFE - filtered by customer
claims = ClaimRecord.objects.filter(customer=request.user.customer)
```

### 4. Exposed Secret Keys

```python
# ❌ CRITICAL
SECRET_KEY = "django-insecure-hardcoded-key"

# ✅ SAFE
SECRET_KEY = os.getenv('SECRET_KEY')
```

---

## High Priority Issues (Warn)

These issues should be fixed but won't block commit:

### 1. Missing Indexes

```python
# ⚠️ HIGH
class ClaimRecord(models.Model):
    customer = models.ForeignKey(Customer)
    service_date = models.DateField()
    # Missing index!

# ✅ BETTER
class Meta:
    indexes = [
        models.Index(fields=['customer', 'service_date']),
    ]
```

### 2. No PHI Validation

```python
# ⚠️ HIGH
def create_payer(self, validated_data):
    # Missing PHI detection!
    return Payer.objects.create(**validated_data)

# ✅ BETTER
def create_payer(self, validated_data):
    has_phi, msg = detect_phi(validated_data['name'])
    if has_phi:
        raise ValidationError(msg)
    return Payer.objects.create(**validated_data)
```

### 3. Unprotected API Endpoint

```python
# ⚠️ HIGH
class ClaimViewSet(viewsets.ModelViewSet):
    # Missing permission classes!
    queryset = ClaimRecord.objects.all()

# ✅ BETTER
class ClaimViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsCustomerOwner]

    def get_queryset(self):
        return ClaimRecord.objects.filter(customer=self.request.user.customer)
```

---

## Medium Priority Issues (Info)

### 1. Missing Docstrings

```python
# ℹ️ MEDIUM
def complex_calculation(data):
    # Missing docstring
    return sum(data) / len(data)

# ✅ BETTER
def complex_calculation(data):
    """Calculate average of data points.

    Args:
        data: List of numeric values

    Returns:
        float: Average value
    """
    return sum(data) / len(data)
```

### 2. Overly Complex Function

```python
# ℹ️ MEDIUM - cyclomatic complexity > 10
def process_claim(claim):
    if claim.status == 'pending':
        if claim.payer == 'Blue Cross':
            if claim.amount > 1000:
                # ... 50 more lines
```

---

## How to Use

### Run Manually

```bash
# Scan entire codebase
python manage.py audit_code_quality

# Scan specific directory
python manage.py audit_code_quality --path upstream/

# Scan specific file
python manage.py audit_code_quality --file upstream/models.py

# Generate detailed report
python manage.py audit_code_quality --report reports/code_quality.json

# Fix auto-fixable issues
python manage.py audit_code_quality --fix
```

### Run via Pre-Commit Hook

Automatically runs on `git commit`:

```bash
# Install hooks
./scripts/install_hooks.sh

# Commit triggers audit
git commit -m "feat: Add new feature"
# → Code Quality Auditor runs
# → Blocks commit if critical issues found
```

### Run via CI/CD

```yaml
# .github/workflows/quality.yml
- name: Code Quality Audit
  run: |
    python manage.py audit_code_quality --fail-on critical
```

---

## Output Format

### Console Output

```
🔍 Code Quality Auditor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scanning 142 Python files...

❌ CRITICAL (3)
  upstream/views.py:45 - PHI in log statement
  upstream/api/views.py:123 - Missing customer filter
  upstream/settings/base.py:12 - Hardcoded secret key

⚠️  HIGH (7)
  upstream/models.py:89 - Missing database index
  upstream/serializers.py:34 - No PHI validation
  ...

ℹ️  MEDIUM (12)
  upstream/services/payer_drift.py:156 - Missing docstring
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 0 critical | ⚠️  7 high | ℹ️  12 medium

❌ COMMIT BLOCKED - Fix critical issues first
```

### Database Record

All findings stored in `Finding` model:

```python
Finding.objects.filter(
    agent_run__agent_type='code_quality',
    severity='critical',
    status='open'
)
```

### JSON Report

```json
{
  "agent_type": "code_quality",
  "timestamp": "2026-01-25T22:00:00Z",
  "files_scanned": 142,
  "findings": [
    {
      "severity": "critical",
      "category": "phi_exposure",
      "file": "upstream/views.py",
      "line": 45,
      "title": "PHI in log statement",
      "description": "Logger statement contains potential patient name",
      "code": "logger.info(f'Processing {patient.name}')",
      "recommendation": "Use patient ID or claim ID instead"
    }
  ],
  "summary": {
    "critical": 3,
    "high": 7,
    "medium": 12,
    "low": 0
  }
}
```

---

## Configuration

### `.pre-commit-config.yaml` Section

```yaml
- repo: local
  hooks:
    - id: code-quality-audit
      name: Code Quality Auditor
      entry: python manage.py audit_code_quality --fast
      language: system
      pass_filenames: false
      always_run: true
      stages: [commit]
```

### Settings Override

```python
# upstream/settings/local.py
CODE_QUALITY_AUDITOR = {
    'enabled': True,
    'block_on_critical': True,
    'block_on_high': False,
    'auto_fix': False,
    'excluded_paths': [
        'migrations/',
        'tests/fixtures/',
        '__pycache__/',
    ],
    'phi_detection': {
        'enabled': True,
        'check_comments': True,
        'check_test_data': True,
    },
    'linting': {
        'black': True,
        'flake8': True,
        'pylint': False,  # Too slow
    }
}
```

---

## Integration Points

### 1. Pre-Commit Hook
- Runs on every `git commit`
- Blocks commit if critical issues found
- Fast mode: scans only changed files

### 2. Pre-Deploy Gate
- Runs before production deployment
- Full scan of entire codebase
- Generates comprehensive report

### 3. CI/CD Pipeline
- Runs on every PR
- Posts findings as PR comments
- Fails build if critical issues

### 4. On-Demand
- Developers run manually
- Generates detailed reports
- Can auto-fix certain issues

---

## Metrics Tracked

1. **Critical Issues Over Time**: Track if codebase is improving
2. **PHI Exposure Incidents**: Count and trend
3. **Security Vulnerability Count**: By severity
4. **Linting Compliance**: % of files passing
5. **Time to Fix**: How long issues stay open

---

## Next Steps After Findings

### Critical Issues
1. Fix immediately - commit is blocked
2. Cannot proceed until resolved
3. Document fix in finding status

### High Priority
1. Create GitHub issue
2. Fix within 1 week
3. Link finding to issue

### Medium/Low
1. Batch fix during refactoring
2. Track in backlog
3. Not urgent

---

## Troubleshooting

### "False positive PHI detection"

If the agent incorrectly flags something as PHI:

```python
# Add to PHI_DETECTION_EXCEPTIONS in settings
PHI_DETECTION_EXCEPTIONS = [
    'blue cross',  # Payer name, not patient
    'medicare',    # Program name
]
```

### "Too slow for pre-commit"

Enable fast mode (scans only changed files):

```bash
python manage.py audit_code_quality --fast --staged
```

### "Want to skip for emergency commit"

```bash
git commit --no-verify -m "Emergency fix"
# Use sparingly!
```

---

## Files Modified by This Agent

- **None** - This agent is read-only
- It only scans and reports
- Use `--fix` flag to auto-fix linting issues

---

## Related Agents

- **HIPAA Compliance Monitor**: Overlaps on PHI detection
- **Database Performance Optimizer**: May suggest index additions
- **Migration Safety Checker**: Validates migration code quality

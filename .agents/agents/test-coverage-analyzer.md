# Test Coverage Analyzer Agent

**Agent Type**: test_coverage
**Purpose**: Identify untested code paths and coverage gaps
**Trigger Points**: pre-commit (warns only), on-demand

---

## What This Agent Does

1. **Coverage Analysis**: Runs pytest with coverage tracking
2. **Untested Code Detection**: Identifies functions with 0% coverage
3. **Critical Path Testing**: Ensures core features have >80% coverage
4. **Test Quality**: Checks for meaningful assertions

---

## Critical Paths Requiring 100% Coverage

- `upstream/utils.py:detect_phi()` - PHI detection
- `upstream/services/payer_drift.py` - Core drift algorithm
- `upstream/api/permissions.py` - Multi-tenant isolation
- `upstream/middleware.py` - Security middleware

---

## Usage

```bash
# Run full coverage analysis
python manage.py analyze_test_coverage

# Check specific module
python manage.py analyze_test_coverage --module upstream.services

# Generate HTML report
python manage.py analyze_test_coverage --html

# Fail if coverage drops below threshold
python manage.py analyze_test_coverage --min-coverage 75
```

---

## Output

```
🔍 Test Coverage Analyzer
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Coverage: 78%

❌ CRITICAL PATHS < 100%
  upstream/utils.py:detect_phi - 85% coverage

⚠️  LOW COVERAGE MODULES
  upstream/services/payer_drift.py - 62%
  upstream/api/serializers.py - 71%

ℹ️  UNTESTED FUNCTIONS (12)
  upstream/views/metrics.py:calculate_stats - 0%
  upstream/utils.py:scrub_phi - 0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendations: Add 23 test cases
```

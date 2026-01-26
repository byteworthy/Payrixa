# Technical Debt Triage Analysis
**Date**: 2026-01-26
**Analyst**: Claude Sonnet 4.5

## Triage Criteria
- ✅ **PROMOTE TO HIGH**: Real business/security/reliability impact, HIPAA risk, or production incidents likely
- 🟡 **KEEP MEDIUM**: Important but system functions without it
- ⬇️ **DEMOTE TO LOW**: Nice to have, theoretical concern, or premature optimization
- ❌ **REJECT/DEFER**: Not applicable, over-engineering, or v2.0 feature

---

## MEDIUM Priority Issues (31 total)

### Database (4 issues)

**No transaction isolation for concurrent drift**
- 🟡 **KEEP MEDIUM** - Race conditions possible but rare in practice with low concurrency
- Impact: Data integrity edge case
- Effort: Medium (add transaction.atomic with select_for_update)
- Risk: Low (drift detection runs infrequently)

**Inefficient count queries**
- ⬇️ **DEMOTE TO LOW** - System is already fast after HIGH-16 optimization
- Impact: Marginal performance gain
- Effort: Small-Medium
- Note: Only optimize if profiling shows actual bottleneck

**Missing covering indexes**
- ⬇️ **DEMOTE TO LOW** - Premature optimization without specific slow queries identified
- Impact: Theoretical
- Effort: Medium (analyze query patterns first)
- Note: Add when profiling identifies specific slow queries

**No database CHECK constraints**
- 🟡 **KEEP MEDIUM** - Business rule enforcement in application layer works but DB constraints add defense
- Impact: Data quality safety net
- Effort: Small (add constraints like positive amounts, valid status enums)

---

### Testing (4 issues)

**No integration tests for webhooks**
- 🟡 **KEEP MEDIUM** - Webhook functionality exists but lacks end-to-end testing
- Impact: Risk of regression breaking webhook integrations
- Effort: Medium (test webhook delivery, retries, signatures)

**No performance/load tests**
- ⬇️ **DEMOTE TO LOW** - Nice to have but not blocking production
- Impact: Helps capacity planning
- Effort: Large (need test infrastructure, load scenarios)
- Note: Defer until scaling issues appear

**Disabled transaction rollback test**
- ✅ **PROMOTE TO HIGH** - Test is commented out, indicates potential transaction integrity issue
- Impact: HIPAA audit trail risk if transactions aren't atomic
- Effort: Small (investigate why disabled, fix root cause)
- Risk: HIGH if audit trail can be corrupted

**Product stub tests (ContractIQ, AuthSignal)**
- ⬇️ **DEMOTE TO LOW** - Products don't exist yet, tests can wait until implementation
- Impact: None (no code to test)
- Effort: N/A

---

### Architecture (7 issues)

**Business logic in views**
- 🟡 **KEEP MEDIUM** - Code organization issue, not a functional bug
- Impact: Maintainability, testability
- Effort: Large (refactor into service layer)
- Note: Refactor incrementally as you touch code

**Direct ORM queries in views**
- 🟡 **KEEP MEDIUM** - Same as above, coupling issue
- Impact: Harder to test, harder to reuse
- Effort: Large
- Note: Combine with above refactor

**Missing drift detection abstraction**
- ⬇️ **DEMOTE TO LOW** - Code duplication but each product has unique needs
- Impact: DRY violation but products work
- Effort: Large (create shared base, refactor 3 products)
- Note: Defer until you have 4+ drift detection implementations

**Alert service coupled to products**
- 🟡 **KEEP MEDIUM** - Tight coupling makes adding new products harder
- Impact: Feature velocity
- Effort: Medium (extract interface, dependency injection)

**Alert suppression uses DB queries in hot path**
- ✅ **PROMOTE TO HIGH** - Performance risk if alert volume increases
- Impact: Could slow down dashboard under load
- Effort: Small (add Redis caching for suppression checks)
- Risk: MEDIUM performance degradation at scale

**Missing interface segregation**
- ❌ **REJECT** - Theoretical design pattern, no actual problem described
- Impact: None
- Effort: Unknown
- Note: Too vague to action

**Duplicate drift/delay logic**
- ⬇️ **DEMOTE TO LOW** - Same as "Missing drift detection abstraction"
- Impact: Code smell but functional
- Effort: Large

---

### API Design (7 issues)

**Missing pagination on custom actions**
- ✅ **PROMOTE TO HIGH** - Risk of OOM if endpoints return unbounded results
- Impact: API reliability, customer experience
- Effort: Small (add PageNumberPagination to specific actions)
- Risk: MEDIUM if large customers hit unpaginated endpoints

**No SearchFilter/DjangoFilterBackend**
- 🟡 **KEEP MEDIUM** - UX improvement, filtering works via query params
- Impact: API usability
- Effort: Small (add django-filter to settings)

**Inconsistent error formats**
- ⬇️ **DEMOTE TO LOW** - Errors work, just not perfectly consistent
- Impact: Developer experience
- Effort: Medium (standardize exception handler)

**No HATEOAS links**
- ❌ **REJECT** - Over-engineering for internal API
- Impact: None (clients know endpoints)
- Effort: Large
- Note: Only needed for public APIs with unknown clients

**Missing ETag support**
- ⬇️ **DEMOTE TO LOW** - HTTP caching optimization
- Impact: Bandwidth savings
- Effort: Small (add ConditionalGetMiddleware)
- Note: Add if mobile app bandwidth is issue

**No OpenAPI parameter docs**
- ⬇️ **DEMOTE TO LOW** - Docs exist via drf-spectacular, just incomplete
- Impact: Developer experience
- Effort: Small (add docstrings to serializers)

**Webhook lacks payload size validation**
- ✅ **PROMOTE TO HIGH** - DoS risk if malicious client sends huge payload
- Impact: Security, resource exhaustion
- Effort: Small (add request size limit in middleware/settings)
- Risk: MEDIUM security exposure

---

### DevOps (9 issues)

**Linting doesn't block CI**
- ✅ **PROMOTE TO HIGH** - Code quality issues can be merged
- Impact: Tech debt accumulation
- Effort: Small (remove || true from GitHub Actions)
- Risk: LOW but easy fix

**No code coverage enforcement**
- 🟡 **KEEP MEDIUM** - Prevents test coverage from regressing
- Impact: Test quality
- Effort: Small (add coverage threshold to CI)

**Missing Redis/PostgreSQL in CI**
- ✅ **PROMOTE TO HIGH** - Tests don't match production environment
- Impact: False positives/negatives in CI
- Effort: Small (add services to GitHub Actions)
- Risk: MEDIUM (Redis-dependent code not tested)

**No secrets scanning**
- 🟡 **KEEP MEDIUM** - Prevents accidental secret commits
- Impact: Security hygiene
- Effort: Small (add truffleHog/git-secrets to pre-commit)

**Missing smoke tests post-deployment**
- ✅ **PROMOTE TO HIGH** - Deployments succeed even if app is broken
- Impact: Production reliability
- Effort: Small (already have scripts/smoke_test.py, just need to run it)
- Risk: MEDIUM (bad deploys could go unnoticed)

**No monitoring/APM enforcement**
- 🟡 **KEEP MEDIUM** - Monitoring exists (Prometheus mentioned) but not enforced
- Impact: Observability
- Effort: Small (document APM requirements)

**Prometheus metrics not exposed**
- 🟡 **KEEP MEDIUM** - Needed for production monitoring
- Impact: Can't monitor system health
- Effort: Small (already have django-prometheus installed, just expose /metrics)

**No log retention policy**
- ⬇️ **DEMOTE TO LOW** - Cloud logging handles this
- Impact: Compliance (minor)
- Effort: Small (document policy)

**No Celery monitoring**
- 🟡 **KEEP MEDIUM** - If using Celery, need to monitor task queue
- Impact: Background job reliability
- Effort: Small (add Flower or similar)
- Note: Only if Celery is in production

---

## LOW Priority Issues (11 total)

**Missing password reset flow**
- 🟡 **PROMOTE TO MEDIUM** - Core auth feature if users have passwords
- Impact: User experience
- Effort: Medium (email flow, token generation, expiry)
- Note: Only if password auth is enabled (may use SSO only)

**Session fixation risk in logout**
- ⬇️ **KEEP LOW** - Using JWT (stateless), session fixation doesn't apply
- Impact: None (JWT doesn't use sessions)
- Effort: N/A

**Sequential IDs for alerts**
- ❌ **REJECT** - Theoretical security concern (info disclosure)
- Impact: Minimal (internal system)
- Effort: Medium (switch to UUIDs)
- Note: Only matters for public-facing systems

**Generic error logging issues**
- ⬇️ **KEEP LOW** - Logging works, could be better structured
- Impact: Debugging efficiency
- Effort: Medium (add structured logging)

**Property-based model computations**
- ⬇️ **KEEP LOW** - Performance micro-optimization
- Impact: Marginal
- Effort: Small (annotate queries instead of properties)
- Note: Only optimize hot paths

**Serializer optimization opportunities**
- ⬇️ **KEEP LOW** - Already optimized (PERF-20)
- Impact: Marginal
- Effort: Small

**Missing RBAC cross-role tests**
- 🟡 **PROMOTE TO MEDIUM** - Security boundary testing
- Impact: Permission bypass risk
- Effort: Small (test user can't access admin endpoints)

**PHI detection in view layer**
- ⬇️ **KEEP LOW** - HIPAA compliance feature
- Impact: Audit trail for PHI access
- Effort: Medium (add decorator to track PHI access)
- Note: May be required for BAA compliance

**No API versioning headers**
- ❌ **REJECT** - Over-engineering for internal API
- Impact: None
- Effort: Medium
- Note: Add if building public API

**Missing deployment notifications**
- ⬇️ **KEEP LOW** - Nice to have (Slack notifications)
- Impact: Team awareness
- Effort: Small (add webhook to Cloud Build)

**Structured logging not enabled**
- 🟡 **PROMOTE TO MEDIUM** - Needed for log aggregation/search
- Impact: Debugging efficiency
- Effort: Small (configure structlog or python-json-logger)

---

## TRIAGE SUMMARY

### ✅ PROMOTE TO HIGH (11 issues)
1. **Disabled transaction rollback test** - HIPAA audit trail risk
2. **Alert suppression uses DB queries in hot path** - Performance at scale
3. **Missing pagination on custom actions** - OOM risk
4. **Webhook lacks payload size validation** - DoS risk
5. **Linting doesn't block CI** - Code quality gate
6. **Missing Redis/PostgreSQL in CI** - Test environment mismatch
7. **Missing smoke tests post-deployment** - Deployment reliability
8. **Missing tests for AlertService** - Core business logic untested
9. **No secrets scanning** - Accidental secret exposure
10. **Missing password reset flow** - Core auth feature (if applicable)
11. **Missing RBAC cross-role tests** - Permission bypass risk

### 🟡 KEEP MEDIUM (13 issues)
- No transaction isolation for concurrent drift
- No database CHECK constraints
- No integration tests for webhooks
- Business logic in views
- Direct ORM queries in views
- Alert service coupled to products
- No SearchFilter/DjangoFilterBackend
- No code coverage enforcement
- No monitoring/APM enforcement
- Prometheus metrics not exposed
- No Celery monitoring
- Structured logging not enabled
- No secrets scanning (if not promoted)

### ⬇️ DEMOTE TO LOW (13 issues)
- Inefficient count queries
- Missing covering indexes
- No performance/load tests
- Product stub tests
- Missing drift detection abstraction
- Duplicate drift/delay logic
- Inconsistent error formats
- Missing ETag support
- No OpenAPI parameter docs
- No log retention policy
- Generic error logging issues
- Property-based model computations
- Serializer optimization opportunities

### ❌ REJECT/DEFER (6 issues)
- Missing interface segregation (too vague)
- No HATEOAS links (over-engineering)
- Sequential IDs for alerts (not applicable)
- Session fixation risk (using JWT)
- No API versioning headers (not needed)
- PHI detection in view layer (defer to BAA requirements)

---

## FINAL RECOMMENDATION

**Tonight's Goal: Fix the 11 promoted HIGH priority issues**

**Total effort estimate: 6-8 hours** (assuming parallel work on small items)

**Order of execution (by effort and dependency):**
1. ✅ Linting doesn't block CI (5 min)
2. ✅ Missing Redis/PostgreSQL in CI (15 min)
3. ✅ Webhook lacks payload size validation (20 min)
4. ✅ Missing pagination on custom actions (30 min)
5. ✅ Missing smoke tests post-deployment (30 min)
6. ✅ Disabled transaction rollback test (1 hour - investigate + fix)
7. ✅ Missing tests for AlertService (2 hours)
8. ✅ Alert suppression uses DB queries in hot path (1 hour - add Redis cache)
9. ✅ Missing RBAC cross-role tests (1 hour)
10. ✅ No secrets scanning (30 min - add pre-commit hook)
11. ⏳ Missing password reset flow (2-3 hours - skip if using SSO only)

**After these 11 are done:**
- Phase 1: 10/10 (100%) ✅
- Phase 2 HIGH: 33/33 (100%) ✅
- **SYSTEM IS PRODUCTION-READY** 🎉

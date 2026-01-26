# Using Ralph for Phases 3-5

## Overview

Phases 3-5 have been structured as Ralph PRDs for autonomous execution. Each phase contains context-sized user stories that can be implemented independently with quality gates.

## Phase Structure

### Phase 3: OpenAPI Documentation & Error Standardization
**Location**: `.planning/phases/03-openapi-documentation-and-error-standardization/ralph-prd.json`
**Stories**: 4 user stories
- Custom exception handler for standardized errors
- @extend_schema annotations on all ViewSet actions
- OpenAPI schema generation and verification
- Comprehensive error handling tests

**Quality Gates**:
- `python manage.py check`
- `python manage.py test upstream.tests_api -v 2`
- `python manage.py spectacular --validate`

### Phase 4: Webhook & RBAC Testing
**Location**: `.planning/phases/04-webhook-and-rbac-testing/ralph-prd.json`
**Stories**: 4 user stories
- Webhook test infrastructure with mock HTTP server
- Webhook delivery and retry logic tests
- RBAC test suite setup (superuser, customer admin, regular user)
- Customer isolation tests across all endpoints

**Quality Gates**:
- `python manage.py check`
- `python manage.py test upstream.tests_webhooks -v 2`
- `python manage.py test upstream.tests_rbac -v 2`

### Phase 5: Performance Testing & Rollback Fix
**Location**: `.planning/phases/05-performance-testing-and-rollback-fix/ralph-prd.json`
**Stories**: 4 user stories
- Locust performance test suite
- Load testing and bottleneck identification
- CI integration with SLA thresholds
- Deployment rollback test fix

**Quality Gates**:
- `python manage.py check`
- `locust -f upstream/tests_performance.py --headless -u 10 -r 2 -t 30s`
- `python -m pytest .github/workflows/test_rollback.py -v`

## Usage Options

### Option 1: Use Ralph Autonomous Loop (Recommended)

If Ralph is installed:

```bash
# Phase 3
cd /workspaces/codespaces-django
cp .planning/phases/03-openapi-documentation-and-error-standardization/ralph-prd.json prd.json
./scripts/ralph/ralph.sh --tool claude 10

# Phase 4 (after Phase 3 completes)
cp .planning/phases/04-webhook-and-rbac-testing/ralph-prd.json prd.json
./scripts/ralph/ralph.sh --tool claude 10

# Phase 5 (after Phase 4 completes)
cp .planning/phases/05-performance-testing-and-rollback-fix/ralph-prd.json prd.json
./scripts/ralph/ralph.sh --tool claude 10
```

Ralph will:
- Read each user story sequentially
- Implement the story
- Run quality gates
- Commit on success
- Mark story as `"passes": true`
- Continue to next story

### Option 2: Use GSD Workflow (Current Approach)

Continue with GSD plan/execute cycle:

```bash
# After Phase 2 completes
/gsd:plan-phase 3
/gsd:execute-phase 3

/gsd:plan-phase 4
/gsd:execute-phase 4

/gsd:plan-phase 5
/gsd:execute-phase 5
```

The Ralph PRDs serve as detailed story breakdowns that GSD can use for planning.

### Option 3: Hybrid Approach

Use GSD for planning, Ralph PRDs as reference:

1. Run `/gsd:plan-phase 3`
2. GSD planner reads `ralph-prd.json` for story ideas
3. Creates PLAN.md files using story structure
4. Execute with `/gsd:execute-phase 3`

## Story Sizing

All stories are sized for single context windows (~15-20 minutes each):

✓ **Right-sized examples:**
- "Create custom exception handler" (1 file, clear implementation)
- "Add @extend_schema to ViewSets" (modify existing file, repetitive pattern)
- "Implement webhook retry tests" (1 test class, mock infrastructure)

✗ **Too large:**
- "Build entire error handling system"
- "Complete all API documentation"

## Quality Gate Strategy

Each phase has specific quality gates that must pass:

**Phase 3**: Django check + API tests + OpenAPI validation
**Phase 4**: Django check + Webhook tests + RBAC tests
**Phase 5**: Django check + Locust load tests + Rollback tests

Stories only marked complete when all quality gates pass.

## Monitoring Progress

```bash
# Check completion status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# Count remaining stories
cat prd.json | jq '[.userStories[] | select(.passes == false)] | length'

# View recent learnings (if using Ralph)
tail -20 progress.txt
```

## Integration with GSD

The Ralph PRDs complement GSD by:
- **Pre-planned stories**: No need for research phase
- **Clear acceptance criteria**: Verifier knows what to check
- **Quality gates**: Automated verification
- **Context sizing**: Stories fit in execution context

GSD can consume these PRDs during planning phase to generate PLAN.md files.

## Next Steps

1. **Wait for Phase 2 completion** (plan 02-02 currently executing)
2. **Choose execution strategy**: Ralph autonomous loop or GSD workflow
3. **Phase 3**: Run with chosen approach
4. **Iterate**: Each phase builds on previous

---

**Note**: Ralph PRDs are living documents. Update `"passes": true` as stories complete, add learnings to `progress.txt`, update `AGENTS.md` with discovered patterns.

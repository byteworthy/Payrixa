---
phase: quick-013
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - upstream/settings/prod.py
  - upstream/settings/dev.py
  - upstream/settings/test.py
autonomous: true

user_setup:
  - service: sentry
    why: "Error tracking and performance monitoring"
    env_vars:
      - name: SENTRY_DSN
        source: "Sentry Dashboard -> Settings -> Projects -> [project] -> Client Keys (DSN)"
      - name: SENTRY_RELEASE
        source: "Set via CI/CD or manually (e.g., git commit SHA)"
      - name: SENTRY_ENVIRONMENT
        source: "Set to 'production', 'staging', 'development', etc."

must_haves:
  truths:
    - "Sentry captures errors in production when SENTRY_DSN is set"
    - "Sentry includes environment tags for filtering"
    - "Sentry performance monitoring is enabled with sample rate"
    - "Development and test environments can optionally use Sentry"
  artifacts:
    - path: "upstream/settings/prod.py"
      provides: "Enhanced Sentry config with environment tags"
      contains: "tags="
    - path: "upstream/settings/dev.py"
      provides: "Optional Sentry config for development"
      contains: "SENTRY_DSN"
    - path: "upstream/settings/test.py"
      provides: "Optional Sentry config for testing"
      contains: "SENTRY_DSN"
  key_links:
    - from: "upstream/settings/prod.py"
      to: "sentry_sdk.init()"
      via: "initialization with environment tags"
      pattern: "tags=.*ENVIRONMENT"
---

<objective>
Enhance Sentry error tracking integration with environment tags, improved documentation, and consistent configuration across all Django settings files.

Purpose: Provide comprehensive error tracking with proper environment filtering for production deployments while maintaining development parity.
Output: Updated settings files with standardized Sentry configuration across environments.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Sentry is already installed (sentry-sdk[django]~=1.40.0) with basic configuration in prod.py.
Current implementation:
- Only configured in prod.py (not in dev.py or test.py)
- Missing environment tags for better filtering
- Performance monitoring enabled but could use better documentation
- PHI scrubbing already implemented via filter_phi_from_errors()

This task enhances the existing integration without changing the core PHI filtering logic.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Enhance production Sentry configuration</name>
  <files>upstream/settings/prod.py</files>
  <action>
Update the Sentry initialization in upstream/settings/prod.py (lines 254-275) to:

1. Add environment tags for better filtering:
   ```python
   tags={
       "environment": config("ENVIRONMENT", default="production"),
       "deployment": config("SENTRY_RELEASE", default="unknown"),
   }
   ```

2. Improve inline documentation for traces_sample_rate:
   - Add comment explaining that 0.1 = 10% of transactions
   - Note that this can be adjusted based on volume/budget

3. Add comment about send_default_pii=False explaining it's for HIPAA compliance

4. Keep all existing configuration (integrations, before_send filter, etc.)

Do NOT:
- Change the filter_phi_from_errors() function (already handles PHI scrubbing)
- Modify the DSN/environment/release config variables
- Change the integrations list (Django, Celery, Redis)
  </action>
  <verify>
grep -A 5 "tags=" upstream/settings/prod.py shows environment tags
grep "10% of transactions" upstream/settings/prod.py shows improved documentation
  </verify>
  <done>
Production settings include environment tags in Sentry init, improved comments explain traces_sample_rate and send_default_pii settings
  </done>
</task>

<task type="auto">
  <name>Task 2: Add optional Sentry configuration to dev and test settings</name>
  <files>upstream/settings/dev.py, upstream/settings/test.py</files>
  <action>
Add optional Sentry configuration to both dev.py and test.py (after the LOGGING section):

```python
# =============================================================================
# ERROR TRACKING (Sentry) - Optional for development/testing
# =============================================================================

SENTRY_DSN = config("SENTRY_DSN", default=None)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=config("ENVIRONMENT", default="development"),  # or "test" for test.py
        # Lower sample rate for dev/test (1% to reduce noise)
        traces_sample_rate=0.01,
        # Enable debug mode to see what Sentry is capturing
        debug=True,
        send_default_pii=False,
        release=config("SENTRY_RELEASE", default=None),
        tags={
            "environment": config("ENVIRONMENT", default="development"),  # or "test"
        },
    )
```

Key differences from production:
- No Celery/Redis integrations (simpler setup)
- Lower traces_sample_rate (0.01 = 1%)
- debug=True for visibility
- No before_send filter (dev/test don't have real PHI)
- Default environment is "development" for dev.py, "test" for test.py

Add this section after the LOGGING configuration in both files.
  </action>
  <verify>
grep -c "SENTRY_DSN" upstream/settings/dev.py returns 1
grep -c "SENTRY_DSN" upstream/settings/test.py returns 1
grep "traces_sample_rate=0.01" upstream/settings/dev.py shows lower sample rate
grep "debug=True" upstream/settings/dev.py shows debug mode enabled
  </verify>
  <done>
Both dev.py and test.py have optional Sentry configuration with appropriate defaults for non-production environments
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify configuration and update documentation</name>
  <files>.env.production.example</files>
  <action>
Verify the .env.production.example already documents Sentry variables (lines 151-165).

If it needs updates, add clarifying comments:
- SENTRY_DSN: Explain how to get it (Project Settings -> Client Keys)
- SENTRY_RELEASE: Recommend using git commit SHA
- ENVIRONMENT: List valid values (production, staging, development)

Check that the file already has proper Sentry documentation. If documentation is already clear and complete, no changes needed.

Run validation:
```bash
python -c "
import sys
sys.path.insert(0, '.')
from upstream.settings import prod
print('✓ Production settings import successfully')
if hasattr(prod, 'SENTRY_DSN'):
    print('✓ Sentry configuration present')
"
```
  </action>
  <verify>
python validation command exits with code 0
grep "SENTRY_DSN" .env.production.example shows documentation exists
  </verify>
  <done>
Settings files import without errors, Sentry configuration is properly documented in example env file
  </done>
</task>

</tasks>

<verification>
After completion:

1. Settings validation:
   ```bash
   python manage.py check --settings=upstream.settings.prod
   python manage.py check --settings=upstream.settings.dev
   python manage.py check --settings=upstream.settings.test
   ```

2. Sentry initialization test (optional, requires SENTRY_DSN):
   ```python
   # In Django shell with SENTRY_DSN set:
   from django.conf import settings
   import sentry_sdk
   sentry_sdk.capture_message("Test message from Django")
   ```

3. Configuration completeness:
   - Production config has environment tags
   - Dev/test configs have optional Sentry with lower sample rates
   - All configs maintain HIPAA compliance (send_default_pii=False)
</verification>

<success_criteria>
1. All three settings files (prod, dev, test) have Sentry configuration
2. Production config includes environment tags for filtering
3. Dev/test configs have lower trace sample rates (1% vs 10%)
4. Settings files import without errors
5. Documentation in .env.production.example remains clear
6. No changes to PHI filtering logic (filter_phi_from_errors unchanged)
</success_criteria>

<output>
After completion, create `.planning/quick/013-add-sentry-error-tracking-integration-in/013-SUMMARY.md`
</output>

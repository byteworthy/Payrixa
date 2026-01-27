---
quick_task: 021
type: execute
wave: 1
depends_on: []
files_modified:
  - upstream/settings/base.py
  - upstream/tests/test_cors_config.py
autonomous: true

must_haves:
  truths:
    - "CORS_EXPOSE_HEADERS configured to expose custom API headers to frontend clients"
    - "JavaScript fetch() can access API-Version, X-Request-Id, X-Request-Duration-Ms, and ETag headers"
    - "Tests verify CORS_EXPOSE_HEADERS configuration exists and contains required headers"
  artifacts:
    - path: "upstream/settings/base.py"
      provides: "CORS_EXPOSE_HEADERS configuration"
      contains: "CORS_EXPOSE_HEADERS"
    - path: "upstream/tests/test_cors_config.py"
      provides: "CORS configuration tests"
      exports: ["TestCorsConfiguration"]
  key_links:
    - from: "upstream/settings/base.py"
      to: "django-cors-headers middleware"
      via: "CORS_EXPOSE_HEADERS setting"
      pattern: "CORS_EXPOSE_HEADERS.*=.*\\["
---

<objective>
Configure CORS_EXPOSE_HEADERS to allow JavaScript clients to access custom API headers added by middleware.

Purpose: Current CORS configuration only sets CORS_ALLOWED_ORIGINS and CORS_ALLOW_CREDENTIALS, but does not expose custom headers added by middleware (API-Version from quick-007, X-Request-Id, X-Request-Duration-Ms). This prevents JavaScript clients from accessing these headers via fetch() or XMLHttpRequest. Proper CORS_EXPOSE_HEADERS configuration is essential for frontend observability and API versioning.

Output: Complete CORS configuration with CORS_EXPOSE_HEADERS and validation tests ensuring proper cross-origin header exposure.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/STATE.md

## Current CORS Configuration

File: `upstream/settings/base.py` (lines 200-207)

```python
# =============================================================================
# CORS SETTINGS
# =============================================================================

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS", default="http://localhost:3000,http://127.0.0.1:3000"
).split(",")

CORS_ALLOW_CREDENTIALS = True
```

## Custom Headers Added by Middleware

From `upstream/middleware.py`:

1. **API-Version**: Added by ApiVersionMiddleware (line 626) - current version "1.0.0"
2. **X-Request-Id**: Added by RequestIdMiddleware (line 179) - for request tracing
3. **X-Request-Duration-Ms**: Added by RequestTimingMiddleware (line 341) - for performance monitoring
4. **ETag**: Added by Django's ConditionalGetMiddleware (quick-010) - for caching

## Why CORS_EXPOSE_HEADERS Matters

**CORS_EXPOSE_HEADERS**: Required to allow JavaScript clients to read custom headers via `response.headers.get()`. Without this, headers are sent but inaccessible to client code due to CORS restrictions.

Per django-cors-headers docs, CORS_EXPOSE_HEADERS defaults to empty list, so custom headers are hidden from cross-origin requests.

## Related Quick Tasks

- quick-007: Added API versioning headers via ApiVersionMiddleware
- quick-010: Added ETag support via ConditionalGetMiddleware
- quick-014: Added security headers via SecurityHeadersMiddleware
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add CORS_EXPOSE_HEADERS configuration</name>
  <files>upstream/settings/base.py</files>
  <action>
Add CORS_EXPOSE_HEADERS configuration after CORS_ALLOW_CREDENTIALS (line 207):

```python
# Expose custom headers to cross-origin JavaScript clients
# Without this, headers are sent but inaccessible via response.headers.get()
CORS_EXPOSE_HEADERS = [
    "API-Version",          # From ApiVersionMiddleware - allows clients to track API version
    "X-Request-Id",         # From RequestIdMiddleware - enables request tracing
    "X-Request-Duration-Ms", # From RequestTimingMiddleware - client-side performance monitoring
    "ETag",                 # From ConditionalGetMiddleware - enables conditional requests
    "Last-Modified",        # Standard caching header - may be present on some responses
    "Cache-Control",        # Standard caching header - allows clients to read cache directives
]
```

**Rationale:**
- API-Version: Required for clients to implement version-based feature detection
- X-Request-Id: Required for distributed tracing and debugging (correlating frontend logs with backend)
- X-Request-Duration-Ms: Required for client-side performance monitoring and alerting
- ETag/Last-Modified/Cache-Control: Required for conditional request logic (If-None-Match, If-Modified-Since)

**Do NOT include security headers** (X-Content-Type-Options, X-XSS-Protection, Strict-Transport-Security) in CORS_EXPOSE_HEADERS. These headers are for browser security, not client application logic.

Preserve existing CORS_ALLOWED_ORIGINS and CORS_ALLOW_CREDENTIALS configuration.
  </action>
  <verify>
grep -A 8 "CORS_EXPOSE_HEADERS" upstream/settings/base.py
  </verify>
  <done>
Acceptance criteria:
- CORS_EXPOSE_HEADERS list added with 6 headers
- Configuration placed after CORS_ALLOW_CREDENTIALS
- Comments explain purpose of each header
  </done>
</task>

<task type="auto">
  <name>Task 2: Add CORS configuration tests</name>
  <files>upstream/tests/test_cors_config.py</files>
  <action>
Create new test file `upstream/tests/test_cors_config.py`:

```python
"""
Tests for CORS configuration.

Verifies that CORS settings are properly configured to expose custom headers
to JavaScript clients for API versioning, request tracing, and caching.
"""
from django.test import TestCase, override_settings
from django.conf import settings
from django.test.client import Client


class TestCorsConfiguration(TestCase):
    """Test CORS configuration for custom header exposure."""

    def test_cors_expose_headers_configured(self):
        """Verify CORS_EXPOSE_HEADERS is configured in settings."""
        # CORS_EXPOSE_HEADERS should exist
        self.assertTrue(hasattr(settings, "CORS_EXPOSE_HEADERS"))
        self.assertIsInstance(settings.CORS_EXPOSE_HEADERS, list)
        self.assertGreater(len(settings.CORS_EXPOSE_HEADERS), 0)

    def test_api_version_header_exposed(self):
        """
        Verify API-Version header is exposed for client version detection.

        Without this, JavaScript clients cannot read the API-Version header
        via response.headers.get('API-Version') in fetch() calls.
        """
        self.assertIn("API-Version", settings.CORS_EXPOSE_HEADERS)

    def test_request_id_header_exposed(self):
        """
        Verify X-Request-Id header is exposed for distributed tracing.

        This enables frontend apps to correlate client-side errors with
        backend logs using the request ID.
        """
        self.assertIn("X-Request-Id", settings.CORS_EXPOSE_HEADERS)

    def test_request_duration_header_exposed(self):
        """
        Verify X-Request-Duration-Ms header is exposed for performance monitoring.

        This allows frontend apps to track backend response times and set up
        client-side alerting for slow requests.
        """
        self.assertIn("X-Request-Duration-Ms", settings.CORS_EXPOSE_HEADERS)

    def test_etag_header_exposed(self):
        """
        Verify ETag header is exposed for conditional request logic.

        Required for clients to implement efficient caching with If-None-Match.
        """
        self.assertIn("ETag", settings.CORS_EXPOSE_HEADERS)

    def test_security_headers_not_exposed(self):
        """
        Verify security headers are NOT in CORS_EXPOSE_HEADERS.

        Security headers (X-Content-Type-Options, X-XSS-Protection, etc.) are
        for browser security policy, not application logic. They should not be
        exposed to JavaScript.
        """
        # These should NOT be in CORS_EXPOSE_HEADERS
        self.assertNotIn("X-Content-Type-Options", settings.CORS_EXPOSE_HEADERS)
        self.assertNotIn("X-XSS-Protection", settings.CORS_EXPOSE_HEADERS)
        self.assertNotIn("Strict-Transport-Security", settings.CORS_EXPOSE_HEADERS)

    @override_settings(CORS_ALLOWED_ORIGINS=["http://testclient.example.com"])
    def test_cors_headers_present_in_response(self):
        """
        Integration test: Verify CORS headers are present in actual responses.

        This tests the full CORS middleware integration, not just settings.
        """
        client = Client()
        response = client.get(
            "/api/v1/health/",
            HTTP_ORIGIN="http://testclient.example.com"
        )

        # CORS middleware should add Access-Control-Expose-Headers
        self.assertIn("Access-Control-Expose-Headers", response)
```

**Test coverage:**
1. CORS_EXPOSE_HEADERS exists and is non-empty
2. Required custom headers are exposed (API-Version, X-Request-Id, X-Request-Duration-Ms, ETag)
3. Security headers are NOT exposed (defense against misconfiguration)
4. Integration test verifies CORS middleware applies settings

Run tests to verify configuration:

```bash
cd /workspaces/codespaces-django
python manage.py test upstream.tests.test_cors_config -v 2
```
  </action>
  <verify>
python manage.py test upstream.tests.test_cors_config -v 2
  </verify>
  <done>
Acceptance criteria:
- test_cors_config.py created with 6 tests
- All tests pass
- Tests verify CORS_EXPOSE_HEADERS configuration and header exposure
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify test environment inheritance</name>
  <files>upstream/settings/test.py</files>
  <action>
Review `upstream/settings/test.py` and ensure CORS_EXPOSE_HEADERS is consistent with base.py.

**Expected behavior**: `upstream/settings/test.py` imports from `base.py` via:

```python
from .base import *
```

This means CORS_EXPOSE_HEADERS should inherit automatically. NO CHANGES needed unless test.py explicitly overrides it.

**Verification approach:**

1. Read test.py to confirm it imports from base.py
2. Verify CORS_EXPOSE_HEADERS is NOT overridden in test.py

If test.py overrides CORS_EXPOSE_HEADERS, update it to match base.py:

```python
CORS_EXPOSE_HEADERS = [
    "API-Version",
    "X-Request-Id",
    "X-Request-Duration-Ms",
    "ETag",
    "Last-Modified",
    "Cache-Control",
]
```

**Most likely outcome:** No changes needed - inheritance works correctly.
  </action>
  <verify>
python -c "from upstream.settings.test import CORS_EXPOSE_HEADERS; print(CORS_EXPOSE_HEADERS)"
  </verify>
  <done>
Acceptance criteria:
- CORS_EXPOSE_HEADERS either inherited or explicitly defined
- Test environment has same CORS configuration as base
- Verification command prints list of 6 headers
  </done>
</task>

</tasks>

<verification>
1. Grep CORS config: `grep -A 10 "CORS_EXPOSE_HEADERS" upstream/settings/base.py`
2. Run CORS tests: `python manage.py test upstream.tests.test_cors_config`
3. Verify settings inheritance: `python -c "from django.conf import settings; print(settings.CORS_EXPOSE_HEADERS)"`
4. Check existing tests still pass: `python manage.py test upstream.tests --parallel`
</verification>

<success_criteria>
Complete when:
- [ ] CORS_EXPOSE_HEADERS added to upstream/settings/base.py with 6 headers
- [ ] test_cors_config.py created with 6 tests covering configuration and integration
- [ ] All new tests pass (6/6)
- [ ] Test environment inherits CORS_EXPOSE_HEADERS from base.py
- [ ] Manual verification: `curl -I https://api.example.com` shows Access-Control-Expose-Headers in CORS responses
</success_criteria>

<output>
After completion, create `.planning/quick/021-review-and-configure-cors-settings/021-SUMMARY.md`
</output>

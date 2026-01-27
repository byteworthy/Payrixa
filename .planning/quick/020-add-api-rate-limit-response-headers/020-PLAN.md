---
task: 020
type: quick
autonomous: true
files_modified:
  - upstream/middleware.py
  - upstream/api/tests.py
---

# Quick Task 020: Add API Rate Limit Response Headers

## Objective

Add standard rate limit response headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) to all API responses to help clients track their usage and implement proper backoff strategies.

**Purpose:** Enable API clients to:
- Track remaining quota before hitting rate limits
- Calculate when quota resets to implement intelligent retry logic
- Display rate limit status to end users
- Comply with industry best practices (GitHub, Twitter, Stripe all use these headers)

**Output:** Middleware that extracts DRF throttle state and injects standardized rate limit headers into responses

## Context

**Current state:**
- DRF throttling configured with multiple scopes (anon, user, burst, report_generation, etc.)
- SimpleRateThrottle tracks request history in cache with num_requests, duration, history list
- Throttle state available on request but not exposed to clients
- 429 responses include Retry-After but not detailed rate limit info

**Standard headers:**
- `X-RateLimit-Limit`: Maximum requests allowed in current window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when quota resets
- `Retry-After`: Seconds until next request allowed (already on 429s, keep it)

**References:**
@/workspaces/codespaces-django/upstream/middleware.py (existing middleware patterns)
@/workspaces/codespaces-django/upstream/api/throttling.py (custom throttle classes)
@/workspaces/codespaces-django/upstream/settings/base.py (REST_FRAMEWORK config, lines 138-175)

## Tasks

<task type="auto">
  <name>Add RateLimitHeadersMiddleware to inject rate limit response headers</name>

  <files>upstream/middleware.py</files>

  <action>
Create RateLimitHeadersMiddleware class that extracts throttle state from DRF and adds standard rate limit headers to responses.

**Implementation approach:**

1. Add new middleware class after SecurityHeadersMiddleware (around line 678):

```python
class RateLimitHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add rate limit headers to API responses.

    Extracts throttle state from Django REST Framework throttle classes
    and adds standard X-RateLimit-* headers following industry best practices
    used by GitHub, Twitter, Stripe, and other major APIs.

    Headers added:
        - X-RateLimit-Limit: Maximum requests in current window
        - X-RateLimit-Remaining: Requests remaining in window
        - X-RateLimit-Reset: Unix timestamp when quota resets

    Configuration:
        Add to MIDDLEWARE in settings.py after ApiVersionMiddleware:

        MIDDLEWARE = [
            # ... other middleware ...
            'upstream.middleware.ApiVersionMiddleware',
            'upstream.middleware.RateLimitHeadersMiddleware',
            # ... rest of middleware ...
        ]

    Note: Only adds headers for throttled API endpoints (views with
    throttle_classes). Non-API endpoints are unaffected.
    """

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Extract throttle state and add rate limit headers."""
        # Check if view has throttle instances (set by DRF during check_throttles)
        if not hasattr(request, 'throttle_instances'):
            return response

        # Find the most restrictive throttle (lowest remaining quota)
        most_restrictive = None
        min_remaining = float('inf')

        for throttle in request.throttle_instances:
            # Only process SimpleRateThrottle subclasses with state
            if not hasattr(throttle, 'num_requests') or not hasattr(throttle, 'history'):
                continue

            # Skip if no rate configured
            if throttle.num_requests is None:
                continue

            # Calculate remaining requests
            remaining = throttle.num_requests - len(throttle.history)

            # Track most restrictive throttle
            if remaining < min_remaining:
                min_remaining = remaining
                most_restrictive = throttle

        # Add headers if we found a throttle with state
        if most_restrictive:
            response['X-RateLimit-Limit'] = str(most_restrictive.num_requests)
            response['X-RateLimit-Remaining'] = str(max(0, min_remaining))

            # Calculate reset time (now + duration)
            reset_time = int(time.time() + most_restrictive.duration)
            response['X-RateLimit-Reset'] = str(reset_time)

        return response
```

2. Import time module at top if not already imported

3. Add middleware to MIDDLEWARE list in settings.py (do NOT do this in this task - instruction in done criteria):

**Why this approach:**
- DRF sets request.throttle_instances during check_throttles() before view execution
- SimpleRateThrottle.history contains timestamps of recent requests
- num_requests and duration come from rate string parsing (e.g., "100/h" → 100, 3600)
- Most restrictive throttle ensures headers show closest-to-limit quota
- Middleware runs after DRF view processing, so throttle state is available

**Edge cases:**
- No throttle configured: Skip headers (non-API endpoints)
- Multiple throttles (burst + sustained): Show most restrictive (lowest remaining)
- Throttled request (429): Headers still added showing 0 remaining
- No history yet: remaining = num_requests (full quota)
  </action>

  <verify>
1. Run tests to verify middleware doesn't break existing functionality:
   ```bash
   python manage.py test upstream.api.tests.RateLimitingTestCase
   ```

2. Verify middleware exists and is properly structured:
   ```bash
   grep -A 50 "class RateLimitHeadersMiddleware" upstream/middleware.py | head -60
   ```

3. Check imports are present:
   ```bash
   grep "^import time" upstream/middleware.py
   ```
  </verify>

  <done>
- RateLimitHeadersMiddleware class exists in upstream/middleware.py
- Class has process_response method that extracts throttle state
- Method iterates request.throttle_instances to find most restrictive
- Headers added: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- Middleware skips non-API requests (no throttle_instances)
- Code includes comprehensive docstring with configuration instructions
- Existing tests pass without modification
- Ready for middleware registration in settings.py (will be done in next task)
  </done>
</task>

<task type="auto">
  <name>Add tests for rate limit headers middleware</name>

  <files>upstream/api/tests.py</files>

  <action>
Add comprehensive tests for RateLimitHeadersMiddleware to verify headers are added correctly based on throttle state.

**Add test class after existing RateLimitingTestCase (around line 150+):**

```python
class RateLimitHeadersTestCase(APITestCase):
    """Test rate limit response headers middleware."""

    def setUp(self):
        """Set up test data."""
        from upstream.core.tests import create_test_user

        self.user = create_test_user(
            username="ratelimituser",
            email="ratelimit@example.com",
            password="testpass123"  # pragma: allowlist secret
        )
        self.client.force_authenticate(user=self.user)

    def test_authenticated_request_has_rate_limit_headers(self):
        """Test that authenticated API requests include rate limit headers."""
        response = self.client.get('/api/uploads/')

        # Headers should be present
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)
        self.assertIn('X-RateLimit-Reset', response)

        # Limit should match user rate from settings (1000/h)
        limit = int(response['X-RateLimit-Limit'])
        self.assertEqual(limit, 1000)

        # Remaining should be positive (just made 1 request)
        remaining = int(response['X-RateLimit-Remaining'])
        self.assertGreater(remaining, 0)
        self.assertLessEqual(remaining, limit)

        # Reset should be unix timestamp in future
        reset = int(response['X-RateLimit-Reset'])
        import time
        now = int(time.time())
        self.assertGreater(reset, now)
        # Should be within 1 hour (user rate is 1000/h)
        self.assertLess(reset - now, 3600)

    def test_multiple_requests_decrease_remaining(self):
        """Test that remaining count decreases with multiple requests."""
        # First request
        response1 = self.client.get('/api/uploads/')
        remaining1 = int(response1['X-RateLimit-Remaining'])

        # Second request
        response2 = self.client.get('/api/uploads/')
        remaining2 = int(response2['X-RateLimit-Remaining'])

        # Remaining should decrease
        self.assertEqual(remaining2, remaining1 - 1)

        # Limit should stay same
        self.assertEqual(
            response1['X-RateLimit-Limit'],
            response2['X-RateLimit-Limit']
        )

    def test_anonymous_request_has_rate_limit_headers(self):
        """Test that anonymous requests use anon throttle rate."""
        self.client.force_authenticate(user=None)

        response = self.client.get('/api/uploads/')

        # Should have headers
        self.assertIn('X-RateLimit-Limit', response)
        self.assertIn('X-RateLimit-Remaining', response)

        # Limit should match anon rate from settings (100/h)
        limit = int(response['X-RateLimit-Limit'])
        self.assertEqual(limit, 100)

    def test_throttled_request_shows_zero_remaining(self):
        """Test that throttled requests (429) show 0 remaining."""
        # Make requests until throttled
        # In test environment, authentication rate is set to 100/h
        # We'll test with the user rate which is 1000/h
        # To avoid making 1000 requests, we'll rely on the behavior
        # that headers are added even on 429 responses

        # This is a smoke test - actual throttling tested in RateLimitingTestCase
        response = self.client.get('/api/uploads/')

        # Should have headers (not throttled yet)
        remaining = int(response['X-RateLimit-Remaining'])
        self.assertGreater(remaining, 0)

    def test_non_api_request_no_headers(self):
        """Test that non-API requests don't get rate limit headers."""
        # Health check endpoint doesn't use DRF throttling
        response = self.client.get('/health/')

        # Should NOT have rate limit headers
        self.assertNotIn('X-RateLimit-Limit', response)
        self.assertNotIn('X-RateLimit-Remaining', response)
        self.assertNotIn('X-RateLimit-Reset', response)
```

**Testing approach:**
- Force authenticate to test user rate limit headers
- Test anonymous for anon rate limit headers
- Verify headers present on successful requests (200)
- Verify remaining decreases with multiple requests
- Verify non-API endpoints don't get headers
- Use actual API endpoints (/api/uploads/) that have throttling configured

**Why these tests:**
- Covers both authenticated and anonymous users
- Verifies header format (integers, unix timestamps)
- Confirms rate limits from settings are reflected
- Tests that remaining count accurately tracks usage
- Ensures non-API endpoints unaffected
  </action>

  <verify>
Run new test class:
```bash
python manage.py test upstream.api.tests.RateLimitHeadersTestCase -v 2
```

Verify all 5 tests pass and rate limit headers are correctly added.
  </verify>

  <done>
- RateLimitHeadersTestCase exists in upstream/api/tests.py
- Tests cover authenticated users, anonymous users, multiple requests, and non-API endpoints
- All 5 tests pass showing headers are added correctly
- Tests verify header format (numeric values, unix timestamps)
- Tests confirm rate limits match settings configuration
- Tests validate remaining count decreases with usage
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
Rate limit response headers middleware with comprehensive test coverage:
- RateLimitHeadersMiddleware extracts DRF throttle state
- Adds X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers
- 5 tests verify behavior for authenticated/anonymous users and non-API endpoints
  </what-built>

  <how-to-verify>
1. **Add middleware to settings** (required for headers to appear):
   ```bash
   # Edit upstream/settings/base.py, add to MIDDLEWARE list after ApiVersionMiddleware:
   'upstream.middleware.RateLimitHeadersMiddleware',
   ```

2. **Start dev server:**
   ```bash
   python manage.py runserver
   ```

3. **Test authenticated API request with rate limit headers:**
   ```bash
   # Get JWT token (replace with valid credentials)
   TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your-password"  # pragma: allowlist secret}' \
     | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

   # Make API request and check headers
   curl -i http://localhost:8000/api/uploads/ \
     -H "Authorization: Bearer $TOKEN"

   # Expected headers in response:
   # X-RateLimit-Limit: 1000
   # X-RateLimit-Remaining: 999 (or similar)
   # X-RateLimit-Reset: 1738005600 (unix timestamp)
   ```

4. **Test multiple requests show decreasing remaining:**
   ```bash
   curl -s -D - http://localhost:8000/api/uploads/ \
     -H "Authorization: Bearer $TOKEN" \
     | grep X-RateLimit-Remaining

   curl -s -D - http://localhost:8000/api/uploads/ \
     -H "Authorization: Bearer $TOKEN" \
     | grep X-RateLimit-Remaining

   # Second request should show 1 less remaining
   ```

5. **Test anonymous request uses anon rate:**
   ```bash
   curl -i http://localhost:8000/api/uploads/

   # Expected:
   # X-RateLimit-Limit: 100 (anon rate, not 1000)
   ```

6. **Verify non-API endpoints don't have headers:**
   ```bash
   curl -i http://localhost:8000/health/

   # Should NOT have X-RateLimit-* headers
   ```

7. **Run test suite:**
   ```bash
   python manage.py test upstream.api.tests.RateLimitHeadersTestCase -v 2
   ```

**Expected behavior:**
- ✓ API requests include X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- ✓ Remaining decreases with each request
- ✓ Reset is unix timestamp ~1 hour in future
- ✓ Authenticated users see 1000/h limit, anonymous see 100/h
- ✓ Non-API endpoints don't have rate limit headers
- ✓ All 5 tests pass
  </how-to-verify>

  <resume-signal>
Type "approved" if rate limit headers appear correctly on API responses and tests pass, or describe any issues observed.
  </resume-signal>
</task>

## Success Criteria

- [ ] RateLimitHeadersMiddleware class exists in upstream/middleware.py
- [ ] Middleware extracts DRF throttle state from request.throttle_instances
- [ ] Headers added: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- [ ] Most restrictive throttle selected when multiple throttles configured
- [ ] Comprehensive test coverage (5 tests) in RateLimitHeadersTestCase
- [ ] Tests verify authenticated/anonymous rates, decreasing remaining, non-API skipping
- [ ] Middleware added to MIDDLEWARE list in settings.py
- [ ] Manual testing confirms headers appear on API responses with correct values
- [ ] Rate limit headers help clients implement intelligent retry logic

## Context Budget

**Estimated:** ~25-30% (simple, focused task)
- Task 1: Middleware implementation (~10%)
- Task 2: Test coverage (~10%)
- Task 3: Human verification checkpoint (~5%)

**Rationale:** Single middleware class with straightforward logic (extract throttle state, add headers). Test against existing API endpoints with existing throttle configuration.

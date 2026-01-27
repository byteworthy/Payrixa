---
phase: quick-028
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/API_TROUBLESHOOTING.md
autonomous: true

must_haves:
  truths:
    - "Developers can diagnose common API errors (401, 403, 404, 429, 500) using the guide"
    - "Rate limit handling strategies are documented with code examples"
    - "Authentication troubleshooting covers JWT lifecycle issues"
  artifacts:
    - path: "docs/API_TROUBLESHOOTING.md"
      provides: "Comprehensive API error troubleshooting guide"
      min_lines: 400
      contains: "## Common API Errors"
  key_links:
    - from: "docs/API_TROUBLESHOOTING.md"
      to: "docs/API_EXAMPLES.md"
      via: "cross-references to authentication and rate limit examples"
      pattern: "See.*API_EXAMPLES"
    - from: "docs/API_TROUBLESHOOTING.md"
      to: "upstream/api/exceptions.py"
      via: "documents error codes and formats from exception handler"
      pattern: "error.*code.*authentication_failed|throttled|validation_error"
---

<objective>
Create comprehensive API troubleshooting guide documenting common API errors, their causes, solutions, and debugging strategies.

Purpose: Enable developers to self-diagnose and resolve API issues quickly without support escalation.
Output: API_TROUBLESHOOTING.md with error catalog, debugging workflows, and code examples.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@docs/API_EXAMPLES.md
@upstream/api/exceptions.py
@upstream/api/throttling.py
@upstream/settings/base.py
</context>

<tasks>

<task type="auto">
  <name>Create API Troubleshooting Guide</name>
  <files>docs/API_TROUBLESHOOTING.md</files>
  <action>
Create comprehensive troubleshooting guide with the following structure:

**1. Introduction**
- Purpose of guide (self-service debugging)
- How to use this guide (error code lookup, symptom-based diagnosis)
- When to escalate to support

**2. Common API Errors (with HTTP status codes)**

For each error (401, 403, 404, 429, 500), document:

**401 Unauthorized**
- Symptom: "Authentication credentials were not provided" or "Given token not valid"
- Common causes:
  - Missing Authorization header
  - Expired access token (1 hour lifetime)
  - Malformed Bearer token format
  - Using refresh token instead of access token
- Solutions:
  - Check Authorization header format: `Bearer <access_token>`
  - Verify token hasn't expired (decode JWT payload, check `exp` claim)
  - Refresh token using `/api/v1/auth/token/refresh/` endpoint
  - Re-authenticate if refresh token expired (24 hour lifetime)
- Debugging steps:
  1. Verify Authorization header is present in request
  2. Decode JWT token (jwt.io or base64 decode) and check expiration
  3. Test with newly obtained token from `/api/v1/auth/token/`
  4. Check logs for specific authentication error details
- Code examples:
  - curl command with proper Authorization header
  - Python/JavaScript examples of token refresh flow
  - JWT token structure and expiration checking

**403 Forbidden**
- Symptom: "You do not have permission to perform this action"
- Common causes:
  - Insufficient RBAC role (viewer attempting write operation)
  - Cross-tenant access attempt (accessing another customer's data)
  - Missing `customer_admin` role for admin-only endpoints
- Solutions:
  - Verify user role in JWT token claims or user profile
  - Confirm resource belongs to authenticated user's customer
  - Request role upgrade from organization admin if needed
- Debugging steps:
  1. Decode JWT token and check role claims
  2. Verify resource customer_id matches authenticated user's customer
  3. Review endpoint documentation for required role
  4. Test with superuser account to confirm resource exists
- Cross-reference to RBAC roles table from API_EXAMPLES.md
- Note: Cross-customer access returns 404 (not 403) to prevent data leakage

**404 Not Found**
- Symptom: "Not found" or "The requested resource was not found"
- Common causes:
  - Invalid resource ID
  - Resource deleted
  - Cross-tenant isolation (resource exists but belongs to different customer)
  - Incorrect URL path or typo
- Solutions:
  - Verify resource ID is correct
  - Check if resource was recently deleted
  - Confirm URL path matches API documentation
  - Ensure resource belongs to your customer (404 used for tenant isolation)
- Debugging steps:
  1. Verify URL path against API documentation
  2. Test with known valid resource ID
  3. Check if resource appears in list endpoint
  4. Test with superuser account to determine if tenant isolation issue
- Security note: 404 returned instead of 403 for cross-tenant access to prevent enumeration

**429 Too Many Requests**
- Symptom: "Request was throttled. Expected available in X seconds"
- Common causes:
  - Exceeded endpoint-specific rate limit
  - Burst traffic pattern triggering throttle
  - Loop or retry logic without backoff
  - Shared API key across multiple clients
- Solutions:
  - Implement exponential backoff with jitter
  - Cache responses to reduce API calls
  - Review rate limits table and adjust request patterns
  - Use `wait_seconds` from error response for precise retry timing
- Debugging steps:
  1. Check error response for `wait_seconds` value
  2. Review rate limits table for endpoint-specific limits
  3. Audit recent request history for burst patterns
  4. Implement request logging to identify tight loops
- Rate limits table:
  - authentication: 5/hour (brute-force protection)
  - bulk_operation: 20/hour (uploads)
  - report_generation: 10/hour (expensive operations)
  - read_only: 2000/hour (liberal for GET requests)
  - write_operation: 500/hour (moderate for POST/PUT/DELETE)
  - user: 1000/hour (default)
- Code examples:
  - Python retry with exponential backoff
  - JavaScript retry with wait_seconds parsing
  - Rate limit response header parsing (if implemented)

**500 Internal Server Error**
- Symptom: "An unexpected error occurred. Please try again later"
- Common causes:
  - Server bug or unhandled exception
  - Database connection issue
  - Timeout on long-running operation
  - Data integrity constraint violation
- Solutions:
  - Retry request (may be transient)
  - Check API status page for known incidents
  - Simplify request (reduce page_size, narrow date range)
  - Report to support with request_id from X-Request-Id header
- Debugging steps:
  1. Capture X-Request-Id header value for support escalation
  2. Retry request to determine if transient
  3. Simplify request parameters to isolate cause
  4. Check API status page: https://status.upstream.example.com
  5. Contact support with request_id and timestamp
- Note: Specific error details logged server-side but not exposed in API response (security)

**3. Authentication Troubleshooting**

**JWT Token Lifecycle**
- Access token: 1 hour expiration
- Refresh token: 24 hour expiration
- Token refresh workflow diagram/pseudocode
- Detecting token expiration before API call (check `exp` claim)
- Pre-emptive token refresh strategy

**Common Authentication Patterns**
- Initial login flow
- Token storage best practices (secure, httpOnly cookies for web)
- Token refresh flow (use refresh token before access token expires)
- Handling refresh token expiration (force re-login)
- Multi-tab/window token synchronization

**Authentication Error Decision Tree**
```
401 Error
├─ "credentials were not provided"
│  └─ Missing Authorization header → Add header
├─ "token not valid"
│  ├─ Access token expired → Refresh token
│  └─ Refresh token expired → Re-authenticate
└─ "No active account found"
   └─ Invalid credentials → Check username/password
```

**4. Rate Limit Handling Strategies**

**Understanding Rate Limits**
- Per-endpoint vs global limits
- Sliding window vs fixed window (DRF uses sliding)
- Authenticated vs anonymous limits
- Rate limit scope hierarchy

**Handling 429 Responses**
- Parse `wait_seconds` from error response
- Implement exponential backoff: start with wait_seconds, then 2x, 4x, 8x (max 60s)
- Add jitter (random 0-1s) to prevent thundering herd
- Queue requests instead of failing
- Circuit breaker pattern for sustained failures

**Optimizing API Usage**
- Caching strategies (respect ETag/Cache-Control headers)
- Batch operations where available
- Pagination best practices (balance page_size vs request count)
- Filtering to reduce response size and processing
- Webhook alternatives to polling for real-time updates

**Code Examples**
- Python requests library with retry logic
- JavaScript fetch with exponential backoff
- Rate limit response parsing
- Queue-based request management

**5. Debugging Workflows**

**Quick Diagnosis Checklist**
```
□ Check HTTP status code (401/403/404/429/500)
□ Read error.message and error.code fields
□ Verify Authorization header present and formatted correctly
□ Decode JWT token and check expiration timestamp
□ Review endpoint-specific rate limits
□ Capture X-Request-Id header for support escalation
□ Check API status page for known issues
```

**Step-by-Step Debugging**

For authentication issues:
1. Test login endpoint to obtain fresh tokens
2. Verify token storage and retrieval
3. Check token format in Authorization header
4. Decode token and verify claims (exp, user_id, customer_id)
5. Test token verification endpoint

For permission issues:
1. Confirm user role (superuser/customer_admin/customer_viewer)
2. Verify resource belongs to user's customer
3. Check endpoint documentation for required permissions
4. Test with known accessible resource

For rate limit issues:
1. Identify throttled endpoint from error response
2. Check current rate limit for endpoint
3. Audit request patterns for bursts or loops
4. Implement backoff and retry logic
5. Consider caching or batching strategies

**6. Testing and Validation**

**Using curl for Debugging**
- Example curl commands for each error scenario
- How to inspect response headers (X-Request-Id, X-Request-Duration-Ms)
- Testing authentication flow end-to-end
- Triggering rate limits intentionally for testing

**Common Pitfalls**
- Using refresh token in Authorization header (should be access token)
- Not handling token expiration (leads to intermittent 401s)
- Ignoring wait_seconds in 429 response (causes continued throttling)
- Retrying 500 errors immediately without backoff (amplifies load)
- Not capturing X-Request-Id before error response disappears

**7. Error Response Format**

Document standardized error response structure from exceptions.py:

```json
{
  "error": {
    "code": "authentication_failed|permission_denied|not_found|throttled|validation_error|internal_server_error",
    "message": "Human-readable error description",
    "details": {
      // Additional context (field-level validation errors, wait_seconds for throttle, etc.)
    }
  }
}
```

Error code catalog:
- `authentication_failed`: 401 - Missing/invalid credentials
- `permission_denied`: 403 - Insufficient permissions
- `not_found`: 404 - Resource doesn't exist or cross-tenant
- `throttled`: 429 - Rate limit exceeded
- `validation_error`: 400 - Invalid input data
- `parse_error`: 400 - Malformed request body
- `method_not_allowed`: 405 - HTTP method not supported
- `unsupported_media_type`: 415 - Invalid Content-Type
- `internal_server_error`: 500 - Unexpected server error

**8. Support Escalation**

**When to Contact Support**
- Persistent 500 errors (with X-Request-Id)
- Suspected rate limit misconfiguration
- Authentication issues after verifying credentials
- Data inconsistencies or unexpected 404s for known resources

**Information to Provide**
- X-Request-Id header value
- Timestamp of error
- Full curl command (with credentials redacted)
- Error response body
- Relevant authentication token (if auth issue)
- Steps to reproduce

**Contact Information**
- Email: support@upstream.example.com
- Status page: https://status.upstream.example.com

**9. Additional Resources**
- Link to API_EXAMPLES.md for working examples
- Link to API_VERSIONING.md for version compatibility
- Link to TESTING.md for test environment setup
- JWT token decoder: https://jwt.io (for debugging token claims)

Follow these principles:
- Use concrete examples with actual error messages from exceptions.py
- Include curl commands and code snippets (Python, JavaScript)
- Cross-reference existing docs (API_EXAMPLES.md, API_VERSIONING.md)
- Keep language clear and action-oriented ("Check X", "Verify Y", "Run Z")
- Organize by symptom (error code) for quick lookup
- Include decision trees and checklists for systematic debugging
- Document error response format from custom exception handler
- Reference actual throttle rates from settings/base.py
- Provide ready-to-use retry logic code examples
  </action>
  <verify>
1. File exists: ls -la docs/API_TROUBLESHOOTING.md
2. Contains all required sections: grep -E "## (Common API Errors|Authentication|Rate Limit|Debugging|Support)" docs/API_TROUBLESHOOTING.md
3. Covers all HTTP status codes: grep -E "(401|403|404|429|500)" docs/API_TROUBLESHOOTING.md
4. Includes code examples: grep -c "```" docs/API_TROUBLESHOOTING.md (should be 10+)
5. Cross-references other docs: grep -c "API_EXAMPLES.md" docs/API_TROUBLESHOOTING.md
6. Documents error codes from exceptions.py: grep -E "(authentication_failed|throttled|validation_error)" docs/API_TROUBLESHOOTING.md
  </verify>
  <done>
- API_TROUBLESHOOTING.md exists with 400+ lines
- All HTTP error codes (401, 403, 404, 429, 500) documented with causes, solutions, debugging steps
- Authentication troubleshooting covers JWT lifecycle and token refresh flow
- Rate limit handling strategies include exponential backoff with code examples
- Debugging workflows provide systematic diagnosis checklists
- Error response format matches custom exception handler structure
- Cross-references to API_EXAMPLES.md and other existing docs
- Support escalation process documented with required information
- Ready for immediate use by API consumers
  </done>
</task>

</tasks>

<verification>
Manual verification:
1. Open docs/API_TROUBLESHOOTING.md and review structure
2. Verify all 5 error types (401, 403, 404, 429, 500) are comprehensively documented
3. Check code examples are syntactically correct and runnable
4. Confirm cross-references to API_EXAMPLES.md work
5. Validate error codes match those in upstream/api/exceptions.py
6. Verify rate limits match settings/base.py values
</verification>

<success_criteria>
- [ ] API_TROUBLESHOOTING.md created with complete error catalog
- [ ] Each error type includes: symptom, causes, solutions, debugging steps, code examples
- [ ] Authentication troubleshooting covers JWT token lifecycle
- [ ] Rate limit handling includes exponential backoff examples
- [ ] Debugging workflows provide actionable checklists
- [ ] Error response format matches custom exception handler
- [ ] Cross-references to existing docs (API_EXAMPLES.md, etc.)
- [ ] Support escalation process documented
- [ ] All verification checks pass
</success_criteria>

<output>
After completion, create `.planning/quick/028-create-api-troubleshooting-guide-docu/028-SUMMARY.md`
</output>

# API Troubleshooting Guide

Comprehensive guide to diagnosing and resolving common API errors in the Upstream Healthcare Platform.

## Table of Contents

1. [Introduction](#introduction)
2. [Common API Errors](#common-api-errors)
   - [401 Unauthorized](#401-unauthorized)
   - [403 Forbidden](#403-forbidden)
   - [404 Not Found](#404-not-found)
   - [429 Too Many Requests](#429-too-many-requests)
   - [500 Internal Server Error](#500-internal-server-error)
3. [Authentication Troubleshooting](#authentication-troubleshooting)
4. [Rate Limit Handling Strategies](#rate-limit-handling-strategies)
5. [Debugging Workflows](#debugging-workflows)
6. [Testing and Validation](#testing-and-validation)
7. [Error Response Format](#error-response-format)
8. [Support Escalation](#support-escalation)
9. [Additional Resources](#additional-resources)

---

## Introduction

### Purpose of This Guide

This guide helps API consumers self-diagnose and resolve common issues without contacting support. Use it to:

- Look up error codes and understand what went wrong
- Follow step-by-step debugging workflows
- Implement proper error handling and retry logic
- Know when to escalate issues to support

### How to Use This Guide

**Quick lookup by error code:** Jump directly to the HTTP status code section (401, 403, 404, 429, 500) for specific guidance.

**Symptom-based diagnosis:** If you're unsure of the error type, start with [Debugging Workflows](#debugging-workflows) for systematic troubleshooting.

**Prevention:** Review [Rate Limit Handling Strategies](#rate-limit-handling-strategies) and [Authentication Troubleshooting](#authentication-troubleshooting) to avoid common issues.

### When to Escalate to Support

Contact support when:

- You encounter persistent 500 errors (include X-Request-Id header value)
- Rate limits appear misconfigured or unreasonable
- Authentication fails after verifying credentials are correct
- You observe data inconsistencies or unexpected 404s for known resources
- None of the troubleshooting steps resolve your issue

See [Support Escalation](#support-escalation) for contact information and required details.

---

## Common API Errors

### 401 Unauthorized

**HTTP Status:** 401

**Symptom:** "Authentication credentials were not provided" or "Given token not valid"

#### Common Causes

1. **Missing Authorization header** - Request doesn't include authentication token
2. **Expired access token** - JWT access tokens expire after 1 hour
3. **Malformed Bearer token format** - Incorrect header format or encoding
4. **Using refresh token instead of access token** - Wrong token type in Authorization header
5. **Invalid or corrupted token** - Token signature invalid or payload corrupted

#### Solutions

**Missing Authorization header:**
```bash
# Incorrect (no authentication)
curl -X GET https://api.upstream.example.com/api/v1/uploads/

# Correct (with Bearer token)
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Expired access token:**
- Access tokens expire after 1 hour
- Use refresh token to obtain new access token
- See [Token Refresh Flow](#token-refresh-flow)

**Malformed Bearer token:**
```bash
# Incorrect format
Authorization: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...  # Missing "Bearer"

# Correct format
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Using refresh token instead of access token:**
- Refresh tokens are ONLY for `/api/v1/auth/token/refresh/` endpoint
- For all other API calls, use the access token from login response

#### Debugging Steps

1. **Verify Authorization header is present:**
   ```bash
   # Add -v flag to curl to see request headers
   curl -v -X GET https://api.upstream.example.com/api/v1/uploads/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Check token expiration:**
   - Decode JWT token at https://jwt.io
   - Check `exp` claim (Unix timestamp)
   - Compare with current time: `date +%s`

3. **Test with fresh token:**
   ```bash
   # Obtain new token
   curl -X POST https://api.upstream.example.com/api/v1/auth/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "your@email.com", "password": "your_password"}'  # pragma: allowlist secret

   # Use new access token immediately
   curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
     -H "Authorization: Bearer NEW_ACCESS_TOKEN"
   ```

4. **Verify token with verification endpoint:**
   ```bash
   curl -X POST https://api.upstream.example.com/api/v1/auth/token/verify/ \
     -H "Content-Type: application/json" \
     -d '{"token": "YOUR_ACCESS_TOKEN"}'
   ```

#### Code Examples

**Python - Token refresh on 401:**
```python
import requests
import time
import jwt

class APIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.login()

    def login(self):
        """Obtain initial access and refresh tokens."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/token/",
            json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access"]
        self.refresh_token = data["refresh"]

    def refresh_access_token(self):
        """Refresh access token using refresh token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/token/refresh/",
            json={"refresh": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access"]

    def is_token_expired(self):
        """Check if access token is expired or expiring soon (within 5 minutes)."""
        try:
            # Decode without verification to check expiration
            payload = jwt.decode(self.access_token, options={"verify_signature": False})
            exp_timestamp = payload.get("exp", 0)
            # Add 5-minute buffer to refresh before expiration
            return time.time() > (exp_timestamp - 300)
        except:
            return True

    def request(self, method, path, **kwargs):
        """Make authenticated API request with automatic token refresh."""
        # Pre-emptively refresh if token expired
        if self.is_token_expired():
            self.refresh_access_token()

        # Add authorization header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        # Make request
        response = requests.request(method, f"{self.base_url}{path}", **kwargs)

        # If 401, try refreshing token once and retry
        if response.status_code == 401:
            try:
                self.refresh_access_token()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.request(method, f"{self.base_url}{path}", **kwargs)
            except:
                # Refresh failed, re-login
                self.login()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = requests.request(method, f"{self.base_url}{path}", **kwargs)

        return response

# Usage
client = APIClient("https://api.upstream.example.com", "user@example.com", "password")
response = client.request("GET", "/api/v1/uploads/")
print(response.json())
```

**JavaScript - Token refresh on 401:**
```javascript
class APIClient {
  constructor(baseURL, username, password) {
    this.baseURL = baseURL;
    this.username = username;
    this.password = password;
    this.accessToken = null;
    this.refreshToken = null;
  }

  async login() {
    const response = await fetch(`${this.baseURL}/api/v1/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: this.username, password: this.password })
    });
    const data = await response.json();
    this.accessToken = data.access;
    this.refreshToken = data.refresh;
  }

  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/api/v1/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: this.refreshToken })
    });
    const data = await response.json();
    this.accessToken = data.access;
  }

  isTokenExpired() {
    if (!this.accessToken) return true;
    try {
      // Decode JWT payload (base64 decode middle part)
      const payload = JSON.parse(atob(this.accessToken.split('.')[1]));
      const expTimestamp = payload.exp;
      // Add 5-minute buffer
      return Date.now() / 1000 > (expTimestamp - 300);
    } catch {
      return true;
    }
  }

  async request(method, path, options = {}) {
    // Pre-emptively refresh if token expired
    if (this.isTokenExpired()) {
      await this.refreshAccessToken();
    }

    // Add authorization header
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };

    // Make request
    let response = await fetch(`${this.baseURL}${path}`, {
      ...options,
      method,
      headers
    });

    // If 401, try refreshing token once and retry
    if (response.status === 401) {
      try {
        await this.refreshAccessToken();
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(`${this.baseURL}${path}`, {
          ...options,
          method,
          headers
        });
      } catch {
        // Refresh failed, re-login
        await this.login();
        headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(`${this.baseURL}${path}`, {
          ...options,
          method,
          headers
        });
      }
    }

    return response;
  }
}

// Usage
const client = new APIClient('https://api.upstream.example.com', 'user@example.com', 'password');
await client.login();
const response = await client.request('GET', '/api/v1/uploads/');
const data = await response.json();
console.log(data);
```

---

### 403 Forbidden

**HTTP Status:** 403

**Symptom:** "You do not have permission to perform this action"

#### Common Causes

1. **Insufficient RBAC role** - User's role doesn't allow the requested operation
2. **Viewer attempting write operation** - Customer viewers have read-only access
3. **Missing customer_admin role** - Endpoint requires admin privileges
4. **Attempting to modify another user's data** - Users can only modify their own data

#### Solutions

**Verify user role:**
```python
# Decode JWT token to check role
import jwt

token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
payload = jwt.decode(token, options={"verify_signature": False})
print(f"User ID: {payload['user_id']}")
print(f"Username: {payload['username']}")
# Note: Role is stored in database, not in JWT token
```

**Request role upgrade:**
- Contact your organization admin to upgrade role
- Customer viewers cannot perform write operations (POST, PUT, DELETE)
- Admin-only endpoints require `customer_admin` role

**Verify resource ownership:**
- Cross-tenant access returns 404 (not 403) to prevent data leakage
- 403 indicates authenticated but insufficient permissions
- Confirm resource belongs to your customer

#### RBAC Roles Reference

| Role | Permissions | Restrictions |
|------|------------|--------------|
| **Superuser** | Full access to all resources across all customers | Django superuser flag required |
| **Customer Admin** | Full CRUD access to customer's data | Cannot access other customers' data |
| **Customer Viewer** | Read-only access to customer's data | Cannot create, update, or delete |

#### Debugging Steps

1. **Check endpoint documentation for required role:**
   - See [API_EXAMPLES.md](./API_EXAMPLES.md) for endpoint permission requirements
   - Admin-only endpoints: uploads (create), reports (trigger), alerts (feedback)

2. **Decode JWT token and check user claims:**
   ```bash
   # Use jwt.io or base64 decode
   echo "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." | cut -d. -f2 | base64 -d | jq
   ```

3. **Test with known accessible resource:**
   ```bash
   # Verify you can read (should work for all roles)
   curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
     -H "Authorization: Bearer YOUR_TOKEN"

   # Try write operation (requires admin role)
   curl -X POST https://api.upstream.example.com/api/v1/uploads/ \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"filename": "test.csv"}'
   ```

4. **Test with superuser account (if available):**
   - Confirms resource exists and endpoint works
   - Isolates permission issue vs other problems

#### Security Note

**404 vs 403 for tenant isolation:**

The API returns **404 Not Found** (not 403 Forbidden) when accessing another customer's data. This prevents attackers from enumerating resources.

**Example:**
```bash
# Accessing another customer's upload
curl -X GET https://api.upstream.example.com/api/v1/uploads/999/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response: 404 (not 403) - prevents confirming resource exists
{
  "error": {
    "code": "not_found",
    "message": "The requested resource was not found.",
    "details": null
  }
}
```

---

### 404 Not Found

**HTTP Status:** 404

**Symptom:** "Not found" or "The requested resource was not found"

#### Common Causes

1. **Invalid resource ID** - ID doesn't exist in database
2. **Resource deleted** - Resource was removed
3. **Cross-tenant isolation** - Resource exists but belongs to different customer (security feature)
4. **Incorrect URL path** - Typo in endpoint URL
5. **Trailing slash mismatch** - Some frameworks require exact slash matching

#### Solutions

**Verify resource ID:**
```bash
# List resources to find valid IDs
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Use ID from list response
curl -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Check if resource was deleted:**
- Query audit logs or recent changes
- Resource may have been deleted by another user
- Check deletion timestamp if available

**Verify URL path:**
```bash
# Common URL mistakes
/api/v1/upload/42/   # Wrong: singular "upload"
/api/v1/uploads/42   # Wrong: missing trailing slash
/api/v1/uploads/42/  # Correct
```

**Test with superuser account:**
- Determine if 404 is due to tenant isolation
- If superuser sees resource, it belongs to different customer
- If superuser gets 404, resource truly doesn't exist

#### Debugging Steps

1. **Verify URL path matches API documentation:**
   - Check [API_EXAMPLES.md](./API_EXAMPLES.md) for correct endpoints
   - Confirm resource type (uploads, claims, drift-events, reports)

2. **Test with known valid resource ID:**
   ```bash
   # List first page to get valid ID
   curl -X GET "https://api.upstream.example.com/api/v1/uploads/?page=1&page_size=1" \
     -H "Authorization: Bearer YOUR_TOKEN"

   # Use ID from response
   curl -X GET https://api.upstream.example.com/api/v1/uploads/VALID_ID/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Check if resource appears in list endpoint:**
   ```bash
   # Search for resource by attributes
   curl -X GET "https://api.upstream.example.com/api/v1/uploads/?filename=claims_2024.csv" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Test with superuser account to determine tenant isolation:**
   - If available, use superuser credentials
   - 404 with superuser = resource doesn't exist
   - 200 with superuser = tenant isolation (resource belongs to another customer)

#### Security Implications

**404 instead of 403 for cross-tenant access:**

This is a security feature to prevent resource enumeration. Attackers cannot determine if a resource exists by observing 404 vs 403 responses.

**What this means:**
- 404 could mean "resource doesn't exist" OR "resource exists but you can't access it"
- You cannot differentiate between these cases (by design)
- Prevents attackers from discovering resource IDs across customer boundaries

---

### 429 Too Many Requests

**HTTP Status:** 429

**Symptom:** "Request was throttled. Expected available in X seconds"

#### Common Causes

1. **Exceeded endpoint-specific rate limit** - Too many requests to one endpoint
2. **Burst traffic pattern** - Rapid succession of requests triggers throttle
3. **Loop or retry logic without backoff** - Code retrying too quickly
4. **Shared API key across multiple clients** - Multiple processes using same credentials

#### Rate Limits by Endpoint

| Scope | Rate Limit | Applies To |
|-------|-----------|------------|
| **authentication** | 5/hour | `/api/v1/auth/token/` (login) |
| **bulk_operation** | 20/hour | File uploads, batch operations |
| **report_generation** | 10/hour | `/api/v1/reports/trigger/` |
| **read_only** | 2000/hour | GET requests (claims, drift-events, etc.) |
| **write_operation** | 500/hour | POST/PUT/DELETE requests |
| **user** (default) | 1000/hour | Endpoints without specific throttle |
| **burst** | 60/minute | High-frequency operations |
| **anon** | 100/hour | Anonymous users (health check, etc.) |

#### Solutions

**Implement exponential backoff:**
```python
import time
import random

def exponential_backoff_request(url, headers, max_retries=5):
    """Make request with exponential backoff on 429."""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code != 429:
            return response

        # Parse wait_seconds from error response
        error_data = response.json().get("error", {})
        wait_seconds = error_data.get("details", {}).get("wait_seconds", 60)

        # Exponential backoff: wait_seconds * 2^attempt + jitter
        backoff = wait_seconds * (2 ** attempt) + random.uniform(0, 1)
        # Cap at 60 seconds
        backoff = min(backoff, 60)

        print(f"Rate limited. Waiting {backoff:.1f} seconds (attempt {attempt + 1}/{max_retries})")
        time.sleep(backoff)

    # All retries exhausted
    return response
```

**Cache responses to reduce API calls:**
```python
import requests
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPIClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.cache = {}

    def get(self, path, cache_ttl=300):
        """GET with caching (TTL in seconds)."""
        cache_key = path
        now = datetime.now()

        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if now - cached_time < timedelta(seconds=cache_ttl):
                return cached_data

        # Cache miss or expired - make request
        response = requests.get(
            f"{self.base_url}{path}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        data = response.json()

        # Update cache
        self.cache[cache_key] = (data, now)
        return data
```

**Use wait_seconds from error response:**
```javascript
async function requestWithRateLimitHandling(url, options) {
  const response = await fetch(url, options);

  if (response.status === 429) {
    const errorData = await response.json();
    const waitSeconds = errorData.error?.details?.wait_seconds || 60;

    console.log(`Rate limited. Waiting ${waitSeconds} seconds...`);
    await new Promise(resolve => setTimeout(resolve, waitSeconds * 1000));

    // Retry once
    return await fetch(url, options);
  }

  return response;
}
```

#### Debugging Steps

1. **Check error response for wait_seconds:**
   ```bash
   curl -X POST https://api.upstream.example.com/api/v1/reports/trigger/ \
     -H "Authorization: Bearer YOUR_TOKEN"

   # Response (429):
   # {
   #   "error": {
   #     "code": "throttled",
   #     "message": "Request was throttled. Please try again later.",
   #     "details": {"wait_seconds": 3600}
   #   }
   # }
   ```

2. **Review rate limits table for endpoint-specific limits:**
   - Identify which endpoint was throttled
   - Check if you're near any rate limit thresholds
   - Consider if your request pattern is appropriate

3. **Audit recent request history for burst patterns:**
   - Check application logs for request timestamps
   - Look for tight loops or missing backoff logic
   - Review error logs for repeated 429 responses

4. **Implement request logging:**
   ```python
   import logging

   logger = logging.getLogger(__name__)

   def logged_request(url, headers):
       logger.info(f"API request: {url}")
       response = requests.get(url, headers=headers)
       logger.info(f"API response: {response.status_code}")
       if response.status_code == 429:
           logger.warning(f"Rate limited: {response.json()}")
       return response
   ```

#### Optimization Strategies

**Batch operations where available:**
- Use pagination with larger page_size to reduce request count
- Balance between fewer requests (high page_size) and response time

**Filter to reduce response size:**
```bash
# Instead of fetching all claims and filtering client-side
curl -X GET "https://api.upstream.example.com/api/v1/claims/?payer=Aetna&outcome=DENIED&submitted_date_after=2024-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Use webhooks instead of polling:**
- Configure webhooks for real-time updates
- Eliminates need for frequent polling requests
- See [API_EXAMPLES.md](./API_EXAMPLES.md#7-webhooks) for webhook setup

**Respect ETag and Cache-Control headers:**
```bash
# First request
curl -v -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response includes: ETag: "abc123"

# Subsequent request with If-None-Match
curl -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "If-None-Match: \"abc123\""
# Response: 304 Not Modified (not counted against rate limit)
```

---

### 500 Internal Server Error

**HTTP Status:** 500

**Symptom:** "An unexpected error occurred. Please try again later"

#### Common Causes

1. **Server bug or unhandled exception** - Code error in API
2. **Database connection issue** - Database unavailable or overloaded
3. **Timeout on long-running operation** - Query or processing exceeded time limit
4. **Data integrity constraint violation** - Data violates database constraints
5. **Resource exhaustion** - Server out of memory or disk space

#### Solutions

**Retry request (transient errors):**
```python
import requests
import time

def retry_on_500(url, headers, max_retries=3):
    """Retry on 500 errors with exponential backoff."""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code != 500:
            return response

        # Exponential backoff: 1s, 2s, 4s
        wait_time = 2 ** attempt
        print(f"500 error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
        time.sleep(wait_time)

    return response
```

**Simplify request to isolate cause:**
```bash
# If large page_size causes timeout
curl -X GET "https://api.upstream.example.com/api/v1/claims/?page_size=1000" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response: 500 (timeout)

# Try smaller page_size
curl -X GET "https://api.upstream.example.com/api/v1/claims/?page_size=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response: 200 (success)
```

**Narrow date range for large datasets:**
```bash
# Instead of querying entire history
curl -X GET "https://api.upstream.example.com/api/v1/claims/?submitted_date_after=2020-01-01" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response: 500 (too much data)

# Query recent data only
curl -X GET "https://api.upstream.example.com/api/v1/claims/?submitted_date_after=2024-01-01&submitted_date_before=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
# Response: 200 (success)
```

**Check API status page:**
- Visit https://status.upstream.example.com
- Check for known incidents or maintenance
- Subscribe to status updates

#### Debugging Steps

1. **Capture X-Request-Id header for support escalation:**
   ```bash
   # Use -v to see response headers
   curl -v -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
     -H "Authorization: Bearer YOUR_TOKEN"

   # Look for: X-Request-Id: abc123-def456-789
   ```

2. **Retry request to determine if transient:**
   - Wait 1-2 seconds and retry
   - If second attempt succeeds, error was transient
   - If persistent, likely a code bug or data issue

3. **Simplify request parameters to isolate cause:**
   - Reduce page_size: 1000 → 100 → 10
   - Narrow date ranges: 1 year → 1 month → 1 day
   - Remove optional filters one by one
   - Test with minimal parameters

4. **Check API status page:**
   - https://status.upstream.example.com
   - Look for current incidents or degraded performance
   - Check historical incidents at similar times

5. **Contact support with X-Request-Id and timestamp:**
   - See [Support Escalation](#support-escalation) section
   - Provide X-Request-Id header value (critical for log lookup)
   - Include exact timestamp of error
   - Share full curl command (with credentials redacted)

#### Security Note

**Limited error details in API responses:**

500 error responses intentionally omit specific error details for security reasons. This prevents leaking sensitive information about server internals, database structure, or file paths.

**Server-side logging:**
- Detailed error information is logged server-side
- Support team can access full stack traces and error context
- Provide X-Request-Id header to support for log lookup

---

## Authentication Troubleshooting

### JWT Token Lifecycle

**Access Token:**
- **Expiration:** 1 hour after issuance
- **Purpose:** Authenticate API requests
- **Used in:** Authorization header for all API endpoints
- **Renewal:** Use refresh token to obtain new access token

**Refresh Token:**
- **Expiration:** 24 hours after issuance
- **Purpose:** Obtain new access token without re-entering credentials
- **Used in:** `/api/v1/auth/token/refresh/` endpoint only
- **Renewal:** Must re-authenticate (login) after expiration

### Token Refresh Flow

```
┌─────────────┐
│   Login     │  POST /api/v1/auth/token/
└──────┬──────┘  {"username": "...", "password": "..."}
       │
       ▼
┌─────────────────────────────┐
│ Receive Tokens              │
│ - access (1h expiration)    │
│ - refresh (24h expiration)  │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Use Access Token            │
│ for API requests            │
│ (Authorization: Bearer ...) │
└──────┬──────────────────────┘
       │
       ▼
   ┌───────────────┐
   │ Token Expired?│
   └───┬───────┬───┘
       │       │
    NO │       │ YES
       │       │
       ▼       ▼
    Use it  ┌────────────────────┐
            │ Refresh Token      │  POST /api/v1/auth/token/refresh/
            │ (use refresh token)│  {"refresh": "..."}
            └────────┬───────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ Receive New Access │
            │ Token (1h exp)     │
            └────────┬───────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ Refresh Expired?   │
            └────┬───────────┬───┘
                 │           │
              NO │           │ YES
                 │           │
                 ▼           ▼
             Continue   Re-Login
             Using      (enter
             API        credentials)
```

### Token Expiration Detection

**Pre-emptive expiration check (recommended):**

```python
import jwt
import time

def is_token_expired(token, buffer_seconds=300):
    """
    Check if JWT token is expired or expiring soon.

    Args:
        token: JWT access token
        buffer_seconds: Refresh token this many seconds before expiration (default: 5 minutes)

    Returns:
        True if token is expired or expiring soon
    """
    try:
        # Decode without verification to read claims
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = payload.get("exp", 0)

        # Check if expired or expiring within buffer
        return time.time() > (exp_timestamp - buffer_seconds)
    except:
        # Assume expired if cannot decode
        return True

# Usage
if is_token_expired(access_token):
    # Refresh token before making API call
    access_token = refresh_access_token(refresh_token)
```

**Reactive expiration handling (less efficient):**

```python
def make_api_request(url, access_token, refresh_token):
    """Make API request with reactive 401 handling."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        # Token expired - refresh and retry
        new_access_token = refresh_access_token(refresh_token)
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = requests.get(url, headers=headers)

    return response
```

### Common Authentication Patterns

**Initial Login Flow:**

```bash
# Step 1: Login to obtain tokens
curl -X POST https://api.upstream.example.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "doctor@healthcorp.com",
    "password": "SecurePassword123!"
  }'  # pragma: allowlist secret

# Response:
# {
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
# }

# Step 2: Store tokens securely
# - Web apps: httpOnly cookies (secure, not accessible to JavaScript)
# - Mobile apps: Secure storage (Keychain on iOS, Keystore on Android)
# - Desktop apps: OS credential manager
# - CLI tools: Encrypted config file

# Step 3: Use access token for API requests
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

**Token Refresh Flow:**

```bash
# When access token expires (after 1 hour)
curl -X POST https://api.upstream.example.com/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "REFRESH_TOKEN"
  }'

# Response:
# {
#   "access": "NEW_ACCESS_TOKEN"
# }

# Continue using new access token
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer NEW_ACCESS_TOKEN"
```

**Handling Refresh Token Expiration:**

```python
def get_access_token(refresh_token):
    """Get access token, handling refresh token expiration."""
    try:
        # Try refreshing
        response = requests.post(
            "https://api.upstream.example.com/api/v1/auth/token/refresh/",
            json={"refresh": refresh_token}
        )
        response.raise_for_status()
        return response.json()["access"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # Refresh token expired - force re-login
            raise AuthenticationError("Refresh token expired. Please log in again.")
        raise
```

### Multi-Tab/Window Token Synchronization

**Problem:** User has multiple browser tabs open. Access token expires in one tab, but other tabs still have old token.

**Solutions:**

**1. Shared token storage (localStorage/sessionStorage):**

```javascript
// Tab 1: Refresh token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/v1/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken })
  });
  const data = await response.json();

  // Update localStorage - other tabs will see this
  localStorage.setItem('access_token', data.access);

  // Broadcast storage event to other tabs
  window.dispatchEvent(new Event('storage'));
}

// All tabs: Listen for token updates
window.addEventListener('storage', (event) => {
  if (event.key === 'access_token') {
    // Token updated by another tab - refresh page or update in memory
    console.log('Access token updated by another tab');
  }
});
```

**2. BroadcastChannel API (modern browsers):**

```javascript
const authChannel = new BroadcastChannel('auth_channel');

// Tab 1: Refresh token and notify others
async function refreshToken() {
  const response = await fetch('/api/v1/auth/token/refresh/', {
    method: 'POST',
    body: JSON.stringify({ refresh: localStorage.getItem('refresh_token') })
  });
  const data = await response.json();

  localStorage.setItem('access_token', data.access);

  // Notify other tabs
  authChannel.postMessage({ type: 'token_refreshed', access: data.access });
}

// All tabs: Listen for notifications
authChannel.onmessage = (event) => {
  if (event.data.type === 'token_refreshed') {
    console.log('Token refreshed by another tab');
    localStorage.setItem('access_token', event.data.access);
  }
};
```

### Authentication Error Decision Tree

```
401 Unauthorized Error
├─ "credentials were not provided"
│  ├─ Missing Authorization header?
│  │  └─ Add: Authorization: Bearer <token>
│  └─ Malformed header?
│     └─ Check format: "Bearer " prefix required
│
├─ "token not valid"
│  ├─ Access token expired? (check exp claim)
│  │  ├─ Refresh token still valid?
│  │  │  ├─ YES → Use refresh endpoint to get new access token
│  │  │  └─ NO → Re-authenticate (full login)
│  │  └─ Check token expiration:
│  │     └─ Decode at jwt.io or base64 decode payload
│  │
│  ├─ Using refresh token in Authorization header?
│  │  └─ Use access token for API calls, refresh token only for /token/refresh/
│  │
│  └─ Token corrupted or invalid signature?
│     └─ Obtain new token via login
│
└─ "No active account found"
   └─ Invalid username or password
      └─ Verify credentials and retry login
```

---

## Rate Limit Handling Strategies

### Understanding Rate Limits

**Rate limit implementation:**
- **Sliding window:** Tracks requests over rolling time period (not fixed hourly buckets)
- **Per-user:** Limits apply per authenticated user (separate from other users)
- **Scope-based:** Different endpoints have different rate limits

**Example:** 1000/hour means 1000 requests in any rolling 60-minute window, not "1000 requests from 2pm-3pm".

### Rate Limit Response Headers

Currently, the API does not expose rate limit information in response headers. Rate limits are enforced silently until exceeded.

**Future enhancement:** Response headers like X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset may be added.

### Exponential Backoff Implementation

**Python example with jitter:**

```python
import time
import random
import requests

def exponential_backoff_request(
    url,
    headers,
    max_retries=5,
    base_wait=1,
    max_wait=60
):
    """
    Make HTTP request with exponential backoff on rate limit errors.

    Args:
        url: API endpoint URL
        headers: Request headers (including Authorization)
        max_retries: Maximum number of retry attempts
        base_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        requests.Response object
    """
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        # Success or non-rate-limit error
        if response.status_code != 429:
            return response

        # Rate limited - calculate backoff
        error_data = response.json().get("error", {})
        wait_seconds = error_data.get("details", {}).get("wait_seconds")

        if wait_seconds:
            # Use wait_seconds from API response
            backoff = wait_seconds
        else:
            # Exponential backoff: base_wait * 2^attempt
            backoff = base_wait * (2 ** attempt)

        # Add jitter (0-1 seconds) to prevent thundering herd
        backoff += random.uniform(0, 1)

        # Cap at max_wait
        backoff = min(backoff, max_wait)

        print(f"Rate limited. Retrying in {backoff:.1f}s (attempt {attempt + 1}/{max_retries})")
        time.sleep(backoff)

    # All retries exhausted
    print(f"Failed after {max_retries} retries")
    return response

# Usage
response = exponential_backoff_request(
    "https://api.upstream.example.com/api/v1/uploads/",
    headers={"Authorization": f"Bearer {access_token}"}
)

if response.status_code == 200:
    data = response.json()
    print(f"Success: {data['count']} uploads")
else:
    print(f"Error: {response.status_code}")
```

**JavaScript example with jitter:**

```javascript
async function exponentialBackoffRequest(
  url,
  options = {},
  maxRetries = 5,
  baseWait = 1000,
  maxWait = 60000
) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const response = await fetch(url, options);

    // Success or non-rate-limit error
    if (response.status !== 429) {
      return response;
    }

    // Rate limited - calculate backoff
    const errorData = await response.json();
    let waitMs;

    if (errorData.error?.details?.wait_seconds) {
      // Use wait_seconds from API response
      waitMs = errorData.error.details.wait_seconds * 1000;
    } else {
      // Exponential backoff: baseWait * 2^attempt
      waitMs = baseWait * Math.pow(2, attempt);
    }

    // Add jitter (0-1000ms) to prevent thundering herd
    waitMs += Math.random() * 1000;

    // Cap at maxWait
    waitMs = Math.min(waitMs, maxWait);

    console.log(`Rate limited. Retrying in ${(waitMs / 1000).toFixed(1)}s (attempt ${attempt + 1}/${maxRetries})`);
    await new Promise(resolve => setTimeout(resolve, waitMs));
  }

  // All retries exhausted
  console.error(`Failed after ${maxRetries} retries`);
  return await fetch(url, options);
}

// Usage
const response = await exponentialBackoffRequest(
  'https://api.upstream.example.com/api/v1/uploads/',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

if (response.ok) {
  const data = await response.json();
  console.log(`Success: ${data.count} uploads`);
} else {
  console.error(`Error: ${response.status}`);
}
```

### Circuit Breaker Pattern

**Purpose:** Stop making requests after sustained failures to prevent cascading failures.

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing - stop requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        """
        Args:
            failure_threshold: Consecutive failures before opening circuit
            timeout: Seconds to wait before testing recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if time.time() - self.last_failure_time >= self.timeout:
                print("Circuit breaker: Testing recovery (half-open)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Check if rate limited
            if hasattr(result, 'status_code') and result.status_code == 429:
                self._record_failure()
                return result

            # Success - reset circuit breaker
            self._record_success()
            return result

        except Exception as e:
            self._record_failure()
            raise

    def _record_success(self):
        """Reset failure count on success."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
        print("Circuit breaker: Closed (recovered)")

    def _record_failure(self):
        """Increment failure count and open circuit if threshold exceeded."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"Circuit breaker: OPEN (failed {self.failure_count} times)")

# Usage
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)

def api_request(url, headers):
    return requests.get(url, headers=headers)

try:
    response = circuit_breaker.call(
        api_request,
        "https://api.upstream.example.com/api/v1/uploads/",
        {"Authorization": f"Bearer {access_token}"}
    )
except Exception as e:
    print(f"Circuit breaker prevented request: {e}")
```

### Request Queue Pattern

**Purpose:** Queue requests instead of failing immediately on rate limit.

```python
import queue
import threading
import time

class RateLimitedQueue:
    def __init__(self, requests_per_second=1):
        """
        Args:
            requests_per_second: Maximum request rate
        """
        self.queue = queue.Queue()
        self.requests_per_second = requests_per_second
        self.running = False
        self.worker_thread = None

    def start(self):
        """Start background worker thread."""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker)
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def stop(self):
        """Stop background worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()

    def enqueue(self, func, *args, **kwargs):
        """Add request to queue."""
        self.queue.put((func, args, kwargs))

    def _worker(self):
        """Background worker that processes queue with rate limiting."""
        while self.running:
            try:
                # Get next request (wait up to 1 second)
                func, args, kwargs = self.queue.get(timeout=1)

                # Execute request
                try:
                    result = func(*args, **kwargs)
                    print(f"Request completed: {result.status_code}")
                except Exception as e:
                    print(f"Request failed: {e}")

                # Rate limit: wait between requests
                time.sleep(1.0 / self.requests_per_second)

            except queue.Empty:
                # No requests in queue
                continue

# Usage
request_queue = RateLimitedQueue(requests_per_second=0.5)  # 1 request per 2 seconds
request_queue.start()

# Enqueue requests
for i in range(10):
    request_queue.enqueue(
        requests.get,
        "https://api.upstream.example.com/api/v1/uploads/",
        headers={"Authorization": f"Bearer {access_token}"}
    )

print("Requests queued. Processing in background...")
time.sleep(30)  # Wait for queue to process
request_queue.stop()
```

---

## Debugging Workflows

### Quick Diagnosis Checklist

Use this checklist for rapid initial diagnosis:

```
□ Check HTTP status code in response (401/403/404/429/500)
□ Read error.message and error.code fields from response body
□ Verify Authorization header is present and formatted correctly
□ Decode JWT token and check exp claim (expiration timestamp)
□ Review endpoint-specific rate limits (see Rate Limits table)
□ Capture X-Request-Id header value from response
□ Check API status page: https://status.upstream.example.com
□ Review application logs for request patterns or errors
```

### Systematic Debugging by Error Type

#### For Authentication Issues (401)

**Step 1: Test login endpoint**
```bash
curl -X POST https://api.upstream.example.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "your_password"}'  # pragma: allowlist secret
```

**Step 2: Verify token storage and retrieval**
```python
# Check token is stored correctly
print(f"Access token: {access_token[:20]}...")
print(f"Refresh token: {refresh_token[:20]}...")
```

**Step 3: Check token format in Authorization header**
```bash
# Use -v flag to see request headers
curl -v -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN" 2>&1 | grep "Authorization"
```

**Step 4: Decode token and verify claims**
```python
import jwt

token = "YOUR_ACCESS_TOKEN"
payload = jwt.decode(token, options={"verify_signature": False})
print(f"User ID: {payload['user_id']}")
print(f"Username: {payload['username']}")
print(f"Expires: {payload['exp']} (Unix timestamp)")

import time
current_time = time.time()
if payload['exp'] < current_time:
    print("Token is EXPIRED")
else:
    expires_in = (payload['exp'] - current_time) / 60
    print(f"Token expires in {expires_in:.1f} minutes")
```

**Step 5: Test token verification endpoint**
```bash
curl -X POST https://api.upstream.example.com/api/v1/auth/token/verify/ \
  -H "Content-Type: application/json" \
  -d '{"token": "YOUR_ACCESS_TOKEN"}'
```

#### For Permission Issues (403)

**Step 1: Confirm user role**
```python
# Role is stored in database, not JWT token
# Query user profile endpoint or check admin panel
```

**Step 2: Verify resource belongs to user's customer**
```bash
# Get resource details to see customer_id
curl -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check customer_id matches your authenticated user's customer
```

**Step 3: Check endpoint documentation for required permissions**
- See [API_EXAMPLES.md](./API_EXAMPLES.md) for endpoint permission requirements
- Admin-only endpoints clearly marked with "Requires customer_admin role"

**Step 4: Test with known accessible resource**
```bash
# GET (read) operations should work for all roles
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# POST (write) operations require admin role
curl -X POST https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.csv"}'
```

#### For Rate Limit Issues (429)

**Step 1: Identify throttled endpoint**
```bash
# Error response includes wait_seconds
curl -X POST https://api.upstream.example.com/api/v1/reports/trigger/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "error": {
#     "code": "throttled",
#     "message": "Request was throttled. Please try again later.",
#     "details": {"wait_seconds": 3600}
#   }
# }
```

**Step 2: Check rate limit for endpoint**
- See [Rate Limits by Endpoint](#rate-limits-by-endpoint) table
- Identify which limit was exceeded

**Step 3: Audit request patterns**
```python
# Add request logging to identify burst patterns
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def logged_api_request(url, headers):
    logger.info(f"API request: {url} at {time.time()}")
    response = requests.get(url, headers=headers)
    logger.info(f"API response: {response.status_code}")
    return response
```

**Step 4: Implement backoff and retry**
- See [Exponential Backoff Implementation](#exponential-backoff-implementation)

---

## Testing and Validation

### Using curl for Debugging

**Verbose mode (-v) to see headers:**
```bash
curl -v -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Shows:
# > GET /api/v1/uploads/42/ HTTP/1.1
# > Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
# < HTTP/1.1 200 OK
# < X-Request-Id: abc123-def456
# < X-Request-Duration-Ms: 45
# < ETag: "abc123"
```

**Save response headers to file:**
```bash
curl -D headers.txt -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Inspect headers
cat headers.txt
```

**Test authentication flow end-to-end:**
```bash
# Step 1: Login
ACCESS_TOKEN=$(curl -X POST https://api.upstream.example.com/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "your_password"}'  # pragma: allowlist secret \
  | jq -r '.access')

echo "Access token: $ACCESS_TOKEN"

# Step 2: Use token
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Step 3: Verify token
curl -X POST https://api.upstream.example.com/api/v1/auth/token/verify/ \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$ACCESS_TOKEN\"}"
```

**Trigger rate limit intentionally:**
```bash
# Send 10 requests rapidly to trigger burst limit
for i in {1..10}; do
  echo "Request $i"
  curl -X POST https://api.upstream.example.com/api/v1/reports/trigger/ \
    -H "Authorization: Bearer YOUR_TOKEN"
  echo ""
done
```

### Common Pitfalls

**1. Using refresh token in Authorization header**

```bash
# WRONG: Using refresh token for API request
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer REFRESH_TOKEN"
# Response: 401 (token not valid)

# CORRECT: Use access token for API requests
curl -X GET https://api.upstream.example.com/api/v1/uploads/ \
  -H "Authorization: Bearer ACCESS_TOKEN"

# CORRECT: Use refresh token ONLY for token refresh endpoint
curl -X POST https://api.upstream.example.com/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "REFRESH_TOKEN"}'
```

**2. Not handling token expiration**

```python
# BAD: Never refreshes token
access_token = login()
while True:
    response = api_request(access_token)  # Fails after 1 hour
    time.sleep(60)

# GOOD: Check expiration before each request
access_token = login()
while True:
    if is_token_expired(access_token):
        access_token = refresh_token()
    response = api_request(access_token)
    time.sleep(60)
```

**3. Ignoring wait_seconds in 429 response**

```python
# BAD: Retry immediately without backoff
for attempt in range(5):
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        continue  # Retry immediately - will fail again

# GOOD: Use wait_seconds from response
for attempt in range(5):
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        wait_seconds = response.json()["error"]["details"]["wait_seconds"]
        time.sleep(wait_seconds)
```

**4. Retrying 500 errors immediately**

```python
# BAD: Amplifies server load during incidents
for attempt in range(10):
    response = requests.get(url, headers=headers)
    if response.status_code == 500:
        continue  # Immediate retry makes problem worse

# GOOD: Exponential backoff with max retries
for attempt in range(3):  # Only 3 retries
    response = requests.get(url, headers=headers)
    if response.status_code == 500:
        time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

**5. Not capturing X-Request-Id before error**

```python
# BAD: Can't provide X-Request-Id to support
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except:
    print("Error occurred")  # No request ID captured

# GOOD: Always capture response headers
response = requests.get(url, headers=headers)
request_id = response.headers.get("X-Request-Id")
if response.status_code >= 400:
    print(f"Error {response.status_code}. Request ID: {request_id}")
```

---

## Error Response Format

All API errors return a standardized JSON structure:

```json
{
  "error": {
    "code": "error_code_string",
    "message": "Human-readable error description",
    "details": {
      // Additional context (optional)
    }
  }
}
```

### Error Code Catalog

| Error Code | HTTP Status | Description | Details Field |
|------------|-------------|-------------|---------------|
| `authentication_failed` | 401 | Missing/invalid credentials | null |
| `permission_denied` | 403 | Insufficient permissions | `{"detail": "reason"}` |
| `not_found` | 404 | Resource doesn't exist | null |
| `throttled` | 429 | Rate limit exceeded | `{"wait_seconds": 3600}` |
| `validation_error` | 400 | Invalid input data | `{"field_name": ["error"]}` |
| `parse_error` | 400 | Malformed request body | `{"detail": "reason"}` |
| `method_not_allowed` | 405 | HTTP method not supported | null |
| `unsupported_media_type` | 415 | Invalid Content-Type | null |
| `internal_server_error` | 500 | Unexpected server error | null |

### Error Response Examples

**Validation error (400):**
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input data.",
    "details": {
      "filename": ["This field is required."],
      "date_min": ["Date has wrong format. Use YYYY-MM-DD."]
    }
  }
}
```

**Authentication failed (401):**
```json
{
  "error": {
    "code": "authentication_failed",
    "message": "Authentication credentials were not provided or are invalid.",
    "details": null
  }
}
```

**Permission denied (403):**
```json
{
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to perform this action.",
    "details": {
      "detail": "Requires customer_admin role."
    }
  }
}
```

**Not found (404):**
```json
{
  "error": {
    "code": "not_found",
    "message": "The requested resource was not found.",
    "details": null
  }
}
```

**Throttled (429):**
```json
{
  "error": {
    "code": "throttled",
    "message": "Request was throttled. Please try again later.",
    "details": {
      "wait_seconds": 3600
    }
  }
}
```

**Internal server error (500):**
```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected error occurred. Please try again later.",
    "details": null
  }
}
```

### Parsing Error Responses

**Python:**
```python
response = requests.get(url, headers=headers)

if response.status_code >= 400:
    error_data = response.json().get("error", {})
    error_code = error_data.get("code")
    error_message = error_data.get("message")
    error_details = error_data.get("details")

    print(f"Error: {error_code}")
    print(f"Message: {error_message}")

    if error_code == "throttled" and error_details:
        wait_seconds = error_details.get("wait_seconds", 60)
        print(f"Rate limited. Wait {wait_seconds} seconds.")

    elif error_code == "validation_error" and error_details:
        print("Validation errors:")
        for field, errors in error_details.items():
            print(f"  {field}: {', '.join(errors)}")
```

**JavaScript:**
```javascript
const response = await fetch(url, options);

if (!response.ok) {
  const errorData = await response.json();
  const error = errorData.error || {};

  console.error(`Error: ${error.code}`);
  console.error(`Message: ${error.message}`);

  if (error.code === 'throttled' && error.details) {
    const waitSeconds = error.details.wait_seconds || 60;
    console.log(`Rate limited. Wait ${waitSeconds} seconds.`);
  }

  if (error.code === 'validation_error' && error.details) {
    console.error('Validation errors:');
    for (const [field, errors] of Object.entries(error.details)) {
      console.error(`  ${field}: ${errors.join(', ')}`);
    }
  }
}
```

---

## Support Escalation

### When to Contact Support

Contact support if:

1. **Persistent 500 errors** despite troubleshooting and retries
2. **Rate limits appear misconfigured** or unreasonably restrictive for your use case
3. **Authentication fails** after verifying credentials are correct and tokens are valid
4. **Data inconsistencies** such as missing or incorrect data in API responses
5. **Unexpected 404s** for resources you believe should exist
6. **None of the troubleshooting steps** in this guide resolve your issue

### Information to Provide

When contacting support, include:

**Required:**
1. **X-Request-Id header value** (critical for log lookup)
   ```bash
   curl -v -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
     -H "Authorization: Bearer YOUR_TOKEN" 2>&1 | grep "X-Request-Id"
   ```

2. **Timestamp of error** (with timezone)
   ```
   2024-01-27T15:30:45Z
   ```

3. **Full error response body**
   ```json
   {
     "error": {
       "code": "internal_server_error",
       "message": "An unexpected error occurred. Please try again later.",
       "details": null
     }
   }
   ```

**Helpful:**
4. **Curl command to reproduce** (with credentials redacted)
   ```bash
   curl -X GET https://api.upstream.example.com/api/v1/uploads/42/ \
     -H "Authorization: Bearer REDACTED"
   ```

5. **Steps to reproduce**
   ```
   1. Login to obtain access token
   2. Call GET /api/v1/claims/?page_size=1000
   3. Observe 500 error
   ```

6. **Relevant authentication token** (for auth issues only - DO NOT share refresh tokens)
   ```
   eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
   ```

7. **Expected vs actual behavior**
   ```
   Expected: Return 200 with claims data
   Actual: Return 500 internal server error
   ```

### Contact Information

**Email:** support@upstream.example.com

**Subject line format:**
```
API Error: [error code] - [brief description]
```

**Example:**
```
Subject: API Error: 500 - Persistent error on GET /api/v1/claims/

Body:
X-Request-Id: abc123-def456-789
Timestamp: 2024-01-27T15:30:45Z
Endpoint: GET /api/v1/claims/?page_size=1000

Error response:
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected error occurred. Please try again later.",
    "details": null
  }
}

Steps to reproduce:
1. Authenticate with credentials
2. Call GET /api/v1/claims/?page_size=1000
3. Observe 500 error consistently

Troubleshooting attempted:
- Reduced page_size to 100 (still fails)
- Retried after 5 minutes (still fails)
- Tested with different date ranges (still fails)

Expected behavior:
Return 200 with claims data
```

### API Status Page

**URL:** https://status.upstream.example.com

**What it provides:**
- Real-time API status (operational / degraded / outage)
- Active incidents and their impact
- Scheduled maintenance windows
- Historical uptime data
- Subscribe to status updates (email/SMS)

**When to check:**
- Before contacting support (issue may already be known)
- After deployment or maintenance windows
- If experiencing widespread errors

---

## Additional Resources

### Documentation

- **[API Examples](./API_EXAMPLES.md)** - Comprehensive curl examples for all endpoints
- **[API Versioning](./API_VERSIONING.md)** - API versioning strategy and compatibility (if exists)
- **[Testing Guide](./TESTING.md)** - Setting up test environments and fixtures (if exists)

### External Tools

- **JWT Token Decoder:** https://jwt.io
  - Decode JWT tokens to inspect claims (exp, user_id, etc.)
  - **Warning:** Don't paste production tokens into third-party sites (use local decoding)

- **Base64 Decoder:** Built into most systems
  ```bash
  # Decode JWT payload (middle section between dots)
  echo "eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImRvY3RvciIsImV4cCI6MTcwNjI4NDgwMH0" | base64 -d | jq  # pragma: allowlist secret
  ```

### Code Examples Repository

For complete working examples in multiple languages:
- Python client library (if available)
- JavaScript/TypeScript SDK (if available)
- Example applications (if available)

### Community and Support

- **Email:** support@upstream.example.com
- **Status Page:** https://status.upstream.example.com
- **Documentation:** https://docs.upstream.example.com (if exists)

---

## Appendix: Quick Reference

### HTTP Status Codes

| Code | Name | Meaning | Action |
|------|------|---------|--------|
| 200 | OK | Success | Process response data |
| 201 | Created | Resource created | Resource available at Location header |
| 202 | Accepted | Async processing | Poll for completion |
| 304 | Not Modified | ETag match | Use cached response |
| 400 | Bad Request | Invalid input | Fix validation errors |
| 401 | Unauthorized | Auth missing/invalid | Provide/refresh token |
| 403 | Forbidden | Insufficient permissions | Check role requirements |
| 404 | Not Found | Resource not found | Verify ID and ownership |
| 405 | Method Not Allowed | Wrong HTTP method | Use correct method (GET/POST/etc) |
| 429 | Too Many Requests | Rate limited | Wait and retry with backoff |
| 500 | Internal Server Error | Server error | Retry, then contact support |

### Token Expiration Reference

| Token Type | Expiration | Used For | Endpoint |
|------------|-----------|----------|----------|
| Access | 1 hour | API requests | All endpoints (Authorization header) |
| Refresh | 24 hours | Get new access token | `/api/v1/auth/token/refresh/` only |

### Rate Limit Quick Reference

| Operation Type | Limit | Typical Endpoints |
|---------------|-------|-------------------|
| Authentication | 5/hour | `/api/v1/auth/token/` |
| Bulk operations | 20/hour | File uploads |
| Report generation | 10/hour | `/api/v1/reports/trigger/` |
| Read operations | 2000/hour | GET endpoints |
| Write operations | 500/hour | POST/PUT/DELETE |

---

**Last Updated:** 2024-01-27

For questions or feedback on this guide, contact: support@upstream.example.com

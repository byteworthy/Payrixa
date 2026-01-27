# API Specifications: Webhooks & Internal APIs

**Document:** 05-api-specifications.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

This document specifies all API endpoints for the Upstream platform, including:
- External webhook receivers (EHR integrations)
- Internal APIs (risk scoring, pre-submission checks)
- Query APIs (UI data fetching)

---

## External Webhook API

### Endpoint: EHR Webhook Receiver

**URL:** `POST /api/v1/webhooks/ehr/{provider}/`

**Supported Providers:** `epic`, `cerner`, `athenahealth`

**Purpose:** Receive real-time claim submission events from EHR systems

**Authentication:** HMAC-SHA256 signature verification (no bearer tokens)

**Headers:**
```
X-Customer-ID: <uuid>
X-Signature: <hmac-sha256 hex digest>
X-Idempotency-Key: <uuid>
X-Timestamp: <iso8601>
Content-Type: application/json
```

**Request Body (Epic FHIR):**
```json
{
  "resourceType": "Claim",
  "id": "claim-12345",
  "status": "active",
  "type": {"coding": [{"code": "professional"}]},
  "patient": {"reference": "Patient/67890"},
  "billablePeriod": {"start": "2026-01-20"},
  "provider": {"reference": "Organization/aetna"},
  "item": [{
    "sequence": 1,
    "productOrService": {"coding": [{"code": "97162"}]},
    "net": {"value": 250.00, "currency": "USD"}
  }]
}
```

**Response (200 OK):**
```json
{
  "status": "accepted",
  "claim_id": "claim-12345",
  "task_id": "celery-task-uuid",
  "message": "Webhook received, processing in background"
}
```

**Response (400 Bad Request):**
```json
{
  "error": "invalid_signature",
  "message": "HMAC signature verification failed"
}
```

**Response (409 Conflict - Duplicate):**
```json
{
  "status": "duplicate",
  "claim_id": "claim-12345",
  "message": "Already processed"
}
```

**Rate Limiting:** 100 requests/minute per customer

**Latency Target:** <50ms (p95)

**Implementation:** See `01-detection-layer.md` for full implementation

---

## Internal Risk Scoring API

### Endpoint: Pre-Submission Risk Check

**URL:** `POST /api/v1/claims/pre-submission-check/`

**Purpose:** Calculate risk score for claim before submission

**Authentication:** JWT bearer token

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "customer_id": "uuid",
  "payer": "Aetna MA",
  "cpt": "97162",
  "diagnosis_codes": ["M54.5", "M54.9"],
  "modifiers": ["GO"],
  "patient_id": "PT-001",
  "service_date": "2026-01-27"
}
```

**Response (200 OK):**
```json
{
  "risk_score": 72,
  "confidence": 0.85,
  "recommendation": "AUTO-FIX: add_modifiers | MANUAL: Update diagnosis codes",
  "factors": [
    {
      "factor": "historical_denial_rate",
      "value": 0.45,
      "weight": 0.40,
      "contribution": 18.0,
      "details": "Based on 150 historical claims"
    },
    {
      "factor": "missing_modifiers",
      "value": 1.0,
      "weight": 0.20,
      "contribution": 20.0,
      "details": "Missing: -59"
    }
  ],
  "auto_fix_actions": [
    {
      "action": "add_modifiers",
      "params": {"modifiers": ["-59"]}
    }
  ],
  "hold_for_review": true
}
```

**Latency Target:** <500ms (p95)

---

### Endpoint: Query Risk Score

**URL:** `GET /api/v1/claims/{claim_id}/risk-score/`

**Purpose:** Retrieve most recent risk score for a claim

**Authentication:** JWT bearer token

**Response (200 OK):**
```json
{
  "claim_id": "claim-12345",
  "risk_score": 72,
  "confidence": 0.85,
  "factors": [...],
  "recommendation": "...",
  "calculated_at": "2026-01-27T10:30:00Z"
}
```

---

## Authorization Management API

### Endpoint: List Expiring Authorizations

**URL:** `GET /api/v1/authorizations/expiring/`

**Purpose:** Get authorizations expiring within N days

**Authentication:** JWT bearer token

**Query Parameters:**
- `days` (optional, default=30): Days until expiration
- `status` (optional, default=ACTIVE): Filter by status
- `payer` (optional): Filter by payer

**Response (200 OK):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "auth_number": "AUTH-12345",
      "patient_identifier": "PT-001",
      "payer": "Blue Cross",
      "service_type": "ABA Therapy",
      "auth_expiration_date": "2026-02-26",
      "days_until_expiration": 30,
      "units_authorized": 52,
      "units_used": 15,
      "units_remaining": 37,
      "auto_reauth_enabled": true
    }
  ]
}
```

---

### Endpoint: Create Authorization

**URL:** `POST /api/v1/authorizations/`

**Purpose:** Create new authorization record

**Request Body:**
```json
{
  "auth_number": "AUTH-12345",
  "patient_identifier": "PT-001",
  "payer": "Blue Cross",
  "service_type": "ABA Therapy",
  "cpt_codes": ["97151", "97152"],
  "auth_start_date": "2026-01-01",
  "auth_expiration_date": "2026-04-01",
  "units_authorized": 52,
  "reauth_lead_time_days": 21,
  "auto_reauth_enabled": false
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "auth_number": "AUTH-12345",
  "created_at": "2026-01-27T10:30:00Z"
}
```

---

## Execution Log API

### Endpoint: Query Execution Logs

**URL:** `GET /api/v1/execution-logs/`

**Purpose:** Audit trail of autonomous actions

**Query Parameters:**
- `customer_id` (required): Filter by customer
- `action_type` (optional): Filter by action type
- `result` (optional): Filter by result (SUCCESS, FAILED, ESCALATED)
- `start_date` (optional): Filter by date range
- `end_date` (optional): Filter by date range

**Response (200 OK):**
```json
{
  "count": 25,
  "results": [
    {
      "id": "uuid",
      "rule_name": "Auto-submit ABA reauth requests",
      "action_taken": "submit_reauth_request",
      "result": "SUCCESS",
      "details": {
        "confirmation_number": "REF-67890",
        "payer": "Blue Cross"
      },
      "execution_time_ms": 3500,
      "executed_at": "2026-01-27T06:15:00Z"
    }
  ]
}
```

---

## Network Intelligence API

### Endpoint: Industry Alerts

**URL:** `GET /api/v1/intelligence/industry-alerts/`

**Purpose:** Get recent industry-wide payer behavior alerts

**Query Parameters:**
- `payer` (optional): Filter by payer
- `days` (optional, default=7): Alert recency

**Response (200 OK):**
```json
{
  "count": 3,
  "results": [
    {
      "payer": "Humana MA",
      "denial_reason": "Medical Necessity",
      "affected_cpt": "97162",
      "customers_affected": 8,
      "total_denials": 47,
      "detected_at": "2026-01-25T14:30:00Z",
      "likely_cause": "Policy change or system issue",
      "recommended_action": "Review Humana bulletins; Upstream auto-updated rules"
    }
  ]
}
```

---

## Authentication & Security

### JWT Token Format

**Header:**
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "customer-uuid",
  "iss": "https://upstream.app",
  "iat": 1706356800,
  "exp": 1706360400,
  "scope": ["read:claims", "write:claims", "read:authorizations"]
}
```

### HMAC Webhook Signature

**Algorithm:** HMAC-SHA256

**Secret:** Per-customer webhook secret (stored in IntegrationConnection)

**Calculation:**
```python
signature = hmac.new(
    secret.encode(),
    request.body,
    hashlib.sha256
).hexdigest()
```

**Verification:**
```python
expected = calculate_signature(body, secret)
is_valid = hmac.compare_digest(signature, expected)
```

---

## Rate Limiting

### Limits by Endpoint

| Endpoint | Rate Limit | Burst |
|----------|-----------|-------|
| EHR Webhook | 100/min per customer | 150 |
| Risk Scoring | 60/min per customer | 100 |
| Query APIs | 300/min per customer | 500 |
| Authorization CRUD | 60/min per customer | 100 |

### Headers in Response

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1706357400
```

### 429 Too Many Requests Response

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit of 100 requests per minute exceeded",
  "retry_after": 45
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {
    "field": "Additional context",
    "request_id": "uuid"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_signature` | 400 | HMAC signature verification failed |
| `invalid_payload` | 400 | Request body validation failed |
| `connection_not_found` | 404 | EHR integration not configured |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Unexpected server error |

---

## Webhook Retry Policy

### Retry Strategy

- **Retry Count:** Up to 3 attempts
- **Backoff:** Exponential (2^retry_count seconds)
- **Timeout:** 30 seconds per attempt

### Retry Example

```
Attempt 1: Immediate (0s)
Attempt 2: After 2s
Attempt 3: After 4s
Attempt 4: After 8s
Give up: After 3 failures
```

### Dead Letter Queue

Failed webhooks after 3 retries → Move to dead letter queue for manual review

---

**Next:** See `06-deployment-infrastructure.md` for GCP deployment setup.

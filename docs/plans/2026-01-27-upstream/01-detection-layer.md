# Detection Layer: Five Early Warning Mechanisms

**Document:** 01-detection-layer.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

The Detection Layer identifies payer risk BEFORE it impacts revenue. Five mechanisms work together to provide 30+ days advance warning vs industry standard 7-14 day reactive detection.

**Philosophy:** Preventive alerts over reactive reports.

---

## Mechanism #1: Calendar-Based Alerts

**Complexity:** Easy (2-4 weeks)
**Advantage:** 30-day advance notice vs 0-day notice

### What It Does

Tracks TIME-BASED EVENTS that will occur in the future:
- Authorization expirations (ABA therapy, PT/OT, imaging)
- Certification renewals (home health)
- Contract term expirations (dialysis MA plans)

### Data Flow

```
Operator uploads CSV with authorization data (manual, one-time)
                    ↓
Upstream stores Authorization records (automatic)
                    ↓
Daily Celery task checks expiration dates (automatic, 6 AM UTC)
                    ↓
Creates AlertEvent 30 days before expiration (automatic)
                    ↓
Email/Slack notification sent to operator (automatic)
                    ↓
Operator acts: Calls payer for reauthorization (manual)
```

**Timeline:** 30-day advance notice (vs 0 notice if not tracked)

### Implementation Requirements

**Database Model:**
```python
class Authorization(models.Model):
    customer = ForeignKey(Customer, on_delete=CASCADE)
    auth_number = CharField(max_length=100, unique=True)
    patient_identifier = CharField(max_length=100)  # De-identified
    payer = CharField(max_length=255, db_index=True)
    service_type = CharField(max_length=100)  # "ABA Therapy", "PT", etc.
    cpt_codes = JSONField(default=list)

    # Date tracking
    auth_start_date = DateField()
    auth_expiration_date = DateField(db_index=True)  # KEY for alerting

    # Unit tracking (for ABA)
    units_authorized = IntegerField()
    units_used = IntegerField(default=0)

    # Status
    status = CharField(max_length=20, choices=[
        ('ACTIVE', 'Active'),
        ('EXPIRING_SOON', 'Expiring Soon'),
        ('EXPIRED', 'Expired'),
        ('RENEWED', 'Renewed'),
    ], default='ACTIVE', db_index=True)

    # Payer-specific reauth timing
    reauth_lead_time_days = IntegerField(default=21)
    # Blue Cross: 21 days, Aetna: 30 days, UHC: 14 days

    # Autonomous execution flag
    auto_reauth_enabled = BooleanField(default=False)

    last_alert_sent = DateTimeField(null=True, blank=True)
```

**Daily Background Task:**
```python
@celery_app.task
@scheduled(cron='0 6 * * *')  # 6 AM UTC daily
def check_expiring_authorizations():
    """
    Daily scan for expiring authorizations.
    Creates alerts 30 days before expiration (configurable per payer).
    """
    today = timezone.now().date()

    for customer in Customer.objects.filter(is_active=True):
        expiring = Authorization.objects.filter(
            customer=customer,
            status='ACTIVE',
            last_alert_sent__isnull=True
        ).annotate(
            days_until_expiration=ExpressionWrapper(
                F('auth_expiration_date') - today,
                output_field=DurationField()
            )
        ).filter(
            days_until_expiration__lte=F('reauth_lead_time_days')
        )

        for auth in expiring:
            if auth.auto_reauth_enabled:
                # AUTONOMOUS: Execute reauth without approval
                execute_auto_reauth.delay(auth.id)
            else:
                # TRADITIONAL: Alert operator
                dispatch_authorization_expiring_alert.delay(auth.id)

            auth.status = 'EXPIRING_SOON'
            auth.last_alert_sent = timezone.now()
            auth.save(update_fields=['status', 'last_alert_sent'])
```

**Alert Template:**
```
Subject: Authorization Expiring in {days} Days - Action Required

Authorization {auth_number} for {patient_id} expires on {expiration_date}.

Service: {service_type}
Payer: {payer}
Units Used: {units_used} / {units_authorized} ({percentage}%)

Reauthorization Deadline: {reauth_deadline_date}

Action Required:
- Contact {payer} for reauthorization request
- Provide utilization report ({units_used} units delivered)
- Submit reauth documentation by {reauth_deadline_date}

Impact if not renewed:
- Service interruption starting {expiration_date}
- Estimated revenue at risk: ${revenue_estimate}

[View Authorization Details] [Mark as Renewed]
```

### Time Savings

- **Before:** Operator manually tracks 100+ authorizations in spreadsheet
- **After:** Upstream alerts 30 days early (configurable per payer)
- **Result:** Zero missed expirations, zero "surprise denial" calls

### ABA Provider ROI

- 15-30% of ABA clinics have authorization lapse denials
- Average authorization: $6,000-8,000 per patient
- 15-20 authorizations per clinic lapse per year
- **Total prevented denials:** $120K+ per clinic annually

---

## Mechanism #2: Real-Time EHR Integration

**Complexity:** Medium (2-4 weeks for Epic, +1 week per additional EHR)
**Advantage:** Same-day warning vs 1 week lag

### What It Does

Automatically pulls claims data as soon as they're submitted (not weekly batch):
- Claim submission events via webhook
- Real-time risk scoring (within 2 seconds)
- Immediate high-risk alerts

### Data Flow

```
Operator submits claim in EHR (Epic/Cerner/athenahealth)
                    ↓
EHR triggers webhook to Upstream (automatic, <1 second)
                    ↓
Webhook receiver validates signature + idempotency (50ms)
                    ↓
Celery task processes claim + calculates risk score (2s)
                    ↓
If risk score > 60: Create AlertEvent (automatic)
                    ↓
Email/Slack notification sent immediately (automatic)
                    ↓
Operator decides: Fix claim or submit anyway (manual)
```

**Timeline:** Same-day warning (vs 1 week to find out it denied)

### EHR Connector Architecture

**Base Abstraction:**
```python
# upstream/integrations/ehr/base.py

class BaseEHRConnector(ABC):
    """Abstract base class for EHR integrations."""

    @abstractmethod
    def authenticate(self, credentials: dict) -> Token:
        """OAuth2 or API key authentication."""
        pass

    @abstractmethod
    def parse_webhook(self, payload: dict, headers: dict) -> ClaimSubmissionEvent:
        """Parse EHR-specific webhook format."""
        pass

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook authenticity (HMAC-SHA256)."""
        pass
```

**Epic FHIR R4 Implementation:**
```python
# upstream/integrations/ehr/epic.py

class EpicFHIRConnector(BaseEHRConnector):
    """Epic FHIR R4 connector (SMART on FHIR)."""

    def authenticate(self, credentials: dict) -> Token:
        """
        OAuth2 + SMART on FHIR authentication.
        Credentials stored encrypted in Google Secret Manager.
        """
        auth_url = f"{credentials['base_url']}/oauth2/authorize"
        token_url = f"{credentials['base_url']}/oauth2/token"

        # OAuth2 authorization code flow
        auth_response = requests.post(auth_url, data={
            'client_id': credentials['client_id'],
            'redirect_uri': credentials['redirect_uri'],
            'response_type': 'code',
            'scope': 'system/Claim.read'
        })

        # Exchange code for token
        token_response = requests.post(token_url, data={
            'grant_type': 'authorization_code',
            'code': auth_response.json()['code'],
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret']
        })

        return Token(
            access_token=token_response.json()['access_token'],
            expires_at=datetime.now() + timedelta(seconds=token_response.json()['expires_in'])
        )

    def parse_webhook(self, payload: dict, headers: dict) -> ClaimSubmissionEvent:
        """
        Parse Epic FHIR Claim resource.

        Epic webhook payload:
        {
            "resourceType": "Claim",
            "id": "claim-12345",
            "status": "active",
            "patient": {"reference": "Patient/67890"},
            "provider": {"reference": "Organization/aetna"},
            "item": [{
                "sequence": 1,
                "productOrService": {"coding": [{"code": "97162"}]},
                "net": {"value": 250.00, "currency": "USD"}
            }]
        }
        """
        claim_resource = payload

        # Extract claim details
        claim_id = claim_resource['id']
        patient_id = claim_resource['patient']['reference'].split('/')[-1]
        payer = claim_resource['provider']['reference'].split('/')[-1]

        # Extract CPT + amount from item
        item = claim_resource['item'][0]
        cpt = item['productOrService']['coding'][0]['code']
        billed_amount = item['net']['value']

        return ClaimSubmissionEvent(
            claim_id=claim_id,
            patient_id=patient_id,
            payer=payer,
            cpt=cpt,
            submitted_date=datetime.now(),
            billed_amount=billed_amount
        )

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Epic HMAC-SHA256 signature."""
        secret = self.get_webhook_secret()
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
```

### Webhook Receiver Endpoint

```python
# upstream/integrations/api/views.py

@api_view(['POST'])
@authentication_classes([])  # Authenticated via HMAC signature
@permission_classes([])
@ratelimit(key='header:X-Customer-ID', rate='100/m', method='POST')
def ehr_webhook_receiver(request, provider):
    """
    POST /api/v1/webhooks/ehr/{provider}/

    Real-time webhook receiver for Epic/Cerner/athenahealth.
    Target latency: < 50ms per webhook.

    Headers:
        X-Customer-ID: <uuid>
        X-Signature: <hmac-sha256>
        X-Idempotency-Key: <uuid>
        X-Timestamp: <iso8601>

    Response (200 OK):
        {
            "status": "accepted",
            "claim_id": "claim-12345",
            "task_id": "celery-task-uuid"
        }
    """

    # 1. Idempotency check (< 5ms)
    idempotency_key = request.headers.get('X-Idempotency-Key')
    if idempotency_key:
        cached_response = redis_client.get(f'webhook:idem:{idempotency_key}')
        if cached_response:
            return JsonResponse(json.loads(cached_response), status=200)

    # 2. Signature verification (< 10ms)
    customer_id = request.headers.get('X-Customer-ID')
    signature = request.headers.get('X-Signature')
    connection = IntegrationConnection.objects.get(
        customer_id=customer_id,
        provider=provider,
        enabled=True
    )

    if not verify_webhook_signature(request.body, signature, connection.webhook_secret):
        return JsonResponse({'error': 'invalid_signature'}, status=400)

    # 3. Parse webhook payload (< 20ms)
    connector = get_ehr_connector(provider)
    claim_event = connector.parse_webhook(request.data, request.headers)

    # 4. Dispatch to Celery (< 10ms)
    task = process_claim_submission.delay(
        customer_id=customer_id,
        claim_event=claim_event.dict(),
        idempotency_key=idempotency_key
    )

    # 5. Cache response for idempotency (< 5ms)
    response_data = {
        'status': 'accepted',
        'claim_id': claim_event.claim_id,
        'task_id': task.id
    }

    if idempotency_key:
        redis_client.setex(
            f'webhook:idem:{idempotency_key}',
            86400,  # 24 hours
            json.dumps(response_data)
        )

    return JsonResponse(response_data, status=200)
```

### Time Savings

- **Before:** Claim denies, operator finds out 1 week later, spends $47 to rework
- **After:** Upstream flags IMMEDIATELY after submission, operator fixes same day
- **Result:** Prevent 20-30% of potential denials

---

## Mechanism #3: Payment Timing Trends

**Complexity:** Medium (2-3 weeks)
**Advantage:** 2-3 week early warning of denial spikes

### What It Does

Detects when payers start paying SLOWER (early signal of bigger problems):
- Median payment time increasing (45 days → 52 days)
- Cash flow impact calculation
- Historical correlation: Payment slowdown → denial spike 2 weeks later

### Data Flow

```
Claims paid over time (captured automatically from CSV uploads)
                    ↓
Daily task analyzes last 4 weeks of payment timing (automatic)
                    ↓
Detects worsening trend: 42 → 45 → 48 → 52 days (automatic)
                    ↓
Calculates cash flow impact (automatic)
                    ↓
Creates AlertEvent: "Payment timing degrading" (automatic)
                    ↓
Email notification with cash impact + historical pattern (automatic)
                    ↓
Operator investigates: Calls payer collections (manual)
```

**Timeline:** 2-3 week early warning before denial spike hits

### Payment Timing Analysis

```python
# upstream/services/delayguard.py

class DelayGuardService:
    """
    Enhanced payment timing monitoring with trend analysis.
    """

    def analyze_payment_timing_trend(self, customer: Customer, payer: str) -> Optional[Alert]:
        """
        Analyze 4-week payment timing trend.
        Alert if 3 consecutive weeks of worsening.
        """

        # Get median payment time for last 4 weeks
        week_4 = self._get_median_payment_time(customer, payer, weeks_ago=4)
        week_3 = self._get_median_payment_time(customer, payer, weeks_ago=3)
        week_2 = self._get_median_payment_time(customer, payer, weeks_ago=2)
        week_1 = self._get_median_payment_time(customer, payer, weeks_ago=1)

        # Check for worsening trend
        if week_1 > week_2 > week_3 > week_4:
            trend = "WORSENING"
            days_added = week_1 - week_4
            percent_increase = (days_added / week_4) * 100

            # Calculate cash flow impact
            avg_weekly_revenue = self._calculate_avg_weekly_revenue(customer, payer)
            delayed_revenue = (days_added / 7) * avg_weekly_revenue

            # Historical pattern lookup
            historical_correlation = self._check_historical_pattern(customer, payer)

            return AlertEvent.objects.create(
                customer=customer,
                alert_type='payment_timing_degrading',
                severity='high',
                title=f"Payment Timing Degrading: {payer}",
                description=(
                    f"{payer} payment time increasing:\n"
                    f"Baseline: {week_4} days\n"
                    f"Current: {week_1} days\n"
                    f"Change: +{days_added} days (+{percent_increase:.1f}%)\n\n"
                    f"Cash Impact:\n"
                    f"${delayed_revenue:,.0f} in delayed payments\n\n"
                    f"Historical Pattern:\n"
                    f"{historical_correlation}\n\n"
                    f"Recommended Action:\n"
                    f"Contact {payer} collections about delays\n"
                    f"Prepare for possible policy changes"
                ),
                evidence_payload={
                    'week_4_days': week_4,
                    'week_3_days': week_3,
                    'week_2_days': week_2,
                    'week_1_days': week_1,
                    'trend': trend,
                    'days_added': days_added,
                    'percent_increase': percent_increase,
                    'delayed_revenue': delayed_revenue,
                    'historical_correlation': historical_correlation
                }
            )

        return None

    def _get_median_payment_time(self, customer: Customer, payer: str, weeks_ago: int) -> int:
        """Get median payment time for specific week."""
        end_date = timezone.now() - timedelta(weeks=weeks_ago)
        start_date = end_date - timedelta(weeks=1)

        payment_times = ClaimRecord.objects.filter(
            customer=customer,
            payer=payer,
            outcome='PAID',
            decided_date__gte=start_date,
            decided_date__lt=end_date
        ).annotate(
            payment_time_days=ExpressionWrapper(
                F('decided_date') - F('submitted_date'),
                output_field=DurationField()
            )
        ).values_list('payment_time_days', flat=True)

        if not payment_times:
            return 0

        return int(statistics.median([pt.days for pt in payment_times]))
```

### Time Savings

- **Before:** Denial spike catches you by surprise → reactive crisis management
- **After:** Payment timing degradation detected → proactive investigation
- **Result:** Catch problems 2-3 weeks early

---

## Mechanism #4: Pre-Submission Risk Scoring

**Complexity:** Hard (3-4 weeks)
**Advantage:** Prevent denials at source (20-30% reduction)

### What It Does

Analyzes claims BEFORE operator submits them:
- Historical denial rate lookup (payer + CPT combination)
- Missing modifier detection
- Authorization status check
- Diagnosis-CPT matching validation

### Data Flow

```
Billing staff prepares claim in EHR (manual)
                    ↓
Operator uses pre-submission check UI (manual)
                    ↓
Upstream calculates risk score 0-100 (automatic, <500ms)
                    ↓
Displays risk factors + recommendations (automatic)
                    ↓
Operator decides: Fix issues or submit anyway (manual)
```

**Timeline:** Just-in-time warning (prevents 20-30% of denials)

### Risk Scoring Algorithm

See `02-intelligence-layer.md` for full implementation details.

**Risk Score = weighted sum of:**
1. Historical denial rate (40% weight)
2. Missing required modifiers (20% weight)
3. Recent denial streak (20% weight)
4. Diagnosis-CPT mismatch (10% weight)
5. Authorization status (10% weight)

### Time Savings

- **Before:** Claim denies → $47 to rework it
- **After:** Claim flagged before submission → operator fixes it → paid first time
- **Result:** Prevent 20-30% of denials at source

---

## Mechanism #5: Network Effects

**Complexity:** Very Hard (8+ weeks)
**Advantage:** 2-4 week head start on policy changes

### What It Does

Detects payer policy changes affecting MULTIPLE practices simultaneously:
- Cross-customer pattern aggregation (anonymized)
- If 3+ customers see same denial spike within 48 hours → industry alert
- Proactive notification to ALL customers with that payer

### Data Flow

```
Practice A, B, C all see Humana MA denial spike (automatic detection)
                    ↓
Upstream aggregates pattern: 8 practices affected (automatic)
                    ↓
Creates IndustryAlert: "Humana MA policy change detected" (automatic)
                    ↓
Notifies ALL Humana MA customers (even those not yet affected) (automatic)
                    ↓
Operators read alert → Prepare for policy change (manual)
```

**Timeline:** 2-4 week advance warning (before your practice is affected)

### Network Intelligence

See `02-intelligence-layer.md` for full implementation details.

**Key Concept:** More customers = faster detection. This is Upstream's competitive moat.

---

## Integration Summary

All five mechanisms feed into the same alerting infrastructure:
- **AlertEvent** model (existing)
- **NotificationChannel** model (existing - email, Slack, webhook)
- **AlertRule** model (existing - customer-configurable thresholds)

**Key Difference:** Mechanisms 1-3 are reactive (detect after submission). Mechanisms 4-5 are preventive (detect before impact).

---

## Success Metrics

### Phase 1 (Mechanisms 1-2)
- Authorization reauth alerts: 100% delivery rate, 30-day advance notice
- Real-time webhook processing: <50ms latency
- Same-day high-risk claim alerts: <2s from submission to alert

### Phase 2 (Mechanisms 3-4)
- Payment timing trend detection: 3 consecutive weeks of worsening
- Pre-submission risk score accuracy: >75%
- Denial prevention rate: 20-30%

### Phase 3 (Mechanism 5)
- Cross-customer pattern detection: 48-hour window
- Industry alert coverage: 100% of customers with affected payer
- Detection speed advantage: 2-4 weeks before single-practice detection

---

**Next:** See `02-intelligence-layer.md` for risk scoring and behavioral prediction algorithms.

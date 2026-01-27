# Execution Layer: Autonomous Rules Engine & Payer Portal Automation

**Document:** 03-execution-layer.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

The Execution Layer implements autonomous workflows that execute WITHOUT human approval. This is the core differentiation vs Adonis.

**Philosophy:** Execute first, notify after (opposite of Adonis)

**Key Principle:** Pre-approved rules + comprehensive audit trail = compliance + speed

---

## Component 1: Rules Engine Framework

### Purpose

Evaluate events against pre-configured automation rules and execute actions autonomously.

**Core Concept:** Customers configure rules once ("If authorization expires in 30 days, submit reauth automatically"). System executes continuously without asking permission each time.

### Architecture

```
Event (claim_submitted, authorization_expiring, etc.)
     ↓
Evaluate All Active Rules for Customer
     ↓
Conditions Met? → Create Action
     ↓
Execute Action (NO approval)
     ↓
Log to ExecutionLog (audit trail)
     ↓
Notify Customer (informational)
```

### Implementation

**File:** `upstream/automation/rules_engine.py`

See full implementation in master implementation prompt (Week 1, Task 6).

**Key Classes:**

1. **Event** - Trigger that activates rule evaluation
2. **Action** - Atomic operation to execute
3. **ExecutionResult** - Outcome of action execution
4. **RulesEngine** - Orchestrates evaluation + execution

### Rule Types

**1. Threshold-Based Rules**

Trigger when numeric threshold crossed:
- Risk score > 60 → Hold for review
- Underpayment > $500 → Auto-appeal
- Authorization expires in < 30 days → Submit reauth

**2. Pattern Detection Rules**

Trigger when pattern detected:
- 3 consecutive denials from payer → Escalate to manager
- Denial rate spike > 10% in 3 days → Pause submissions

**3. Calendar-Based Rules**

Trigger on specific dates:
- Authorization expires 2026-02-15 → Submit reauth on 2026-01-15
- Contract renewal due → Send notification 60 days prior

**4. Chained Action Rules**

Trigger based on previous action result:
- IF reauth submitted → THEN check status in 7 days
- IF appeal denied → THEN escalate to secondary appeal

### Example Rule Configurations

**Rule 1: Auto-Submit Authorization Reauth**

```python
AutomationRule.objects.create(
    customer=customer,
    name='Auto-submit ABA reauth requests',
    rule_type='SCHEDULE',
    trigger_event='authorization_expiring',
    conditions={
        'days_until_expiration': {'operator': 'lte', 'value': 30},
        'service_type': 'ABA Therapy'
    },
    action_type='submit_reauth_request',
    action_params={
        'include_utilization_report': True,
        'request_same_units': True
    },
    enabled=True,
    escalate_on_error=True
)
```

**Rule 2: Auto-Appeal Underpayments**

```python
AutomationRule.objects.create(
    customer=customer,
    name='Auto-appeal underpayments over $500',
    rule_type='THRESHOLD',
    trigger_event='underpayment_detected',
    conditions={
        'amount': {'operator': 'gt', 'value': 500},
        'confidence': {'operator': 'gt', 'value': 0.8}
    },
    action_type='generate_and_submit_appeal',
    action_params={
        'consolidate_by_payer': True,
        'attach_supporting_docs': True
    },
    enabled=True,
    escalate_on_error=False  # Don't escalate, just log
)
```

**Rule 3: Hold High-Risk Claims**

```python
AutomationRule.objects.create(
    customer=customer,
    name='Hold claims with risk score > 70',
    rule_type='THRESHOLD',
    trigger_event='claim_submitted',
    conditions={
        'risk_score': {'operator': 'gt', 'value': 70},
        'confidence': {'operator': 'gt', 'value': 0.6}
    },
    action_type='hold_for_review',
    action_params={
        'assign_to': 'billing_manager',
        'priority': 'high'
    },
    enabled=True,
    escalate_on_error=False
)
```

### Audit Trail

**CRITICAL:** Every autonomous action MUST be logged in `ExecutionLog`.

**Fields:**
- `customer` - Who authorized this rule
- `rule` - Which rule triggered execution
- `trigger_event` - What event activated the rule
- `action_taken` - What action was executed
- `result` - SUCCESS | FAILED | ESCALATED
- `details` - Confirmation numbers, error messages, etc.
- `execution_time_ms` - Performance tracking
- `executed_at` - Timestamp

**Compliance Value:** Complete audit trail for HIPAA, SOC2, insurance audits.

---

## Component 2: Payer Portal Automation (RPA)

### Purpose

Automate interactions with payer portals that don't provide APIs. Use Selenium for web automation.

**Supported Payers (Phase 1):**
- Aetna (provider portal)
- UnitedHealthcare (provider portal)
- Blue Cross Blue Shield (varies by state)

**Expansion (Phase 2):**
- Humana
- Cigna
- Tricare

### Architecture

```
Automation Task (submit_reauth, submit_appeal, check_claim_status)
     ↓
PayerPortalAutomation.login(payer)
     ↓
Navigate to form page
     ↓
Fill form fields (patient ID, auth number, etc.)
     ↓
Attach documents (utilization reports, medical records)
     ↓
Submit form
     ↓
Wait for confirmation page
     ↓
Extract confirmation number
     ↓
Return SubmissionResult
```

### Implementation

**File:** `upstream/automation/payer_portals.py`

See full implementation in master implementation prompt (Week 2, Task 11).

**Key Classes:**

1. **PayerPortalAutomation** - Main orchestrator
2. **ReauthRequest** - Reauth data structure
3. **Appeal** - Appeal data structure
4. **SubmissionResult** - Outcome of portal submission

### Security Considerations

**Credential Storage:**
- Payer portal credentials stored in **Google Secret Manager**
- Encrypted at rest, encrypted in transit
- Access logged via Cloud Audit Logs
- Rotation every 90 days

**Session Management:**
- Each automation session uses fresh browser instance
- Headless Chrome with `--no-sandbox` flag
- Session cookies cleared after each run
- No persistent storage of session tokens

**Error Handling:**
- Portal timeout → Retry up to 3 times
- Portal maintenance page → Escalate to human
- Invalid credentials → Alert customer immediately
- Captcha detected → Escalate to human (cannot automate)

### Payer-Specific Implementations

**Aetna Provider Portal:**

```python
def _login_aetna(self):
    """Login to Aetna provider portal."""
    self.driver.get('https://www.aetna.com/healthcare-professionals/login.html')

    # Enter username
    username_field = self.driver.find_element(By.ID, 'username')
    username_field.send_keys(self.credentials['username'])

    # Enter password
    password_field = self.driver.find_element(By.ID, 'password')
    password_field.send_keys(self.credentials['password'])

    # Submit
    login_button = self.driver.find_element(By.ID, 'login-button')
    login_button.click()

    # Wait for dashboard
    WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.ID, 'provider-dashboard'))
    )
```

**UnitedHealthcare Provider Portal:**

```python
def _login_uhc(self):
    """Login to UnitedHealthcare provider portal."""
    self.driver.get('https://www.uhcprovider.com/login')

    # UHC uses 2-step login
    # Step 1: Username
    username_field = self.driver.find_element(By.NAME, 'userId')
    username_field.send_keys(self.credentials['username'])

    continue_button = self.driver.find_element(By.ID, 'continue')
    continue_button.click()

    # Step 2: Password (different page)
    WebDriverWait(self.driver, 5).until(
        EC.presence_of_element_located((By.NAME, 'password'))
    )

    password_field = self.driver.find_element(By.NAME, 'password')
    password_field.send_keys(self.credentials['password'])

    login_button = self.driver.find_element(By.ID, 'login')
    login_button.click()

    # Wait for MFA (if required)
    # TODO: Implement MFA handling
```

---

## Component 3: Appeal Generation Engine

### Purpose

Automatically generate payer-specific appeal letters with supporting evidence. Use historical success patterns to optimize appeal arguments.

### Appeal Letter Templates

**Template Structure:**

```
[Letterhead with provider NPI, tax ID, address]

Date: {current_date}

{Payer Name}
{Payer Address}

Re: Appeal for Claim {claim_id} - {patient_name} (DOB: {dob})
    Service Date: {service_date}
    Claim Amount: ${claim_amount}
    Denial Reason: {denial_reason}

Dear Claims Review Team,

I am writing to appeal the denial of the above-referenced claim.

SUMMARY OF APPEAL:
{1-2 sentence summary of why denial was incorrect}

MEDICAL NECESSITY:
{Clinical justification for service}

POLICY COMPLIANCE:
{Reference to specific payer policy sections}

SUPPORTING DOCUMENTATION:
- {List of attached documents}

REQUESTED ACTION:
We respectfully request that you overturn the denial and process payment
in the amount of ${claim_amount}.

If you have any questions, please contact me at {provider_phone}.

Sincerely,
{provider_name}
{provider_credentials}

Attachments:
{List of attachments}
```

**Template Customization by Payer:**

- **Aetna:** Emphasize CPT coding guidelines + medical necessity
- **UnitedHealthcare:** Reference MCG criteria + clinical guidelines
- **Blue Cross:** State-specific medical policy citations
- **Medicare:** LCD/NCD policy references

### Implementation

**File:** `upstream/automation/appeal_generation.py`

```python
from jinja2 import Template
from weasyprint import HTML
from dataclasses import dataclass
from typing import List
from upstream.models import ClaimRecord
import logging

logger = logging.getLogger(__name__)


@dataclass
class Appeal:
    """Appeal data structure."""
    claim_ids: List[str]
    payer: str
    reason: str
    letter_pdf: bytes
    supporting_docs: List[bytes]
    total_amount: float
    expected_overturn_probability: float


class AppealGenerator:
    """
    Generates payer-specific appeal letters.
    Uses templates + historical success patterns.
    """

    def generate_appeal(self, claim: ClaimRecord, denial_reason: str) -> Appeal:
        """
        Generate appeal letter for denied claim.

        Templates are payer-specific and reason-specific.
        Historical data informs which arguments work best.
        """

        # Load payer-specific template
        template = self._load_template(claim.payer, denial_reason)

        # Gather supporting evidence
        evidence = self._gather_evidence(claim)

        # Generate letter text
        letter_text = template.render(
            claim=claim,
            denial_reason=denial_reason,
            evidence=evidence,
            medical_necessity=self._generate_medical_necessity_statement(claim),
            policy_references=self._get_policy_references(claim.payer, claim.cpt)
        )

        # Convert to PDF
        letter_pdf = HTML(string=letter_text).write_pdf()

        return Appeal(
            claim_ids=[claim.id],
            payer=claim.payer,
            reason=denial_reason,
            letter_pdf=letter_pdf,
            supporting_docs=evidence['documents'],
            total_amount=claim.billed_amount - claim.paid_amount,
            expected_overturn_probability=self._calculate_overturn_probability(
                claim.payer, denial_reason
            )
        )

    def consolidate_appeals(self, claims: List[ClaimRecord]) -> List[Appeal]:
        """
        Group multiple underpayments into one consolidated appeal.

        Strategy: Group by payer + similar denial reasons.
        Payers are more likely to overturn when multiple claims show pattern.
        """

        from collections import defaultdict

        # Group claims by payer + denial reason
        grouped = defaultdict(list)
        for claim in claims:
            key = (claim.payer, claim.denial_reason)
            grouped[key].append(claim)

        appeals = []
        for (payer, denial_reason), claim_group in grouped.items():
            # Create single appeal for entire group
            total_amount = sum(
                c.billed_amount - c.paid_amount for c in claim_group
            )

            # Enhanced letter for consolidated appeal
            letter_text = self._generate_consolidated_appeal_letter(
                claim_group, payer, denial_reason, total_amount
            )

            appeals.append(Appeal(
                claim_ids=[c.id for c in claim_group],
                payer=payer,
                reason=denial_reason,
                letter_pdf=HTML(string=letter_text).write_pdf(),
                supporting_docs=self._gather_consolidated_evidence(claim_group),
                total_amount=total_amount,
                expected_overturn_probability=0.65  # Higher for consolidated appeals
            ))

        return appeals

    def _load_template(self, payer: str, denial_reason: str) -> Template:
        """Load Jinja2 template for payer + denial reason."""
        # TODO: Implement template loader
        return Template("Appeal letter template")

    def _gather_evidence(self, claim: ClaimRecord) -> dict:
        """Gather supporting documents for appeal."""
        # TODO: Implement evidence gathering
        return {'documents': []}

    def _generate_medical_necessity_statement(self, claim: ClaimRecord) -> str:
        """Generate medical necessity justification."""
        # TODO: Implement medical necessity generation
        return "Medical necessity statement"

    def _get_policy_references(self, payer: str, cpt: str) -> List[str]:
        """Get relevant payer policy references."""
        # TODO: Implement policy reference lookup
        return []

    def _calculate_overturn_probability(self, payer: str, denial_reason: str) -> float:
        """Calculate probability of appeal success based on historical data."""
        # TODO: Implement historical success rate lookup
        return 0.55  # 55% average overturn rate

    def _generate_consolidated_appeal_letter(
        self, claims: List[ClaimRecord], payer: str, denial_reason: str, total_amount: float
    ) -> str:
        """Generate appeal letter for multiple claims."""
        # TODO: Implement consolidated letter generation
        return "Consolidated appeal letter"

    def _gather_consolidated_evidence(self, claims: List[ClaimRecord]) -> List[bytes]:
        """Gather evidence for multiple claims."""
        # TODO: Implement consolidated evidence gathering
        return []
```

### Overturn Rate Tracking

**Purpose:** Learn which appeal arguments work best for each payer + denial reason.

**Implementation:**

```python
# upstream/models.py

class AppealOutcome(BaseModel):
    """Track appeal outcomes to optimize future appeals."""
    appeal_id = models.CharField(max_length=100, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    payer = models.CharField(max_length=255, db_index=True)
    denial_reason = models.CharField(max_length=255, db_index=True)
    claim_count = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Outcome
    decision = models.CharField(
        max_length=20,
        choices=[
            ('APPROVED', 'Approved'),
            ('DENIED', 'Denied'),
            ('PARTIAL', 'Partial Approval'),
            ('PENDING', 'Pending'),
        ],
        db_index=True
    )
    amount_recovered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    decision_date = models.DateField(null=True, blank=True)

    # Appeal strategy used
    template_used = models.CharField(max_length=100)
    arguments_used = models.JSONField(default=list)

    # Learning
    days_to_decision = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['payer', 'denial_reason', 'decision']),
            models.Index(fields=['customer', '-decision_date']),
        ]
```

**Query for Optimal Strategy:**

```python
# Get best-performing appeal strategy for Aetna + "Medical Necessity" denials
successful_appeals = AppealOutcome.objects.filter(
    payer='Aetna',
    denial_reason='Medical Necessity',
    decision='APPROVED'
).order_by('-amount_recovered')[:10]

# Extract common arguments from successful appeals
common_arguments = {}
for appeal in successful_appeals:
    for arg in appeal.arguments_used:
        common_arguments[arg] = common_arguments.get(arg, 0) + 1

# Use most frequent arguments in future appeals
top_arguments = sorted(common_arguments.items(), key=lambda x: x[1], reverse=True)[:3]
```

---

## Component 4: Autonomous Workflows

### Workflow 1: Authorization Reauth

**Trigger:** Authorization expires in ≤30 days (configurable per payer)

**Execution Steps:**

1. **Daily Check** (6 AM UTC via Celery beat)
   - Query all authorizations with `status='ACTIVE'`
   - Filter where `days_until_expiration <= reauth_lead_time_days`

2. **Generate Reauth Request**
   - Patient ID (de-identified)
   - Service type + CPT codes
   - Units used vs authorized (utilization rate)
   - Generate utilization report PDF

3. **Submit via Payer Portal** (RPA)
   - Login to payer portal
   - Navigate to reauth form
   - Fill fields + attach utilization report
   - Submit + extract confirmation number

4. **Log Execution**
   - Create `ExecutionLog` record
   - Store confirmation number in `details` field

5. **Notify Customer** (informational only)
   - Email: "Auto-submitted reauth for AUTH-12345. Confirmation: REF-67890."
   - Slack: Same message
   - In-app notification

**Implementation:** See Week 2, Tasks 9-11 in master implementation prompt.

---

### Workflow 2: Underpayment Appeal

**Trigger:** Claim paid with `paid_amount < expected_amount` AND `underpayment > $500`

**Execution Steps:**

1. **Detect Underpayment**
   - Calculate `expected_amount` from fee schedule
   - Compare to `paid_amount`
   - If difference > $500 → Trigger appeal workflow

2. **Consolidate Appeals** (optional)
   - Group multiple underpayments by payer
   - Single appeal letter for all claims (stronger evidence)

3. **Generate Appeal Letter**
   - Use payer-specific template
   - Include medical necessity justification
   - Attach supporting docs (medical records, policy references)

4. **Submit via Payer Portal** (RPA)
   - Login to payer portal
   - Navigate to appeals section
   - Attach PDF letter + supporting docs
   - Submit + extract confirmation number

5. **Track Response** (7-14 days)
   - Schedule follow-up task to check portal for decision
   - If approved → Update claim record + notify customer
   - If denied → Escalate to secondary appeal or human review

6. **Log Execution**
   - Create `ExecutionLog` record
   - Store confirmation number + expected response date

**Implementation:** See Week 6-7 in master implementation prompt.

---

### Workflow 3: High-Risk Claim Hold

**Trigger:** Pre-submission risk score > 70 AND confidence > 0.6

**Execution Steps:**

1. **Calculate Risk Score**
   - Operator enters claim data in pre-submission check UI
   - Risk scorer calculates score 0-100

2. **Evaluate Rules**
   - If score > 70 → Trigger "hold for review" action

3. **Hold Claim**
   - Move claim to "Pending Review" queue
   - Assign to billing manager
   - Flag as high-priority

4. **Notify Billing Manager**
   - Email: "Claim held for review. Risk score: 72/100. Issue: Missing OASIS G-code."
   - In-app notification with risk breakdown

5. **Manager Decision**
   - Option 1: Fix issues → Submit claim
   - Option 2: Override hold → Submit anyway (logs override reason)
   - Option 3: Reject claim → Don't submit

**Implementation:** See Week 5 in master implementation prompt.

---

## Component 5: Escalation Handling

### When to Escalate

**Automatic Escalation Triggers:**

1. **Action Failure:** RPA fails after 3 retries
2. **Edge Case Detection:** Payer portal shows captcha, maintenance page, or unexpected UI
3. **High-Stakes Decision:** Appeal amount > $5,000 (configurable)
4. **Compliance Risk:** HIPAA-sensitive data handling required
5. **Customer Request:** Customer disables auto-execution for specific workflow

### Escalation Flow

```
Action Fails
     ↓
Log ExecutionLog with result='ESCALATED'
     ↓
Create AlertEvent (severity='high')
     ↓
Notify Customer via Email + Slack + In-App
     ↓
Assign to Human Operator
     ↓
Operator Reviews + Takes Action
     ↓
Operator Logs Resolution Notes
```

### Implementation

```python
# upstream/automation/rules_engine.py

def _escalate_to_human(self, action: Action, error: Exception):
    """Escalate failed action to human operator."""
    from upstream.models import AlertEvent

    AlertEvent.objects.create(
        customer=action.rule.customer,
        alert_type='automation_escalation',
        severity='high',
        title=f"Automation Failed: {action.action_type}",
        description=(
            f"Automated action failed and requires human review.\n\n"
            f"Action: {action.action_type}\n"
            f"Error: {str(error)}\n\n"
            f"Please review the execution log and take manual action."
        ),
        evidence_payload={
            'rule_id': action.rule.id,
            'rule_name': action.rule.name,
            'action_type': action.action_type,
            'error': str(error),
            'trigger_event': action.event.to_dict()
        }
    )

    logger.error(f"Action escalated: {action.action_type} - {error}")
```

---

## Success Metrics

### Execution Performance
- **Success Rate:** >95% of autonomous actions complete successfully
- **Latency:** <10s per action (p95)
- **Retry Rate:** <5% of actions require retry
- **Escalation Rate:** <2% of actions escalate to human

### Business Impact
- **Time Saved:** 80%+ reduction in manual payer portal interactions
- **Cost Savings:** $47 per prevented denial × 20-30% denial reduction
- **Customer Satisfaction:** >90% customers enable auto-execution after 30-day trial

### Compliance
- **Audit Trail:** 100% of actions logged in ExecutionLog
- **Credential Security:** Zero credential leaks (Google Secret Manager)
- **Error Handling:** 100% of errors logged + escalated appropriately

---

**Next:** See `04-database-schema.md` for complete database migrations.

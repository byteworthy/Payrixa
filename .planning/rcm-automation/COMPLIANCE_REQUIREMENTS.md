# RCM Automation Compliance Requirements

**Legal and Regulatory Constraints for Autonomous Healthcare Billing**

## Executive Summary

Healthcare automation faces unique compliance challenges. **The provider bears 100% liability** for all billing actions regardless of automation. This document defines hard red lines that cannot be crossed, audit trail requirements, and implementation guidelines for HIPAA, False Claims Act, and emerging state AI laws.

---

## Hard Red Lines: Actions That Legally Require Human Review

### 1. Medical Necessity Determinations

**Why Human Review Required:**
- State laws explicitly mandate human review (CA SB 1120, FL SB 794, CT HB 5587)
- Clinical judgment cannot be safely delegated to AI
- False Claims Act exposure if automated without clinical expertise

**Implementation:**
```python
if action.involves_medical_necessity:
    claim_score.requires_human_review = True
    claim_score.red_line_reason = "Medical necessity determination - State law requirement"
    claim_score.recommended_action = "escalate"
```

**States with Explicit Requirements:**
- **California SB 1120:** Requires qualified humans to review utilization management decisions
- **Florida SB 794:** Mandates claim denial decisions reviewed by "qualified human professional"
- **Connecticut HB 5587/5590:** Prohibits AI as primary denial method
- **Illinois, New York, Utah:** Similar requirements emerging

### 2. Code Changes Affecting Reimbursement

**Why Human Review Required:**
- False Claims Act liability: $13,946-$27,894 per false claim + treble damages
- "Knowingly" defined to include "reckless disregard"
- Automated code changes without oversight = reckless disregard

**Implementation:**
```python
if action.modifies_cpt_code and action.affects_reimbursement_amount:
    claim_score.requires_human_review = True
    claim_score.red_line_reason = "Code change affects reimbursement - FCA liability"
    claim_score.recommended_action = "escalate"
```

**Safe Automation Scenarios:**
- Administrative code corrections (typos, formatting)
- Non-reimbursement fields (patient demographics)
- Status updates with no dollar impact

### 3. Denial Appeals with Legal Certifications

**Why Human Review Required:**
- Appeals contain legal certifications requiring clinical judgment
- Medical records must be reviewed by qualified clinician
- Sign-off under penalty of perjury

**Implementation:**
```python
if action.action_type == "submit_appeal":
    claim_score.requires_human_review = True  # ALWAYS
    claim_score.red_line_reason = "Appeal requires clinical judgment and legal certification"
    claim_score.recommended_action = "escalate"
```

**What AI CAN Do:**
- Draft appeal letter (saves 90% of time)
- Pull relevant clinical guidelines
- Suggest supporting documentation
- Identify similar successful appeals

**What AI CANNOT Do:**
- Submit appeal without human sign-off
- Make clinical judgments about medical necessity
- Certify medical record accuracy

### 4. Stark Law Referral Exceptions

**Why Human Review Required:**
- Stark Law prohibits physician self-referrals unless exception applies
- Exception compliance must be verified by legal/compliance
- Anti-Kickback Statute exposure

**Implementation:**
```python
if claim.involves_referral and claim.stark_law_applicable:
    claim_score.requires_human_review = True
    claim_score.red_line_reason = "Stark Law referral - Exception compliance verification required"
    claim_score.recommended_action = "escalate"
    claim_score.compliance_risk_score = 1.0
```

**Safe Automation Scenarios:**
- Claims without referral relationships
- Verified exception already documented
- Non-designated health services

### 5. 60-Day Overpayment Determinations

**Why Human Review Required:**
- False Claims Act requires return within 60 days of "identification"
- Automated detection = "identification" trigger
- Legal deadline with treble damage exposure

**Implementation:**
```python
if analysis.detects_overpayment:
    claim_score.requires_human_review = True
    claim_score.red_line_reason = "Overpayment detected - 60-day FCA deadline triggered"
    claim_score.recommended_action = "escalate"
    # Escalate to compliance officer immediately
    escalate_to_compliance(claim, reason="overpayment_60day_trigger")
```

### 6. Fraud Indicators Detected

**Why Human Review Required:**
- SIU (Special Investigations Unit) must investigate
- Legal implications if incorrectly flagged
- Potential criminal referral

**Implementation:**
```python
if claim_score.fraud_risk_score > 0.7:
    claim_score.requires_human_review = True
    claim_score.red_line_reason = "Fraud indicators detected - SIU review required"
    claim_score.recommended_action = "escalate"
    # Route to Special Investigations Unit
    create_siu_investigation(claim)
```

**Common Fraud Indicators:**
- Unbundling/upcoding patterns
- Duplicate billing
- Services not rendered
- Phantom providers (NPI mismatches)
- Billing for deceased patients

---

## HIPAA Audit Trail Requirements (45 CFR 164.312)

### Minimum Required Fields

**Security Rule mandates capturing:**
1. **User Identification:** User ID, role, credentials
2. **Access Details:** Files accessed and modified
3. **Timestamps:** With timezone (ISO 8601 format)
4. **Business Purpose:** Justification for access
5. **Action Outcomes:** Success/failure status

### Implementation in ExecutionLog Model

```python
class ExecutionLog(models.Model):
    """Enhanced audit trail exceeding HIPAA minimums"""

    # Existing fields (customer, rule, trigger_event, action_taken, result)

    # HIPAA required fields
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="User who authorized action (or 'SYSTEM' for autonomous)"
    )
    user_role = models.CharField(
        max_length=100,
        help_text="Role/permissions of user (e.g., 'billing_manager', 'compliance_officer')"
    )
    business_justification = models.TextField(
        help_text="Why action was taken (business purpose per HIPAA)"
    )
    ip_address = models.GenericIPAddressField(
        help_text="Source IP address for audit trail"
    )
    session_id = models.CharField(
        max_length=255,
        help_text="Session identifier for correlation"
    )

    # AI-specific explainability (beyond HIPAA requirements)
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI confidence score for transparency"
    )
    model_version = models.CharField(
        max_length=50,
        help_text="ML model version used (e.g., 'rf_v2.1')"
    )
    feature_importance = models.JSONField(
        default=dict,
        help_text="Top features influencing decision: {'payer_history': 0.35, ...}"
    )
    prediction_reasoning = models.TextField(
        blank=True,
        help_text="Human-readable explanation of AI decision"
    )

    # Compliance tracking
    requires_human_review = models.BooleanField(
        default=False,
        help_text="Was human review legally required?"
    )
    human_reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_executions",
        help_text="User who reviewed action (if applicable)"
    )
    review_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When human review occurred"
    )
    review_outcome = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=[
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("modified", "Modified"),
        ],
        help_text="Human review decision"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Human reviewer comments"
    )

    # Reversal tracking
    was_reversed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Was this action undone?"
    )
    reversal_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When action was reversed"
    )
    reversal_reason = models.TextField(
        blank=True,
        help_text="Why action was reversed"
    )
    reversed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reversed_executions",
        help_text="User who reversed action"
    )

    # Timestamps (ISO 8601 with timezone)
    executed_at = models.DateTimeField(auto_now_add=True, db_index=True)
```

### Retention Periods by Regulation

| Regulation | Retention Period | Scope |
|------------|------------------|-------|
| HIPAA | 6 years | All PHI access logs |
| Medicare Managed Care | 10+ years | Claims and billing records |
| State requirements | Up to 11 years | Some states require extended retention |
| False Claims Act | 10 years | Claims with government payer involvement |

**Implementation:**
```python
AUDIT_RETENTION_YEARS = {
    'default': 6,  # HIPAA minimum
    'medicare': 10,  # Medicare Managed Care
    'medicaid': 11,  # Some states require 11 years
    'fca_exposure': 10,  # False Claims Act statute of limitations
}

def should_retain_audit_log(log: ExecutionLog) -> bool:
    """Determine if audit log should be retained based on payer type."""
    payer = log.details.get('payer', '').lower()

    if 'medicare' in payer:
        retention_years = AUDIT_RETENTION_YEARS['medicare']
    elif 'medicaid' in payer:
        retention_years = AUDIT_RETENTION_YEARS['medicaid']
    else:
        retention_years = AUDIT_RETENTION_YEARS['default']

    retention_date = log.executed_at + timedelta(days=retention_years * 365)
    return timezone.now() < retention_date
```

---

## Business Associate Agreements (BAA) - AI-Specific Provisions

### Required Clauses for Automation Vendors

**1. AI Transparency Clause:**
```
Vendor shall provide documentation of AI decision-making processes,
including model architecture, training data sources, and confidence
scoring methodologies. Customer has right to audit AI decisions.
```

**2. Data Use Limitations:**
```
Vendor shall NOT use Customer PHI for:
- Training AI models without written authorization
- Sharing with third parties (including model providers)
- Creating de-identified datasets for research
- Benchmarking across customers
```

**3. Model Training Restrictions:**
```
If Vendor trains AI models on Customer data:
- Customer must explicitly opt-in
- Training data must be de-identified per HIPAA Safe Harbor
- Customer owns derivative models trained on their data
- Vendor must delete training data upon termination
```

**4. Incident Response - AI-Specific:**
```
Vendor shall notify Customer within 24 hours if:
- AI model makes decision with <70% confidence
- Red-line action attempted without human review
- Confidence score accuracy drops >10% from baseline
- Model version updated with material changes
```

**5. Human Oversight Guarantee:**
```
Vendor shall maintain human oversight for:
- Medical necessity determinations (state law requirement)
- Code changes affecting reimbursement (FCA liability)
- Denial appeals (legal certification requirement)
- Any action with compliance risk score >0.7
```

---

## State AI Legislation Compliance Matrix

### Current Laws (2025-2026)

| State | Bill | Requirement | Implementation |
|-------|------|-------------|----------------|
| California | SB 1120 | Qualified human review of utilization management | `claim_score.requires_human_review = True` if medical necessity |
| Florida | SB 794 | Qualified human professional reviews denials | `escalate_to_human(role='clinical_reviewer')` |
| Connecticut | HB 5587/5590 | Prohibit AI as primary denial method | AI can recommend, human must approve |
| Illinois | Pending | Human review of AI claim decisions | Shadow mode + human approval before execution |
| New York | Pending | Transparency in AI healthcare decisions | Store `prediction_reasoning` in ExecutionLog |
| Utah | Pending | Human oversight of AI billing | Configurable human-in-loop per customer |

### Compliance Implementation

```python
def check_state_compliance(claim: ClaimRecord, action: str) -> bool:
    """
    Verify action complies with state AI laws based on patient location.

    Returns False if action violates state law, requiring human review.
    """
    patient_state = claim.patient_state  # Would need to add this field

    # California: Medical necessity requires human review
    if patient_state == 'CA' and action in ['deny_claim', 'modify_authorization']:
        claim_score = claim.score
        claim_score.requires_human_review = True
        claim_score.red_line_reason = "CA SB 1120: Medical necessity determination requires qualified human"
        return False

    # Florida: Denials require human professional review
    if patient_state == 'FL' and action == 'deny_claim':
        claim_score = claim.score
        claim_score.requires_human_review = True
        claim_score.red_line_reason = "FL SB 794: Denial decision requires qualified human professional"
        return False

    # Connecticut: AI cannot be primary denial method
    if patient_state == 'CT' and action == 'deny_claim':
        # AI can recommend, but human must make final decision
        claim_score = claim.score
        claim_score.recommended_action = "queue_review"
        claim_score.red_line_reason = "CT HB 5587: AI cannot be primary denial method"
        return False

    return True  # No state law violation
```

---

## False Claims Act (FCA) Liability Protection

### Penalty Structure (2024 Rates)

- **Per Claim Penalty:** $13,946 to $27,894
- **Treble Damages:** 3x the amount of false claim
- **Example:** $10,000 false claim = $30,000 + $13,946 penalty = $43,946 total

### "Knowingly" Standard Includes Automation

**31 U.S.C. § 3729(b)(1) defines "knowingly" as:**
1. Actual knowledge
2. Deliberate ignorance (head-in-the-sand)
3. **Reckless disregard** ← Applies to inadequately supervised automation

**Legal Precedent:**
- *United States v. Krizek* (1996): Billing errors from lack of oversight = reckless disregard
- Automated billing without human review for high-risk actions = reckless disregard

### Protection Through Documentation

```python
class FCAComplianceCheck(models.Model):
    """
    Document FCA compliance review for high-risk claims.

    Required before auto-executing claims >$1K or with compliance risk.
    """

    claim = models.ForeignKey(ClaimRecord, on_delete=models.CASCADE)
    execution_log = models.ForeignKey(ExecutionLog, on_delete=models.CASCADE)

    # Compliance checklist
    medical_necessity_verified = models.BooleanField(
        help_text="Medical necessity supported by documentation"
    )
    coding_accuracy_verified = models.BooleanField(
        help_text="CPT codes match documentation"
    )
    authorization_obtained = models.BooleanField(
        help_text="Prior authorization obtained if required"
    )
    no_stark_violation = models.BooleanField(
        help_text="No Stark Law referral issues"
    )
    no_duplicate_billing = models.BooleanField(
        help_text="Claim not already submitted/paid"
    )

    # Human sign-off (if required)
    reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Compliance reviewer (if required)"
    )
    review_timestamp = models.DateTimeField(null=True, blank=True)

    # Notes
    compliance_notes = models.TextField(
        blank=True,
        help_text="Compliance reviewer comments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Compliance Monitoring and Reporting

### Weekly Compliance Report

**Metrics to Track:**
- Red-line violations attempted (should be 0)
- Human review compliance rate (100% for red-line actions)
- Shadow mode accuracy vs. target (>95%)
- False positive rate (<2%)
- Reversal rate (<5%)
- State law compliance violations (should be 0)

### Monthly Audit Review

**Compliance Officer Reviews:**
- Random sample of autonomous actions (10% of total)
- All escalated actions
- All reversed actions
- All actions with <80% confidence
- All actions >$10K

### Quarterly External Audit Preparation

**Documentation Package:**
1. Audit trail completeness verification (100%)
2. Human review compliance for red-line actions (100%)
3. BAA compliance with AI vendors
4. State law compliance verification
5. FCA exposure analysis
6. Model accuracy metrics
7. Customer satisfaction (NPS)

---

## Implementation Checklist

### Phase 1: Foundation (Weeks 1-4)
- [ ] Add compliance fields to ExecutionLog model
- [ ] Implement red-line detection in ClaimScore
- [ ] Build state compliance checking
- [ ] Create FCAComplianceCheck model
- [ ] Set up audit retention policies

### Phase 2: Monitoring (Weeks 5-8)
- [ ] Build weekly compliance dashboard
- [ ] Implement random sampling for audit
- [ ] Create monthly compliance report
- [ ] Set up alerts for red-line violations
- [ ] Build reversal tracking

### Phase 3: External Audit (Weeks 9-12)
- [ ] Prepare quarterly audit package
- [ ] Train compliance officers on system
- [ ] Document AI decision-making for auditors
- [ ] Create BAA templates with AI clauses
- [ ] Validate HIPAA audit trail completeness

---

## Risk Mitigation Strategies

### 1. Conservative Thresholds
- Start with 98% confidence threshold (not 95%)
- Lower dollar thresholds ($500 not $1,000)
- Shorter undo windows initially (1 hour not 2)

### 2. Shadow Mode Extended Period
- Run shadow mode 6-8 weeks (not 4)
- Require 97% accuracy before enabling (not 95%)
- Get compliance officer sign-off

### 3. Gradual Expansion
- Start with status checks only (lowest risk)
- Then eligibility verification
- Then claim submission
- **NEVER** auto-submit appeals (legal requirement)

### 4. Continuous Monitoring
- Real-time alerts for red-line attempts
- Daily accuracy metrics
- Weekly compliance review
- Monthly external audit

---

**Document Version:** 1.0
**Last Updated:** 2026-01-31
**Owner:** Compliance Team
**Status:** Legal Review Required

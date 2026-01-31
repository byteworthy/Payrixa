# Healthcare RCM Automation: From Alerts to Autonomous Execution

**Strategic Implementation Roadmap for Upstream Healthcare Platform**

## Executive Summary

Healthcare revenue cycle management is shifting from recommendation engines to true autonomous execution. This roadmap outlines our path to building a competitive autonomous RCM platform that balances aggressive automation with robust safeguards, compliance, and customer trust.

**Current State (Week 1 Complete):**
- ✅ Authorization tracking (multi-vertical)
- ✅ ExecutionLog for HIPAA audit trails
- ✅ AutomationRule framework
- ✅ RulesEngine foundation
- ✅ EHR webhook integration

**Target State:**
- Autonomous claim submission with 95%+ confidence
- Three-tier automation model (Auto-Execute, Queue, Escalate)
- Voice AI for payer phone calls
- Appeal letter generation with RAG
- Full compliance audit trails exceeding HIPAA minimums

---

## Competitive Landscape Analysis

### Tier 1: True Autonomous Execution
**Adonis Intelligence** - Claims 90% autonomous resolution
- ✅ Auto-dials payers and navigates IVR
- ✅ Converses with live representatives
- ✅ PM system write-backs
- ❌ No independent KLAS verification
- ❌ Appeals still require human review

**AKASA** - Human-in-the-loop leader (99.5% accuracy)
- ✅ Autonomous coding at Cleveland Clinic
- ✅ Worklogger observes humans to improve AI
- ✅ Explicit uncertainty flagging
- ⚠️ Conservative approach (flags vs. executes)

### Tier 2: Portal Automation + APIs
**Waystar** - 85% prior auth auto-approval
- ✅ RPA + direct payer APIs
- ✅ Acquired Olive AI assets
- ✅ Clearinghouse + patient access
- ❌ Appeals drafted, not submitted

**Infinx** - 50% cost reduction via RPA
- ✅ Prior auth submission/follow-up
- ✅ Automated payer polling
- ⚠️ Hybrid with human specialists

### Tier 3: Alert/Prioritize Only
**Experian Health** - No autonomous execution
- ✅ Predicts denials before submission
- ✅ 4% denial rate vs 10% industry avg
- ❌ Humans decide all actions

### Critical Gaps in Market
1. **No competitor fully auto-submits appeals** without review
2. **Voice AI** claimed by Adonis, not validated elsewhere
3. **End-to-end touchless claims** still rare
4. **Real-time payer rule adaptation** requires manual maintenance

---

## Technical Architecture

### Core Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Upstream Platform                     │
├─────────────────────────────────────────────────────────┤
│  Intelligence Layer (Our Week 2-4 Build)                │
│  - Confidence scoring (ML models: AUC 0.83-0.88)        │
│  - Risk baseline tracking                                │
│  - Denial prediction                                     │
├─────────────────────────────────────────────────────────┤
│  Orchestration Layer (AutomationRule + RulesEngine)     │
│  - Threshold-based routing                              │
│  - Three-tier automation model                          │
│  - Human-in-loop escalation                             │
├─────────────────────────────────────────────────────────┤
│  AI Agents Layer (Week 9-12 Future)                     │
│  - Payer portal RPA (UiPath/Playwright)                │
│  - Voice AI (Twilio/Vapi.ai integration)               │
│  - Appeal generation (LLM + RAG)                        │
│  - EHR write-back (FHIR R4)                             │
└─────────────────────────────────────────────────────────┘
```

### Integration Points

**EHR Integration (FHIR R4):**
```
RPA Bot → Mirth Connect → Epic Interconnect → EHR
- OAuth 2.0 for write operations
- MRN-based patient matching
- CMS-0057-F compliance (2026 mandate)
```

**Payer Portal RPA:**
- UiPath AI Computer Vision (dynamic UI handling)
- Azure Key Vault (credential management)
- TOTP integration (2FA automation)
- Proxy rotation + CAPTCHA services

**Voice AI (Future):**
- Twilio/Vapi.ai for outbound dialing
- IVR navigation with ASR
- Live agent conversation (NLU)
- Structured outcome logging

---

## Three-Tier Automation Model

### Tier 1: Auto-Execute (High Confidence)

**Criteria:**
- Confidence score: **>95%**
- Dollar value: **<$1,000**
- Complete documentation
- Clean coding match
- Known payer rules

**Actions:**
- ✅ Auto-adjudicate
- ✅ Auto-post
- ✅ Auto-submit
- ✅ Status checks
- ✅ Eligibility verification

**Implementation:**
```python
class AutoExecuteRule(AutomationRule):
    """Tier 1: Autonomous execution without human review"""

    rule_type = "auto_execute"
    trigger_conditions = {
        "confidence_threshold": 0.95,
        "max_dollar_amount": 1000,
        "documentation_complete": True,
        "payer_rules_matched": True
    }
    actions = {
        "action_type": "submit_claim",
        "notify_user": False,  # Silent execution
        "undo_window_hours": 2
    }
```

### Tier 2: Queue for Review (Medium Confidence)

**Criteria:**
- Confidence score: **70-95%**
- Dollar value: **$1,000-$10,000**
- Minor documentation gaps
- Complex coding scenarios

**Actions:**
- 🔍 Route to appropriate queue (coding, eligibility, clinical)
- 📝 Pre-populate context
- 🎯 Highlight specific issues
- ⚡ One-click approval available

**Implementation:**
```python
class QueueForReviewRule(AutomationRule):
    """Tier 2: AI recommends, human approves"""

    rule_type = "queue_for_review"
    trigger_conditions = {
        "confidence_threshold": 0.70,
        "max_dollar_amount": 10000,
        "min_confidence": 0.70
    }
    actions = {
        "action_type": "create_review_task",
        "queue": "coding_review",  # or eligibility, clinical
        "pre_populate": True,
        "priority": "medium"
    }
```

### Tier 3: Escalate (Low Confidence / High Risk)

**Criteria:**
- Confidence score: **<70%**
- Dollar value: **>$10,000**
- Fraud indicators detected
- Medical necessity questions
- Appeals requiring clinical judgment

**Actions:**
- 🚨 Route to senior adjuster
- 👨‍⚕️ Medical director review
- 📋 Compliance officer notification
- 🔒 SIU (Special Investigations Unit)

**Implementation:**
```python
class EscalateRule(AutomationRule):
    """Tier 3: Mandatory human review"""

    rule_type = "escalate"
    trigger_conditions = {
        "max_confidence": 0.70,
        "min_dollar_amount": 10000,
        "fraud_indicators": ["..."],
        "medical_necessity_flag": True
    }
    actions = {
        "action_type": "escalate_to_human",
        "assignee_role": "senior_adjuster",  # or medical_director
        "priority": "high",
        "sla_hours": 24
    }
```

---

## Compliance Hard Red Lines

**Actions That LEGALLY Require Human Review:**

1. **Medical Necessity Determinations**
   - State laws mandate human review (CA SB 1120, FL SB 794)
   - Cannot be fully automated

2. **Code Changes Affecting Reimbursement**
   - False Claims Act liability ($13,946-$27,894 per claim)
   - "Reckless disregard" standard applies to automation

3. **Denial Appeals**
   - Contain legal certifications requiring clinical judgment
   - No competitor auto-submits appeals

4. **Stark Law Referrals**
   - Exception compliance verification required
   - Anti-kickback statute exposure

5. **60-Day Overpayment Determinations**
   - Triggers legal repayment deadline
   - False Claims Act liability

6. **Any Modification Affecting Reimbursement Amount**
   - Human accountability required

### Audit Trail Requirements (HIPAA Security Rule 45 CFR 164.312)

**Minimum Capture Requirements:**
- User ID/role/credentials
- Files accessed and modified
- Timestamps with timezone
- Business purpose/justification
- Action outcomes (success/failure)

**Retention Periods:**
- HIPAA: 6 years
- Medicare Managed Care: 10+ years
- Some states: 11 years

**Implementation:**
```python
class ExecutionLog(models.Model):
    """Enhanced audit trail exceeding HIPAA minimums"""

    # Existing fields...

    # Add for compliance:
    user_id = models.CharField(max_length=255, db_index=True)
    user_role = models.CharField(max_length=100)
    business_justification = models.TextField()
    ip_address = models.GenericIPAddressField()
    session_id = models.CharField(max_length=255)

    # AI-specific fields:
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    model_version = models.CharField(max_length=50)
    feature_importance = models.JSONField(default=dict)  # Explainability

    # Compliance tracking:
    requires_human_review = models.BooleanField(default=False)
    human_reviewer = models.ForeignKey(User, null=True, blank=True)
    review_timestamp = models.DateTimeField(null=True, blank=True)
    review_outcome = models.CharField(max_length=50, null=True, blank=True)
```

---

## Trust Calibration Framework

**Four-Stage Customer Onboarding:**

### Stage 1: Observe (Weeks 1-2)
- AI shows recommendations
- Human takes all actions
- "We recommend submitting this claim."
- **Goal:** Build confidence in AI accuracy

### Stage 2: Suggest (Weeks 3-4)
- AI pre-fills actions
- Human confirms with one click
- "Ready to submit? [Confirm] [Edit]"
- **Goal:** Reduce friction, maintain control

### Stage 3: Act + Notify (Weeks 5-8)
- AI executes automatically
- Human notified after with undo
- "Claim submitted. [Undo] (2 hours)"
- **Goal:** Transition to post-action review

### Stage 4: Full Autonomy (Week 9+)
- AI executes silently for routine tasks
- Exceptions escalated to humans
- Summary reports only
- **Goal:** Touchless processing for 80%+ of claims

### Shadow Mode (Parallel for 4-6 weeks)
- Run AI decisions alongside human decisions
- Log but don't execute
- Compare accuracy metrics
- Build statistical confidence before enabling

**Implementation:**
```python
class CustomerAutomationProfile(models.Model):
    """Track customer's trust calibration stage"""

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)

    # Trust stage
    automation_stage = models.CharField(
        max_length=20,
        choices=[
            ("observe", "Stage 1: Observe"),
            ("suggest", "Stage 2: Suggest"),
            ("act_notify", "Stage 3: Act + Notify"),
            ("full_autonomy", "Stage 4: Full Autonomy"),
        ],
        default="observe"
    )

    # Thresholds (customer-configurable)
    auto_execute_confidence = models.FloatField(default=0.95)
    auto_execute_max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=1000
    )
    queue_review_confidence = models.FloatField(default=0.70)
    escalate_min_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=10000
    )

    # Action-specific overrides
    auto_submit_claims = models.BooleanField(default=False)
    auto_submit_appeals = models.BooleanField(default=False)  # Always False in v1
    auto_modify_codes = models.BooleanField(default=False)

    # Shadow mode
    shadow_mode_enabled = models.BooleanField(default=True)
    shadow_mode_start_date = models.DateField(null=True, blank=True)
    shadow_accuracy_rate = models.FloatField(null=True, blank=True)
```

---

## UX Patterns for Transparency

### Post-Action Notifications (Three-Tier Severity)

**High Attention (Modal + Push + Email):**
- Denials received
- Payment failures
- Compliance escalations
- Large dollar amount actions (>$10K)

**Medium Attention (In-App Toast):**
- Claims submitted successfully
- Status updates received
- Authorizations expiring soon

**Low Attention (Daily/Weekly Digest):**
- Summary of autonomous actions
- Performance metrics
- Routine status checks

**Every Notification Must Include:**
1. **What** action was taken
2. **Why** (AI reasoning + confidence score)
3. **Result** (success/failure)
4. **Undo window** (if applicable)
5. **Link to audit log** (full details)

### Undo Functionality by Action Impact

**Session-Based Undo:**
- Status checks (immediate)
- Eligibility queries (immediate)

**Time-Windowed Undo:**
- Claim submissions (2-24 hours while in clearinghouse)
- Code changes (before payer submission)

**Soft-Delete + Recovery:**
- Actions before external submission (30 days)
- Database records (90 days)

**Cannot Be Reversed:**
- Claims adjudicated by payers
- Appeals submitted to payers
- Actions with external legal implications
- **Requires manual intervention**

### Dashboard Design Principles

**Clear Visual Hierarchy:**
```
┌─────────────────────────────────────────────────────┐
│  🟢 AUTOMATED (No Action Needed)                    │
│  - 347 claims submitted automatically today         │
│  - 95.2% confidence average                         │
│  - $428,320 total submitted                         │
├─────────────────────────────────────────────────────┤
│  🟡 NEEDS REVIEW (AI Recommends)                    │
│  - 23 claims queued for review                      │
│  - Average confidence: 82%                          │
│  - Total value: $89,450                             │
│  [Review Queue] →                                   │
├─────────────────────────────────────────────────────┤
│  🔴 REQUIRES ACTION (Human Only)                    │
│  - 8 escalations awaiting assignment                │
│  - 3 appeals need clinical justification            │
│  - 2 fraud alerts                                   │
│  [View Escalations] →                               │
└─────────────────────────────────────────────────────┘
```

**Real-Time Activity Feed:**
- Filter by action type, confidence, dollar amount
- Color-coded by automation tier
- Click for full audit trail

**Exception Queues:**
- Priority classification (high/medium/low)
- SLA countdown timers
- Pre-populated context from AI

**Automation Performance Metrics:**
- Throughput (claims/day)
- Accuracy (human agreement rate)
- Time saved (hours)
- Financial impact ($ collected faster)

---

## Implementation Phases

### Phase 1: Confidence Scoring Infrastructure (Weeks 2-4)
**Deliverables:**
- ClaimScore model with ML predictions
- Confidence threshold configuration per customer
- RiskBaseline integration for scoring
- Shadow mode tracking

**Models to Add:**
```python
class ClaimScore(models.Model):
    """ML-based confidence scoring for automation decisions"""

    claim = models.ForeignKey(ClaimRecord, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    # Confidence metrics
    overall_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    coding_confidence = models.FloatField()
    eligibility_confidence = models.FloatField()
    medical_necessity_confidence = models.FloatField()

    # Risk factors
    denial_risk_score = models.FloatField()
    fraud_risk_score = models.FloatField()
    compliance_risk_score = models.FloatField()

    # Model metadata
    model_version = models.CharField(max_length=50)
    feature_importance = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    # Automation decision
    recommended_action = models.CharField(
        max_length=50,
        choices=[
            ("auto_execute", "Auto Execute"),
            ("queue_review", "Queue for Review"),
            ("escalate", "Escalate to Human"),
        ]
    )
    automation_tier = models.IntegerField(choices=[(1, "Tier 1"), (2, "Tier 2"), (3, "Tier 3")])
```

### Phase 2: Three-Tier Automation Rules (Weeks 5-8)
**Deliverables:**
- Expand AutomationRule model with tier-specific logic
- Threshold-based routing in RulesEngine
- Customer-configurable thresholds
- Exception escalation workflows

### Phase 3: Portal RPA Integration (Weeks 9-12)
**Deliverables:**
- UiPath/Playwright for payer portals
- Credential vault integration
- 2FA automation (TOTP)
- Status check automation

### Phase 4: Appeal Generation (Weeks 13-16)
**Deliverables:**
- LLM + RAG for appeal letters
- Clinical guideline retrieval
- Success pattern matching
- Human review workflow (always required)

### Phase 5: Voice AI (Future - Weeks 17-20)
**Deliverables:**
- Twilio/Vapi.ai integration
- IVR navigation
- Live agent conversation (NLU)
- Structured outcome logging

---

## Strategic Differentiation from Adonis

### Competitive Advantages to Build

1. **Validated Accuracy Over Marketing Claims**
   - Target KLAS Research rating
   - Publish customer benchmarks
   - Third-party validation

2. **Explainable AI by Default**
   - Feature importance in every ExecutionLog
   - Confidence score breakdowns
   - Human-readable reasoning

3. **Compliance-First Design**
   - Audit trails exceeding HIPAA minimums
   - State AI law compliance (CA, FL, CT)
   - Configurable human oversight

4. **Threshold Configurability**
   - Customer sets own risk tolerance
   - Action-specific automation levels
   - Compliance officer controls

5. **Appeals Automation** (Differentiation Opportunity)
   - First to market with safe appeal generation
   - Clinical justification RAG
   - Always require human approval (but save 90% of time)

### Market Positioning

**Tagline:** "Autonomous RCM with Human Oversight Where It Matters"

**Key Messages:**
- "We automate what's safe, escalate what's not"
- "95%+ accuracy validated by customers, not marketing"
- "Your compliance officer controls the guardrails"
- "Built for KLAS ratings, not just case studies"

---

## Success Metrics

### Technical Metrics
- **AUC Score:** >0.85 (industry benchmark: 0.83-0.88)
- **Automation Rate:** 60-90% of routine claims
- **Accuracy:** >95% human agreement rate
- **Denial Reduction:** 25-50% from coding improvements

### Business Metrics
- **Time to Resolution:** 50%+ reduction
- **Cost per Claim:** 30-50% reduction
- **Days in AR:** 15-25% improvement
- **Clean Claim Rate:** >95% (vs 85% industry avg)

### Compliance Metrics
- **Audit Trail Completeness:** 100%
- **Human Review Compliance:** 100% for red-line actions
- **False Positive Rate:** <2%
- **FCA Violations:** 0

### Customer Trust Metrics
- **Shadow Mode Accuracy:** >95% before enabling
- **Customer Advancement Rate:** 80% reach Stage 3 within 6 months
- **Undo Action Rate:** <5% of autonomous submissions
- **Customer Satisfaction (NPS):** >50

---

## Next Steps

**Immediate (Next 2 Weeks):**
1. Add ClaimScore model and confidence scoring
2. Implement CustomerAutomationProfile for trust calibration
3. Enhance ExecutionLog with compliance fields
4. Build threshold-based routing logic

**Near-Term (Weeks 3-8):**
1. Develop three-tier automation rules
2. Build exception queue UI
3. Implement shadow mode tracking
4. Create customer dashboard with transparency

**Medium-Term (Weeks 9-16):**
1. Integrate payer portal RPA
2. Build appeal generation (LLM + RAG)
3. Achieve KLAS Research rating
4. Launch with 3-5 pilot customers

**Long-Term (Weeks 17+):**
1. Voice AI integration
2. Real-time payer rule adaptation
3. Multi-state compliance automation
4. Scale to 50+ customers

---

## Appendix: Vendor Technology Stack

| Vendor | RPA Platform | EHR Integration | Voice AI | Appeal Generation |
|--------|--------------|-----------------|----------|-------------------|
| Adonis | Claimed (unverified) | Claimed | ✅ Claimed | ❌ Human review |
| Waystar | UiPath + APIs | FHIR R4 | ❌ | Draft only |
| AKASA | Computer vision RPA | HL7v2 + FHIR | ❌ | Limited |
| Infinx | UiPath | Proprietary | ❌ | Template-based |
| **Upstream** | **Playwright + UiPath** | **FHIR R4** | **Planned** | **LLM + RAG** |

---

**Document Version:** 1.0
**Last Updated:** 2026-01-31
**Owner:** Product Team
**Status:** Approved for Implementation

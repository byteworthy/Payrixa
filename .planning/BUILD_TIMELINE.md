# Build Timeline: 5-7 Months to Revenue

**Target:** Revenue-ready MVP with 20+ paying customers
**Strategy:** Ship fast, validate early, iterate based on feedback
**Philosophy:** Prevention-first architecture for mid-market specialty practices

---

## ✅ Month 1: Foundation + First Integration (COMPLETE)

### Week 1: Infrastructure Setup (DONE)
- ✅ GCP project setup (Cloud Run, Cloud SQL, Secret Manager)
- ✅ Django 5.1 base project with DRF
- ✅ PostgreSQL schema (Customer, ClaimRecord, AlertEvent, Authorization)
- ✅ Redis setup (caching + Celery)
- ✅ CI/CD pipeline (Cloud Build)
- ✅ Multi-vertical Authorization model (6 service types)
- ✅ ExecutionLog with HIPAA audit trails
- ✅ AutomationRule framework + RulesEngine
- **Deliverable:** Deployed staging environment with Week 1 foundation

### Week 2: CSV Import + Data Quality (DONE)
- ✅ CSV upload endpoint with validation
- ✅ Payer name normalization service
- ✅ CPT code validation against CMS database
- ✅ PHI detection and blocking
- ✅ Data quality dashboard
- ✅ ClaimRecord model with multi-channel tracking (csv_upload, ehr_webhook, api, batch_import)
- **Deliverable:** Can ingest real claims data

### Week 3: Authorization Tracking (DONE - First Prevention Feature)
- ✅ Authorization model with specialty_metadata JSON field
- ✅ Multi-vertical support (ABA, PT, OT, IMAGING, HOME_HEALTH, DIALYSIS)
- ✅ Service type choices with db_index
- ✅ Composite index (customer, service_type, status)
- ✅ Test fixtures updated for submitted_via field
- **Deliverable:** Foundation for calendar-based prevention alerts

### Week 4: EHR Webhook Integration (DONE)
- ✅ FHIR webhook receiver endpoint (`/api/v1/webhooks/ehr/<provider>/`)
- ✅ API key authentication (X-API-Key header)
- ✅ Idempotency handling (Redis)
- ✅ Celery task `process_claim_with_automation`
- ✅ 8 comprehensive tests passing
- **Deliverable:** Real-time claims ingestion foundation

**Month 1 Status:** ✅ **COMPLETE**
- Infrastructure stable and deployed
- Authorization tracking ready for expiration logic
- EHR webhook foundation built
- Test suite passing

---

## 🚧 Month 2: Core Detection + Pre-Submission (IN PROGRESS)

### Week 5: Risk Baseline Calculation + ClaimScore Model
**Goals:** Foundation for pre-submission scoring and confidence-based routing

**Tasks:**
- [ ] Add ClaimScore model to migrations
  ```python
  class ClaimScore(models.Model):
      claim = OneToOneField(ClaimRecord)
      overall_confidence = FloatField(0.0-1.0)
      denial_risk_score = FloatField()
      recommended_action = CharField(choices=['auto_execute', 'queue_review', 'escalate'])
      automation_tier = IntegerField(1-3)
      requires_human_review = BooleanField()  # Red-line detection
      red_line_reason = CharField()
  ```

- [ ] Historical denial rate aggregation by payer+CPT
  ```python
  def calculate_risk_baseline(customer_id, payer, cpt):
      claims = ClaimRecord.objects.filter(
          customer_id=customer_id,
          payer=payer,
          cpt=cpt,
          decided_date__gte=now() - timedelta(days=90)
      )
      denial_rate = claims.filter(outcome='DENIED').count() / claims.count()
      sample_size = claims.count()
      confidence = calculate_statistical_confidence(sample_size)

      RiskBaseline.objects.update_or_create(
          customer=customer, payer=payer, cpt=cpt,
          defaults={'denial_rate': denial_rate, 'sample_size': sample_size, 'confidence': confidence}
      )
  ```

- [ ] Statistical confidence scoring (based on sample size)
- [ ] RiskBaseline model + automated updates
- [ ] Nightly Celery task to recalculate baselines
- [ ] Add CustomerAutomationProfile model (trust calibration stages)
- [ ] Add ShadowModeResult model (AI vs human validation)

**Deliverable:** Risk scoring foundation + confidence-based routing models

---

### Week 6: Pre-Submission Risk Scoring + Three-Tier Routing
**Goals:** Implement three-tier automation model (auto/review/escalate)

**Tasks:**
- [ ] Risk scoring algorithm (0-100 scale)
  ```python
  def calculate_claim_score(claim):
      baseline = RiskBaseline.objects.get(customer=claim.customer, payer=claim.payer, cpt=claim.cpt)

      # Base score from historical denial rate
      denial_risk = baseline.denial_rate

      # Adjust for recent denials (streak detection)
      recent_denials = ClaimRecord.objects.filter(
          customer=claim.customer,
          payer=claim.payer,
          cpt=claim.cpt,
          decided_date__gte=now() - timedelta(days=7),
          outcome='DENIED'
      ).count()
      if recent_denials >= 3:
          denial_risk *= 1.5  # Increase risk

      # Confidence factors
      coding_confidence = validate_cpt_diagnosis_match(claim)
      eligibility_confidence = check_patient_eligibility(claim)
      documentation_completeness = check_required_fields(claim)

      overall_confidence = (coding_confidence + eligibility_confidence + documentation_completeness) / 3

      # Determine automation tier
      profile = claim.customer.automation_profile
      if overall_confidence >= profile.auto_execute_confidence and \
         claim.allowed_amount <= profile.auto_execute_max_amount:
          recommended_action = 'auto_execute'
          automation_tier = 1
      elif overall_confidence >= profile.queue_review_min_confidence:
          recommended_action = 'queue_review'
          automation_tier = 2
      else:
          recommended_action = 'escalate'
          automation_tier = 3

      ClaimScore.objects.create(claim=claim, overall_confidence=overall_confidence, ...)
  ```

- [ ] Modifier requirement validation (check PayerRule table)
- [ ] Recent denial streak detection (3+ denials in 7 days)
- [ ] Pre-submission API endpoint (`POST /api/v1/claims/score/`)
- [ ] Risk score dashboard widget (React component)
- [ ] Red-line detection for compliance (medical necessity, code changes, etc.)

**Deliverable:** Second prevention feature live with three-tier routing

---

### Week 7: Smart Worklists + Alert Management
**Goals:** Workflow management for Tier 2 (queue for review) claims

**Tasks:**
- [ ] Alert prioritization algorithm
  ```python
  def calculate_alert_priority(alert):
      # Revenue impact × urgency
      revenue_impact = alert.evidence_payload.get('claim_amount', 0)

      # Urgency factors
      urgency = 0
      if alert.severity == 'CRITICAL':
          urgency = 100
      elif alert.alert_type == 'authorization_expiring':
          days_until_expiry = (alert.evidence_payload['expiration_date'] - now().date()).days
          urgency = 100 - (days_until_expiry * 3)  # 30 days = 10, 10 days = 70, 3 days = 91
      elif alert.alert_type == 'payment_slowdown':
          urgency = 60
      elif alert.alert_type == 'denial_spike':
          urgency = 80

      priority_score = (revenue_impact * 0.4) + (urgency * 0.6)
      return priority_score
  ```

- [ ] Work queue UI with filters (React)
  - Filter by: severity, alert_type, customer, date range
  - Sort by: priority_score, created_at, revenue_impact
  - Actions: acknowledge, mark noise, resolve

- [ ] Bulk actions (acknowledge multiple, mark noise, assign to user)
- [ ] Resolution tracking (status transitions, resolution_notes)
- [ ] SLA monitoring (time in queue, overdue alerts)

**Deliverable:** Workflow management complete for Tier 2 claims

---

### Week 8: Custom Dashboards + React Frontend
**Goals:** Self-service analytics for non-technical users

**Tasks:**
- [ ] React frontend scaffold
  ```bash
  npx create-react-app frontend
  npm install chart.js react-chartjs-2 tailwindcss @shadcn/ui
  ```

- [ ] Chart.js integration (line charts, bar charts, pie charts)
- [ ] Payer performance dashboard
  - Denial rate trends by payer (last 90 days)
  - Payment timing by payer (average days to payment)
  - Top 5 payers by denial count

- [ ] CPT-level drill-down
  - Denial rate by CPT code
  - Revenue impact by CPT
  - Modifier requirements by CPT

- [ ] Location comparison (multi-location practices)
  - Side-by-side location metrics
  - Outlier detection (which location underperforming?)

- [ ] Dashboard API endpoints (DRF serializers + views)

**Deliverable:** Self-service analytics dashboard usable by billing managers

**Month 2 Success Metrics:**
- Pre-submission scoring accuracy >75%
- Can identify high-risk claims before submission
- Dashboard usable by non-technical users
- 3-5 beta customers onboarded

---

## 📅 Month 3: Specialty Intelligence (Weeks 9-12)

### Week 9: Dialysis MA Variance Tracking
**Goals:** First specialty module - dialysis Medicare Advantage payment variance

**Tasks:**
- [ ] Traditional Medicare baseline calculation
  - Aggregate claims for traditional Medicare (payer='Medicare Part B')
  - Calculate average payment per CPT code
  - Store in RiskBaseline with specialty='DIALYSIS'

- [ ] MA payment comparison algorithm
  ```python
  def detect_ma_variance(claim):
      if claim.payer not in MA_PAYER_LIST:
          return None

      # Get traditional Medicare baseline
      baseline = RiskBaseline.objects.get(
          customer=claim.customer,
          payer='Medicare Part B',
          cpt=claim.cpt,
          specialty='DIALYSIS'
      )

      # Calculate MA payment as % of traditional
      ma_payment_ratio = claim.paid_amount / baseline.average_payment

      # Alert if < 85% threshold
      if ma_payment_ratio < 0.85:
          AlertEvent.objects.create(
              customer=claim.customer,
              alert_type='ma_variance_detected',
              severity='MEDIUM',
              title=f'MA payment {ma_payment_ratio:.1%} of traditional Medicare',
              evidence_payload={'claim_id': claim.id, 'ratio': ma_payment_ratio, ...}
          )
  ```

- [ ] Variance threshold alerts (<85% baseline)
- [ ] Revenue impact projection ($ lost per patient over year)
- [ ] Specialty metadata: `{'ma_plan_type': 'Advantage', 'esrd_pps_bundle': 'CA2F'}`

**Deliverable:** First specialty module complete

---

### Week 10: ABA Authorization Unit Tracking
**Goals:** Second specialty module - ABA authorization lifecycle management

**Tasks:**
- [ ] Unit consumption tracking
  ```python
  def track_aba_units(claim):
      # Find authorization for this patient
      auth = Authorization.objects.get(
          customer=claim.customer,
          patient_identifier=hash_patient_id(claim.patient_id),
          service_type='ABA',
          status='ACTIVE'
      )

      # Extract units from claim (CPT 97151, 97153, etc.)
      units_billed = claim.procedure_count  # or parse from CPT units

      # Update authorization
      auth.units_used += units_billed
      auth.save()

      # Check exhaustion threshold
      utilization_rate = auth.units_used / auth.units_authorized
      if utilization_rate > 0.9:
          # 90% units used - alert
          AlertEvent.objects.create(...)
  ```

- [ ] Visit exhaustion projection
  - Calculate weekly usage rate
  - Project date of unit exhaustion
  - Alert when < 2 weeks remaining

- [ ] Re-auth deadline calculation (30/14/3 days)
  ```python
  def check_auth_expiration(auth):
      days_until_expiry = (auth.auth_expiration_date - now().date()).days

      if days_until_expiry == 30 and not auth.last_alert_sent:
          send_alert(auth, 'MEDIUM', '30 days until authorization expires')
      elif days_until_expiry == 14:
          send_alert(auth, 'HIGH', '14 days until authorization expires')
      elif days_until_expiry == 3:
          send_alert(auth, 'CRITICAL', '3 days until authorization expires')
  ```

- [ ] Credential expiration tracking (BCBA)
  - specialty_metadata: `{'bcba_required': true, 'credential_expiration': '2025-06-30'}`
  - Alert 60/30/14 days before credential expires

**Deliverable:** Second specialty module complete

---

### Week 11: PT/OT 8-Minute Rule Validation
**Goals:** Third specialty module - PT/OT time-based billing compliance

**Tasks:**
- [ ] Time-based CPT validation
  ```python
  TIME_BASED_CPTS = {
      '97110': 15,  # Therapeutic exercise - 15 min
      '97112': 15,  # Neuromuscular reeducation
      '97140': 15,  # Manual therapy
      # ... etc
  }

  def validate_8_minute_rule(claim):
      total_minutes = 0
      for cpt in claim.cpt_codes:
          if cpt in TIME_BASED_CPTS:
              total_minutes += TIME_BASED_CPTS[cpt] * claim.units[cpt]

      # 8-minute rule: 1 unit = 8-22 min, 2 units = 23-37 min, etc.
      expected_units = calculate_units_from_minutes(total_minutes)
      billed_units = sum(claim.units.values())

      if billed_units != expected_units:
          AlertEvent.objects.create(
              alert_type='8_minute_rule_violation',
              severity='HIGH',
              title=f'8-minute rule: {billed_units} units billed, {expected_units} expected',
              ...
          )
  ```

- [ ] Unit calculation verification
- [ ] Real-time compliance checking (pre-submission)
- [ ] KX threshold monitoring ($2,410 for 2025)
  ```python
  def check_kx_threshold(claim, patient_ytd_charges):
      if patient_ytd_charges > 2410:
          # KX modifier required
          if 'KX' not in claim.modifiers:
              AlertEvent.objects.create(
                  alert_type='missing_kx_modifier',
                  severity='CRITICAL',
                  title='KX modifier required (exceeded therapy cap)',
                  ...
              )
  ```

**Deliverable:** Third specialty module complete

---

### Week 12: Epic Integration (Polling)
**Goals:** Second EHR integration using FHIR R4 polling

**Tasks:**
- [ ] Epic FHIR R4 connector
  - OAuth 2.0 authentication (client credentials flow)
  - SMART on FHIR App registration
  - Token refresh logic

- [ ] 15-minute polling schedule (Celery beat)
  ```python
  @shared_task
  def poll_epic_claims():
      for customer in Customer.objects.filter(epic_enabled=True):
          # Get OAuth token
          token = get_epic_oauth_token(customer)

          # Fetch ExplanationOfBenefit resources (claims)
          last_poll = customer.last_epic_poll or (now() - timedelta(hours=24))
          eobs = fetch_epic_eobs(customer, since=last_poll)

          # Parse and create ClaimRecords
          for eob in eobs:
              claim = parse_fhir_eob(eob)
              ClaimRecord.objects.create(
                  customer=customer,
                  source='API',
                  submitted_via='ehr_webhook',
                  ...
              )

          customer.last_epic_poll = now()
          customer.save()
  ```

- [ ] ExplanationOfBenefit resource parsing
- [ ] Error handling + retry logic
- [ ] Rate limiting (Epic throttles at 10K requests/day)

**Deliverable:** Second EHR integration complete

**Month 3 Success Metrics:**
- 3 specialty modules live
- Dialysis practices see MA variance alerts
- ABA practices prevent auth expiration denials
- 8-10 paying customers

---

## 📅 Month 4: Advanced Detection + Network Effects (Weeks 13-16)

### Week 13: Imaging RBM Requirements
**Goals:** Fourth specialty module - imaging center prior authorization

**Tasks:**
- [ ] eviCore PA requirement database
  - Import eviCore PA requirements by CPT code
  - Store in PayerRule table with rule_type='AUTHORIZATION'

- [ ] AIM PA requirement database
- [ ] PA requirement checker API
  ```python
  def check_imaging_pa_required(claim):
      # Check if PA required for this CPT+payer combo
      rule = PayerRule.objects.filter(
          payer=claim.payer,
          rule_type='AUTHORIZATION',
          conditions__cpt=claim.cpt
      ).first()

      if rule and rule.authorization_required:
          # Check if authorization obtained
          auth = Authorization.objects.filter(
              customer=claim.customer,
              cpt_codes__contains=[claim.cpt],
              status='ACTIVE'
          ).first()

          if not auth:
              AlertEvent.objects.create(
                  alert_type='missing_prior_authorization',
                  severity='CRITICAL',
                  title=f'PA required for {claim.cpt} (not obtained)',
                  ...
              )
  ```

- [ ] Medical necessity documentation validation
  - specialty_metadata: `{'rbm_provider': 'eviCore', 'pa_required': true}`

**Deliverable:** Fourth specialty module complete

---

### Week 14: Home Health PDGM Validation
**Goals:** Fifth specialty module - home health PDGM grouper

**Tasks:**
- [ ] PDGM grouper logic (simplified, 50 most common groups)
  ```python
  PDGM_GROUPS = {
      # Timing × Clinical × Functional × Comorbidity
      ('Early': 'MS-Rehab', 'Low', 'Low'): 'PDGM_1A1',
      # ... 50 most common combinations
  }

  def validate_pdgm_grouping(claim):
      timing = claim.specialty_metadata.get('timing')  # Early/Late
      clinical = claim.specialty_metadata.get('clinical_group')  # MS-Rehab, Neuro-Rehab, etc.
      functional = claim.specialty_metadata.get('functional_score')  # Low/Medium/High
      comorbidity = claim.specialty_metadata.get('comorbidity_score')  # Low/Medium/High

      expected_group = PDGM_GROUPS.get((timing, clinical, functional, comorbidity))
      billed_group = claim.specialty_metadata.get('pdgm_group')

      if expected_group != billed_group:
          AlertEvent.objects.create(
              alert_type='pdgm_grouping_error',
              severity='HIGH',
              title=f'PDGM grouping mismatch: {billed_group} vs expected {expected_group}',
              ...
          )
  ```

- [ ] Face-to-Face timing validation
  - specialty_metadata: `{'f2f_completed': true, 'f2f_date': '2025-01-15'}`
  - Validate F2F occurred within required timeframe

- [ ] NOA deadline tracking (Notice of Admission)
  - Must be submitted within 5 days of start of care
  - Alert if approaching deadline

- [ ] OASIS-E validation
  - Check OASIS assessment dates
  - specialty_metadata: `{'oasis_date': '2025-01-15'}`

**Deliverable:** Fifth specialty module complete

---

### Week 15: Cross-Customer Intelligence (Network Effects)
**Goals:** Anonymized aggregation to detect industry-wide patterns

**Tasks:**
- [ ] Anonymized data aggregation
  ```python
  def aggregate_industry_patterns():
      # Aggregate denial rates by payer+CPT across ALL customers (anonymized)
      industry_baselines = ClaimRecord.objects.values('payer', 'cpt').annotate(
          denial_rate=Avg(Case(When(outcome='DENIED', then=1), default=0)),
          sample_size=Count('id')
      ).filter(sample_size__gte=30)  # Statistical significance

      # Store in IndustryBaseline table (not customer-specific)
      for baseline in industry_baselines:
          IndustryBaseline.objects.update_or_create(
              payer=baseline['payer'],
              cpt=baseline['cpt'],
              defaults={'denial_rate': baseline['denial_rate'], 'sample_size': baseline['sample_size']}
          )
  ```

- [ ] Industry-wide pattern detection
  - Compare customer's denial rate vs industry average
  - Alert if significantly worse (statistical outlier)

- [ ] Network effect alerts
  ```python
  def detect_payer_rule_change():
      # Detect sudden denial rate spike across multiple customers
      recent_denials = ClaimRecord.objects.filter(
          decided_date__gte=now() - timedelta(days=7),
          outcome='DENIED',
          payer='UnitedHealthcare',
          cpt='97110'
      ).values('customer').annotate(
          count=Count('id')
      )

      affected_customers = [c for c in recent_denials if c['count'] >= 3]

      if len(affected_customers) >= 5:
          # Payer rule change detected (5+ customers affected)
          for customer in Customer.objects.filter(id__in=[c['customer'] for c in affected_customers]):
              AlertEvent.objects.create(
                  customer=customer,
                  alert_type='payer_rule_change_detected',
                  severity='HIGH',
                  title=f'UnitedHealthcare rule change detected (8 practices affected)',
                  evidence_payload={'affected_customer_count': len(affected_customers), ...}
              )
  ```

- [ ] Privacy-preserving architecture
  - Never expose customer-specific data across tenants
  - Only aggregate statistics (denial rates, not claim details)

**Deliverable:** Network intelligence live

---

### Week 16: ML Pattern Recognition
**Goals:** AI-powered insights using scikit-learn

**Tasks:**
- [ ] Basic ML model (Random Forest)
  ```python
  from sklearn.ensemble import RandomForestClassifier
  from sklearn.model_selection import train_test_split

  def train_denial_prediction_model(customer_id):
      # Features: payer, cpt, modifiers, diagnosis, recent_denial_streak
      claims = ClaimRecord.objects.filter(
          customer_id=customer_id,
          decided_date__gte=now() - timedelta(days=180)
      )

      X = extract_features(claims)  # Encode categorical variables
      y = [1 if c.outcome == 'DENIED' else 0 for c in claims]

      X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

      model = RandomForestClassifier(n_estimators=100)
      model.fit(X_train, y_train)

      # Evaluate
      accuracy = model.score(X_test, y_test)

      # Save model
      import joblib
      joblib.dump(model, f'models/customer_{customer_id}_rf.pkl')

      return model, accuracy
  ```

- [ ] Denial probability prediction
  - Predict denial probability for new claims
  - Use in ClaimScore calculation

- [ ] Payer behavior clustering
  - Cluster payers by behavior patterns
  - Identify "high risk" payer groups

- [ ] Model retraining pipeline (monthly Celery task)
  - Retrain models with latest data
  - Track model performance over time

**Deliverable:** AI-powered insights (>70% accuracy target)

**Month 4 Success Metrics:**
- All 5 specialty modules complete
- Cross-customer intelligence providing value
- ML model accuracy >70%
- 15-20 paying customers

---

## 📅 Month 5: Polish + Launch Prep (Weeks 17-20)

### Week 17: Executive Reporting
**Goals:** CFO-ready weekly summary emails

**Tasks:**
- [ ] Weekly summary email generation
  - Top 3 risks this week
  - Trending metrics (better/worse indicators)
  - Recommended actions

- [ ] PDF export functionality
  ```python
  from weasyprint import HTML

  def generate_executive_summary_pdf(customer_id):
      # Render HTML template with week's data
      context = {
          'week_start': now() - timedelta(days=7),
          'week_end': now(),
          'top_risks': AlertEvent.objects.filter(customer_id=customer_id, severity='HIGH')[:3],
          'denial_rate_trend': calculate_trend(...),
          'payment_timing_trend': calculate_trend(...),
          ...
      }
      html = render_to_string('executive_summary.html', context)

      # Convert to PDF
      pdf = HTML(string=html).write_pdf()
      return pdf
  ```

- [ ] Trend visualization (better/worse indicators)
  - Green ↑ for improving metrics
  - Red ↓ for worsening metrics

- [ ] Recommended actions generation
  - AI-generated action items based on alerts

**Deliverable:** CFO-ready reporting

---

### Week 18: Self-Service Onboarding
**Goals:** No-touch customer acquisition

**Tasks:**
- [ ] Stripe integration for payments
  ```python
  import stripe

  def create_stripe_customer(user):
      stripe_customer = stripe.Customer.create(
          email=user.email,
          name=user.customer.name,
          metadata={'customer_id': user.customer.id}
      )

      user.customer.stripe_customer_id = stripe_customer.id
      user.customer.save()

  def create_subscription(customer, tier):
      price_id = TIER_PRICE_IDS[tier]  # 'tier1' -> 'price_xxx'

      subscription = stripe.Subscription.create(
          customer=customer.stripe_customer_id,
          items=[{'price': price_id}],
          trial_period_days=30
      )

      customer.stripe_subscription_id = subscription.id
      customer.tier = tier
      customer.save()
  ```

- [ ] Self-service signup flow
  1. Create account (email + password)
  2. Select tier (Essentials/Professional/Enterprise)
  3. Enter payment details (Stripe checkout)
  4. Upload CSV (optional - can do later)
  5. Redirect to dashboard

- [ ] Automated onboarding emails
  - Welcome email with getting started guide
  - Day 3: "Upload your first CSV"
  - Day 7: "See your first insights"
  - Day 14: "Schedule strategy call"

- [ ] In-app tutorial (React Joyride)
  - Step 1: Upload CSV
  - Step 2: View dashboard
  - Step 3: Review alerts
  - Step 4: Configure thresholds

**Deliverable:** No-touch customer acquisition

---

### Week 19: HIPAA Compliance Audit
**Goals:** HIPAA-ready for enterprise customers

**Tasks:**
- [ ] External HIPAA audit ($5K-10K)
  - Hire compliance firm (Compliancy Group, HIPAA One)
  - Security risk assessment
  - Gap analysis

- [ ] Penetration testing
  - Hire pentesting firm ($2K-5K)
  - Test for SQL injection, XSS, CSRF
  - Remediate findings

- [ ] Security documentation
  - Security policies (access control, incident response)
  - Privacy policies (data retention, PHI handling)
  - HIPAA training materials

- [ ] BAA template creation
  - Business Associate Agreement template
  - AI-specific clauses (from COMPLIANCE_REQUIREMENTS.md)
  - Legal review ($1K)

**Deliverable:** HIPAA-ready for enterprise

---

### Week 20: Production Launch
**Goals:** Open for business

**Tasks:**
- [ ] Marketing website live (Next.js)
  - Homepage with value proposition
  - Pricing page (transparent pricing)
  - Use cases by specialty
  - Comparison page (vs-enterprise-rcm)
  - Blog (SEO content)

- [ ] SEO optimization
  - Keyword research (Ahrefs/SEMrush)
  - On-page SEO (title tags, meta descriptions)
  - Schema markup (Organization, Product)
  - Blog content (20 posts from Month 1-3 plan)

- [ ] Case study creation (3 early customers)
  - Customer interviews
  - Quantify results (denials prevented, $ saved)
  - Design case study PDFs

- [ ] Public launch announcement
  - LinkedIn post
  - Email to beta list
  - MGMA/HFMA forum posts
  - Reddit (r/medicalbilling)

**Deliverable:** Open for business

**Month 5 Success Metrics:**
- 25-30 paying customers
- $8K-12K MRR
- Self-service acquisition working
- <5% churn

---

## 📅 Months 6-7: Growth & Iteration

### Focus Areas

**Additional EHR Integrations:**
- Cerner/Oracle Health (polling)
- Tebra/Kareo (SOAP API)
- athenahealth production credentials

**SOC 2 Type 1 Preparation:**
- Hire SOC 2 auditor ($15K-25K)
- Implement security controls
- Documentation + evidence collection
- Target: Certified Month 9-12

**Customer Success Automation:**
- Onboarding playbook
- Health score calculation
- Proactive outreach for at-risk customers
- Quarterly business reviews (QBR) for Tier 3

**Feature Requests from Top Customers:**
- Prioritize based on revenue + strategic fit
- Ship 1-2 customer-requested features/month

**Partnership Development:**
- State association partnerships (APTA, ASHA)
- Conference sponsorships
- Webinar series

### Success Metrics

- 40-50 paying customers
- $15K-20K MRR ($180K-240K ARR)
- >90% retention
- Profitable unit economics
- 3+ EHR integrations live

---

## Timeline Summary

| Month | Focus | Deliverables | Customers | MRR |
|-------|-------|--------------|-----------|-----|
| **1** ✅ | Foundation | Infrastructure, CSV, Authorization, EHR webhooks | 0 | $0 |
| **2** 🚧 | Detection | Risk scoring, pre-submission, dashboards | 3-5 beta | $2K-3K |
| **3** 📅 | Specialty | Dialysis, ABA, PT/OT modules, Epic integration | 8-10 | $5K-7K |
| **4** 📅 | Advanced | Imaging, home health, network intelligence, ML | 15-20 | $9K-13K |
| **5** 📅 | Launch | Reporting, self-service, HIPAA, website | 25-30 | $12K-18K |
| **6-7** 📅 | Growth | EHR integrations, SOC 2, partnerships | 40-50 | $20K-30K |

**Total Timeline:** 5-7 months to revenue-ready MVP
**Path to $100K ARR:** Month 12 (35-45 customers)
**Path to $1M ARR:** Month 24 (100-130 customers)

---

**Last Updated:** January 31, 2026
**Status:** Month 1 Complete, Month 2 Week 5 Starting
**Owner:** Kevin (Founder)

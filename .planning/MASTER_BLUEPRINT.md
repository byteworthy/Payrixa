# UPSTREAM: Complete Master Blueprint
## Building Better, Faster, Bootstrapped

**Last Updated:** January 31, 2026
**Status:** Week 1 Complete, Phase 1 Ready to Start
**Timeline:** 5-7 months to revenue-ready MVP
**Target:** $100K ARR in 12 months, $1M ARR in 24 months

**⚠️ CONFIDENTIAL - Internal Strategy Document**
*Contains competitive analysis and pricing strategy. Not for public GitHub.*

---

## EXECUTIVE SUMMARY

Upstream targets the **mid-market segments enterprise RCM vendors ignore**: 5-25 provider specialty practices with 15-30% denial rates who can't afford $6K+/year enterprise pricing or 6-month implementations.

**Core Strategy:**
- **Match on detection** (real-time denial alerts, pattern recognition)
- **Beat on prevention** (authorization tracking, pre-submission scoring, calendar-based alerts)
- **Dominate on execution** (30-day implementation vs 6 months, $299-999/mo vs $6K+/year, transparent vs opaque)

**Competitive Advantages:**
1. **Prevention-first architecture** - Detect problems before submission, not after
2. **Specialty-specific intelligence** - Built for ABA/PT/dialysis/imaging/home health from day 1
3. **Transparent pricing & fast deployment** - Published pricing, CSV-first integration, self-service onboarding
4. **Solo founder velocity** - Ship features in days with Claude Code, not quarters with committees

**Revenue Model:** Tiered SaaS subscription
- Tier 1: $299/month (1-3 providers)
- Tier 2: $599/month (4-10 providers)
- Tier 3: $999/month (11-25 providers)

**Target Metrics:**
- **Month 6:** Beta launch, 3-5 paying customers, $2K-5K MRR
- **Month 12:** Production launch, 15-25 customers, $8K-15K MRR ($100K ARR)
- **Month 24:** Market validation, 80-120 customers, $80K-120K MRR ($1M ARR)

---

## CURRENT STATUS (January 31, 2026)

### ✅ Week 1 Foundation Complete

**Implemented:**
- Multi-vertical Authorization model (ABA, PT, OT, IMAGING, HOME_HEALTH, DIALYSIS)
- ExecutionLog with HIPAA-compliant audit trails
- AutomationRule framework with rules engine
- EHR webhook endpoint (`/api/v1/webhooks/ehr/<provider>/`)
- ClaimRecord model with multi-channel ingestion tracking
- RiskBaseline, ExecutionLog models for autonomous execution

**Documentation:**
- RCM Automation Strategic Framework (3,800+ lines)
- Compliance Requirements (red-line actions, state AI laws)
- UX Trust Patterns (4-stage calibration framework)
- Competitive positioning analysis

**Git Commits:**
- `348f1b57`: Week 1 autonomous execution foundation
- `1a4960ad`: Multi-vertical Authorization support
- `42407690`: RCM automation strategic framework
- `a8892a65`: RCM automation README

### 📋 Next Steps: Phase 1 (Weeks 2-4)

See [BUILD_TIMELINE.md](./BUILD_TIMELINE.md) for detailed roadmap.

---

## COMPETITIVE LANDSCAPE (INTERNAL)

### Market Leaders

**Enterprise RCM Platforms:**
- **Adonis Intelligence:** $54M raised, $13.3B claims processed, 35+ EHR integrations
  - Strengths: Deep pockets, AI Agents (phone calls), enterprise credibility
  - Weaknesses: Zero public reviews, opaque pricing, 6-month implementation, post-submission only

- **Waystar:** 85% prior auth auto-approval, RPA + APIs
  - Strengths: Clearinghouse + patient access, KLAS rated
  - Weaknesses: Enterprise focus, appeals draft-only

- **AKASA:** Human-in-loop leader, 99.5% accuracy
  - Strengths: Cleveland Clinic deployment, explicit accuracy claims
  - Weaknesses: Conservative (flags vs executes), expensive

**Mid-Market Gap:**
- No vendor focused on 5-25 provider specialty practices
- All require 6+ month implementations
- None offer published pricing
- Zero prevention features (all post-submission detection)

### Our Competitive Advantages

1. **Prevention vs Detection**
   - Competitors: Detect denials after submission
   - Upstream: Prevent denials before submission + detect after
   - Features they don't have: Authorization tracking, pre-submission scoring, calendar alerts

2. **Specialty-Specific Intelligence**
   - Competitors: Generic platform adapted to specialties
   - Upstream: Built for ABA/PT/dialysis/imaging/home health from day 1
   - Deep domain logic: 8-minute rule, MA variance, PDGM validation

3. **Transparent & Fast**
   - Competitors: "Call for quote", 6-month implementation
   - Upstream: $299-999/month published, 30-day implementation, CSV import day 1

4. **Solo Founder Velocity**
   - Ship features in days (not quarters)
   - Direct customer relationships
   - Claude Code 10x productivity

### Strategic Positioning (Public Messaging)

**Never mention Adonis by name in public materials.**

Instead: "enterprise RCM platforms" or "traditional denial management tools"

**Comparison Page (vs-enterprise-rcm):**
```
| Feature | Enterprise Tools | Upstream |
|---------|-----------------|----------|
| Detection Speed | 24-48 hours post-submission | Real-time + 30-day prevention |
| Prevention | Minimal | Authorization, pre-submission, calendar |
| Implementation | 6-9 months | 30 days |
| Pricing | $6K+/year, call for quote | $299-999/month, published |
| Integration | Requires EHR partnership | CSV import day 1 |
| Support | Ticketed queues | Direct email/chat |
| Specialty Focus | Generic platform | ABA, PT, dialysis, imaging, home health |
```

---

## TECHNICAL ARCHITECTURE

See [TECHNICAL_ARCHITECTURE.md](./TECHNICAL_ARCHITECTURE.md) for complete details.

**Stack:**
- Django 5.1+ (Python 3.12), DRF, Celery, Redis, PostgreSQL 15+
- GCP: Cloud Run, Cloud SQL, Cloud Storage, Secret Manager
- Frontend (Phase 2): React 18+, TypeScript, Tailwind, Shadcn/UI

**Core Models:**
- Customer, Location, ClaimRecord, Authorization, RiskBaseline
- AlertEvent, PayerRule, ExecutionLog, AutomationRule
- ClaimScore, CustomerAutomationProfile, ShadowModeResult

**Three-Tier Automation:**
- Tier 1 (Auto-Execute): >95% confidence, <$1K
- Tier 2 (Queue Review): 70-95% confidence, $1K-$10K
- Tier 3 (Escalate): <70% confidence, >$10K, red-line actions

---

## BUILD TIMELINE (5-7 MONTHS)

See [BUILD_TIMELINE.md](./BUILD_TIMELINE.md) for week-by-week breakdown.

### ✅ Month 1: Foundation + First Integration (COMPLETE)
- Week 1: Infrastructure, CSV import, authorization tracking
- Week 2-3: Authorization expiration alerts, unit tracking
- Week 4: athenahealth webhook integration

### 🚧 Month 2: Core Detection + Pre-Submission (IN PROGRESS)
- Week 5: Risk baseline calculation
- Week 6: Pre-submission risk scoring
- Week 7: Smart worklists, alert prioritization
- Week 8: Custom dashboards (React frontend)

### 📅 Month 3: Specialty Intelligence
- Week 9: Dialysis MA variance tracking
- Week 10: ABA authorization unit tracking
- Week 11: PT/OT 8-minute rule validation
- Week 12: Epic integration (polling)

### 📅 Month 4: Advanced Detection + Network Effects
- Week 13: Imaging RBM requirements
- Week 14: Home Health PDGM validation
- Week 15: Cross-customer intelligence
- Week 16: ML pattern recognition

### 📅 Month 5: Polish + Launch Prep
- Week 17: Executive reporting, PDF export
- Week 18: Self-service onboarding, Stripe integration
- Week 19: HIPAA compliance audit
- Week 20: Production launch, marketing website

### 📅 Months 6-7: Growth & Iteration
- Additional EHR integrations
- SOC 2 Type 1 preparation
- Customer success automation
- Partnership development

---

## GO-TO-MARKET STRATEGY

See [GTM_STRATEGY.md](./GTM_STRATEGY.md) for complete details.

### Customer Acquisition Channels (Prioritized)

**Channel 1: Content Marketing + SEO (Highest ROI)**
- Blog: 20 posts Month 1-3, 10 competitive posts Month 4-6, 24 industry insights Month 7-12
- SEO: "ABA authorization tracking software", "[specialty] denial management", "enterprise alternative"
- Distribution: LinkedIn 3x/week, Reddit, MGMA/HFMA forums

**Channel 2: State Association Partnerships**
- APTA, ASHA, BACB-adjacent, state dialysis associations
- Sponsor newsletters ($500-1K/month), webinars, preferred vendor status
- Expected: 10-20 warm leads/quarter, 20-30% close rate

**Channel 3: Direct Outreach (Fast Validation)**
- Cold email: 50/day manually personalized
- Target: ZoomInfo/Apollo, 5-25 providers, $500K-$5M revenue
- Expected: 2 demos/week, 3 customers/month

**Channel 4: Paid Ads (Months 6+)**
- Google Ads: $2K-3K/month, 2-5 customers/month, CAC $400-1,500
- LinkedIn Ads: $1K-2K/month, 1-3 customers/month, CAC $500-2,000

### Sales Process (Founder-Led)

1. Discovery (15 min): Qualify, understand pain
2. Demo (30 min): Show specialty module, real alerts
3. Trial Setup (15 min): Upload CSV, configure alerts
4. 30-Day Trial: Weekly check-ins, ROI calculation
5. Close: Show denials prevented, offer annual discount

**Conversion:** 60% discovery→demo, 50% demo→trial, 70% trial→paid = 21% overall

---

## PRICING STRATEGY

**Tiered Monthly Subscription:**

| Tier | Price | Providers | Features |
|------|-------|-----------|----------|
| **Essentials** | $299/mo | 1-3 | CSV, core detection, email alerts |
| **Professional** | $599/mo | 4-10 | +1 EHR, prevention, custom dashboards |
| **Enterprise** | $999/mo | 11-25 | +2 EHRs, specialty modules, priority support |

**Add-ons:**
- Additional EHR: $199/month
- Additional locations (25+ providers): $50/provider/month
- Dedicated CSM: $500/month

**Annual Discount:** 2 months free (16.7% off)

**Expected Distribution:**
- 20% Tier 1 ($299), 60% Tier 2 ($599), 20% Tier 3 ($999)
- Average: $639/customer
- Target: 100 customers = $64K MRR = $768K ARR

---

## FINANCIAL PROJECTIONS

### Revenue Milestones

| Month | Customers | MRR | ARR |
|-------|-----------|-----|-----|
| 6 | 20 | $12,780 | $153K |
| 12 | 40 | $25,560 | $307K |
| 18 | 70 | $44,730 | $537K |
| 24 | 120 | $76,680 | $920K |

### Cost Structure

**Fixed Costs:** $2,700/month (GCP $2K, tools $500, misc $200)
**Variable Costs:** $15-20/customer/month
**CAC:** $50 (Months 1-6), $300-500 (Months 6-12), $500-800 (Months 13-24)

### Profitability

- **Month 6:** Profitable ($12,780 revenue - $3,100 costs = $9,680 profit)
- **Month 12:** Cash flow positive ($25,560 - $6,000 = $19,560)
- **Month 24:** High margin ($76,680 - $15,000 = $61,680)

**Path to $1M ARR:**
- Conservative: Month 26-27
- Aggressive: Month 20
- Required: 130 customers @ $639/month average

---

## SUCCESS METRICS

### Product Metrics

- **Month 3:** 3 specialty modules, >75% scoring accuracy, athenahealth working
- **Month 5:** 5 specialty modules, self-service signup, HIPAA documented
- **Month 12:** SOC 2 Type 1, 3+ EHR integrations, >70% ML accuracy

### Business Metrics

- **Month 6:** 20-25 customers, $12K-15K MRR, <10% churn
- **Month 12:** 35-45 customers, $25K-30K MRR, profitable
- **Month 24:** 100-130 customers, $65K-85K MRR, LTV/CAC >4:1

### Competitive Win Metrics

- **Month 6:** Win 2 competitive deals, 2 case studies, 10+ G2 reviews
- **Month 12:** Win 5+ competitive deals, #1 for "[competitor] alternative"
- **Month 24:** 20% competitive wins, category leader recognition

---

## RISKS & MITIGATION

### Technical Risks

1. **EHR Integration Complexity**
   - Mitigation: CSV-first, athenahealth only Month 1
   - Fallback: Polling vs webhooks

2. **HIPAA Compliance Delays**
   - Mitigation: External audit Month 5
   - Fallback: De-identified data only

3. **ML Model Accuracy**
   - Mitigation: Rules-based first, ML gradual
   - Fallback: Rules are 86-90% effective anyway

### Market Risks

1. **Competitors Copy Prevention**
   - Mitigation: Speed advantage (weeks vs quarters)
   - Differentiation: Specialty focus + transparent pricing

2. **Slow Customer Acquisition**
   - Mitigation: Diversified channels
   - Trigger: If <5 customers Month 6, pivot ICP

3. **High Churn**
   - Mitigation: Weekly check-ins first 90 days
   - Trigger: If >15%, diagnose before scaling

### Execution Risks

1. **Solo Founder Burnout**
   - Mitigation: Maintain DaVita through Month 12
   - Schedule: 28 hrs/week, no work Sunday

2. **Feature Scope Creep**
   - Mitigation: Strict roadmap, no custom <$10K
   - Rule: Prevention or detection only

3. **Cash Flow Crunch**
   - Mitigation: Profitable Month 6
   - Reserve: $10K emergency fund

---

## NEXT ACTIONS

**This Week:**
1. Review Phase 1 implementation plan (Weeks 2-4)
2. Set up ClaimScore model migration
3. Design confidence scoring algorithm

**Next Week:**
1. Start Week 5: Risk baseline calculation
2. Train initial ML models (Random Forest, Gradient Boosting)
3. Implement threshold-based routing

**Month 2:**
1. Complete Phase 1 (confidence scoring, pre-submission, dashboards)
2. Onboard 3-5 beta customers
3. Begin Phase 2 planning (specialty modules)

---

**Last Updated:** January 31, 2026
**Status:** Week 1 Complete, Phase 1 Ready
**Owner:** Kevin (Founder)

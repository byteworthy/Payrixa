# Upstream Healthcare Roadmap

**Product Vision:** Early-warning revenue intelligence for specialty healthcare practices.

We detect payer behavior changes, authorization risks, and claim issues 30-60 days before they become denials—giving operators time to act while options still exist.

---

## Product Philosophy

**Prevention-First Architecture**
- Traditional RCM tools detect problems after submission
- Upstream prevents problems before they happen
- Authorization tracking, pre-submission scoring, calendar-based alerts

**Built for Specialists**
- Deep domain logic for ABA, PT/OT, dialysis, imaging, home health
- Not a generic platform adapted to specialties
- Specialty-specific intelligence from day 1

**Transparent & Fast**
- Published pricing: $299-999/month
- 30-day implementation (not 6 months)
- CSV import works day 1 (not "requires EHR integration")

---

## Current Status (January 2026)

### ✅ Foundation Complete (Month 1)

**Infrastructure:**
- Django 5.1+ backend with PostgreSQL, Redis, Celery
- GCP deployment (Cloud Run, Cloud SQL)
- Multi-tenant architecture with row-level security

**Core Models:**
- Authorization tracking (multi-vertical: ABA, PT, OT, imaging, home health, dialysis)
- Claim records with multi-channel ingestion (CSV, webhook, API)
- Risk baselines for historical denial rate tracking
- Audit logs (HIPAA-compliant)

**Integrations:**
- CSV import (universal fallback)
- EHR webhook foundation (FHIR R4/R5)
- API key authentication
- Idempotency handling

---

## Roadmap

### 🚧 Phase 1: Core Detection + Pre-Submission (Month 2)

**Target:** March 2026

**Features:**
- **Risk Scoring Engine:** 0-100 risk score per claim based on historical denial rates
- **Pre-Submission Scanner:** Flag risky claims before submission
- **Smart Worklists:** Prioritized alert queues by revenue impact × urgency
- **Custom Dashboards:** Self-service analytics for billing managers

**Success Metrics:**
- Pre-submission scoring accuracy >75%
- 3-5 beta customers onboarded
- Dashboard usable by non-technical users

---

### 📅 Phase 2: Specialty Intelligence (Month 3)

**Target:** April 2026

**Specialty Modules:**
1. **Dialysis:** Medicare Advantage payment variance tracking
   - Compare MA payments vs traditional Medicare baseline
   - Alert when <85% of baseline
   - Revenue impact projection

2. **ABA Therapy:** Authorization lifecycle management
   - Unit consumption tracking
   - Visit exhaustion projection
   - 30/14/3 day expiration alerts
   - BCBA credential expiration

3. **PT/OT:** 8-minute rule compliance
   - Time-based CPT validation
   - Real-time unit calculation
   - KX threshold monitoring ($2,410 cap)

4. **Epic Integration:** FHIR R4 polling (second EHR)

**Success Metrics:**
- 3 specialty modules live
- Prevent first authorization expiration denials
- 8-10 paying customers

---

### 📅 Phase 3: Advanced Detection (Month 4)

**Target:** May 2026

**Features:**
5. **Imaging:** RBM prior authorization requirements
   - eviCore/AIM PA database
   - Medical necessity validation
   - PA requirement checker

6. **Home Health:** PDGM grouper validation
   - 50 most common PDGM groups
   - Face-to-face timing validation
   - NOA deadline tracking
   - OASIS-E validation

7. **Network Intelligence:** Cross-customer pattern detection
   - Industry-wide denial rate benchmarks
   - Payer rule change detection
   - "8 practices affected" alerts

8. **ML Pattern Recognition:** AI-powered insights
   - Denial probability prediction (scikit-learn)
   - Payer behavior clustering
   - >70% accuracy target

**Success Metrics:**
- All 5 specialty modules complete
- Network intelligence providing value
- 15-20 paying customers

---

### 📅 Phase 4: Polish + Launch (Month 5)

**Target:** June 2026

**Features:**
- **Executive Reporting:** Weekly CFO summaries with PDF export
- **Self-Service Onboarding:** Stripe integration, automated signup
- **HIPAA Compliance:** External audit, penetration testing, BAA template
- **Marketing Website:** Next.js site with SEO optimization

**Launch:**
- Public production launch
- Published pricing ($299-999/month)
- 3 customer case studies
- 20+ blog posts (SEO content)

**Success Metrics:**
- 25-30 paying customers
- $8K-12K MRR
- Self-service acquisition working
- <5% churn

---

### 📅 Phase 5: Growth & Scale (Months 6-7)

**Target:** July-August 2026

**Features:**
- Additional EHR integrations (Cerner, Tebra/Kareo)
- SOC 2 Type 1 preparation
- Customer success automation
- State association partnerships

**Success Metrics:**
- 40-50 paying customers
- $15K-20K MRR ($180K-240K ARR)
- >90% retention
- Profitable unit economics

---

### 📅 Future: Enterprise & Scale (Months 8-12)

**Target:** September 2026 - January 2027

**Features:**
- SOC 2 Type 2 certification
- Enterprise features (SSO, advanced RBAC)
- API for third-party integrations
- Mobile app (iOS/Android)
- Advanced ML models (deep learning)

**Success Metrics:**
- $100K ARR (35-45 customers)
- KLAS Research rating
- Conference speaking slots
- Strategic partnerships

---

## Feature Comparison

### Detection Features

| Feature | Status | ETA |
|---------|--------|-----|
| Denial rate drift detection (week-over-week) | ✅ Built | Done |
| Statistical significance testing | ✅ Built | Done |
| CPT-level denial patterns | ✅ Built | Done |
| Payment timing trends | ✅ Built | Done |
| Smart worklists (prioritization) | 🚧 Building | Mar 2026 |
| Denial clustering/categorization | 📅 Planned | Apr 2026 |

### Prevention Features (Our Differentiation)

| Feature | Status | ETA |
|---------|--------|-----|
| Authorization expiration tracking | ✅ Built | Done |
| Pre-submission risk scoring | 🚧 Building | Mar 2026 |
| Modifier validation | 🚧 Building | Mar 2026 |
| Calendar-based alerts (30/14/3 days) | 🚧 Building | Mar 2026 |
| Medical necessity checking | 📅 Planned | May 2026 |

### Specialty Modules

| Specialty | Status | ETA |
|-----------|--------|-----|
| Dialysis MA variance | 📅 Planned | Apr 2026 |
| ABA authorization units | 📅 Planned | Apr 2026 |
| PT/OT 8-minute rule | 📅 Planned | Apr 2026 |
| Imaging RBM requirements | 📅 Planned | May 2026 |
| Home health PDGM | 📅 Planned | May 2026 |

### Integrations

| Integration | Status | ETA |
|-------------|--------|-----|
| CSV import | ✅ Built | Done |
| athenahealth (FHIR R5 webhooks) | ✅ Built | Done |
| Epic (FHIR R4 polling) | 📅 Planned | Apr 2026 |
| Cerner/Oracle Health | 📅 Planned | Jul 2026 |
| Tebra/Kareo | 📅 Planned | Jul 2026 |

---

## Pricing

**Transparent, published pricing (no "call for quote"):**

| Tier | Price | Providers | Features |
|------|-------|-----------|----------|
| **Essentials** | $299/mo | 1-3 | CSV, core detection, email alerts |
| **Professional** | $599/mo | 4-10 | +1 EHR, prevention features, custom dashboards |
| **Enterprise** | $999/mo | 11-25 | +2 EHRs, specialty modules, priority support |

**Add-ons:**
- Additional EHR integration: $199/month
- Additional locations (25+ providers): $50/provider/month
- Dedicated CSM: $500/month

**Annual discount:** 2 months free (16.7% off)

---

## Success Metrics

### Product Metrics
- **Accuracy:** >95% for risk scoring, >70% for ML predictions
- **Speed:** Real-time detection + 30-day prevention
- **Coverage:** 5 specialties, 3+ EHR integrations

### Business Metrics
- **Month 6:** 20-25 customers, $12K-15K MRR
- **Month 12:** 35-45 customers, $25K-30K MRR ($300K ARR)
- **Month 24:** 100-130 customers, $80K-120K MRR ($1M ARR)

### Customer Metrics
- **Retention:** >90% annual retention
- **Churn:** <10% annual churn
- **NPS:** >50 (industry benchmark)
- **ROI:** $5-10 saved for every $1 spent

---

## Contributing

We welcome feedback on our roadmap! If you're a beta customer or interested in specific features:

1. Open an issue with the `roadmap-feedback` label
2. Email us at [email protected]
3. Join our monthly product roadmap call

**Prioritization Criteria:**
1. Customer revenue impact ($)
2. Number of customers affected
3. Strategic fit (prevention vs detection)
4. Implementation effort

---

## FAQ

**Q: Can I request custom features?**
A: Yes! For customers on Enterprise tier ($999/mo), we offer custom development at $1,000/one-time fee. For smaller requests, we prioritize based on revenue impact.

**Q: What if my EHR isn't supported yet?**
A: CSV import works day 1 for all EHRs. We're adding Epic, Cerner, Tebra in Months 3-7. Vote for your EHR in our GitHub issues.

**Q: Do you integrate with clearinghouses?**
A: Not yet. We focus on detection/prevention, not submission. But we're exploring partnerships with Waystar, Change Healthcare for future.

**Q: How fast are new features shipped?**
A: We ship weekly. Solo founder with Claude Code enables 10x velocity compared to enterprise vendors (weeks vs quarters).

**Q: Will you raise VC funding?**
A: No plans to raise. Bootstrapped, profitable, customer-driven. This keeps us focused on mid-market (not forced into enterprise by investors).

---

**Last Updated:** January 31, 2026
**Next Update:** March 2026 (after Phase 1 complete)
**Roadmap Maintainer:** Kevin (Founder)

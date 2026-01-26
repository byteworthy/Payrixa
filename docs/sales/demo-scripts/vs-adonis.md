# Demo Comparison Script: Upstream vs. Adonis Intelligence

**Last Updated:** January 26, 2026
**Purpose:** Side-by-side feature demonstration highlighting Upstream's differentiators vs. Adonis
**Demo Duration:** 30-45 minutes
**Target Audience:** CFO, RCM Director, Clinical Director, Practice Manager

---

## Demo Structure

1. **Introduction & Discovery** (5 min)
2. **Early-Warning Detection Demo** (10 min) - *Upstream's core differentiator*
3. **Specialty-Specific Intelligence Demo** (10 min) - *Dialysis/ABA/Imaging/Home Health*
4. **Implementation Speed Walkthrough** (5 min) - *30 days vs. 3-6 months*
5. **Pricing Transparency Demo** (5 min) - *Fixed vs. variable*
6. **Q&A & Next Steps** (5-10 min)

---

## 1. Introduction & Discovery (5 min)

### Opening Script

*"Thanks for joining today. I'm going to show you how Upstream's early-warning payer intelligence differs from Adonis's real-time alerts. Before we dive in, let me ask a few quick questions to tailor the demo to your needs:"*

### Discovery Questions

1. **Current state:** "Are you currently using Adonis, or are you evaluating both products?"
   - *If using Adonis:* "What's working well? What's frustrating?"
   - *If evaluating both:* "What are your top 3 decision criteria?"

2. **Specialty focus:** "Are you in [dialysis / ABA therapy / imaging / home health]?"
   - *Tailor demo to their specialty*

3. **Pain points:** "What's your current denial rate? [Listen for 8-15%+] What would it be worth to reduce that by 20-35%?"

4. **Timeline:** "What's your urgency? Do you need to go live in 30-60 days, or can you wait 3-6 months for EHR integration?"

5. **Pricing:** "Do you prefer predictable fixed pricing or variable percentage-based pricing?"

### Positioning Statement

*"Here's what you'll see today: Adonis provides real-time alerts the moment claims are submitted - that's valuable for quick recovery. Upstream provides early-warning alerts 2-4 weeks before denials are expected - that's prevention, not recovery. We're also purpose-built for [dialysis / ABA / imaging / home health] with specialty-specific intelligence that Adonis doesn't offer. Let's see the difference."*

---

## 2. Early-Warning Detection Demo (10 min)

### Demo Goal
Show how Upstream detects payer behavioral changes 2-4 weeks before Adonis alerts at submission.

### Adonis's Approach (Explain, Don't Show)

*"Adonis provides real-time alerts at the moment claims are submitted. For example, if you submit a claim today and the payer starts denying a certain CPT code, Adonis alerts you today or tomorrow. That's valuable for immediate action, but by then the claim is already out - you can't prevent the denial, only appeal."*

**Visual:** Show Adonis alert example (screenshot or slide) with timestamp "Alert triggered: Day of submission."

### Upstream's Approach (Live Demo)

*"Upstream works differently. Our DriftWatch™ algorithm analyzes longitudinal payer behavior over weeks and months to detect subtle shifts before denials appear. Let me show you an example."*

#### Demo Scenario 1: Dialysis ESRD PPS Change Detection

**Setup:** Show Upstream dashboard with "DriftWatch Alerts" tab.

**Walkthrough:**
1. **Alert:** "Medicare Advantage Plan X: Comorbidity Code Denial Pattern Detected"
2. **Timing:** "Alert triggered: 3 weeks before next claim batch"
3. **Details:**
   - "Payer started denying dialysis claims with comorbidity code [N18.6] in combination with [E11.22]"
   - "Trend started 2 weeks ago, detected by behavioral drift analysis"
   - "Impact: 15% of your dialysis claims use this combination"
   - "Recommendation: Review clinical documentation for [N18.6 + E11.22] claims, consider alternative comorbidity codes if supported by medical record"

**Contrast with Adonis:**
*"Adonis would alert you the day you submit these claims - too late to prevent the denial. Upstream alerts you 3 weeks early, giving you time to adjust coding practices before submission. That's prevention vs. recovery."*

**ROI calculation:**
*"For a 10-station dialysis center, this single alert prevented $47,000 in denials in one quarter. Adonis would've caught it after submission, requiring appeals and resubmissions. Upstream prevented it entirely."*

#### Demo Scenario 2: Medicare Advantage Authorization Requirement Change

**Setup:** Show second DriftWatch alert.

**Walkthrough:**
1. **Alert:** "Medicare Advantage Plan Y: New Prior Authorization Requirement Detected"
2. **Timing:** "Alert triggered: 4 weeks before enforcement date"
3. **Details:**
   - "Payer added prior authorization requirement for [CPT 90837 - ABA therapy, 60+ min session]"
   - "Enforcement starts [date 4 weeks out]"
   - "Impact: 40% of your ABA claims use this CPT code"
   - "Recommendation: Begin obtaining prior authorizations for 90837 sessions immediately"

**Contrast with Adonis:**
*"Adonis would alert you when the first claim gets denied - 4 weeks after enforcement starts. By then, you'd have 4 weeks of denied claims to appeal. Upstream caught it 4 weeks before enforcement, so you can start getting prior auths proactively. Zero denials."*

---

### Key Takeaway for Early-Warning Demo

*"The core difference is timing: Adonis alerts at submission (reactive). Upstream alerts 2-4 weeks before denials (proactive). Which is more valuable to your practice: prevention or recovery?"*

---

## 3. Specialty-Specific Intelligence Demo (10 min)

### Demo Goal
Show specialty-specific rules that Adonis doesn't offer (dialysis, ABA, imaging, home health).

### Adonis's Approach (Explain, Don't Show)

*"Adonis provides general denial pattern detection across specialties. They work well for primary care, urgent care, orthopedics - but they don't have custom rules for dialysis ESRD PPS, ABA authorization tracking, imaging prior auth patterns, or home health OASIS documentation. Let me show you what Upstream offers that Adonis doesn't."*

---

### Demo Scenario 3A: Dialysis ESRD PPS Bundle Change Tracking

**Setup:** Show Upstream "Specialty Intelligence" tab > Dialysis module.

**Walkthrough:**
1. **Feature:** "ESRD PPS Bundle Change Detection"
2. **What it does:**
   - Tracks Medicare MAC policy changes affecting ESRD PPS bundled dialysis payments
   - Monitors comorbidity modifier shifts (MBI adjustments, Case-Mix Classification changes)
   - Alerts on injectable code denial patterns (ESAs, IV iron, etc.)
   - Tracks composite rate vs. bundled rate coding issues

3. **Example alert:**
   - "MAC [Region X]: ESRD PPS Case-Mix Classification Changed"
   - "New comorbidity combinations no longer qualify for [Kidney Disease Level 3] reimbursement"
   - "Affected patient list: [15 patients] - review clinical documentation and adjust case-mix classification"

**Contrast with Adonis:**
*"Adonis doesn't have this. They don't track ESRD PPS bundle changes because they're not built for dialysis. For a dialysis center, this is the #1 denial risk - and Adonis won't catch it until after submission. Upstream is purpose-built for dialysis."*

---

### Demo Scenario 3B: ABA Therapy Authorization Expiration Tracking

**Setup:** Show Upstream "Specialty Intelligence" tab > ABA module.

**Walkthrough:**
1. **Feature:** "Authorization Expiration Tracking"
2. **What it does:**
   - Tracks authorization expiration dates across multiple payers (Anthem, Aetna, UHC, etc.)
   - Monitors session limits (e.g., 40 hours/month authorized, 38 hours used)
   - Alerts 2 weeks before expirations to allow proactive renewal
   - Flags medical necessity criteria changes by payer

3. **Example alert:**
   - "Patient [John Doe]: Anthem Authorization Expires in 14 Days"
   - "Current authorization: 40 hours/month, expires [date]"
   - "Action: Submit renewal request to Anthem immediately to avoid service disruption"
   - "Attached: Renewal request template for Anthem"

**Contrast with Adonis:**
*"Adonis would alert you when the first claim gets denied due to expired authorization - after the expiration date. By then, you've already provided services you can't bill for. Upstream alerts you 2 weeks before expiration, so you can renew proactively. For an ABA clinic, authorization denials are 60% of total denials - this is huge."*

---

### Demo Scenario 3C: Imaging Prior Authorization Pattern Tracking

**Setup:** Show Upstream "Specialty Intelligence" tab > Imaging module.

**Walkthrough:**
1. **Feature:** "Prior Authorization Pattern Shift Detection"
2. **What it does:**
   - Tracks prior authorization approval patterns for high-cost imaging (MRI, CT, PET)
   - Monitors medical necessity criteria changes by payer and CPT code
   - Alerts on radiology benefit manager (RBM) policy changes (AIM, National Imaging Associates, etc.)
   - Flags sudden increases in prior auth denials by anatomical region (brain MRI, lumbar spine MRI, etc.)

3. **Example alert:**
   - "Payer [Cigna]: MRI Lumbar Spine (72148) Prior Auth Denial Rate Increased 35%"
   - "Trend started 3 weeks ago - medical necessity criteria tightened"
   - "New requirement: Must document failed conservative treatment (6 weeks PT) before approval"
   - "Action: Update prior auth requests to include conservative treatment documentation"

**Contrast with Adonis:**
*"Adonis would alert you when claims get denied due to lack of prior auth - after imaging services are rendered. Upstream detects the pattern shift 3 weeks early, so you can adjust prior auth requests before imaging. That prevents claim denials and patient satisfaction issues."*

---

### Demo Scenario 3D: Home Health OASIS Documentation Tracking

**Setup:** Show Upstream "Specialty Intelligence" tab > Home Health module.

**Walkthrough:**
1. **Feature:** "OASIS Documentation Requirement Monitoring"
2. **What it does:**
   - Tracks Medicare MAC policy changes affecting OASIS documentation
   - Monitors homebound status interpretation shifts by payer
   - Alerts on LUPA (Low Utilization Payment Adjustment) risk factors
   - Flags episode timing issues (60-day episode billing compliance)

3. **Example alert:**
   - "MAC [Region Y]: Homebound Status Documentation Requirements Tightened"
   - "New requirement: Must document patient's inability to leave home without considerable and taxing effort (specific language required)"
   - "Affected patients: [12 patients] - review homebound documentation and add specific language to clinical notes"

**Contrast with Adonis:**
*"Adonis doesn't track OASIS documentation requirements because they're not built for home health. Upstream is. For a home health agency, OASIS documentation denials are the #1 denial risk - and Upstream catches policy changes before claims are denied."*

---

### Key Takeaway for Specialty Intelligence Demo

*"Adonis treats all specialties the same - general denial pattern detection. Upstream is purpose-built for [dialysis / ABA / imaging / home health] with custom rules that Adonis doesn't offer. If you're in one of these specialties, Upstream's intelligence is far deeper than Adonis's general rules."*

---

## 4. Implementation Speed Walkthrough (5 min)

### Demo Goal
Show 30-day implementation process vs. Adonis's 3-6 month EHR integration.

### Adonis's Implementation (Explain, Don't Demo)

*"Adonis requires 3-6 months for EHR integration with athenahealth, AdvancedMD, or eClinicalWorks. The timeline includes:*
- *Month 1-2: EHR vendor coordination and API access setup*
- *Month 3-4: Integration development and testing*
- *Month 5-6: Pilot, training, and go-live*

*That's 3-6 months of continued denial losses while you wait to go live. If you're losing $50k-$200k per month to preventable denials, that's $150k-$1.2M in opportunity cost during implementation."*

### Upstream's 30-Day Implementation (Show Process)

**Setup:** Show Upstream "Implementation Roadmap" slide or dashboard.

**Walkthrough:**

**Week 1: Kickoff & Data Connection**
- *"Initial onboarding call with dedicated specialist (30 minutes)"*
- *"Connect data feed from clearinghouse OR set up CSV upload"*
- *"Verify historical claims data visibility (3-6 months of history preferred)"*

**Week 2-3: Configuration & Specialty Rules Setup**
- *"Configure specialty-specific rules (dialysis ESRD PPS, ABA auth tracking, imaging prior auth, home health OASIS)"*
- *"Set alert thresholds based on your denial tolerance (e.g., alert when denial rate increases 10%+)"*
- *"Train staff on DriftWatch™ and DenialScope™ dashboards (1-day training)"*

**Week 4: Testing & Launch**
- *"Test alert delivery (email, in-app, Slack integration if desired)"*
- *"Review first batch of early-warning alerts with onboarding specialist"*
- *"Go live with production monitoring"*

**Fast-Track Option:**
*"If you have an urgent need, we can fast-track to 2 weeks. We've done that for practices losing $100k+/month to denials who need to stop the bleeding immediately."*

---

### Key Takeaway for Implementation Demo

*"Upstream is live in 30 days with no EHR vendor coordination. Adonis requires 3-6 months for EHR integration. If you're losing $50k-$200k per month to denials, every month you wait costs you money. Would you rather start seeing ROI in 30 days or 3-6 months?"*

---

## 5. Pricing Transparency Demo (5 min)

### Demo Goal
Show transparent fixed pricing (Upstream) vs. variable percentage-based pricing (Adonis).

### Adonis's Pricing (Explain, Show Estimate)

*"Adonis charges a percentage of your recovered denials - typically 10-15%, though they don't disclose pricing publicly. That means:*
- *Your costs fluctuate every month based on denial volume*
- *Higher denial rates = higher costs (counterintuitive incentive)*
- *Difficult to budget accurately for annual RCM technology spend"*

**Show slide:** "Adonis Pricing Estimate" with monthly variability graph (costs fluctuate month-to-month).

**Example for Medium Dialysis Center:**
- *Month 1: Denials = $100k, Recovery = $60k, Adonis fee (12%) = $7,200*
- *Month 2: Denials = $150k, Recovery = $90k, Adonis fee (12%) = $10,800*
- *Month 3: Denials = $80k, Recovery = $48k, Adonis fee (12%) = $5,760*
- *"Your Adonis bill fluctuates from $5,760 to $10,800 per month. Hard to budget."*

---

### Upstream's Pricing (Show Transparent Pricing Table)

**Setup:** Show Upstream "Pricing" slide with transparent tiers.

**Walkthrough:**

| Practice Size | Monthly Fee | Annual Cost |
|---------------|-------------|-------------|
| **Small (1-5 providers or 5-10 dialysis stations)** | $1,500 | $18,000 |
| **Medium (6-20 providers or 10-20 dialysis stations)** | $3,500 | $42,000 |
| **Large (20+ providers or 20+ dialysis stations)** | Custom ($5,000-$7,000) | $60,000-$84,000 |

**Key points:**
- *"Fixed monthly fee - same cost every month, regardless of denial volume"*
- *"Transparent pricing - no surprises, no fluctuations"*
- *"Predictable budgeting - your CFO can forecast accurately for board approval"*

**Example for Medium Dialysis Center:**
- *"Upstream costs $3,500/month = $42,000/year (fixed)"*
- *"Adonis costs an estimated $7,000-$11,000/month = $84,000-$132,000/year (variable)"*
- *"Savings with Upstream: $42,000-$90,000/year (50-68% lower)"*

---

### Cost + ROI Walkthrough

**Setup:** Show "ROI Calculator" slide.

**Walkthrough:**

*"The real value isn't just cost savings on the platform fee. It's the ROI from preventing denials before submission."*

**Example for Medium Dialysis Center:**
- **Current denial rate:** 11.8%
- **Annual denials:** $1,416,000
- **After Upstream (25-35% reduction):** $924,000-$1,068,000
- **Annual savings from prevention:** $348,000-$492,000
- **Upstream cost:** $42,000/year
- **Net ROI:** $306,000-$450,000/year (7-11x ROI)
- **Payback period:** 1 month

*"Does that ROI meet your CFO's approval threshold?"*

---

### Key Takeaway for Pricing Demo

*"Upstream is typically 50-68% lower in annual cost AND provides 7-11x ROI through denial prevention. Adonis's percentage-based model is unpredictable and more expensive. Which model works better for your CFO: fixed + predictable (Upstream) or variable + opaque (Adonis)?"*

---

## 6. Q&A & Next Steps (5-10 min)

### Common Questions & Answers

**Q: "Can we run Upstream and Adonis in parallel?"**
**A:** *"Yes. Many of our customers started that way - Adonis for real-time alerts, Upstream for early-warning prevention. Over time, they found Upstream caught more issues and canceled Adonis. But there's no requirement to switch on day one. Would you be open to a 60-day parallel trial?"*

**Q: "Does Upstream integrate with our EHR like Adonis?"**
**A:** *"No - Upstream is EHR-independent, which allows 30-day implementation vs. 3-6 months for Adonis. Trade-off: speed + specialty intelligence vs. EHR embedding. What's more important: fast implementation or embedded alerts?"*

**Q: "What if we're already mid-contract with Adonis?"**
**A:** *"We can run Upstream in parallel until your Adonis renewal. By renewal time, you'll have data showing which product caught more issues. If Upstream wins, you cancel Adonis. If Adonis wins, you cancel Upstream. Fair?"*

**Q: "Does Upstream provide real-time alerts like Adonis?"**
**A:** *"No - Upstream provides early-warning alerts 2-4 weeks before denials. That's by design - we're prevention-focused, not recovery-focused. If real-time alerts at submission are critical, Adonis wins. If prevention is more valuable, Upstream wins. Which aligns better with your goals?"*

---

### Next Steps

**Option 1: 30-Day Free Trial (Ideal)**
*"Let's set up a 30-day free trial. We'll connect your data feed, configure [dialysis / ABA / imaging / home health]-specific rules, and show you live alerts. By day 30, you'll have data showing how many denials Upstream prevented that Adonis would've missed. Fair?"*

**Option 2: Parallel Trial with Adonis (If Already Using Adonis)**
*"Let's run Upstream and Adonis in parallel for 60 days. We'll track which product catches more issues, generates fewer false positives, and provides better ROI. By day 60, you'll know which to keep. Fair?"*

**Option 3: Custom ROI Analysis (If CFO Approval Needed)**
*"Let me prepare a customized ROI analysis for your practice size and specialty. I'll show you:*
1. *Upstream's fixed cost vs. Adonis's estimated variable cost*
2. *ROI from preventing denials (based on your current denial rate)*
3. *Total cost of ownership over 3 years*

*Can we schedule 30 minutes next week to review with your CFO?"*

---

## Demo Best Practices

### Do's
1. **Tailor to their specialty** - Show dialysis/ABA/imaging/home health-specific examples
2. **Contrast with Adonis explicitly** - Don't assume they know the differences
3. **Quantify ROI** - Use their actual denial data to calculate savings
4. **Show live alerts** - Don't just explain, demonstrate
5. **Ask discovery questions** - Uncover pain points throughout demo
6. **Acknowledge Adonis strengths** - Real-time alerts, EHR integration (fair positioning)
7. **Close with clear next step** - Trial, parallel trial, or ROI analysis

### Don'ts
1. **Don't bash Adonis** - Position as "different approaches" not "better vs. worse"
2. **Don't over-promise** - Be honest about Upstream weaknesses (no real-time alerts, no EHR embedding)
3. **Don't rush** - Take time to show specialty-specific intelligence in depth
4. **Don't skip pricing** - CFO decision = cost + ROI, address both
5. **Don't forget to ask for the close** - Always propose next step

---

## Summary: Demo Key Messages

1. **Early-warning prevention** (Upstream) vs. **real-time recovery** (Adonis) - *Timing is the core difference*
2. **Specialty-specific intelligence** (Upstream) vs. **general rules** (Adonis) - *Depth for dialysis/ABA/imaging/home health*
3. **30-day implementation** (Upstream) vs. **3-6 months EHR integration** (Adonis) - *Speed = faster ROI*
4. **Transparent fixed pricing** (Upstream) vs. **variable percentage-based** (Adonis) - *Predictability + lower cost*
5. **7-11x ROI from prevention** (Upstream) vs. **recovery-only ROI** (Adonis) - *Prevention > recovery*

**Closing question:** *"Based on what you've seen, does Upstream's early-warning prevention + specialty intelligence + 30-day implementation + transparent pricing align better with your goals than Adonis's real-time alerts + EHR integration + 3-6 month timeline + variable pricing?"*

---

*Last updated: January 26, 2026. Refresh quarterly or when new product features are released.*

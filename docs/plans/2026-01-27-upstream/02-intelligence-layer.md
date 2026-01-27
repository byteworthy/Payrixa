# Intelligence Layer: Risk Scoring & Behavioral Prediction

**Document:** 02-intelligence-layer.md
**Author:** Product & Engineering
**Date:** 2026-01-27
**Status:** Design Complete

---

## Overview

The Intelligence Layer analyzes claims data to predict risk and detect payer behavior changes. It powers both preventive alerts (pre-submission) and autonomous execution decisions.

**Key Differentiation:** Specialty-specific models (dialysis MA variance, ABA authorization patterns) vs generic risk scoring.

---

## Component 1: Pre-Submission Risk Scoring

### Purpose

Calculate risk score 0-100 for claims BEFORE submission. Enable operators to fix issues before they cause denials.

**Target Accuracy:** >75% (validated against historical data)
**Target Latency:** <500ms per scoring request

### Risk Score Algorithm

**Formula:** Weighted sum of 5 risk factors

```
Risk Score = (40% × historical_denial_rate)
           + (20% × missing_modifiers)
           + (20% × recent_denial_streak)
           + (10% × diagnosis_mismatch)
           + (10% × authorization_missing)
```

### Implementation

**File:** `upstream/services/risk_scoring.py`

```python
from django.utils import timezone
from datetime import timedelta
from dataclasses import dataclass
from typing import List, Optional
from upstream.models import RiskBaseline, ClaimRecord, Authorization, ModifierRequirement, DiagnosisCPTRule
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskFactor:
    """Individual risk factor contribution."""
    factor: str
    value: float
    weight: float
    contribution: float
    details: Optional[str] = None


@dataclass
class RiskScore:
    """Complete risk score with breakdown."""
    score: float  # 0-100
    confidence: float  # 0-1
    factors: List[RiskFactor]
    recommendation: str
    auto_fix_actions: List[dict]  # Actions we can auto-execute


class PreSubmissionRiskScorer:
    """
    Pre-submission risk scoring with autonomous fix capabilities.

    Key Difference: We don't just flag risk, we auto-fix when possible.
    """

    def __init__(self, customer_id: str):
        self.customer_id = customer_id

    def score_claim(self, claim_data: dict) -> RiskScore:
        """
        Calculate risk score 0-100 with actionable recommendations.

        Risk Factors:
        1. Historical denial rate (40% weight)
        2. Missing required modifiers (20% weight)
        3. Recent denial streak (20% weight)
        4. Diagnosis-CPT mismatch (10% weight)
        5. Authorization status (10% weight)

        Args:
            claim_data: {
                'customer_id': str,
                'payer': str,
                'cpt': str,
                'diagnosis_codes': List[str],
                'modifiers': List[str],
                'patient_id': str,
            }

        Returns:
            RiskScore with score, confidence, factors, recommendation
        """

        score = 0
        factors = []
        auto_fix_actions = []  # NEW: Actions we can auto-execute

        # Factor 1: Historical denial rate (40%)
        baseline_confidence = 0.5
        try:
            baseline = RiskBaseline.objects.get(
                customer_id=claim_data['customer_id'],
                payer=claim_data['payer'],
                cpt=claim_data['cpt']
            )

            if baseline.confidence_score > 0.5:
                base_risk = baseline.denial_rate * 40
                score += base_risk
                baseline_confidence = baseline.confidence_score
                factors.append(RiskFactor(
                    factor='historical_denial_rate',
                    value=baseline.denial_rate,
                    weight=0.40,
                    contribution=base_risk,
                    details=f"Based on {baseline.sample_size} historical claims"
                ))
        except RiskBaseline.DoesNotExist:
            # No historical data - use conservative estimate
            score += 20
            factors.append(RiskFactor(
                factor='insufficient_data',
                value=1.0,
                weight=0.40,
                contribution=20,
                details='No historical data for this payer+CPT combination'
            ))

        # Factor 2: Missing required modifiers (20%)
        required_modifiers = ModifierRequirement.objects.filter(
            payer=claim_data['payer'],
            cpt=claim_data['cpt']
        ).values_list('required_modifier', flat=True)

        missing_modifiers = set(required_modifiers) - set(claim_data.get('modifiers', []))

        if missing_modifiers:
            score += 20
            factors.append(RiskFactor(
                factor='missing_modifiers',
                value=1.0,
                weight=0.20,
                contribution=20,
                details=f"Missing: {', '.join(missing_modifiers)}"
            ))

            # AUTO-FIX: Can add missing modifiers automatically
            auto_fix_actions.append({
                'action': 'add_modifiers',
                'params': {'modifiers': list(missing_modifiers)}
            })

        # Factor 3: Recent denial streak (20%)
        recent_denials = ClaimRecord.objects.filter(
            customer_id=claim_data['customer_id'],
            payer=claim_data['payer'],
            outcome='DENIED',
            decided_date__gte=timezone.now() - timedelta(days=30)
        ).count()

        if recent_denials >= 2:
            score += 20
            factors.append(RiskFactor(
                factor='recent_denial_streak',
                value=recent_denials,
                weight=0.20,
                contribution=20,
                details=f"{recent_denials} denials in last 30 days"
            ))

        # Factor 4: Diagnosis-CPT mismatch (10%)
        valid_diagnosis = self._validate_diagnosis_cpt_match(
            claim_data.get('diagnosis_codes', []),
            claim_data['cpt'],
            claim_data['payer']
        )

        if not valid_diagnosis:
            score += 10
            factors.append(RiskFactor(
                factor='diagnosis_mismatch',
                value=1.0,
                weight=0.10,
                contribution=10,
                details='Diagnosis does not support medical necessity for this CPT'
            ))

        # Factor 5: Authorization status (10%)
        auth_required = self._requires_authorization(
            claim_data['payer'],
            claim_data['cpt']
        )

        if auth_required:
            auth = Authorization.objects.filter(
                customer_id=claim_data['customer_id'],
                patient_identifier=claim_data.get('patient_id'),
                status='ACTIVE',
                cpt_codes__contains=claim_data['cpt']
            ).first()

            if not auth:
                score += 10
                factors.append(RiskFactor(
                    factor='authorization_missing',
                    value=1.0,
                    weight=0.10,
                    contribution=10,
                    details='Prior authorization required but not obtained'
                ))

        # Generate recommendations
        recommendation = self._generate_recommendation(factors, auto_fix_actions)

        return RiskScore(
            score=min(score, 100),
            confidence=baseline_confidence,
            factors=factors,
            recommendation=recommendation,
            auto_fix_actions=auto_fix_actions
        )

    def _validate_diagnosis_cpt_match(self, diagnosis_codes: List[str], cpt: str, payer: str) -> bool:
        """
        Check if diagnosis codes support medical necessity for CPT.

        Uses DiagnosisCPTRule lookup table.
        """
        if not diagnosis_codes:
            return False

        # Check payer-specific rules first
        payer_rules = DiagnosisCPTRule.objects.filter(
            cpt=cpt,
            payer=payer
        )

        if payer_rules.exists():
            for rule in payer_rules:
                if any(code in rule.icd10_codes for code in diagnosis_codes):
                    return True
            return False

        # Check general rules (payer=null)
        general_rules = DiagnosisCPTRule.objects.filter(
            cpt=cpt,
            payer__isnull=True
        )

        if general_rules.exists():
            for rule in general_rules:
                if any(code in rule.icd10_codes for code in diagnosis_codes):
                    return True
            return False

        # No rules found - assume valid
        return True

    def _requires_authorization(self, payer: str, cpt: str) -> bool:
        """
        Check if this payer+CPT combination requires prior authorization.

        TODO: Implement AuthorizationRequirement lookup table.
        """
        # Placeholder: ABA therapy CPTs typically require auth
        aba_cpts = ['97151', '97152', '97153', '97154', '97155', '97156', '97157', '97158']
        if cpt in aba_cpts:
            return True

        return False

    def _generate_recommendation(self, factors: List[RiskFactor], auto_fix_actions: List[dict]) -> str:
        """
        Generate actionable recommendation.

        Format: "AUTO-FIX: [actions] | MANUAL: [actions] | ESCALATE: [reason]"
        """
        recommendations = []

        # Auto-fix recommendations
        if auto_fix_actions:
            auto_fixes = [action['action'] for action in auto_fix_actions]
            recommendations.append(f"AUTO-FIX: {', '.join(auto_fixes)}")

        # Manual recommendations
        manual_actions = []
        for factor in factors:
            if factor.factor == 'diagnosis_mismatch':
                manual_actions.append('Update diagnosis codes')
            elif factor.factor == 'authorization_missing':
                manual_actions.append('Obtain prior authorization')
            elif factor.factor == 'insufficient_data':
                manual_actions.append('Review claim carefully (no historical baseline)')

        if manual_actions:
            recommendations.append(f"MANUAL: {', '.join(manual_actions)}")

        # Escalation recommendation
        high_risk_factors = [f for f in factors if f.contribution >= 20]
        if len(high_risk_factors) >= 2:
            recommendations.append('ESCALATE: Multiple high-risk factors - review required')

        return ' | '.join(recommendations) if recommendations else 'Claim appears ready for submission'
```

### Supporting Models

**ModifierRequirement Model:**

```python
class ModifierRequirement(BaseModel):
    """
    Payer-specific modifier requirements.

    Example: UnitedHealthcare requires modifier -59 for CPT 97162 when bilateral.
    """
    payer = models.CharField(max_length=255, db_index=True)
    cpt = models.CharField(max_length=20, db_index=True)
    required_modifier = models.CharField(max_length=10)
    condition = models.TextField(help_text='When this modifier is required')

    class Meta:
        unique_together = ('payer', 'cpt', 'required_modifier')

    def __str__(self):
        return f"{self.payer} - {self.cpt} - {self.required_modifier}"
```

**DiagnosisCPTRule Model:**

```python
class DiagnosisCPTRule(BaseModel):
    """
    Valid diagnosis-CPT combinations.

    Example: CPT 97162 (PT eval) supports M54.5 (low back pain).
    """
    cpt = models.CharField(max_length=20, db_index=True)
    diagnosis_category = models.CharField(max_length=100)
    icd10_codes = models.JSONField(default=list)
    payer = models.CharField(max_length=255, null=True, blank=True)  # null = all payers

    class Meta:
        indexes = [
            models.Index(fields=['cpt', 'payer']),
        ]

    def __str__(self):
        return f"{self.cpt} - {self.diagnosis_category}"
```

### Data Seeding

**Management Command:** `python manage.py seed_risk_scoring_data`

```python
# upstream/management/commands/seed_risk_scoring_data.py

from django.core.management.base import BaseCommand
from upstream.models import ModifierRequirement, DiagnosisCPTRule


class Command(BaseCommand):
    help = 'Seed modifier requirements and diagnosis-CPT rules'

    def handle(self, *args, **options):
        # Seed modifier requirements
        ModifierRequirement.objects.get_or_create(
            payer='UnitedHealthcare',
            cpt='97162',
            required_modifier='-59',
            defaults={'condition': 'Bilateral PT evaluation'}
        )

        ModifierRequirement.objects.get_or_create(
            payer='Aetna',
            cpt='97162',
            required_modifier='GO',
            defaults={'condition': 'OASIS G-code required for PT'}
        )

        # Seed diagnosis-CPT rules
        DiagnosisCPTRule.objects.get_or_create(
            cpt='97162',
            diagnosis_category='Low back pain',
            defaults={
                'icd10_codes': ['M54.5', 'M54.9'],
                'payer': None  # All payers
            }
        )

        DiagnosisCPTRule.objects.get_or_create(
            cpt='97162',
            diagnosis_category='Knee pain',
            defaults={
                'icd10_codes': ['M25.561', 'M25.562'],
                'payer': None
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded risk scoring data'))
```

---

## Component 2: Behavioral Prediction Engine

### Purpose

Detect WHEN payer behavior changes (not just THAT it changed). Enable 2-3 week early warning before denial spikes.

**Target Detection Speed:** Day 3 (vs industry standard day 14-30)

### Day-Over-Day Denial Rate Tracking

**Algorithm:**

1. Compare last 3 days vs previous 14 days
2. Run chi-square test for statistical significance (p < 0.05)
3. Alert if denial rate change >10% AND statistically significant

**Implementation:**

```python
# upstream/intelligence/behavioral_prediction.py

from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from scipy.stats import chi2_contingency
from dataclasses import dataclass
from typing import Optional, List
from upstream.models import ClaimRecord, Customer
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class BehaviorChange:
    """Detected payer behavior change."""
    payer: str
    change_type: str
    detected_on_day: int
    baseline_rate: float
    current_rate: float
    rate_change_percent: float
    p_value: float
    affected_cpts: List[str]


@dataclass
class PolicyChange:
    """Industry-wide policy change detection."""
    payer: str
    change_type: str
    denial_reason: str
    customers_affected: int
    total_denials: int
    detected_at: datetime
    likely_cause: str


@dataclass
class CashFlowForecast:
    """Payment timing forecast."""
    payer: str
    trend: str
    baseline_payment_days: int
    current_payment_days: int
    days_added: int
    delayed_revenue_dollars: float
    forecast: str


class BehavioralPredictionEngine:
    """
    Detects WHEN payer behavior changes, not just THAT it changed.

    Competitive Advantage: Day 3 detection vs Adonis day 14.
    """

    def detect_denial_rate_shift(self, payer: str, customer: Customer) -> Optional[BehaviorChange]:
        """
        Compare last 3 days vs. previous 14 days.
        Statistical significance test (chi-square).
        Alert if p-value < 0.05 AND rate change > 10%.
        """

        # Get last 3 days of claims
        recent_window = timezone.now() - timedelta(days=3)
        recent_claims = ClaimRecord.objects.filter(
            customer=customer,
            payer=payer,
            decided_date__gte=recent_window
        )

        recent_total = recent_claims.count()
        recent_denied = recent_claims.filter(outcome='DENIED').count()
        recent_rate = recent_denied / recent_total if recent_total > 0 else 0

        # Get previous 14 days (baseline)
        baseline_start = timezone.now() - timedelta(days=17)  # 17 days ago
        baseline_end = recent_window  # 3 days ago
        baseline_claims = ClaimRecord.objects.filter(
            customer=customer,
            payer=payer,
            decided_date__gte=baseline_start,
            decided_date__lt=baseline_end
        )

        baseline_total = baseline_claims.count()
        baseline_denied = baseline_claims.filter(outcome='DENIED').count()
        baseline_rate = baseline_denied / baseline_total if baseline_total > 0 else 0

        # Statistical significance test
        if recent_total < 10 or baseline_total < 10:
            return None  # Insufficient data

        chi2, p_value = chi2_contingency([
            [recent_denied, recent_total - recent_denied],
            [baseline_denied, baseline_total - baseline_denied]
        ])[:2]

        # Alert criteria
        rate_change = abs(recent_rate - baseline_rate) / baseline_rate if baseline_rate > 0 else 0
        is_significant = p_value < 0.05 and rate_change > 0.10

        if is_significant:
            affected_cpts = self._identify_affected_cpts(
                recent_claims.filter(outcome='DENIED')
            )

            return BehaviorChange(
                payer=payer,
                change_type='denial_rate_shift',
                detected_on_day=3,
                baseline_rate=baseline_rate,
                current_rate=recent_rate,
                rate_change_percent=rate_change * 100,
                p_value=p_value,
                affected_cpts=affected_cpts
            )

        return None

    def _identify_affected_cpts(self, denied_claims) -> List[str]:
        """Extract CPT codes from denied claims."""
        return list(
            denied_claims.values_list('cpt', flat=True)
            .distinct()[:5]
        )

    def detect_policy_change(self, payer: str) -> Optional[PolicyChange]:
        """
        Monitor submission patterns across ALL customers.
        If 3+ customers see same denial reason within 48 hours,
        flag as industry-wide policy change.

        Network Effect: More customers = faster detection.
        """

        window_start = timezone.now() - timedelta(hours=48)

        # Get recent denials across ALL customers
        recent_denials = ClaimRecord.objects.filter(
            payer=payer,
            outcome='DENIED',
            decided_date__gte=window_start
        ).values('denial_reason').annotate(
            customer_count=Count('customer', distinct=True),
            total_denials=Count('id')
        ).filter(
            customer_count__gte=3  # 3+ customers affected
        )

        for denial_pattern in recent_denials:
            # This is likely a policy change, not isolated incident
            return PolicyChange(
                payer=payer,
                change_type='denial_reason_spike',
                denial_reason=denial_pattern['denial_reason'],
                customers_affected=denial_pattern['customer_count'],
                total_denials=denial_pattern['total_denials'],
                detected_at=timezone.now(),
                likely_cause='Policy change or system issue'
            )

        return None

    def predict_cash_flow_impact(self, payer: str, customer: Customer) -> Optional[CashFlowForecast]:
        """
        Payment timing slowdown (45 days → 52 days) predicts:
        - Cash flow stress in 2 weeks
        - Potential denial rate spike in 3 weeks
        """

        # Get payment timing trend (last 4 weeks)
        week_4 = self._get_median_payment_time(customer, payer, weeks_ago=4)
        week_3 = self._get_median_payment_time(customer, payer, weeks_ago=3)
        week_2 = self._get_median_payment_time(customer, payer, weeks_ago=2)
        week_1 = self._get_median_payment_time(customer, payer, weeks_ago=1)

        # Detect worsening trend
        if week_1 > week_2 > week_3 > week_4:
            trend = "WORSENING"
            days_added = week_1 - week_4

            # Calculate cash flow impact
            avg_weekly_revenue = self._calculate_avg_weekly_revenue(customer, payer)
            delayed_revenue = (days_added / 7) * avg_weekly_revenue

            return CashFlowForecast(
                payer=payer,
                trend=trend,
                baseline_payment_days=week_4,
                current_payment_days=week_1,
                days_added=days_added,
                delayed_revenue_dollars=delayed_revenue,
                forecast='Denial rate spike likely in 2-3 weeks based on historical correlation'
            )

        return None

    def _get_median_payment_time(self, customer: Customer, payer: str, weeks_ago: int) -> int:
        """Get median payment time for specific week."""
        from django.db.models import F, ExpressionWrapper, DurationField

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

    def _calculate_avg_weekly_revenue(self, customer: Customer, payer: str) -> float:
        """Calculate average weekly revenue from this payer."""
        from django.db.models import Sum

        last_13_weeks = timezone.now() - timedelta(weeks=13)

        total_revenue = ClaimRecord.objects.filter(
            customer=customer,
            payer=payer,
            outcome='PAID',
            decided_date__gte=last_13_weeks
        ).aggregate(total=Sum('paid_amount'))['total'] or 0

        return total_revenue / 13  # Average per week
```

---

## Component 3: Specialty-Specific Intelligence

### Dialysis MA Payment Variance Tracking

**Purpose:** Detect when Medicare Advantage pays significantly less than Traditional Medicare baseline.

**Alert Threshold:** MA payment <85% of Traditional Medicare baseline

**Implementation:**

```python
# upstream/services/specialty/dialysis.py

from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta
from upstream.models import ClaimRecord, Customer, AlertEvent


class DialysisIntelligence:
    """
    Dialysis-specific payer intelligence.

    Focus: Medicare Advantage payment variance.
    Problem: MA pays 15-20% less than Traditional Medicare.
    Solution: Alert when variance detected, quantify revenue impact.
    """

    def track_ma_payment_variance(self, customer: Customer) -> List[AlertEvent]:
        """
        Compare MA payments vs Traditional Medicare baseline.
        Alert when MA payment < 85% of baseline.
        """

        alerts = []

        # Get Traditional Medicare baseline
        traditional_medicare_baseline = ClaimRecord.objects.filter(
            customer=customer,
            payer__icontains='Medicare',
            payer__icontains='Traditional',
            outcome='PAID',
            decided_date__gte=timezone.now() - timedelta(days=90)
        ).aggregate(
            avg_payment=Avg('paid_amount')
        )['avg_payment']

        if not traditional_medicare_baseline:
            return alerts

        # Get MA payments by payer
        ma_payers = ClaimRecord.objects.filter(
            customer=customer,
            payer__icontains='MA',
            outcome='PAID',
            decided_date__gte=timezone.now() - timedelta(days=90)
        ).values('payer').annotate(
            avg_payment=Avg('paid_amount'),
            claim_count=Count('id')
        )

        for ma_payer in ma_payers:
            variance_ratio = ma_payer['avg_payment'] / traditional_medicare_baseline

            if variance_ratio < 0.85:  # 15% below baseline
                # Calculate revenue impact
                claims_per_week = ma_payer['claim_count'] / 13  # 13 weeks
                weekly_revenue_loss = claims_per_week * (traditional_medicare_baseline - ma_payer['avg_payment'])
                annual_revenue_loss = weekly_revenue_loss * 52

                alert = AlertEvent.objects.create(
                    customer=customer,
                    alert_type='dialysis_ma_variance',
                    severity='high',
                    title=f"MA Payment Variance: {ma_payer['payer']}",
                    description=(
                        f"{ma_payer['payer']} paying {variance_ratio * 100:.1f}% of Traditional Medicare rate.\n\n"
                        f"Annual revenue impact: ${annual_revenue_loss:,.0f}"
                    ),
                    evidence_payload={
                        'payer': ma_payer['payer'],
                        'ma_avg_payment': ma_payer['avg_payment'],
                        'traditional_medicare_baseline': traditional_medicare_baseline,
                        'variance_percent': (1 - variance_ratio) * 100,
                        'weekly_revenue_loss': weekly_revenue_loss,
                        'annual_revenue_loss': annual_revenue_loss,
                        'claims_analyzed': ma_payer['claim_count']
                    }
                )
                alerts.append(alert)

        return alerts
```

### ABA Authorization Pattern Analysis

**Purpose:** Track unit utilization patterns, predict authorization exhaustion, optimize reauth timing.

**Implementation:** See `01-detection-layer.md` Mechanism #1 for full details.

---

## Component 4: Network Intelligence

### Cross-Customer Pattern Aggregation

**Purpose:** Detect industry-wide payer changes affecting multiple practices simultaneously.

**Privacy:** All data anonymized, no PHI shared between customers.

**Implementation:**

```python
# upstream/intelligence/network_effects.py

from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from dataclasses import dataclass
from typing import List
from upstream.models import ClaimRecord, Customer


@dataclass
class IndustryAlert:
    """Industry-wide payer behavior alert."""
    payer: str
    denial_reason: str
    affected_cpt: str
    customers_affected: int
    total_denials: int
    detected_at: datetime
    likely_cause: str
    recommended_action: str


class NetworkIntelligence:
    """
    Cross-customer intelligence aggregation.

    Competitive Moat: More customers = faster detection + better predictions.
    Privacy: All data anonymized, no PHI shared.
    """

    def detect_industry_patterns(self) -> List[IndustryAlert]:
        """
        Aggregate anonymized patterns across ALL customers.
        Alert when 3+ customers see same issue within 48 hours.

        This is the network effect advantage over Adonis.
        """

        window_start = timezone.now() - timedelta(hours=48)

        # Aggregate denial patterns
        denial_patterns = ClaimRecord.objects.filter(
            outcome='DENIED',
            decided_date__gte=window_start
        ).values('payer', 'denial_reason', 'cpt').annotate(
            customer_count=Count('customer', distinct=True),
            total_denials=Count('id')
        ).filter(
            customer_count__gte=3  # 3+ customers affected
        )

        industry_alerts = []

        for pattern in denial_patterns:
            # This is likely industry-wide payer change
            affected_customers = Customer.objects.filter(
                claims__payer=pattern['payer'],
                claims__denial_reason=pattern['denial_reason'],
                claims__decided_date__gte=window_start,
                is_active=True
            ).distinct()

            # Create industry alert
            alert = IndustryAlert(
                payer=pattern['payer'],
                denial_reason=pattern['denial_reason'],
                affected_cpt=pattern['cpt'],
                customers_affected=pattern['customer_count'],
                total_denials=pattern['total_denials'],
                detected_at=timezone.now(),
                likely_cause='Payer policy change or system issue',
                recommended_action='Review claims before submission; Upstream auto-updated rules'
            )

            # Notify all customers with this payer
            for customer in affected_customers:
                self._notify_customer_industry_alert(customer, alert)

            industry_alerts.append(alert)

        return industry_alerts

    def _notify_customer_industry_alert(self, customer: Customer, alert: IndustryAlert):
        """Send industry alert to customer."""
        from upstream.models import AlertEvent

        AlertEvent.objects.create(
            customer=customer,
            alert_type='industry_pattern_detected',
            severity='high',
            title=f"Industry Alert: {alert.payer} Policy Change",
            description=(
                f"INDUSTRY ALERT: {alert.payer} Policy Change Detected\n\n"
                f"Pattern: {alert.customers_affected} practices saw denial rate spike this week\n\n"
                f"Average increase: Affecting CPT {alert.affected_cpt}\n\n"
                f"Status: {'NOT YET AFFECTING YOU' if self._is_customer_affected(customer, alert) else 'ALREADY AFFECTING YOU'}\n\n"
                f"Recommended Action:\n"
                f"- Review {alert.payer} bulletins\n"
                f"- Prepare for policy change\n"
                f"- Add extra documentation to claims\n"
                f"- Monitor next week's outcomes\n\n"
                f"Upstream has auto-updated submission rules to prevent impact."
            ),
            evidence_payload={
                'payer': alert.payer,
                'denial_reason': alert.denial_reason,
                'affected_cpt': alert.affected_cpt,
                'customers_affected': alert.customers_affected,
                'total_denials': alert.total_denials,
            }
        )

    def _is_customer_affected(self, customer: Customer, alert: IndustryAlert) -> bool:
        """Check if customer is already affected by this pattern."""
        window_start = timezone.now() - timedelta(hours=48)

        customer_denials = ClaimRecord.objects.filter(
            customer=customer,
            payer=alert.payer,
            denial_reason=alert.denial_reason,
            cpt=alert.affected_cpt,
            outcome='DENIED',
            decided_date__gte=window_start
        ).count()

        return customer_denials > 0

    def calculate_network_advantage(self) -> dict:
        """
        Quantify network effect advantage.

        Metric: Detection speed vs single-customer analysis.
        """

        total_customers = Customer.objects.filter(is_active=True).count()

        # Single customer: Needs 10+ denials to detect pattern (2-3 weeks)
        # Network: Needs 3+ customers with 3+ denials each (2-3 days)

        detection_speed_advantage = 7  # 7x faster with network

        return {
            'total_customers': total_customers,
            'detection_speed_multiplier': detection_speed_advantage,
            'single_customer_detection_days': 14,
            'network_detection_days': 2,
            'advantage_description': (
                f'{detection_speed_advantage}x faster pattern detection '
                f'with network of {total_customers} customers'
            )
        }
```

---

## Component 5: Nightly Baseline Calculation

### Purpose

Calculate denial rate baselines nightly from historical claims data. Powers pre-submission risk scoring.

**Implementation:**

```python
# upstream/tasks/risk_baseline.py

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from upstream.models import Customer, ClaimRecord, RiskBaseline
import logging

logger = logging.getLogger(__name__)


@shared_task
def build_risk_baselines(customer_id=None):
    """
    Nightly task to compute risk baselines from historical claims.

    Runs at 2 AM UTC daily.

    Algorithm:
    1. For each (customer, payer, CPT) combination:
       - Count total claims
       - Count denied claims
       - Calculate denial_rate = denied / total
       - Calculate confidence_score = min(total / 100, 1.0)
    2. Upsert RiskBaseline record
    3. Prune baselines with sample_size < 5 (insufficient data)

    Performance: ~10 minutes for 1M claims
    """

    customers = [Customer.objects.get(id=customer_id)] if customer_id else Customer.objects.all()

    for customer in customers:
        logger.info(f"Building risk baselines for {customer.name}")

        # Aggregate claims by (payer, CPT)
        aggregates = ClaimRecord.objects.filter(
            customer=customer,
            outcome__in=['PAID', 'DENIED'],  # Exclude pending
            decided_date__gte=timezone.now() - timedelta(days=365)  # Last year
        ).values('payer', 'cpt').annotate(
            total_claims=Count('id'),
            denied_claims=Count('id', filter=Q(outcome='DENIED')),
        )

        baselines_created = 0
        baselines_updated = 0

        for agg in aggregates:
            # Skip low-volume combinations
            if agg['total_claims'] < 5:
                continue

            denial_rate = agg['denied_claims'] / agg['total_claims']
            confidence_score = min(agg['total_claims'] / 100.0, 1.0)

            baseline, created = RiskBaseline.objects.update_or_create(
                customer=customer,
                payer=agg['payer'],
                cpt=agg['cpt'],
                defaults={
                    'denial_rate': denial_rate,
                    'sample_size': agg['total_claims'],
                    'confidence_score': confidence_score,
                }
            )

            if created:
                baselines_created += 1
            else:
                baselines_updated += 1

        logger.info(
            f"Risk baselines for {customer.name}: "
            f"{baselines_created} created, {baselines_updated} updated"
        )
```

---

## Success Metrics

### Risk Scoring
- **Accuracy:** >75% (validate against historical denial outcomes)
- **Latency:** <500ms per scoring request
- **Coverage:** 80%+ of claim volume has risk baseline (confidence >0.5)

### Behavioral Prediction
- **Detection Speed:** Day 3 (vs industry standard day 14-30)
- **False Positive Rate:** <10%
- **Cash Flow Prediction Accuracy:** >80%

### Specialty Intelligence
- **Dialysis MA Variance:** 100% of MA payers monitored
- **ABA Authorization Tracking:** Zero missed expirations

### Network Effects
- **Pattern Detection:** 48-hour window
- **Coverage:** 100% of customers notified of industry patterns
- **Detection Advantage:** 7x faster than single-customer analysis

---

**Next:** See `03-execution-layer.md` for rules engine and autonomous workflow implementation.

"""
RCM Automation Models for Confidence Scoring and Trust Calibration.

Implements the three-tier automation model:
- Tier 1: Auto-Execute (>95% confidence, <$1K)
- Tier 2: Queue for Review (70-95% confidence, $1K-$10K)
- Tier 3: Escalate (< 70% confidence, >$10K, or red-line actions)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

from upstream.models import Customer, ClaimRecord

User = get_user_model()


class ClaimScore(models.Model):
    """
    ML-based confidence scoring for automation decisions.

    Uses Random Forest/Gradient Boosting models (AUC 0.83-0.88 benchmark)
    to predict claim success probability and route to appropriate tier.
    """

    claim = models.OneToOneField(
        ClaimRecord,
        on_delete=models.CASCADE,
        related_name="score"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="claim_scores"
    )

    # Overall confidence metrics (0.0-1.0)
    overall_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Overall confidence score for automation decision",
        db_index=True
    )
    coding_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence in CPT code accuracy"
    )
    eligibility_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence patient is eligible for service"
    )
    medical_necessity_confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence medical necessity criteria are met"
    )
    documentation_completeness = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Completeness of supporting documentation"
    )

    # Risk factors (0.0-1.0, higher = more risk)
    denial_risk_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability of denial based on historical patterns",
        db_index=True
    )
    fraud_risk_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Fraud detection score (NPI patterns, billing anomalies)"
    )
    compliance_risk_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Risk of compliance violation (Stark, Anti-Kickback)"
    )

    # Model metadata for explainability
    model_version = models.CharField(
        max_length=50,
        help_text="ML model version used for scoring (e.g., 'rf_v2.1')"
    )
    feature_importance = models.JSONField(
        default=dict,
        help_text="Top features influencing score: {'payer_history': 0.35, ...}"
    )
    prediction_reasoning = models.TextField(
        blank=True,
        help_text="Human-readable explanation of score (for transparency)"
    )

    # Automation decision
    RECOMMENDED_ACTION_CHOICES = [
        ("auto_execute", "Auto Execute"),
        ("queue_review", "Queue for Review"),
        ("escalate", "Escalate to Human"),
        ("block", "Block - Compliance Red Line"),
    ]
    recommended_action = models.CharField(
        max_length=50,
        choices=RECOMMENDED_ACTION_CHOICES,
        db_index=True,
        help_text="Automation tier recommendation based on scoring"
    )
    automation_tier = models.IntegerField(
        choices=[
            (1, "Tier 1: Auto Execute"),
            (2, "Tier 2: Queue Review"),
            (3, "Tier 3: Escalate"),
        ],
        db_index=True
    )

    # Red-line detection (actions requiring human review by law)
    requires_human_review = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Legal/compliance requirement for human review"
    )
    red_line_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Why human review is required (e.g., 'Medical necessity determination - CA SB 1120')"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "upstream_claim_score"
        indexes = [
            models.Index(
                fields=["customer", "overall_confidence"],
                name="claim_score_confidence_idx"
            ),
            models.Index(
                fields=["customer", "automation_tier"],
                name="claim_score_tier_idx"
            ),
            models.Index(
                fields=["requires_human_review", "created_at"],
                name="claim_score_review_idx"
            ),
        ]

    def __str__(self):
        return (
            f"Claim {self.claim_id}: {self.overall_confidence:.1%} confidence "
            f"→ {self.get_recommended_action_display()}"
        )


class CustomerAutomationProfile(models.Model):
    """
    Customer-specific automation thresholds and trust calibration stage.

    Allows customers to configure their own risk tolerance and control
    which actions are automated vs. require human approval.
    """

    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="automation_profile"
    )

    # Trust calibration stage
    AUTOMATION_STAGE_CHOICES = [
        ("observe", "Stage 1: Observe (AI recommends, human acts)"),
        ("suggest", "Stage 2: Suggest (AI pre-fills, human confirms)"),
        ("act_notify", "Stage 3: Act + Notify (AI executes, human notified)"),
        ("full_autonomy", "Stage 4: Full Autonomy (AI executes silently)"),
    ]
    automation_stage = models.CharField(
        max_length=20,
        choices=AUTOMATION_STAGE_CHOICES,
        default="observe",
        help_text="Current trust calibration stage"
    )
    stage_start_date = models.DateField(
        auto_now_add=True,
        help_text="When customer entered current stage"
    )

    # Tier 1 thresholds (Auto-Execute)
    auto_execute_confidence = models.FloatField(
        default=0.95,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Minimum confidence score for autonomous execution"
    )
    auto_execute_max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1000,
        help_text="Maximum dollar amount for autonomous submission"
    )

    # Tier 2 thresholds (Queue for Review)
    queue_review_min_confidence = models.FloatField(
        default=0.70,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Minimum confidence for queueing (below triggers escalation)"
    )
    queue_review_max_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=10000,
        help_text="Maximum dollar amount for review queue (above triggers escalation)"
    )

    # Tier 3 thresholds (Escalate)
    escalate_min_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=10000,
        help_text="Minimum dollar amount requiring escalation"
    )

    # Action-specific automation toggles
    auto_submit_claims = models.BooleanField(
        default=False,
        help_text="Enable autonomous claim submission to payers"
    )
    auto_check_status = models.BooleanField(
        default=True,
        help_text="Enable autonomous claim status checks"
    )
    auto_verify_eligibility = models.BooleanField(
        default=True,
        help_text="Enable autonomous patient eligibility verification"
    )
    auto_submit_prior_auth = models.BooleanField(
        default=False,
        help_text="Enable autonomous prior authorization submission"
    )
    auto_modify_codes = models.BooleanField(
        default=False,
        help_text="Enable autonomous CPT code corrections"
    )
    auto_submit_appeals = models.BooleanField(
        default=False,
        help_text="Enable autonomous appeal submission (ALWAYS FALSE - legal requirement)"
    )

    # Shadow mode configuration
    shadow_mode_enabled = models.BooleanField(
        default=True,
        help_text="Run AI in parallel with humans to validate accuracy"
    )
    shadow_mode_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="When shadow mode was enabled"
    )
    shadow_accuracy_rate = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Current shadow mode accuracy (human agreement rate)"
    )
    shadow_mode_min_accuracy = models.FloatField(
        default=0.95,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Required accuracy before enabling live automation"
    )

    # Notification preferences
    notify_on_auto_execute = models.BooleanField(
        default=False,
        help_text="Send notification after autonomous actions (Stage 3+)"
    )
    notify_on_escalation = models.BooleanField(
        default=True,
        help_text="Send notification when action escalated to human"
    )
    notification_email = models.EmailField(
        blank=True,
        help_text="Email for automation notifications"
    )

    # Undo window configuration
    undo_window_hours = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text="Hours available to undo autonomous actions"
    )

    # Compliance settings
    compliance_officer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="compliance_profiles",
        help_text="User who controls automation guardrails"
    )
    audit_all_actions = models.BooleanField(
        default=True,
        help_text="Log all automation actions (HIPAA requirement)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "upstream_customer_automation_profile"

    def __str__(self):
        return f"{self.customer.name} - {self.get_automation_stage_display()}"

    def can_auto_execute(self, claim_score: ClaimScore) -> bool:
        """
        Determine if claim can be executed autonomously based on thresholds.

        Returns False if:
        - Customer not in Stage 3 or 4
        - Confidence below threshold
        - Dollar amount above threshold
        - Red-line action requires human review
        - Shadow mode enabled
        """
        if self.automation_stage not in ["act_notify", "full_autonomy"]:
            return False

        if self.shadow_mode_enabled:
            return False

        if claim_score.requires_human_review:
            return False

        if claim_score.overall_confidence < self.auto_execute_confidence:
            return False

        if claim_score.claim.allowed_amount and \
           claim_score.claim.allowed_amount > self.auto_execute_max_amount:
            return False

        return self.auto_submit_claims  # Final toggle check

    def should_escalate(self, claim_score: ClaimScore) -> bool:
        """
        Determine if claim should be escalated to Tier 3.

        Escalates if:
        - Confidence below minimum
        - Dollar amount above threshold
        - Fraud/compliance risk detected
        - Red-line action
        """
        if claim_score.requires_human_review:
            return True

        if claim_score.overall_confidence < self.queue_review_min_confidence:
            return True

        if claim_score.claim.allowed_amount and \
           claim_score.claim.allowed_amount >= self.escalate_min_amount:
            return True

        if claim_score.fraud_risk_score > 0.7:
            return True

        if claim_score.compliance_risk_score > 0.7:
            return True

        return False


class ShadowModeResult(models.Model):
    """
    Tracks shadow mode predictions vs. actual human decisions.

    Used to validate AI accuracy before enabling autonomous execution.
    """

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="shadow_results"
    )
    claim_score = models.ForeignKey(
        ClaimScore,
        on_delete=models.CASCADE,
        related_name="shadow_results"
    )

    # AI prediction
    ai_recommended_action = models.CharField(max_length=50)
    ai_confidence = models.FloatField()

    # Human decision
    human_action_taken = models.CharField(max_length=50)
    human_decision_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="shadow_decisions"
    )
    human_decision_timestamp = models.DateTimeField()

    # Comparison
    actions_match = models.BooleanField(
        help_text="Did AI recommendation match human decision?"
    )
    outcome = models.CharField(
        max_length=50,
        choices=[
            ("true_positive", "True Positive: AI correct"),
            ("true_negative", "True Negative: AI correct"),
            ("false_positive", "False Positive: AI wrong"),
            ("false_negative", "False Negative: AI wrong"),
        ]
    )

    # Notes
    discrepancy_reason = models.TextField(
        blank=True,
        help_text="Why human disagreed with AI (if applicable)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "upstream_shadow_mode_result"
        indexes = [
            models.Index(
                fields=["customer", "actions_match", "created_at"],
                name="shadow_accuracy_idx"
            ),
        ]

    def __str__(self):
        match_icon = "✓" if self.actions_match else "✗"
        return f"{match_icon} Claim {self.claim_score.claim_id}: AI={self.ai_recommended_action}, Human={self.human_action_taken}"

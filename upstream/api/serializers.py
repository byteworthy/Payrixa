"""
Upstream API Serializers

DRF serializers for all Upstream models with proper field exposure
and security considerations for PHI data.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from ..models import (
    Customer,
    Settings,
    Upload,
    ClaimRecord,
    ReportRun,
    DriftEvent,
    UserProfile,
    PayerMapping,
    CPTGroupMapping,
)
from upstream.alerts.models import AlertEvent, OperatorJudgment


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model.

    Represents healthcare organization accounts in the platform.

    **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Memorial Hospital System"
    }
    ```
    """

    class Meta:
        model = Customer
        fields = ["id", "name"]
        read_only_fields = ["id"]


class SettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for Settings model.

    Customer-specific configuration for report delivery and notification preferences.

    **Request Example (Update):**
    ```json
    {
        "to_email": "billing@hospital.com",
        "cc_email": "manager@hospital.com",
        "attach_pdf": true
    }
    ```

    **Success Response (200 OK):**
    ```json
    {
        "id": 5,
        "customer": 1,
        "to_email": "billing@hospital.com",
        "cc_email": "manager@hospital.com",
        "attach_pdf": true
    }
    ```
    """

    class Meta:
        model = Settings
        fields = ["id", "customer", "to_email", "cc_email", "attach_pdf"]
        read_only_fields = ["id", "customer"]


class UploadSerializer(serializers.ModelSerializer):
    """
    Serializer for Upload model.

    Represents claim data file uploads with processing status, validation results,
    and temporal coverage metadata.

    **Request Example (Create Upload):**
    ```json
    {
        "filename": "claims_q1_2025.csv",
        "date_min": "2025-01-01",
        "date_max": "2025-03-31"
    }
    ```

    **Success Response (201 Created):**
    ```json
    {
        "id": 567,
        "customer": 1,
        "uploaded_at": "2025-01-26T10:45:00Z",
        "filename": "claims_q1_2025.csv",
        "status": "completed",
        "error_message": null,
        "row_count": 8543,
        "date_min": "2025-01-01",
        "date_max": "2025-03-31"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "filename": ["This field is required."],
        "date_max": ["Date cannot be in the future."]
    }
    ```

    **Status Values:**
    - `pending`: Upload queued for processing
    - `processing`: Currently validating and importing claims
    - `completed`: Successfully processed all records
    - `failed`: Processing failed (see error_message)
    """

    class Meta:
        model = Upload
        fields = [
            "id",
            "customer",
            "uploaded_at",
            "filename",
            "status",
            "error_message",
            "row_count",
            "date_min",
            "date_max",
        ]
        read_only_fields = [
            "id",
            "customer",
            "uploaded_at",
            "status",
            "error_message",
            "row_count",
        ]


class UploadSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for Upload listings."""

    class Meta:
        model = Upload
        fields = ["id", "filename", "uploaded_at", "status", "row_count"]


class ClaimRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for ClaimRecord model.

    Represents healthcare claim records with payer information, procedure codes,
    and payment outcomes.

    **Request Example (Create):**
    ```json
    {
        "payer": "Aetna Health Plans",
        "cpt": "99213",
        "cpt_group": "Office Visits",
        "submitted_date": "2025-01-15",
        "decided_date": "2025-02-01",
        "outcome": "paid",
        "allowed_amount": "125.50"
    }
    ```

    **Success Response (200 OK):**
    ```json
    {
        "id": 12345,
        "customer": 1,
        "upload": 567,
        "payer": "Aetna Health Plans",
        "cpt": "99213",
        "cpt_group": "Office Visits",
        "submitted_date": "2025-01-15",
        "decided_date": "2025-02-01",
        "outcome": "paid",
        "allowed_amount": "125.50"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "payer": ["This field is required."],
        "outcome": [
            "'invalid' is not a valid choice. Choose: paid, denied, pending"
        ]
    }
    ```
    """

    class Meta:
        model = ClaimRecord
        fields = [
            "id",
            "customer",
            "upload",
            "payer",
            "cpt",
            "cpt_group",
            "submitted_date",
            "decided_date",
            "outcome",
            "allowed_amount",
        ]
        read_only_fields = ["id", "customer", "upload"]


class ClaimRecordSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for ClaimRecord listings."""

    class Meta:
        model = ClaimRecord
        fields = ["id", "payer", "cpt", "outcome", "decided_date"]


class DriftEventSerializer(serializers.ModelSerializer):
    """
    Serializer for DriftEvent model with computed fields.

    Represents detected anomalies in claim patterns with baseline comparison,
    severity scoring, and confidence metrics.

    **Success Response (200 OK):**
    ```json
    {
        "id": 789,
        "customer": 1,
        "report_run": 456,
        "payer": "Blue Cross Blue Shield",
        "cpt_group": "Cardiology",
        "drift_type": "denial_rate",
        "baseline_value": 15.5,
        "current_value": 32.8,
        "delta_value": 17.3,
        "delta_percent": 111.61,
        "severity": 0.85,
        "severity_label": "CRITICAL",
        "confidence": 0.92,
        "baseline_start": "2024-10-01",
        "baseline_end": "2024-12-31",
        "current_start": "2025-01-01",
        "current_end": "2025-01-25",
        "created_at": "2025-01-26T10:30:00Z"
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Not found."
    }
    ```

    **Computed Fields:**
    - `delta_percent`: Percentage change from baseline (calculated)
    - `severity_label`: Human-readable severity (CRITICAL/HIGH/MEDIUM/LOW)
    """

    delta_percent = serializers.SerializerMethodField()
    severity_label = serializers.SerializerMethodField()

    class Meta:
        model = DriftEvent
        fields = [
            "id",
            "customer",
            "report_run",
            "payer",
            "cpt_group",
            "drift_type",
            "baseline_value",
            "current_value",
            "delta_value",
            "delta_percent",
            "severity",
            "severity_label",
            "confidence",
            "baseline_start",
            "baseline_end",
            "current_start",
            "current_end",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_delta_percent(self, obj):
        """Calculate percentage change from baseline."""
        if obj.baseline_value and obj.baseline_value != 0:
            return round((obj.delta_value / obj.baseline_value) * 100, 2)
        return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_severity_label(self, obj):
        """Human-readable severity label."""
        if obj.severity >= 0.8:
            return "CRITICAL"
        elif obj.severity >= 0.6:
            return "HIGH"
        elif obj.severity >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"


class ReportRunSerializer(serializers.ModelSerializer):
    """
    Serializer for ReportRun model with nested drift events.

    Represents analytics report execution with embedded drift event results,
    summary statistics, and execution metadata.

    **Request Example (Trigger Report):**
    ```json
    {
        "run_type": "monthly_analysis"
    }
    ```

    **Success Response (200 OK):**
    ```json
    {
        "id": 456,
        "customer": 1,
        "run_type": "monthly_analysis",
        "started_at": "2025-01-26T09:00:00Z",
        "finished_at": "2025-01-26T09:15:32Z",
        "status": "completed",
        "summary_json": {
            "total_claims_analyzed": 15420,
            "drift_events_detected": 12,
            "high_severity_count": 3
        },
        "drift_events": [
            {
                "id": 789,
                "payer": "Aetna",
                "drift_type": "denial_rate",
                "severity": 0.85,
                "severity_label": "CRITICAL"
            }
        ],
        "drift_event_count": 12
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "run_type": ["'invalid_type' is not a valid choice."]
    }
    ```
    """

    drift_events = DriftEventSerializer(many=True, read_only=True)
    drift_event_count = serializers.SerializerMethodField()

    class Meta:
        model = ReportRun
        fields = [
            "id",
            "customer",
            "run_type",
            "started_at",
            "finished_at",
            "status",
            "summary_json",
            "drift_events",
            "drift_event_count",
        ]
        read_only_fields = ["id", "started_at", "finished_at", "status", "summary_json"]

    @extend_schema_field(OpenApiTypes.INT)
    def get_drift_event_count(self, obj):
        """Count of drift events in this report (PERF-20: uses annotated count)."""
        return getattr(obj, "drift_event_count", obj.drift_events.count())


class ReportRunSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for ReportRun listings."""

    drift_event_count = serializers.SerializerMethodField()

    class Meta:
        model = ReportRun
        fields = ["id", "run_type", "started_at", "status", "drift_event_count"]

    @extend_schema_field(OpenApiTypes.INT)
    def get_drift_event_count(self, obj):
        """PERF-20: Use annotated count to avoid N+1 queries."""
        return getattr(obj, "drift_event_count", obj.drift_events.count())


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.

    User account with customer association and RBAC role information.

    **Success Response (200 OK):**
    ```json
    {
        "id": 3,
        "username": "jane.analyst",
        "email": "jane@hospital.com",
        "customer": 1,
        "customer_name": "Memorial Hospital System"
    }
    ```
    """

    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = UserProfile
        fields = ["id", "username", "email", "customer", "customer_name"]
        read_only_fields = ["id", "username", "email"]


class PayerMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for PayerMapping model.

    Maps raw payer names from claim files to standardized normalized names,
    enabling consistent analytics across data sources.

    **Request Example (Create):**
    ```json
    {
        "raw_name": "BCBS of California",
        "normalized_name": "Blue Cross Blue Shield"
    }
    ```

    **Success Response (201 Created):**
    ```json
    {
        "id": 42,
        "customer": 1,
        "raw_name": "BCBS of California",
        "normalized_name": "Blue Cross Blue Shield"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "raw_name": ["This field is required."],
        "normalized_name": ["Ensure this field has no more than 255 characters."]
    }
    ```
    """

    class Meta:
        model = PayerMapping
        fields = ["id", "customer", "raw_name", "normalized_name"]
        read_only_fields = ["id", "customer"]


class CPTGroupMappingSerializer(serializers.ModelSerializer):
    """
    Serializer for CPTGroupMapping model.

    Maps CPT procedure codes to logical groupings for aggregated analytics.

    **Request Example (Create):**
    ```json
    {
        "cpt_code": "99213",
        "cpt_group": "Office Visits"
    }
    ```

    **Success Response (201 Created):**
    ```json
    {
        "id": 88,
        "customer": 1,
        "cpt_code": "99213",
        "cpt_group": "Office Visits"
    }
    ```
    """

    class Meta:
        model = CPTGroupMapping
        fields = ["id", "customer", "cpt_code", "cpt_group"]
        read_only_fields = ["id", "customer"]


# =============================================================================
# Analytics Serializers (for dashboard/reporting endpoints)
# =============================================================================


class PayerSummarySerializer(serializers.Serializer):
    """
    Aggregated payer statistics.

    Analytics summary showing claim outcomes and financial metrics by payer.

    **Success Response (200 OK):**
    ```json
    {
        "payer": "Blue Cross Blue Shield",
        "total_claims": 4523,
        "paid_count": 3890,
        "denied_count": 512,
        "other_count": 121,
        "denial_rate": 11.32,
        "avg_allowed_amount": "187.45"
    }
    ```
    """

    payer = serializers.CharField()
    total_claims = serializers.IntegerField()
    paid_count = serializers.IntegerField()
    denied_count = serializers.IntegerField()
    other_count = serializers.IntegerField()
    denial_rate = serializers.FloatField()
    avg_allowed_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, allow_null=True
    )


class DriftInsightSerializer(serializers.Serializer):
    """AI-generated insight for drift events."""

    event_id = serializers.IntegerField()
    payer = serializers.CharField()
    insight_text = serializers.CharField()
    recommendation = serializers.CharField()
    confidence_score = serializers.FloatField()


class DashboardSerializer(serializers.Serializer):
    """
    Dashboard overview data.

    High-level metrics and trends for executive summary view.

    **Success Response (200 OK):**
    ```json
    {
        "total_claims": 45820,
        "total_uploads": 12,
        "active_drift_events": 7,
        "last_report_date": "2025-01-26T09:15:32Z",
        "denial_rate_trend": [
            {"month": "2024-11", "rate": 10.5},
            {"month": "2024-12", "rate": 11.2},
            {"month": "2025-01", "rate": 12.8}
        ],
        "top_drift_payers": [
            {"payer": "Aetna", "severity": 0.85},
            {"payer": "UnitedHealthcare", "severity": 0.72}
        ]
    }
    ```
    """

    total_claims = serializers.IntegerField()
    total_uploads = serializers.IntegerField()
    active_drift_events = serializers.IntegerField()
    last_report_date = serializers.DateTimeField(allow_null=True)
    denial_rate_trend = serializers.ListField(child=serializers.DictField())
    top_drift_payers = serializers.ListField(child=serializers.DictField())


# =============================================================================
# Alert & Operator Judgment Serializers
# =============================================================================


class OperatorJudgmentSerializer(serializers.ModelSerializer):
    """
    Serializer for OperatorJudgment model.

    Captures operator feedback on alert events, including verdict classification,
    reason codes, and recovery tracking for financial impact assessment.

    **Request Example (Create Judgment):**
    ```json
    {
        "alert_event": 234,
        "verdict": "real",
        "reason_codes_json": ["coding_error", "payer_policy_change"],
        "recovered_amount": "2450.00",
        "recovered_date": "2025-02-15",
        "notes": "Identified systematic coding issue affecting Cardiology claims"
    }
    ```

    **Success Response (201 Created):**
    ```json
    {
        "id": 67,
        "customer": 1,
        "alert_event": 234,
        "verdict": "real",
        "reason_codes_json": ["coding_error", "payer_policy_change"],
        "recovered_amount": "2450.00",
        "recovered_date": "2025-02-15",
        "notes": "Identified systematic coding issue affecting Cardiology claims",
        "operator": 3,
        "operator_username": "jane.analyst",
        "created_at": "2025-01-26T14:20:00Z",
        "updated_at": "2025-01-26T14:20:00Z"
    }
    ```

    **Error Response (400 Bad Request):**
    ```json
    {
        "verdict": ["This field is required."],
        "alert_event": ["Invalid pk '999' - object does not exist."]
    }
    ```

    **Verdict Choices:**
    - `noise`: False positive, no action needed
    - `real`: Legitimate issue requiring follow-up
    - `needs_followup`: Uncertain, requires additional investigation
    """

    operator_username = serializers.CharField(
        source="operator.username", read_only=True
    )

    class Meta:
        model = OperatorJudgment
        fields = [
            "id",
            "customer",
            "alert_event",
            "verdict",
            "reason_codes_json",
            "recovered_amount",
            "recovered_date",
            "notes",
            "operator",
            "operator_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer",
            "operator",
            "operator_username",
            "created_at",
            "updated_at",
        ]


class AlertEventSerializer(serializers.ModelSerializer):
    """
    Serializer for AlertEvent model with operator judgments.

    Represents alert notifications triggered by drift events, including delivery
    status, operator feedback, and resolution tracking.

    **Success Response (200 OK):**
    ```json
    {
        "id": 234,
        "customer": 1,
        "alert_rule": 45,
        "drift_event": 789,
        "report_run": 456,
        "triggered_at": "2025-01-26T10:30:15Z",
        "status": "delivered",
        "payload": {
            "severity": "CRITICAL",
            "message": "Denial rate spike detected for Aetna"
        },
        "notification_sent_at": "2025-01-26T10:30:18Z",
        "error_message": null,
        "operator_judgments": [
            {
                "id": 67,
                "verdict": "real",
                "notes": "Confirmed pattern change",
                "operator_username": "jane.analyst"
            }
        ],
        "has_judgment": true,
        "latest_judgment_verdict": "real",
        "created_at": "2025-01-26T10:30:15Z",
        "updated_at": "2025-01-26T14:20:00Z"
    }
    ```

    **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Not found."
    }
    ```
    """

    operator_judgments = serializers.SerializerMethodField()
    has_judgment = serializers.SerializerMethodField()
    latest_judgment_verdict = serializers.SerializerMethodField()

    class Meta:
        model = AlertEvent
        fields = [
            "id",
            "customer",
            "alert_rule",
            "drift_event",
            "report_run",
            "triggered_at",
            "status",
            "payload",
            "notification_sent_at",
            "error_message",
            "operator_judgments",
            "has_judgment",
            "latest_judgment_verdict",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "triggered_at"]

    def get_operator_judgments(self, obj):
        """
        Get operator judgments (PERF-20: uses prefetched data).
        """
        # Use prefetched operator_judgments to avoid N+1 queries
        # Prefetch is defined in AlertEventViewSet.queryset
        judgments = obj.operator_judgments.all()
        return OperatorJudgmentSerializer(judgments, many=True).data

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_judgment(self, obj):
        """
        Check if alert has operator judgment (PERF-20: uses prefetched).
        """
        # Use prefetched operator_judgments to avoid N+1 queries
        return len(obj.operator_judgments.all()) > 0

    @extend_schema_field(OpenApiTypes.STR)
    def get_latest_judgment_verdict(self, obj):
        """
        Get latest judgment verdict (PERF-20: uses prefetched data).
        """
        # Use prefetched operator_judgments and sort in Python to avoid N+1 queries
        judgments = list(obj.operator_judgments.all())
        if not judgments:
            return None
        latest = max(judgments, key=lambda j: j.created_at)
        return latest.verdict


class OperatorFeedbackSerializer(serializers.Serializer):
    """
    Serializer for operator feedback submission.

    Structured input form for operator judgment creation on alert events.

    **Request Example:**
    ```json
    {
        "verdict": "real",
        "reason_codes": ["coding_error", "payer_policy_change"],
        "recovered_amount": "2450.00",
        "recovered_date": "2025-02-15",
        "notes": "Systematic coding issue identified"
    }
    ```

    **Validation Error (400 Bad Request):**
    ```json
    {
        "verdict": ["This field is required."],
        "recovered_amount": ["Ensure that there are no more than 12 digits in total."]
    }
    ```
    """

    verdict = serializers.ChoiceField(
        choices=[
            ("noise", "Noise"),
            ("real", "Real/Legitimate"),
            ("needs_followup", "Needs Follow-up"),
        ]
    )
    reason_codes = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    recovered_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    recovered_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check endpoint response."""

    status = serializers.CharField(help_text="Health status: 'healthy' or 'unhealthy'")
    version = serializers.CharField(help_text="Application version")
    timestamp = serializers.DateTimeField(help_text="Current server timestamp")

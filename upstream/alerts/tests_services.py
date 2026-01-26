"""
Comprehensive tests for alert services.

Tests cover:
- Alert evaluation for drift events and payment delay signals
- Notification sending (email, Slack)
- Alert suppression logic
- Historical context retrieval
"""

from django.test import TestCase
from django.utils import timezone
from django.core import mail
from unittest.mock import patch, MagicMock
from datetime import timedelta
from decimal import Decimal

from upstream.models import Customer, DriftEvent, ReportRun
from upstream.products.delayguard.models import PaymentDelaySignal
from upstream.alerts.models import (
    AlertRule,
    AlertEvent,
    OperatorJudgment,
    NotificationChannel,
)
from upstream.alerts.services import (
    evaluate_drift_event,
    evaluate_payment_delay_signal,
    send_alert_notification,
    send_email_notification,
    _is_suppressed,
    get_suppression_context,
)
from upstream.core.tenant import customer_context, set_current_customer, clear_current_customer


class EvaluateDriftEventTests(TestCase):
    """Tests for evaluate_drift_event function."""

    def setUp(self):
        """Create test fixtures and set customer context."""
        self.customer = Customer.objects.create(name="Test Healthcare Corp")

        # Set customer context for tenant-isolated queries
        set_current_customer(self.customer)

        self.report_run = ReportRun.objects.create(
            customer=self.customer,
            status="success",
        )

        today = timezone.now().date()
        self.drift_event = DriftEvent.objects.create(
            customer=self.customer,
            report_run=self.report_run,
            payer="Aetna",
            cpt_group="Office Visits",
            drift_type="DENIAL_RATE",
            baseline_value=Decimal("0.10"),
            current_value=Decimal("0.25"),
            delta_value=Decimal("0.15"),
            severity=Decimal("0.75"),
            confidence=Decimal("0.90"),
            baseline_start=today - timedelta(days=90),
            baseline_end=today - timedelta(days=15),
            current_start=today - timedelta(days=14),
            current_end=today,
        )

    def tearDown(self):
        """Clean up customer context."""
        clear_current_customer()

    def test_evaluate_drift_event_creates_alert(self):
        """Test that drift event evaluation creates alert when rule matches."""
        # Create a rule that should trigger
        rule = AlertRule.objects.create(
            customer=self.customer,
            name="High Denial Rate Alert",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,  # Trigger if severity >= 0.70
        )

        # Evaluate drift event
        alert_events = evaluate_drift_event(self.drift_event)

        # Should create alert event
        self.assertEqual(len(alert_events), 1)
        alert_event = alert_events[0]
        self.assertEqual(alert_event.customer, self.customer)
        self.assertEqual(alert_event.alert_rule, rule)
        self.assertEqual(alert_event.drift_event, self.drift_event)
        self.assertEqual(alert_event.status, "pending")

    def test_evaluate_drift_event_no_matching_rules(self):
        """Test that no alerts created when no rules match."""
        # Create rule with high threshold (won't trigger)
        AlertRule.objects.create(
            customer=self.customer,
            name="Very High Denial Rate Alert",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.95,  # Too high to trigger (drift event has 0.75)
        )

        # Evaluate drift event
        alert_events = evaluate_drift_event(self.drift_event)

        # Should create no alerts
        self.assertEqual(len(alert_events), 0)

    def test_evaluate_drift_event_disabled_rule_ignored(self):
        """Test that disabled rules are ignored."""
        AlertRule.objects.create(
            customer=self.customer,
            name="Disabled Alert",
            enabled=False,  # Disabled
            metric="severity",
            threshold_type="gte",
            threshold_value=0.50,  # Would trigger, but disabled
        )

        alert_events = evaluate_drift_event(self.drift_event)

        self.assertEqual(len(alert_events), 0)

    def test_evaluate_drift_event_prevents_duplicates(self):
        """Test that duplicate alert events are not created."""
        rule = AlertRule.objects.create(
            customer=self.customer,
            name="Test Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,
        )

        # First evaluation - should create alert
        alerts1 = evaluate_drift_event(self.drift_event)
        self.assertEqual(len(alerts1), 1)

        # Second evaluation - should return existing alert, not create new
        alerts2 = evaluate_drift_event(self.drift_event)
        self.assertEqual(len(alerts2), 1)
        self.assertEqual(alerts1[0].id, alerts2[0].id)

        # Verify only one alert event exists
        total_alerts = AlertEvent.objects.filter(
            drift_event=self.drift_event, alert_rule=rule
        ).count()
        self.assertEqual(total_alerts, 1)

    def test_evaluate_drift_event_creates_audit_trail(self):
        """Test that audit events are created for alert creation."""
        rule = AlertRule.objects.create(
            customer=self.customer,
            name="Audit Test Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,
        )

        # Evaluate and create alert
        with patch("upstream.core.services.create_audit_event") as mock_audit:
            evaluate_drift_event(self.drift_event)

            # Should have called create_audit_event
            mock_audit.assert_called_once()
            call_kwargs = mock_audit.call_args[1]
            self.assertEqual(call_kwargs["action"], "alert_event_created")
            self.assertEqual(call_kwargs["entity_type"], "AlertEvent")
            self.assertEqual(call_kwargs["customer"], self.customer)


class EvaluatePaymentDelaySignalTests(TestCase):
    """Tests for evaluate_payment_delay_signal function."""

    def setUp(self):
        """Create test fixtures and set customer context."""
        self.customer = Customer.objects.create(name="DelayGuard Test Corp")

        # Set customer context for tenant-isolated queries
        set_current_customer(self.customer)

        # Create alert rule (required by evaluate_payment_delay_signal)
        self.alert_rule = AlertRule.objects.create(
            customer=self.customer,
            name="DelayGuard Alert Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.50,
        )

        today = timezone.now().date()
        self.payment_signal = PaymentDelaySignal.objects.create(
            customer=self.customer,
            payer="UnitedHealthcare",
            signal_type="payment_delay_drift",
            window_start_date=today - timedelta(days=14),
            window_end_date=today,
            baseline_start_date=today - timedelta(days=104),
            baseline_end_date=today - timedelta(days=14),
            baseline_avg_days=30.0,
            current_avg_days=45.0,
            delta_days=15.0,
            delta_percent=50.0,
            baseline_claim_count=100,
            current_claim_count=80,
            severity="high",
            confidence=Decimal("0.85"),
            estimated_dollars_at_risk=Decimal("150000.00"),
        )

    def tearDown(self):
        """Clean up customer context."""
        clear_current_customer()

    def test_evaluate_payment_delay_creates_alert(self):
        """Test that payment delay signals create alerts."""
        alert_events = evaluate_payment_delay_signal(self.payment_signal)

        # Should create alert for high severity signal
        self.assertEqual(len(alert_events), 1)
        alert_event = alert_events[0]
        self.assertEqual(alert_event.customer, self.customer)
        self.assertEqual(alert_event.payment_delay_signal, self.payment_signal)
        self.assertEqual(alert_event.status, "pending")

    def test_evaluate_low_severity_low_confidence_suppressed(self):
        """Test that low severity + low confidence signals are suppressed."""
        today = timezone.now().date()
        low_signal = PaymentDelaySignal.objects.create(
            customer=self.customer,
            payer="LowSignalPayer",
            signal_type="payment_delay_drift",
            window_start_date=today - timedelta(days=14),
            window_end_date=today,
            baseline_start_date=today - timedelta(days=104),
            baseline_end_date=today - timedelta(days=14),
            baseline_avg_days=30.0,
            current_avg_days=32.0,
            delta_days=2.0,
            delta_percent=6.7,
            baseline_claim_count=100,
            current_claim_count=90,
            severity="low",
            confidence=Decimal("0.45"),  # Below threshold
            estimated_dollars_at_risk=Decimal("5000.00"),
        )

        alert_events = evaluate_payment_delay_signal(low_signal)

        # Should not create alert (suppressed)
        self.assertEqual(len(alert_events), 0)

    def test_evaluate_payment_delay_prevents_duplicates(self):
        """Test that duplicate alerts are not created for payment signals."""
        # First evaluation
        alerts1 = evaluate_payment_delay_signal(self.payment_signal)
        self.assertEqual(len(alerts1), 1)

        # Second evaluation
        alerts2 = evaluate_payment_delay_signal(self.payment_signal)
        self.assertEqual(len(alerts2), 1)
        self.assertEqual(alerts1[0].id, alerts2[0].id)


class AlertSuppressionTests(TestCase):
    """Tests for alert suppression logic."""

    def setUp(self):
        """Create test fixtures and set customer context."""
        self.customer = Customer.objects.create(name="Suppression Test Corp")

        # Set customer context for tenant-isolated queries
        set_current_customer(self.customer)

        self.alert_rule = AlertRule.objects.create(
            customer=self.customer,
            name="Test Suppression Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,
        )

    def tearDown(self):
        """Clean up customer context."""
        clear_current_customer()

    def test_suppression_cooldown_period(self):
        """Test that recent alerts trigger cooldown suppression."""
        # Create recent alert (2 hours ago)
        recent_time = timezone.now() - timedelta(hours=2)
        recent_alert = AlertEvent.objects.create(
            customer=self.customer,
            alert_rule=self.alert_rule,
            triggered_at=recent_time,
            status="sent",
            notification_sent_at=recent_time,
            payload={
                "product_name": "DriftWatch",
                "signal_type": "DENIAL_RATE",
                "entity_label": "Aetna",
                "payer": "Aetna",
            },
        )

        # New evidence for same payer/type
        evidence = {
            "product_name": "DriftWatch",
            "signal_type": "DENIAL_RATE",
            "entity_label": "Aetna",
            "payer": "Aetna",
            "severity": 0.75,
        }

        suppressed = _is_suppressed(self.customer, evidence)

        # Should be suppressed (within cooldown)
        self.assertTrue(suppressed)

    def test_suppression_noise_pattern(self):
        """Test that repeated 'noise' judgments trigger suppression."""
        # Create 3 historical alerts marked as noise
        for i in range(3):
            past_time = timezone.now() - timedelta(days=10 + i)
            alert = AlertEvent.objects.create(
                customer=self.customer,
                alert_rule=self.alert_rule,
                triggered_at=past_time,
                status="resolved",
                payload={
                    "product_name": "DriftWatch",
                    "signal_type": "DENIAL_RATE",
                    "entity_label": "NoisePayerCorp",
                    "payer": "NoisePayerCorp",
                },
            )
            OperatorJudgment.objects.create(
                customer=self.customer,
                alert_event=alert,
                verdict="noise",
                notes="False positive",
            )

        # New evidence for same payer
        evidence = {
            "product_name": "DriftWatch",
            "signal_type": "DENIAL_RATE",
            "entity_label": "NoisePayerCorp",
            "payer": "NoisePayerCorp",
            "severity": 0.70,
        }

        suppressed = _is_suppressed(self.customer, evidence)

        # Should be suppressed (noise pattern detected)
        self.assertTrue(suppressed)

    def test_no_suppression_different_payer(self):
        """Test that alerts for different payers are not suppressed."""
        # Create recent alert for Payer A
        notification_time = timezone.now() - timedelta(hours=1)
        recent_alert = AlertEvent.objects.create(
            customer=self.customer,
            alert_rule=self.alert_rule,
            triggered_at=notification_time,
            status="sent",
            notification_sent_at=notification_time,
            payload={
                "product_name": "DriftWatch",
                "signal_type": "DENIAL_RATE",
                "entity_label": "PayerA",
                "payer": "PayerA",
            },
        )

        # New evidence for Payer B
        evidence = {
            "product_name": "DriftWatch",
            "signal_type": "DENIAL_RATE",
            "entity_label": "PayerB",
            "payer": "PayerB",
            "severity": 0.75,
        }

        suppressed = _is_suppressed(self.customer, evidence)

        # Should NOT be suppressed (different payer)
        self.assertFalse(suppressed)


class SendEmailNotificationTests(TestCase):
    """Tests for email notification sending."""

    def setUp(self):
        """Create test fixtures and set customer context."""
        self.customer = Customer.objects.create(name="Email Test Corp")

        # Set customer context for tenant-isolated queries
        set_current_customer(self.customer)

        self.alert_rule = AlertRule.objects.create(
            customer=self.customer,
            name="Test Email Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,
        )

        self.report_run = ReportRun.objects.create(
            customer=self.customer,
            status="success",
        )

        self.channel = NotificationChannel.objects.create(
            customer=self.customer,
            channel_type="email",
            name="Test Email Channel",
            config={"recipients": ["ops@example.com", "alerts@example.com"]},
        )

        today = timezone.now().date()
        self.drift_event = DriftEvent.objects.create(
            customer=self.customer,
            report_run=self.report_run,
            payer="Aetna",
            cpt_group="Office Visits",
            drift_type="DENIAL_RATE",
            baseline_value=Decimal("0.10"),
            current_value=Decimal("0.25"),
            delta_value=Decimal("0.15"),
            severity=Decimal("0.75"),
            confidence=Decimal("0.90"),
            baseline_start=today - timedelta(days=90),
            baseline_end=today - timedelta(days=15),
            current_start=today - timedelta(days=14),
            current_end=today,
        )

        self.alert_event = AlertEvent.objects.create(
            customer=self.customer,
            alert_rule=self.alert_rule,
            drift_event=self.drift_event,
            triggered_at=timezone.now(),
            status="pending",
            payload={
                "product_name": "DriftWatch",
                "signal_type": "DENIAL_RATE",
                "entity_label": "Aetna",
                "payer": "Aetna",
                "severity": 0.75,
                "delta": 0.15,
            },
        )

    def tearDown(self):
        """Clean up customer context."""
        clear_current_customer()

    def test_send_email_notification_success(self):
        """Test that email notifications are sent successfully."""
        evidence_payload = {
            "product_name": "DriftWatch",
            "entity_label": "Aetna",
            "severity": 0.75,
            "summary": "Denial rate increased significantly",
            "urgency_level": "high",
            "urgency_label": "Investigate Today",
        }

        send_email_notification(self.alert_event, self.channel, evidence_payload)

        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn("ops@example.com", email.to)
        self.assertIn("alerts@example.com", email.to)
        self.assertIn("DriftWatch", email.subject)
        self.assertIn("Email Test Corp", email.subject)

    def test_send_email_notification_no_recipients(self):
        """Test that email fails gracefully with no recipients."""
        channel_no_recipients = NotificationChannel.objects.create(
            customer=self.customer,
            channel_type="email",
            name="Empty Channel",
            config={"recipients": []},
        )

        evidence_payload = {"product_name": "DriftWatch", "entity_label": "Aetna"}

        # Should not raise exception
        send_email_notification(
            self.alert_event, channel_no_recipients, evidence_payload
        )

        # No email sent
        self.assertEqual(len(mail.outbox), 0)


class GetSuppressionContextTests(TestCase):
    """Tests for historical suppression context retrieval."""

    def setUp(self):
        """Create test fixtures and set customer context."""
        self.customer = Customer.objects.create(name="Context Test Corp")

        # Set customer context for tenant-isolated queries
        set_current_customer(self.customer)

        self.alert_rule = AlertRule.objects.create(
            customer=self.customer,
            name="Test Context Rule",
            enabled=True,
            metric="severity",
            threshold_type="gte",
            threshold_value=0.70,
        )

        self.report_run = ReportRun.objects.create(
            customer=self.customer,
            status="success",
        )

        today = timezone.now().date()
        self.drift_event = DriftEvent.objects.create(
            customer=self.customer,
            report_run=self.report_run,
            payer="ContextPayer",
            cpt_group="Office Visits",
            drift_type="DENIAL_RATE",
            baseline_value=Decimal("0.10"),
            current_value=Decimal("0.25"),
            delta_value=Decimal("0.15"),
            severity=Decimal("0.75"),
            confidence=Decimal("0.90"),
            baseline_start=today - timedelta(days=90),
            baseline_end=today - timedelta(days=15),
            current_start=today - timedelta(days=14),
            current_end=today,
        )

        self.alert_event = AlertEvent.objects.create(
            customer=self.customer,
            alert_rule=self.alert_rule,
            drift_event=self.drift_event,
            triggered_at=timezone.now(),
            status="pending",
            payload={
                "product_name": "DriftWatch",
                "signal_type": "DENIAL_RATE",
                "entity_label": "ContextPayer",
                "payer": "ContextPayer",
            },
        )

    def tearDown(self):
        """Clean up customer context."""
        clear_current_customer()

    def test_get_suppression_context_with_noise_judgment(self):
        """Test suppression context returns noise history."""
        # Create 2 historical alerts marked as noise (threshold is 2)
        for i in range(2):
            past_alert = AlertEvent.objects.create(
                customer=self.customer,
                alert_rule=self.alert_rule,
                drift_event=self.drift_event,
                triggered_at=timezone.now() - timedelta(days=5 + i),
                status="resolved",
                payload={
                    "product_name": "DriftWatch",
                    "signal_type": "DENIAL_RATE",
                    "entity_label": "ContextPayer",
                    "payer": "ContextPayer",
                },
            )

            OperatorJudgment.objects.create(
                customer=self.customer,
                alert_event=past_alert,
                verdict="noise",
                notes="False alarm",
            )

        context = get_suppression_context(self.alert_event)

        self.assertIsNotNone(context)
        self.assertEqual(context["type"], "noise")
        self.assertEqual(context["count"], 2)

    def test_get_suppression_context_no_history(self):
        """Test that no context returned when no historical alerts."""
        # Create alert for different payer (no history)
        today = timezone.now().date()
        new_drift = DriftEvent.objects.create(
            customer=self.customer,
            report_run=self.report_run,
            payer="NewPayer",
            cpt_group="Office Visits",
            drift_type="DENIAL_RATE",
            baseline_value=Decimal("0.10"),
            current_value=Decimal("0.20"),
            delta_value=Decimal("0.10"),
            severity=Decimal("0.60"),
            confidence=Decimal("0.85"),
            baseline_start=today - timedelta(days=90),
            baseline_end=today - timedelta(days=15),
            current_start=today - timedelta(days=14),
            current_end=today,
        )

        new_alert = AlertEvent.objects.create(
            customer=self.customer,
            alert_rule=self.alert_rule,
            drift_event=new_drift,
            triggered_at=timezone.now(),
            status="pending",
            payload={
                "product_name": "DriftWatch",
                "signal_type": "DENIAL_RATE",
                "entity_label": "NewPayer",
                "payer": "NewPayer",
            },
        )

        context = get_suppression_context(new_alert)

        self.assertIsNone(context)

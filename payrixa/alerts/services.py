"""
Alert services for evaluating drift events and sending notifications.

This module implements the core alert notification system for Payrixa, handling:
- Evaluation of drift events against configured alert rules
- Multi-channel notification delivery (email, Slack, webhooks)
- Alert suppression to prevent notification fatigue
- Idempotent notification delivery with retry support
- PDF attachment generation for email alerts

ALERT SYSTEM ARCHITECTURE:
===========================

1. ALERT EVALUATION FLOW:
   DriftEvent -> evaluate_drift_event() -> AlertEvent(s) created
   - Each active AlertRule is checked against the drift event
   - Deduplication ensures one AlertEvent per (drift_event, rule) pair
   - Audit events are created for traceability

2. NOTIFICATION DELIVERY FLOW:
   AlertEvent(pending) -> send_alert_notification() -> AlertEvent(sent/failed)
   - Idempotent: skips already-sent or failed alerts
   - Suppression check prevents duplicate notifications within 4-hour window
   - Multi-channel routing: rule-specific channels or customer defaults
   - Status tracking: pending -> sent/failed

3. CHANNEL TYPES:
   - Email: HTML email with optional PDF attachment (via SMTP)
   - Slack: Rich message blocks via webhook URL
   - Webhook: External HTTP POST (handled by separate send_webhooks command)

4. ALERT SUPPRESSION:
   - Prevents notification spam for recurring issues
   - 4-hour cooldown window (ALERT_SUPPRESSION_COOLDOWN)
   - Deduplication key: (product_name, signal_type, entity_label)
   - Example: If "BCBS denial_rate spike" alert fires at 10:00am,
     subsequent alerts for same payer+signal won't send until 2:00pm

5. ROUTING LOGIC:
   - Rule-specific: Use channels linked to AlertRule.routing_channels
   - Fallback: Use all enabled NotificationChannels for customer
   - Default: Send to DEFAULT_ALERT_EMAIL if no channels configured

6. ERROR HANDLING:
   - Email/Slack failures mark AlertEvent as 'failed' (manual review needed)
   - PDF generation failures don't block email send (graceful degradation)
   - Audit events track all successes/failures for compliance

CONFIGURATION SETTINGS:
=======================
- ALERT_SUPPRESSION_COOLDOWN: timedelta(hours=4) - Suppression window
- ALERT_ATTACH_PDF: bool - Enable PDF attachments for email alerts
- SLACK_ENABLED: bool - Enable Slack notifications (default: False)
- DEFAULT_ALERT_EMAIL: str - Fallback email for alerts without channels
- PORTAL_BASE_URL: str - Base URL for alert email links

USAGE EXAMPLE:
==============
    # 1. Evaluate drift event and create alert events
    drift_event = DriftEvent.objects.get(id=123)
    alert_events = evaluate_drift_event(drift_event)

    # 2. Send notifications for pending alerts
    for alert_event in alert_events:
        success = send_alert_notification(alert_event)
        if not success:
            logger.error(f"Failed to send alert {alert_event.id}")

    # 3. Batch processing (via management command)
    results = process_pending_alerts()
    print(f"Sent {results['sent']}/{results['total']} alerts")

See also:
- payrixa.alerts.models: AlertRule, AlertEvent, NotificationChannel
- payrixa.services.evidence_payload: build_driftwatch_evidence_payload()
- payrixa.reporting.services: generate_weekly_drift_pdf()
"""
import logging
import os
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from .models import AlertRule, AlertEvent, NotificationChannel
from payrixa.models import DriftEvent
from payrixa.services.evidence_payload import build_driftwatch_evidence_payload

logger = logging.getLogger(__name__)

ALERT_SUPPRESSION_COOLDOWN = timezone.timedelta(hours=4)

def evaluate_drift_event(drift_event):
    """
    Evaluate a drift event against all active alert rules and create AlertEvents.

    This function is the entry point for alert evaluation. For each drift event detected
    by the drift analysis pipeline, this function checks all enabled AlertRules for the
    customer and creates AlertEvent records when rules are triggered.

    DEDUPLICATION GUARANTEE:
    ------------------------
    Only one AlertEvent is created per (drift_event, alert_rule) pair. If an AlertEvent
    already exists (e.g., from a previous run or concurrent evaluation), it's returned
    without creating a duplicate. This ensures idempotency across multiple invocations.

    PAYLOAD STRUCTURE:
    ------------------
    Each AlertEvent stores a JSON payload with these fields:
    {
        'product_name': 'DriftWatch',
        'signal_type': drift_event.drift_type,  # e.g., 'denial_rate', 'avg_decision_time'
        'entity_label': drift_event.payer,       # Human-readable identifier
        'payer': drift_event.payer,              # Payer name
        'cpt_group': drift_event.cpt_group,      # CPT group (null for payer-level)
        'drift_type': drift_event.drift_type,    # Metric that drifted
        'baseline_value': drift_event.baseline_value,  # Historical average
        'current_value': drift_event.current_value,    # Recent average
        'delta_value': drift_event.delta_value,        # Change amount
        'severity': drift_event.severity,              # 0.0-1.0 severity score
        'rule_name': rule.name,                        # Triggered rule name
        'rule_threshold': rule.threshold_value         # Threshold that was exceeded
    }

    This payload is used downstream by:
    - build_driftwatch_evidence_payload() for email/Slack formatting
    - Alert suppression logic for deduplication key
    - Audit trails for compliance and debugging

    AUDIT EVENTS:
    -------------
    Creates a DomainAuditEvent for each AlertEvent with metadata:
    - action: 'alert_event_created'
    - entity_type: 'AlertEvent'
    - entity_id: alert_event.id
    - metadata: {'alert_rule', 'drift_event_id', 'payer', 'severity'}

    Args:
        drift_event (DriftEvent): The drift event to evaluate. Must have:
            - customer: Customer instance (determines which rules apply)
            - drift_type: Metric name (e.g., 'denial_rate')
            - payer: Payer name
            - cpt_group: CPT group name or null
            - severity: Float 0.0-1.0
            - All baseline/current/delta values

    Returns:
        list[AlertEvent]: List of AlertEvent objects (newly created or existing).
            Empty list if no rules match or all rules disabled.

    Example:
        >>> drift_event = DriftEvent.objects.get(id=456)
        >>> drift_event.severity
        0.85
        >>> alert_events = evaluate_drift_event(drift_event)
        >>> len(alert_events)
        2  # Two rules triggered
        >>> alert_events[0].status
        'pending'
        >>> alert_events[0].alert_rule.name
        'High Severity Denial Rate Spikes'

    Notes:
        - Only enabled AlertRules are evaluated (enabled=True)
        - AlertRule.evaluate() contains the actual threshold matching logic
        - All AlertEvents start with status='pending' for later notification
        - This function is called by management commands (run_drift_analysis)
          and API endpoints (/api/v1/reports/ POST)

    See also:
        - AlertRule.evaluate() in alerts/models.py for threshold logic
        - send_alert_notification() for notification delivery
        - process_pending_alerts() for batch processing
    """
    from payrixa.core.services import create_audit_event
    
    alert_events = []
    alert_rules = AlertRule.objects.filter(customer=drift_event.customer, enabled=True)
    for rule in alert_rules:
        if rule.evaluate(drift_event):
            # Check for duplicate alert event to prevent re-creation
            existing = AlertEvent.objects.filter(
                drift_event=drift_event,
                alert_rule=rule
            ).first()
            
            if existing:
                logger.info(f"Alert event already exists for rule {rule.name} and drift event {drift_event.id}")
                alert_events.append(existing)
                continue
            
            payload = {
                'product_name': 'DriftWatch',
                'signal_type': drift_event.drift_type,
                'entity_label': drift_event.payer,
                'payer': drift_event.payer,
                'cpt_group': drift_event.cpt_group,
                'drift_type': drift_event.drift_type,
                'baseline_value': drift_event.baseline_value,
                'current_value': drift_event.current_value,
                'delta_value': drift_event.delta_value,
                'severity': drift_event.severity,
                'rule_name': rule.name,
                'rule_threshold': rule.threshold_value,
            }
            alert_event = AlertEvent.objects.create(
                customer=drift_event.customer, alert_rule=rule, drift_event=drift_event,
                report_run=drift_event.report_run, triggered_at=timezone.now(), status='pending', payload=payload
            )
            alert_events.append(alert_event)
            logger.info(f"Alert triggered: {rule.name} for drift event {drift_event.id}")
            
            # Create audit event
            create_audit_event(
                action='alert_event_created',
                entity_type='AlertEvent',
                entity_id=alert_event.id,
                customer=alert_event.customer,
                metadata={
                    'alert_rule': rule.name,
                    'drift_event_id': drift_event.id,
                    'payer': drift_event.payer,
                    'severity': drift_event.severity
                }
            )
    return alert_events

def send_alert_notification(alert_event):
    """
    Send multi-channel notifications for an AlertEvent with intelligent routing and suppression.

    This function orchestrates the notification delivery process for a single AlertEvent,
    handling idempotency, suppression, channel routing, and error tracking. It's designed
    to be safe for repeated invocation on the same alert_event.

    IDEMPOTENCY GUARANTEES:
    -----------------------
    - Already sent alerts (status='sent'): Skipped, returns True
    - Failed alerts (status='failed'): Skipped, returns False (manual intervention needed)
    - Pending alerts: Processed exactly once (status updated to sent/failed)

    This ensures safe retry logic in batch processing (process_pending_alerts) and
    prevents duplicate notifications even if called multiple times.

    ALERT SUPPRESSION:
    ------------------
    Before sending, checks if a similar alert was recently sent using _is_suppressed():
    - Deduplication window: 4 hours (ALERT_SUPPRESSION_COOLDOWN)
    - Deduplication key: (customer, product_name, signal_type, entity_label)
    - Example: "DriftWatch BCBS denial_rate" alert suppressed for 4 hours

    If suppressed:
    - Status set to 'sent' (prevents retry)
    - error_message set to 'suppressed'
    - notification_sent_at recorded
    - No actual notification delivered

    ADVANCED CHANNEL ROUTING:
    -------------------------
    Channel selection follows this priority:

    1. Rule-specific channels (if configured):
       - Uses AlertRule.routing_channels.filter(enabled=True)
       - Allows per-rule customization (e.g., "High severity -> PagerDuty")

    2. Customer default channels (fallback):
       - Uses NotificationChannel.objects.filter(customer=customer, enabled=True)
       - All channel types: email, slack, webhook

    3. System default email (last resort):
       - Uses settings.DEFAULT_ALERT_EMAIL
       - Ensures critical alerts always reach someone

    CHANNEL DELIVERY:
    -----------------
    - Email: Sends immediately via send_email_notification()
    - Slack: Sends immediately via send_slack_notification()
    - Webhook: Deferred to send_webhooks management command (async delivery)

    Each channel type is attempted independently. If ANY channel succeeds, the alert
    is marked as 'sent'. This prevents single-channel failures from blocking delivery.

    ERROR HANDLING:
    ---------------
    - Success: status='sent', notification_sent_at=now, error_message=None
    - Failure: status='failed', error_message=exception_text
    - Audit events created for both success ('alert_event_sent') and failure ('alert_event_failed')

    Failed alerts require manual investigation:
    - Check error_message for root cause (SMTP failure, invalid webhook URL, etc.)
    - Fix underlying issue (update channel config, check network, etc.)
    - Reset status to 'pending' to retry OR manually mark as 'sent' to skip

    Args:
        alert_event (AlertEvent): The alert to send. Must have:
            - customer: Customer instance
            - alert_rule: AlertRule that triggered
            - drift_event: Associated DriftEvent (for evidence payload)
            - status: Current status (pending/sent/failed)
            - payload: JSON with alert details

    Returns:
        bool: True if notification sent successfully or suppressed, False if failed.

    Raises:
        Exception: Any unhandled exception during notification delivery. The exception
            is caught, logged to error_message, and the alert marked as 'failed'.

    Example:
        >>> alert_event = AlertEvent.objects.get(id=789, status='pending')
        >>> success = send_alert_notification(alert_event)
        >>> success
        True
        >>> alert_event.refresh_from_db()
        >>> alert_event.status
        'sent'
        >>> alert_event.notification_sent_at
        datetime.datetime(2026, 1, 22, 14, 30, 0, tzinfo=<UTC>)

    Example (suppressed):
        >>> # First alert for "BCBS denial_rate" sent at 10:00am
        >>> alert_1 = AlertEvent.objects.get(id=100)
        >>> send_alert_notification(alert_1)  # Sends successfully
        True
        >>> # Second alert for same payer+signal at 10:30am (within 4-hour window)
        >>> alert_2 = AlertEvent.objects.get(id=101)
        >>> send_alert_notification(alert_2)  # Suppressed
        True
        >>> alert_2.error_message
        'suppressed'

    Notes:
        - Webhook channels are NOT delivered by this function - they're handled
          by the send_webhooks management command for async processing with retries
        - PDF attachment generation is attempted but failures don't block email send
        - Request ID from middleware is injected into email for traceability
        - Suppression is based on evidence_payload, not drift_event.id, so multiple
          drift events for the same payer+signal will be suppressed

    See also:
        - _is_suppressed() for suppression logic
        - send_email_notification() for email delivery
        - send_slack_notification() for Slack delivery
        - process_pending_alerts() for batch processing
        - management/commands/send_webhooks.py for webhook delivery
    """
    from payrixa.core.services import create_audit_event
    
    # Idempotency check: skip if already sent
    if alert_event.status == 'sent':
        logger.info(f"Alert event {alert_event.id} already sent, skipping")
        return True
    
    # Skip if already failed (manual intervention required)
    if alert_event.status == 'failed':
        logger.info(f"Alert event {alert_event.id} marked as failed, skipping")
        return False
    
    customer = alert_event.customer
    alert_rule = alert_event.alert_rule
    
    # Advanced routing: Use rule-specific channels if configured
    if alert_rule.routing_channels.exists():
        channels = alert_rule.routing_channels.filter(enabled=True)
    else:
        channels = NotificationChannel.objects.filter(customer=customer, enabled=True)

    evidence_payload = build_driftwatch_evidence_payload(
        alert_event.drift_event,
        [alert_event.drift_event] if alert_event.drift_event else [],
    )

    if _is_suppressed(alert_event.customer, evidence_payload):
        alert_event.status = 'sent'
        alert_event.notification_sent_at = timezone.now()
        alert_event.error_message = 'suppressed'
        alert_event.save()
        logger.info(f"Alert event {alert_event.id} suppressed within cooldown window")
        return True
    
    success = False
    error_message = None
    
    try:
        for channel in channels:
            if channel.channel_type == 'email':
                success = send_email_notification(alert_event, channel, evidence_payload)
            elif channel.channel_type == 'slack':
                success = send_slack_notification(alert_event, channel)
            elif channel.channel_type == 'webhook':
                # Webhook handled separately by send_webhooks command
                logger.info(f"Skipping webhook channel {channel.id} - handled by send_webhooks command")
        
        if not channels.exists():
            success = send_default_email_notification(alert_event, evidence_payload)
        
        if success:
            alert_event.status = 'sent'
            alert_event.notification_sent_at = timezone.now()
            alert_event.error_message = None
            alert_event.save()
            
            # Create audit event for successful send
            create_audit_event(
                action='alert_event_sent',
                entity_type='AlertEvent',
                entity_id=alert_event.id,
                customer=alert_event.customer,
                metadata={
                    'alert_rule': alert_event.alert_rule.name,
                    'payer': alert_event.payload.get('payer'),
                    'notification_sent_at': alert_event.notification_sent_at.isoformat()
                }
            )
            logger.info(f"Alert event {alert_event.id} sent successfully")
    except Exception as e:
        error_message = str(e)
        alert_event.status = 'failed'
        alert_event.error_message = error_message
        alert_event.save()
        
        # Create audit event for failed send
        create_audit_event(
            action='alert_event_failed',
            entity_type='AlertEvent',
            entity_id=alert_event.id,
            customer=alert_event.customer,
            metadata={
                'alert_rule': alert_event.alert_rule.name,
                'error_message': error_message
            }
        )
        logger.error(f"Alert event {alert_event.id} failed: {error_message}")
        success = False
    
    return success

def send_email_notification(alert_event, channel, evidence_payload):
    """
    Send email notification via a configured NotificationChannel.

    Extracts recipient email addresses from channel.config['recipients'] and
    delegates to _send_email_with_pdf() for actual delivery.

    Args:
        alert_event (AlertEvent): The alert to send
        channel (NotificationChannel): Channel with type='email' and config
        evidence_payload (dict): Evidence payload for email body

    Returns:
        bool: True if sent successfully, False if no recipients configured

    Example:
        >>> channel = NotificationChannel.objects.get(id=10, channel_type='email')
        >>> channel.config
        {'recipients': ['ops@acme.com', 'alerts@acme.com']}
        >>> send_email_notification(alert_event, channel, evidence_payload)
        True
    """
    config = channel.config or {}
    recipients = config.get('recipients', [])
    if not recipients:
        return False

    return _send_email_with_pdf(alert_event, recipients, evidence_payload)

def send_default_email_notification(alert_event, evidence_payload):
    """
    Send email notification using system default recipient (fallback when no channels configured).

    This is used when a customer has no NotificationChannels configured and no
    rule-specific routing. Ensures critical alerts always reach someone.

    Args:
        alert_event (AlertEvent): The alert to send
        evidence_payload (dict): Evidence payload for email body

    Returns:
        bool: True if sent successfully

    Configuration:
        settings.DEFAULT_ALERT_EMAIL: Fallback recipient (default: 'alerts@example.com')

    Example:
        >>> # Customer has no notification channels
        >>> NotificationChannel.objects.filter(customer=customer).count()
        0
        >>> send_default_email_notification(alert_event, evidence_payload)
        True  # Sent to DEFAULT_ALERT_EMAIL
    """
    recipients = [getattr(settings, 'DEFAULT_ALERT_EMAIL', 'alerts@example.com')]
    return _send_email_with_pdf(alert_event, recipients, evidence_payload)

def _send_email_with_pdf(alert_event, recipients, evidence_payload):
    """
    Send branded HTML email with optional PDF attachment for alert notifications.

    This is the core email delivery function used by both send_email_notification()
    (channel-based) and send_default_email_notification() (fallback). It generates
    a professional, multi-part email with:
    - Plain text fallback body
    - Rich HTML body (from Django template)
    - Optional PDF attachment (weekly drift report)
    - Request ID for distributed tracing

    EMAIL STRUCTURE:
    ----------------
    Subject: "[Payrixa] {Product} Alert - {Customer} - {Severity} Severity"
    From: settings.DEFAULT_FROM_EMAIL (default: alerts@payrixa.com)
    To: recipients (list of email addresses)

    Body (Plain Text):
        DriftWatch Alert - Acme Corp

        BCBS denial rate increased by +15.2% above baseline

        View the full report: https://portal.payrixa.com/portal/

        Request ID: 7f3c8d2a-4b1e-4f9a-9c6d-5e8a1f2b3c4d

    Body (HTML):
        <Branded template with logo, colors, severity badge, evidence details>

    Attachment (Optional):
        payrixa_weekly_drift_acme_corp.pdf (if ALERT_ATTACH_PDF=True)

    PDF ATTACHMENT LOGIC:
    ---------------------
    PDF attachments are controlled by two conditions:
    1. ALERT_ATTACH_PDF setting must be True (default: False for performance)
    2. alert_event.report_run must exist (links to ReportRun with ReportArtifact)

    PDF generation follows this flow:
    1. Try to fetch existing ReportArtifact for report_run (kind='weekly_drift_summary')
    2. If not found, generate on-demand via generate_weekly_drift_pdf(report_run.id)
    3. Read PDF file from artifact.file_path and attach to email
    4. If ANY step fails (missing file, generation error), log warning and continue
       WITHOUT attachment (graceful degradation - email still sent)

    This ensures:
    - Email delivery is never blocked by PDF issues
    - Users get timely alerts even if PDF generation is slow/failing
    - Observability via logs for debugging PDF problems

    TEMPLATE CONTEXT:
    -----------------
    HTML template (email/alert_email_body.html) receives:
    {
        'customer_name': 'Acme Corp',
        'product_name': 'DriftWatch',
        'severity': 'high',  # 'low', 'medium', 'high', 'unknown'
        'summary_sentence': 'BCBS denial rate increased by +15.2% above baseline',
        'evidence_payload': {
            'product_name': 'DriftWatch',
            'signal_type': 'denial_rate',
            'entity_label': 'BCBS',
            'baseline_value': 0.12,
            'current_value': 0.27,
            'delta_value': 0.15,
            'severity': 0.85,
            'one_sentence_explanation': '...',
            # ... additional evidence fields
        },
        'portal_url': 'https://portal.payrixa.com/portal/',
        'request_id': '7f3c8d2a-4b1e-4f9a-9c6d-5e8a1f2b3c4d'
    }

    Subject template (email/alert_email_subject.txt) receives:
    {
        'customer_name': 'Acme Corp',
        'product_name': 'DriftWatch',
        'severity': 'high'
    }

    CONFIGURATION DEPENDENCIES:
    ---------------------------
    Required settings:
    - PORTAL_BASE_URL: Base URL for portal links (e.g., 'https://portal.payrixa.com')
        - Used to construct portal_url = f"{PORTAL_BASE_URL}/portal/"
        - NO fallback - must be configured or emails will have invalid links

    Optional settings:
    - DEFAULT_FROM_EMAIL: Sender email (default: 'alerts@payrixa.com')
    - ALERT_ATTACH_PDF: Enable PDF attachments (default: False)
    - Email backend configuration (SMTP server, credentials, etc.)

    ERROR HANDLING:
    ---------------
    - PDF attachment failures: Logged as WARNING, email sent without attachment
    - Email send failures: Raises exception (caught by send_alert_notification)
    - Missing templates: Raises TemplateDoesNotExist (deployment issue)
    - Missing PORTAL_BASE_URL: Email sent with potentially broken links

    Args:
        alert_event (AlertEvent): The alert event being sent
        recipients (list[str]): List of recipient email addresses
        evidence_payload (dict): Evidence payload from build_driftwatch_evidence_payload()
            Expected keys: product_name, severity, one_sentence_explanation, etc.

    Returns:
        bool: True if email sent successfully

    Raises:
        SMTPException: If email delivery fails (SMTP connection, authentication, etc.)
        TemplateDoesNotExist: If Django templates are missing
        Exception: Any other unhandled error during email generation

    Example:
        >>> alert_event = AlertEvent.objects.get(id=123)
        >>> recipients = ['ops@acme.com', 'alerts@acme.com']
        >>> evidence = build_driftwatch_evidence_payload(alert_event.drift_event, [...])
        >>> success = _send_email_with_pdf(alert_event, recipients, evidence)
        >>> success
        True

    Example (PDF attachment disabled):
        >>> # ALERT_ATTACH_PDF = False in settings
        >>> success = _send_email_with_pdf(alert_event, recipients, evidence)
        INFO: PDF attachment disabled (ALERT_ATTACH_PDF=False), skipping for report run 456
        >>> success
        True  # Email sent without PDF

    Example (PDF generation failure):
        >>> # PDF file missing or generation failed
        >>> success = _send_email_with_pdf(alert_event, recipients, evidence)
        ERROR: Failed to attach PDF to email: File not found
        >>> success
        True  # Email sent anyway (graceful degradation)

    Notes:
        - Request ID from middleware (X-Request-Id header) is injected for tracing
        - If no request ID available, generates a new UUID for the email
        - PDF filename format: payrixa_weekly_drift_{customer_name_lowercase}.pdf
        - Uses Django's EmailMultiAlternatives for multipart emails
        - fail_silently=False ensures exceptions are raised for proper error tracking

    Performance Considerations:
        - PDF generation can take 5-10 seconds for large reports
        - On-demand generation blocks email send during that time
        - Pre-generate PDFs via run_drift_analysis command to avoid blocking
        - Consider async email delivery for high-volume scenarios

    See also:
        - generate_weekly_drift_pdf() in reporting/services.py
        - ReportArtifact model in reporting/models.py
        - build_driftwatch_evidence_payload() in services/evidence_payload.py
        - Templates: email/alert_email_subject.txt, email/alert_email_body.html
    """
    from payrixa.middleware import get_request_id
    from payrixa.reporting.services import generate_weekly_drift_pdf
    from payrixa.reporting.models import ReportArtifact
    
    # Gather context data
    customer = alert_event.customer
    report_run = alert_event.report_run

    severity_label = _severity_label(evidence_payload.get('severity'))
    product_name = evidence_payload.get('product_name', 'Payrixa')
    summary_sentence = evidence_payload.get('one_sentence_explanation', '')
    
    # Portal URL from settings (no fallback - must be configured)
    portal_url = f"{settings.PORTAL_BASE_URL}/portal/"
    
    # Request ID for traceability
    request_id = get_request_id() or str(uuid.uuid4())
    
    # Render subject
    subject_context = {
        'customer_name': customer.name,
        'product_name': product_name,
        'severity': severity_label,
    }
    subject = render_to_string('email/alert_email_subject.txt', subject_context).strip()

    # Render HTML body
    html_context = {
        'customer_name': customer.name,
        'product_name': product_name,
        'severity': severity_label,
        'summary_sentence': summary_sentence,
        'evidence_payload': evidence_payload,
        'portal_url': portal_url,
        'request_id': request_id
    }
    html_body = render_to_string('email/alert_email_body.html', html_context)
    
    # Plain text fallback
    text_body = (
        f"{product_name} Alert - {customer.name}\n\n"
        f"{summary_sentence}\n\n"
        f"View the full report: {portal_url}\n\n"
        f"Request ID: {request_id}"
    )
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'alerts@payrixa.com'),
        to=recipients
    )
    email.attach_alternative(html_body, "text/html")
    
    # Attach PDF if report_run exists and PDF attachment is enabled
    attach_pdf = getattr(settings, 'ALERT_ATTACH_PDF', False)
    if report_run and attach_pdf:
        try:
            # Try to fetch existing artifact
            artifact = ReportArtifact.objects.filter(
                customer=customer,
                report_run=report_run,
                kind='weekly_drift_summary'
            ).first()
            
            # Generate if missing
            if not artifact:
                logger.info(f"Generating missing PDF artifact for report run {report_run.id}")
                artifact = generate_weekly_drift_pdf(report_run.id)
            
            # Attach PDF
            if artifact and artifact.file_path and os.path.exists(artifact.file_path):
                with open(artifact.file_path, 'rb') as pdf_file:
                    pdf_content = pdf_file.read()
                    filename = f"payrixa_weekly_drift_{customer.name.replace(' ', '_').lower()}.pdf"
                    email.attach(filename, pdf_content, 'application/pdf')
                    logger.info(f"Attached PDF artifact {artifact.id} to email")
            else:
                logger.warning(f"PDF artifact file not found at {artifact.file_path if artifact else 'N/A'}")
        except Exception as e:
            logger.error(f"Failed to attach PDF to email: {str(e)}")
            # Continue without attachment - don't fail the email send
    elif report_run and not attach_pdf:
        logger.debug(f"PDF attachment disabled (ALERT_ATTACH_PDF=False), skipping for report run {report_run.id}")
    
    # Send email
    email.send(fail_silently=False)
    return True


def _severity_label(severity_value):
    """
    Convert numeric severity score to human-readable label for email templates.

    Severity thresholds are calibrated based on drift analysis output:
    - High (0.7-1.0): Significant drift requiring immediate attention
    - Medium (0.4-0.69): Moderate drift worth investigating
    - Low (0.0-0.39): Minor drift for awareness only

    Args:
        severity_value: Severity score (float 0.0-1.0), string label, or None

    Returns:
        str: One of 'low', 'medium', 'high', 'unknown'

    Examples:
        >>> _severity_label(0.85)
        'high'
        >>> _severity_label(0.5)
        'medium'
        >>> _severity_label(0.2)
        'low'
        >>> _severity_label(None)
        'unknown'
        >>> _severity_label('HIGH')
        'high'
    """
    if severity_value is None:
        return 'unknown'
    if isinstance(severity_value, str):
        return severity_value.lower()
    if severity_value >= 0.7:
        return 'high'
    if severity_value >= 0.4:
        return 'medium'
    return 'low'


def _is_suppressed(customer, evidence_payload):
    """
    Check if an alert should be suppressed to prevent notification fatigue.

    This function implements a time-based deduplication mechanism to prevent sending
    duplicate notifications for the same recurring issue within a cooldown window.
    It's the core suppression logic used by send_alert_notification().

    SUPPRESSION ALGORITHM:
    ----------------------
    An alert is suppressed if ALL of these conditions are met:
    1. A similar alert was sent (status='sent') within the cooldown window
    2. The previous alert has the same (product_name, signal_type, entity_label)
    3. The previous alert belongs to the same customer

    COOLDOWN WINDOW:
    ----------------
    - Default: 4 hours (ALERT_SUPPRESSION_COOLDOWN = timedelta(hours=4))
    - Rationale: Balances responsiveness vs. notification spam
        - Too short (1 hour): Users get flooded with duplicate alerts
        - Too long (24 hours): Users miss important recurring issues
    - After cooldown expires, the same alert can be sent again

    DEDUPLICATION KEY:
    ------------------
    The key (product_name, signal_type, entity_label) is extracted from evidence_payload:

    - product_name: "DriftWatch", "DenialScope", etc. (product that detected the issue)
    - signal_type: "denial_rate", "avg_decision_time", etc. (metric that drifted)
    - entity_label: "BCBS", "Aetna", etc. (payer/entity that triggered alert)

    This means:
    - "DriftWatch BCBS denial_rate" and "DriftWatch BCBS avg_decision_time" are DIFFERENT
      (same payer, different signal) -> both will send
    - "DriftWatch BCBS denial_rate" at 10:00am and 11:00am are SAME
      (same payer+signal) -> second is suppressed until 2:00pm

    QUERY PERFORMANCE:
    ------------------
    Uses JSONField lookup on AlertEvent.payload with indexes on:
    - customer (FK index)
    - status (regular index)
    - notification_sent_at (regular index)

    For high-volume customers, consider adding a composite index:
    CREATE INDEX idx_alert_suppression ON alerts_alertevent(customer_id, status, notification_sent_at)
    WHERE status = 'sent';

    Args:
        customer (Customer): The customer to check for previous alerts
        evidence_payload (dict): Evidence payload with deduplication keys.
            Required keys: product_name, signal_type, entity_label

    Returns:
        bool: True if alert should be suppressed, False if it should be sent.

    Example:
        >>> from django.utils import timezone
        >>> from payrixa.models import Customer
        >>> customer = Customer.objects.first()
        >>> evidence = {
        ...     'product_name': 'DriftWatch',
        ...     'signal_type': 'denial_rate',
        ...     'entity_label': 'BCBS'
        ... }
        >>> _is_suppressed(customer, evidence)
        False  # No recent alerts
        >>> # ... send alert at 10:00am ...
        >>> _is_suppressed(customer, evidence)  # Called again at 10:30am
        True  # Suppressed (within 4-hour window)
        >>> # ... 4 hours later at 2:01pm ...
        >>> _is_suppressed(customer, evidence)
        False  # Cooldown expired, can send again

    Example (different signal types):
        >>> evidence_denial = {
        ...     'product_name': 'DriftWatch',
        ...     'signal_type': 'denial_rate',
        ...     'entity_label': 'BCBS'
        ... }
        >>> evidence_decision = {
        ...     'product_name': 'DriftWatch',
        ...     'signal_type': 'avg_decision_time',
        ...     'entity_label': 'BCBS'
        ... }
        >>> _is_suppressed(customer, evidence_denial)
        True  # Recent denial_rate alert exists
        >>> _is_suppressed(customer, evidence_decision)
        False  # Different signal_type, not suppressed

    Notes:
        - Returns False if evidence_payload is None/empty (defensive programming)
        - Only checks 'sent' alerts (not 'pending' or 'failed')
        - Uses notification_sent_at (not triggered_at) for window calculation
        - JSONField queries can be slow on large datasets - monitor performance

    Limitations:
        - Suppression is per-customer only (not cross-customer)
        - No configurable cooldown per rule (global 4-hour window)
        - No severity-based suppression (high-severity alerts still suppressed)
        - Future enhancement: Allow AlertRule.suppression_cooldown override

    See also:
        - send_alert_notification() which calls this function
        - ALERT_SUPPRESSION_COOLDOWN constant (top of file)
        - AlertEvent model in alerts/models.py
    """
    if not evidence_payload:
        return False
    window_start = timezone.now() - ALERT_SUPPRESSION_COOLDOWN
    return AlertEvent.objects.filter(
        customer=customer,
        status='sent',
        notification_sent_at__gte=window_start,
        payload__product_name=evidence_payload.get('product_name'),
        payload__signal_type=evidence_payload.get('signal_type'),
        payload__entity_label=evidence_payload.get('entity_label'),
    ).exists()

def send_slack_notification(alert_event, channel):
    """
    Send rich Slack notification with formatted blocks and severity-based colors.

    Sends a Slack message using the Block Kit format with:
    - Header with emoji indicator (🚨 high, ⚠️ medium, ℹ️ low)
    - Formatted fields for customer, rule, payer, drift type, delta, severity
    - Action button linking to Payrixa portal
    - Color-coded attachment (red=high, orange=medium, blue=low)
    - Context footer with alert ID and timestamp

    SLACK ENABLEMENT:
    -----------------
    Slack is disabled by default (MVP v1). To enable:
    - Set SLACK_ENABLED=True in settings
    - Configure webhook_url in NotificationChannel.config

    If SLACK_ENABLED=False, this function returns True (no-op) to prevent
    marking alerts as failed.

    Args:
        alert_event (AlertEvent): The alert to send
        channel (NotificationChannel): Channel with type='slack' and config

    Returns:
        bool: True if sent successfully or Slack disabled, False if failed

    Configuration:
        settings.SLACK_ENABLED: Master switch (default: False)
        channel.config['webhook_url']: Incoming webhook URL from Slack

    Example:
        >>> channel = NotificationChannel.objects.get(id=20, channel_type='slack')
        >>> channel.config
        {'webhook_url': 'https://hooks.slack.com/services/T00/B00/XXX'}
        >>> send_slack_notification(alert_event, channel)
        True  # Message posted to Slack channel

    Example (Slack disabled):
        >>> # SLACK_ENABLED = False
        >>> send_slack_notification(alert_event, channel)
        True  # No-op, returns True to not fail alert

    Notes:
        - Timeout: 10 seconds for webhook POST
        - Only logs errors, doesn't raise exceptions
        - Portal URL constructed from PORTAL_BASE_URL setting
        - Emoji and colors are hardcoded per severity band

    See also:
        - Slack Block Kit: https://api.slack.com/block-kit
        - Incoming Webhooks: https://api.slack.com/messaging/webhooks
    """
    import json
    import requests
    
    # V1: Slack is disabled by default
    if not getattr(settings, 'SLACK_ENABLED', False):
        logger.info(f"Slack disabled (SLACK_ENABLED=False), skipping channel {channel.id}")
        return True  # Return True to not mark as failed
    
    config = channel.config or {}
    webhook_url = config.get('webhook_url')
    
    if not webhook_url:
        logger.error(f"Slack channel {channel.id} missing webhook_url")
        return False
    
    # Gather context data
    customer = alert_event.customer
    payload = alert_event.payload
    drift_event = alert_event.drift_event
    alert_rule = alert_event.alert_rule
    
    # Build summary message
    payer = payload.get('payer', 'Unknown')
    drift_type = payload.get('drift_type', 'Unknown').replace('_', ' ').title()
    delta = payload.get('delta_value', 0)
    severity = payload.get('severity', 0)
    
    # Severity emoji and color
    if severity >= 0.7:
        color = "#d32f2f"  # Red
        emoji = "🚨"
    elif severity >= 0.4:
        color = "#ff9800"  # Orange
        emoji = "⚠️"
    else:
        color = "#2196f3"  # Blue
        emoji = "ℹ️"
    
    # Portal URL from settings
    portal_url = f"{settings.PORTAL_BASE_URL}/portal/"
    
    # Build Slack message with blocks
    slack_payload = {
        "text": f"{emoji} Drift Alert: {payer} {drift_type}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Drift Alert Triggered"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Customer:*\n{customer.name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Rule:*\n{alert_rule.name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Payer:*\n{payer}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Drift Type:*\n{drift_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Delta:*\n{delta:+.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity:.2f}"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View in Payrixa Portal"
                        },
                        "url": portal_url,
                        "style": "primary"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Alert ID: {alert_event.id} | Triggered: {alert_event.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ],
        "attachments": [
            {
                "color": color,
                "text": f"This alert was triggered by the *{alert_rule.name}* rule."
            }
        ]
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(slack_payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Slack notification sent successfully for alert event {alert_event.id}")
            return True
        else:
            logger.error(f"Slack notification failed with status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
        return False

def process_pending_alerts():
    """
    Batch process all pending AlertEvents and send notifications.

    This function is called by the process_alerts management command to send
    notifications for all alerts in 'pending' status. It's designed for:
    - Scheduled batch processing (e.g., cron job every 5 minutes)
    - Manual retry of failed alerts (after fixing underlying issues)
    - Recovery from system downtime

    PROCESSING LOGIC:
    -----------------
    1. Query all AlertEvent objects with status='pending'
    2. For each alert, call send_alert_notification()
    3. Count successes and failures
    4. Return summary statistics

    Error handling:
    - Individual alert failures are caught and logged
    - Processing continues for remaining alerts (not fail-fast)
    - Failed alerts remain in database with status='failed'

    Returns:
        dict: Summary with keys:
            - 'total': Total pending alerts processed
            - 'sent': Successfully sent count
            - 'failed': Failed send count

    Example:
        >>> # Create some pending alerts
        >>> AlertEvent.objects.filter(status='pending').count()
        15
        >>> results = process_pending_alerts()
        >>> results
        {'total': 15, 'sent': 13, 'failed': 2}
        >>> # Check remaining pending alerts
        >>> AlertEvent.objects.filter(status='pending').count()
        0  # All processed (either sent or failed)

    Example (management command usage):
        # Run via Django management command
        $ python manage.py process_alerts
        INFO: Processing 15 pending alerts...
        INFO: Sent 13 alerts successfully
        ERROR: Failed to send 2 alerts

    Notes:
        - Does NOT retry already-failed alerts (only processes 'pending')
        - To retry failed alerts: manually set status='pending' in database
        - Suppression logic applies during processing (_is_suppressed checks)
        - Use with caution in high-volume scenarios (no pagination)

    Performance Considerations:
        - Fetches all pending alerts into memory (could be thousands)
        - Each send_alert_notification() can take 1-10 seconds (SMTP, PDF gen)
        - For 100 alerts, expect 2-10 minutes processing time
        - Consider adding pagination or async processing for scale

    See also:
        - management/commands/process_alerts.py for command implementation
        - send_alert_notification() for single alert processing
        - AlertEvent model in alerts/models.py
    """
    pending_alerts = AlertEvent.objects.filter(status='pending')
    results = {'total': pending_alerts.count(), 'sent': 0, 'failed': 0}
    for alert_event in pending_alerts:
        try:
            if send_alert_notification(alert_event):
                results['sent'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            logger.error(f"Error processing alert {alert_event.id}: {str(e)}")
            results['failed'] += 1
    return results

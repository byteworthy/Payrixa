---
phase: quick-022
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - upstream/models.py
  - upstream/migrations/0XXX_add_automation_rule.py
  - upstream/migrations/0XXX_add_execution_log.py
  - upstream/migrations/0XXX_add_authorization.py
  - upstream/migrations/0XXX_add_claim_submitted_via.py
  - upstream/views.py
  - upstream/automation/rules_engine.py
  - upstream/automation/__init__.py
  - upstream/tasks.py
autonomous: true

must_haves:
  truths:
    - "AutomationRule model exists and can store pre-approved workflow rules"
    - "ExecutionLog model exists and captures HIPAA audit trail"
    - "Authorization model exists and tracks ABA authorizations with expiration dates"
    - "ClaimRecord has submitted_via field tracking ingestion source"
    - "EHR webhook endpoint accepts FHIR R4 formatted POST requests"
    - "Rules engine evaluates conditions and executes actions autonomously"
    - "Background Celery task processes claims with risk scoring"
  artifacts:
    - path: "upstream/models.py"
      provides: "AutomationRule, ExecutionLog, Authorization models"
      contains: "class AutomationRule"
    - path: "upstream/migrations/0XXX_add_automation_rule.py"
      provides: "AutomationRule migration"
      min_lines: 40
    - path: "upstream/migrations/0XXX_add_execution_log.py"
      provides: "ExecutionLog migration"
      min_lines: 40
    - path: "upstream/migrations/0XXX_add_authorization.py"
      provides: "Authorization migration"
      min_lines: 60
    - path: "upstream/migrations/0XXX_add_claim_submitted_via.py"
      provides: "ClaimRecord submitted_via field"
      min_lines: 25
    - path: "upstream/views.py"
      provides: "EHR webhook receiver endpoint"
      contains: "ehr_webhook"
    - path: "upstream/automation/rules_engine.py"
      provides: "Rules engine framework"
      contains: "class RulesEngine"
    - path: "upstream/tasks.py"
      provides: "process_claim_with_automation Celery task"
      contains: "@shared_task"
  key_links:
    - from: "upstream/views.py"
      to: "upstream/tasks.py"
      via: "process_claim_with_automation.delay()"
      pattern: "process_claim_with_automation\\.delay"
    - from: "upstream/tasks.py"
      to: "upstream/automation/rules_engine.py"
      via: "RulesEngine import and evaluation"
      pattern: "from upstream\\.automation\\.rules_engine import"
    - from: "upstream/automation/rules_engine.py"
      to: "upstream.models.ExecutionLog"
      via: "audit trail creation"
      pattern: "ExecutionLog\\.objects\\.create"
---

<objective>
Complete Week 1 Tasks 2-7 for autonomous execution platform: AutomationRule model, ExecutionLog model, Authorization model, ClaimRecord enhancement, EHR webhook endpoint, rules engine, and background task.

Purpose: Establish foundation for autonomous workflow execution that operates WITHOUT manual approval, matching Adonis speed while providing 30-day calendar advantage.

Output: Four new models migrated to database, EHR webhook receiver accepting FHIR R4 data, rules engine framework for condition evaluation, and Celery task for async claim processing.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/workspaces/codespaces-django/.planning/STATE.md
@/workspaces/codespaces-django/docs/plans/2026-01-27-upstream/00-MASTER-PLAN.md
@/workspaces/codespaces-django/docs/plans/2026-01-27-upstream/03-execution-layer.md
@/workspaces/codespaces-django/docs/plans/2026-01-27-upstream/04-database-schema.md
@/workspaces/codespaces-django/upstream/models.py
@/workspaces/codespaces-django/upstream/tasks.py
</context>

<tasks>

<task type="auto">
  <name>Add AutomationRule, ExecutionLog, Authorization models + ClaimRecord enhancement</name>
  <files>
    upstream/models.py
    upstream/migrations/0XXX_add_automation_rule.py
    upstream/migrations/0XXX_add_execution_log.py
    upstream/migrations/0XXX_add_authorization.py
    upstream/migrations/0XXX_add_claim_submitted_via.py
  </files>
  <action>
    Four sequential migrations are needed because they all modify upstream/models.py.

    **Migration 1: AutomationRule model**

    Add to upstream/models.py after RiskBaseline model:
    - AutomationRule model with fields: customer (FK), name, rule_type (THRESHOLD/PATTERN/SCHEDULE/CHAIN), trigger_event, conditions (JSONField), action_type, action_params (JSONField), enabled (default True), escalate_on_error (default True), created_at, updated_at
    - Use CustomerScopedManager for tenant isolation
    - Add composite index on [customer, enabled, trigger_event]
    - See 04-database-schema.md Migration 2 for exact specification

    Run: `python manage.py makemigrations upstream -n add_automation_rule`

    **Migration 2: ExecutionLog model**

    Add to upstream/models.py after AutomationRule:
    - ExecutionLog model with fields: customer (FK), rule (FK to AutomationRule, null=True), trigger_event (JSONField), action_taken, result (SUCCESS/FAILED/ESCALATED), details (JSONField), execution_time_ms, executed_at
    - Use CustomerScopedManager for tenant isolation
    - Add indexes on [customer, -executed_at] and [rule, result]
    - Meta ordering: ['-executed_at']
    - See 04-database-schema.md Migration 3 for exact specification

    Run: `python manage.py makemigrations upstream -n add_execution_log`

    **Migration 3: Authorization model**

    Add to upstream/models.py after ExecutionLog:
    - Authorization model with fields: customer (FK), auth_number (unique), patient_identifier, payer, service_type, cpt_codes (JSONField list), auth_start_date, auth_expiration_date, units_authorized, units_used (default 0), status (ACTIVE/EXPIRING_SOON/EXPIRED/RENEWED), reauth_lead_time_days (default 21), auto_reauth_enabled (default False), last_alert_sent (null=True), created_at, updated_at
    - Use CustomerScopedManager for tenant isolation
    - Add indexes on [customer, status, auth_expiration_date] and [customer, payer, status]
    - See 04-database-schema.md Migration 5 for exact specification

    Run: `python manage.py makemigrations upstream -n add_authorization`

    **Migration 4: Add submitted_via field to ClaimRecord**

    Add field to ClaimRecord model:
    - submitted_via CharField with choices: csv_upload, ehr_webhook, api, batch_import
    - Default 'csv_upload' to preserve existing data semantics
    - db_index=True for analytics queries
    - Add composite index [customer, submitted_via, decided_date] for analytics
    - See 04-database-schema.md Migration 4 for exact specification

    Run: `python manage.py makemigrations upstream -n add_claim_submitted_via`

    After all migrations created, run: `python manage.py migrate`

    **Important:** Maintain existing imports at bottom of models.py (BaseModel, ValidationRule, AlertRule, etc.). Do not modify existing models except ClaimRecord.
  </action>
  <verify>
    - `python manage.py showmigrations upstream | grep -E "(add_automation_rule|add_execution_log|add_authorization|add_claim_submitted_via)"` shows [X] for all four migrations
    - `python manage.py shell -c "from upstream.models import AutomationRule, ExecutionLog, Authorization; print('Models imported successfully')"` succeeds
    - `python manage.py shell -c "from upstream.models import ClaimRecord; print(ClaimRecord._meta.get_field('submitted_via'))"` shows CharField with choices
  </verify>
  <done>
    Four new models (AutomationRule, ExecutionLog, Authorization) exist in upstream/models.py with CustomerScopedManager, proper indexes, and constraints. ClaimRecord has submitted_via field. All four migrations applied successfully to database.
  </done>
</task>

<task type="auto">
  <name>Create EHR webhook receiver endpoint</name>
  <files>
    upstream/views.py
  </files>
  <action>
    Add EHR webhook receiver endpoint to upstream/views.py that accepts FHIR R4 claim notifications.

    Implementation:

    ```python
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_http_methods
    from django.http import JsonResponse
    import json
    import logging

    logger = logging.getLogger(__name__)

    @csrf_exempt
    @require_http_methods(["POST"])
    def ehr_webhook(request):
        """
        EHR webhook receiver for FHIR R4 claim notifications.

        Accepts claim data from EHR systems (Epic, Cerner, athenahealth) and
        triggers async processing with risk scoring.

        Expected payload format (FHIR R4 Claim resource):
        {
          "resourceType": "Claim",
          "patient": {"reference": "Patient/123"},
          "provider": {"reference": "Organization/456"},
          "billablePeriod": {"start": "2024-01-01", "end": "2024-01-31"},
          "item": [
            {
              "productOrService": {"coding": [{"code": "97153"}]},
              "unitPrice": {"value": 150.00}
            }
          ],
          "insurance": [{"coverage": {"display": "Blue Cross"}}]
        }

        Returns:
        - 202 Accepted: Claim queued for async processing
        - 400 Bad Request: Invalid FHIR format
        - 500 Internal Server Error: Processing failure
        """
        try:
            # Parse FHIR R4 payload
            payload = json.loads(request.body.decode('utf-8'))

            # Validate FHIR structure
            if payload.get('resourceType') != 'Claim':
                return JsonResponse(
                    {'error': 'Invalid resourceType. Expected "Claim"'},
                    status=400
                )

            # Extract customer from API key header or auth
            # For now, use test customer (TODO: implement API key auth)
            from upstream.models import Customer
            customer = Customer.objects.first()

            if not customer:
                return JsonResponse(
                    {'error': 'No customer found for authentication'},
                    status=401
                )

            # Queue async processing
            from upstream.tasks import process_claim_with_automation

            task = process_claim_with_automation.delay(
                customer_id=customer.id,
                fhir_payload=payload,
                source='ehr_webhook'
            )

            logger.info(
                f"EHR webhook claim queued for processing: task_id={task.id}, "
                f"customer={customer.id}"
            )

            return JsonResponse(
                {
                    'status': 'accepted',
                    'task_id': str(task.id),
                    'message': 'Claim queued for processing'
                },
                status=202
            )

        except json.JSONDecodeError:
            logger.error("EHR webhook received invalid JSON")
            return JsonResponse(
                {'error': 'Invalid JSON payload'},
                status=400
            )
        except Exception as e:
            logger.error(f"EHR webhook processing error: {str(e)}")
            return JsonResponse(
                {'error': 'Internal processing error'},
                status=500
            )
    ```

    Add URL route to upstream/urls.py (if exists) or note in summary that URL wiring needed.

    Note: This is a minimal FHIR R4 receiver. Full FHIR parsing (HAPI, fhir.resources) should be added in Phase 2. For Week 1, focus on accepting webhook and queueing async task.
  </action>
  <verify>
    - `grep -n "def ehr_webhook" upstream/views.py` shows function definition
    - `grep -n "@csrf_exempt" upstream/views.py` shows CSRF exemption (required for webhooks)
    - `grep -n "process_claim_with_automation.delay" upstream/views.py` shows async task invocation
    - Manual test: `curl -X POST http://localhost:8000/webhooks/ehr -H "Content-Type: application/json" -d '{"resourceType":"Claim"}` (note: will fail with "No route" until URL wired - document this)
  </verify>
  <done>
    EHR webhook endpoint exists in upstream/views.py, validates FHIR R4 Claim resourceType, queues async task via process_claim_with_automation.delay(), returns 202 Accepted. CSRF exemption added for external webhook calls.
  </done>
</task>

<task type="auto">
  <name>Create rules engine framework and background task</name>
  <files>
    upstream/automation/__init__.py
    upstream/automation/rules_engine.py
    upstream/tasks.py
  </files>
  <action>
    Create rules engine framework for autonomous action execution.

    **Step 1: Create automation package**

    Create directory: `mkdir -p upstream/automation`
    Create: `upstream/automation/__init__.py` (empty or with package docstring)

    **Step 2: Create rules engine**

    Create `upstream/automation/rules_engine.py` based on 03-execution-layer.md specification:

    ```python
    """
    Rules Engine for Autonomous Workflow Execution.

    Evaluates pre-approved AutomationRule conditions against incoming events
    and executes actions WITHOUT human approval. All executions logged to
    ExecutionLog for HIPAA audit compliance.
    """

    from dataclasses import dataclass
    from typing import List, Dict, Any, Optional
    from datetime import datetime
    import logging
    from upstream.models import AutomationRule, ExecutionLog, Customer

    logger = logging.getLogger(__name__)


    @dataclass
    class Event:
        """Event that triggers rule evaluation."""
        event_type: str  # 'claim_submitted', 'authorization_expiring', etc.
        customer_id: int
        payload: Dict[str, Any]
        timestamp: datetime


    @dataclass
    class Action:
        """Action to execute when rule conditions met."""
        rule: AutomationRule
        event: Event
        action_type: str
        action_params: Dict[str, Any]


    @dataclass
    class ExecutionResult:
        """Result of action execution."""
        success: bool
        result_type: str  # 'SUCCESS', 'FAILED', 'ESCALATED'
        details: Dict[str, Any]
        execution_time_ms: int


    class RulesEngine:
        """
        Rules engine orchestrator.

        Loads active rules, evaluates conditions, executes actions,
        and logs all activity for audit trail.
        """

        def __init__(self, customer: Customer):
            self.customer = customer

        def evaluate_event(self, event: Event) -> List[Action]:
            """
            Evaluate event against all active rules.

            Returns list of actions to execute.
            """
            actions = []

            # Load active rules for this customer and event type
            rules = AutomationRule.objects.filter(
                customer=self.customer,
                is_active=True,
                # TODO: Add trigger_event field match once schema updated
            )

            for rule in rules:
                if self._conditions_met(rule, event):
                    actions.append(Action(
                        rule=rule,
                        event=event,
                        action_type=rule.actions.get('type', 'unknown'),
                        action_params=rule.actions
                    ))

            return actions

        def execute_actions(self, actions: List[Action]) -> List[ExecutionResult]:
            """
            Execute all actions and log results.

            Each action execution is logged to ExecutionLog for audit trail.
            Errors are escalated if rule.escalate_on_error=True.
            """
            results = []

            for action in actions:
                start_time = datetime.now()

                try:
                    # Execute action based on type
                    result = self._execute_action(action)
                    execution_time_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    # Log successful execution
                    ExecutionLog.objects.create(
                        customer=self.customer,
                        rule=action.rule,
                        trigger_event=action.event.payload,
                        action_taken=action.action_type,
                        result='SUCCESS',
                        details=result.details,
                        execution_time_ms=execution_time_ms
                    )

                    results.append(result)

                except Exception as e:
                    execution_time_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    logger.error(
                        f"Action execution failed: {action.action_type} - {str(e)}"
                    )

                    # Determine if escalation needed
                    if action.rule.escalate_on_error:
                        result_type = 'ESCALATED'
                        self._escalate_to_human(action, e)
                    else:
                        result_type = 'FAILED'

                    # Log failed execution
                    ExecutionLog.objects.create(
                        customer=self.customer,
                        rule=action.rule,
                        trigger_event=action.event.payload,
                        action_taken=action.action_type,
                        result=result_type,
                        details={'error': str(e)},
                        execution_time_ms=execution_time_ms
                    )

                    results.append(ExecutionResult(
                        success=False,
                        result_type=result_type,
                        details={'error': str(e)},
                        execution_time_ms=execution_time_ms
                    ))

            return results

        def _conditions_met(self, rule: AutomationRule, event: Event) -> bool:
            """
            Evaluate if rule conditions are met for this event.

            Conditions are stored in rule.trigger_conditions JSONField.
            Example: {'risk_score': {'operator': 'gt', 'value': 70}}
            """
            conditions = rule.trigger_conditions

            for key, condition in conditions.items():
                operator = condition.get('operator')
                expected_value = condition.get('value')
                actual_value = event.payload.get(key)

                if not self._compare(actual_value, operator, expected_value):
                    return False

            return True

        def _compare(self, actual: Any, operator: str, expected: Any) -> bool:
            """Compare actual value against expected using operator."""
            if operator == 'gt':
                return actual > expected
            elif operator == 'gte':
                return actual >= expected
            elif operator == 'lt':
                return actual < expected
            elif operator == 'lte':
                return actual <= expected
            elif operator == 'eq':
                return actual == expected
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False

        def _execute_action(self, action: Action) -> ExecutionResult:
            """
            Execute single action.

            For Week 1, this is a stub that logs the action.
            Week 2-4 will implement actual payer portal automation.
            """
            logger.info(
                f"Executing action: {action.action_type} for rule {action.rule.id}"
            )

            # Stub implementation - Week 2+ will add actual execution
            return ExecutionResult(
                success=True,
                result_type='SUCCESS',
                details={
                    'message': f'Action {action.action_type} executed (stub)',
                    'rule_id': action.rule.id
                },
                execution_time_ms=50
            )

        def _escalate_to_human(self, action: Action, error: Exception):
            """
            Escalate failed action to human operator.

            Creates AlertEvent for human review.
            """
            # Import here to avoid circular dependency
            from upstream.alerts.models import AlertEvent

            AlertEvent.objects.create(
                customer=self.customer,
                alert_type='automation_escalation',
                severity='high',
                title=f"Automation Failed: {action.action_type}",
                description=(
                    f"Automated action failed and requires human review.\n\n"
                    f"Action: {action.action_type}\n"
                    f"Error: {str(error)}\n\n"
                    f"Please review the execution log and take manual action."
                ),
                evidence_payload={
                    'rule_id': action.rule.id,
                    'action_type': action.action_type,
                    'error': str(error),
                    'trigger_event': action.event.payload
                }
            )

            logger.error(f"Action escalated: {action.action_type} - {error}")
    ```

    **Step 3: Add Celery task**

    Add to upstream/tasks.py after existing tasks:

    ```python
    @shared_task(name="upstream.tasks.process_claim_with_automation", base=MonitoredTask)
    def process_claim_with_automation(
        customer_id: int, fhir_payload: Dict[str, Any], source: str
    ) -> Dict[str, Any]:
        """
        Process claim from EHR webhook with autonomous rules evaluation.

        Args:
            customer_id: Customer ID
            fhir_payload: FHIR R4 Claim resource
            source: Ingestion source ('ehr_webhook', 'api', etc.)

        Returns:
            dict: Processing result with risk score and actions taken
        """
        from upstream.models import Customer, ClaimRecord
        from upstream.automation.rules_engine import RulesEngine, Event
        from datetime import datetime

        logger.info(
            f"Processing claim with automation: customer={customer_id}, source={source}"
        )

        try:
            customer = Customer.objects.get(id=customer_id)

            # Parse FHIR payload into ClaimRecord (simplified for Week 1)
            # Full FHIR parsing will be added in Phase 2
            claim_data = {
                'customer': customer,
                'submitted_via': source,
                # TODO: Extract payer, cpt, dates from FHIR payload
                'payer': fhir_payload.get('insurance', [{}])[0].get('coverage', {}).get('display', 'Unknown'),
                'cpt': 'UNKNOWN',  # Extract from item[0].productOrService
                'submitted_date': datetime.now().date(),
                'decided_date': datetime.now().date(),
                'outcome': 'PAID',  # Default until adjudication
            }

            # Create ClaimRecord (stub for Week 1)
            # claim = ClaimRecord.objects.create(**claim_data)

            # Create event for rules engine
            event = Event(
                event_type='claim_submitted',
                customer_id=customer_id,
                payload={
                    'claim_id': 'stub',  # claim.id
                    'payer': claim_data['payer'],
                    'cpt': claim_data['cpt'],
                    'risk_score': 0,  # Placeholder - risk scoring in Week 2
                },
                timestamp=datetime.now()
            )

            # Evaluate rules
            engine = RulesEngine(customer)
            actions = engine.evaluate_event(event)
            results = engine.execute_actions(actions)

            logger.info(
                f"Claim processing complete: customer={customer_id}, "
                f"actions_executed={len(results)}"
            )

            return {
                'customer_id': customer_id,
                'source': source,
                'actions_executed': len(results),
                'status': 'success'
            }

        except Exception as e:
            logger.error(
                f"Error processing claim with automation: customer={customer_id}, "
                f"error={str(e)}"
            )
            raise
    ```

    **Note:** This is a minimal Week 1 implementation. Full claim parsing, risk scoring, and actual payer portal automation will be added in subsequent weeks per 00-MASTER-PLAN.md.
  </action>
  <verify>
    - `ls -la upstream/automation/` shows `__init__.py` and `rules_engine.py`
    - `python -c "from upstream.automation.rules_engine import RulesEngine, Event, Action; print('Import successful')"` succeeds
    - `grep -n "def process_claim_with_automation" upstream/tasks.py` shows task definition
    - `grep -n "@shared_task" upstream/tasks.py` shows task decorator with MonitoredTask base
    - `python manage.py shell -c "from upstream.tasks import process_claim_with_automation; print(process_claim_with_automation.name)"` prints task name
  </verify>
  <done>
    Rules engine framework exists in upstream/automation/rules_engine.py with RulesEngine, Event, Action, ExecutionResult classes. Engine evaluates conditions, executes actions (stub), logs to ExecutionLog, and escalates failures. Celery task process_claim_with_automation exists in upstream/tasks.py, accepts FHIR payload, creates Event, and invokes rules engine.
  </done>
</task>

</tasks>

<verification>
Run all verification checks:

1. **Models exist:** `python manage.py shell -c "from upstream.models import AutomationRule, ExecutionLog, Authorization; print('OK')"` succeeds
2. **Migrations applied:** `python manage.py showmigrations upstream` shows [X] for all four new migrations
3. **ClaimRecord enhanced:** `python manage.py shell -c "from upstream.models import ClaimRecord; print(ClaimRecord._meta.get_field('submitted_via').choices)"` shows tuple of choices
4. **Rules engine imports:** `python -c "from upstream.automation.rules_engine import RulesEngine; print('OK')"` succeeds
5. **Webhook endpoint exists:** `grep -n "def ehr_webhook" upstream/views.py` finds function
6. **Celery task registered:** `python manage.py shell -c "from upstream.tasks import process_claim_with_automation; print(process_claim_with_automation.name)"` prints task name
7. **Database tables created:** `python manage.py dbshell -c "SELECT COUNT(*) FROM upstream_automation_rule;"` returns 0 (empty table exists)

Check for critical wiring:
- EHR webhook calls `process_claim_with_automation.delay()`
- Celery task imports `RulesEngine` from `upstream.automation.rules_engine`
- RulesEngine creates `ExecutionLog` records
</verification>

<success_criteria>
1. Four new models (AutomationRule, ExecutionLog, Authorization) exist in database with proper indexes and constraints
2. ClaimRecord has submitted_via field with choices (csv_upload, ehr_webhook, api, batch_import)
3. EHR webhook endpoint accepts POST requests with FHIR R4 Claim resources and returns 202 Accepted
4. Rules engine framework evaluates conditions using operators (gt, gte, lt, lte, eq)
5. Rules engine logs all executions to ExecutionLog with result (SUCCESS/FAILED/ESCALATED)
6. Rules engine escalates failures to AlertEvent when rule.escalate_on_error=True
7. Celery task process_claim_with_automation queues async processing for webhook claims
8. All code follows existing patterns (CustomerScopedManager, MonitoredTask base, logging)

Deliverable: Foundation for autonomous execution that operates WITHOUT manual approval, ready for Week 2 payer portal RPA implementation.
</success_criteria>

<output>
After completion, create `.planning/quick/022-complete-week-1-tasks-2-7-for-autonomous/022-SUMMARY.md`

Document in summary:
- Four new models and migrations created
- EHR webhook endpoint location and FHIR format expectations
- Rules engine architecture and evaluation flow
- Stub implementations that need completion in Week 2+ (claim parsing, risk scoring, payer portal automation)
- Next steps: Wire URL route for /webhooks/ehr endpoint, implement API key authentication, add FHIR parsing library (fhir.resources)
</output>

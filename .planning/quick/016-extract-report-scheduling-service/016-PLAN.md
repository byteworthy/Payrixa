---
task_id: "016"
type: quick
title: "Extract report scheduling service"
autonomous: true
files_modified:
  - upstream/services/report_scheduler.py
  - upstream/services/__init__.py
  - upstream/tasks.py

must_haves:
  truths:
    - "Report scheduling logic exists in dedicated service layer"
    - "Celery tasks delegate to service methods"
    - "Service is stateless and framework-agnostic"
  artifacts:
    - path: "upstream/services/report_scheduler.py"
      provides: "ReportSchedulerService class with scheduling logic"
      min_lines: 100
      exports: ["ReportSchedulerService"]
    - path: "upstream/services/__init__.py"
      provides: "Service exports including ReportSchedulerService"
      contains: "ReportSchedulerService"
  key_links:
    - from: "upstream/tasks.py"
      to: "upstream/services/report_scheduler.py"
      via: "imports and calls service methods"
      pattern: "from upstream\\.services\\.report_scheduler import ReportSchedulerService"
---

<objective>
Extract report scheduling business logic from Celery tasks into a dedicated service layer.

**Purpose:** Separates async orchestration (Celery) from business logic (service), improving testability and maintainability. Follows established pattern of ReportGenerationService, DataQualityService, and AlertProcessingService.

**Output:** New `services/report_scheduler.py` with stateless, framework-agnostic report scheduling logic. Tasks become thin wrappers that call service methods.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-quick.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@upstream/tasks.py
@upstream/services/report_generation.py
@upstream/services/__init__.py
@upstream/reporting/services.py
@upstream/reporting/models.py

**Existing Pattern:** Services are stateless classes with static methods. They accept domain objects and return structured dicts. Tasks remain thin - they fetch Django models, call service methods, handle exceptions, and return results.

**Current State:** Three report-related tasks in `tasks.py`:
1. `send_scheduled_report_task` - calls `generate_and_send_weekly_report` (doesn't exist!)
2. `compute_report_drift_task` - calls `compute_weekly_payer_drift`, updates ReportRun status
3. `generate_report_artifact_task` - calls `generate_weekly_drift_pdf` or `export_drift_events_csv`

**Goal:** Extract scheduling orchestration (ReportRun creation, status updates, artifact generation coordination) into `ReportSchedulerService`. Keep PDF/CSV generation in `reporting/services.py` (that's artifact generation, not scheduling).
</context>

<tasks>

<task type="auto">
  <name>Create ReportSchedulerService with scheduling logic</name>
  <files>upstream/services/report_scheduler.py</files>
  <action>
Create new service class following established pattern (see ReportGenerationService, DataQualityService).

**Service structure:**
```python
class ReportSchedulerService:
    """
    Stateless service for report scheduling and orchestration.

    Coordinates report run lifecycle:
    - Creating ReportRun records
    - Triggering drift computation
    - Coordinating artifact generation
    - Managing report status transitions

    All methods are static - no instance state.
    """

    @staticmethod
    def schedule_weekly_report(
        customer: Customer,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """
        Schedule a weekly drift report for a customer.

        Creates ReportRun, coordinates drift computation and PDF generation.
        This is the business logic currently in send_scheduled_report_task.

        Returns:
            dict with keys: report_run_id, status, events_detected, artifact_id
        """
        pass

    @staticmethod
    def compute_report_drift(report_run: ReportRun) -> Dict[str, Any]:
        """
        Compute drift events for a report run.

        Coordinates drift computation and updates ReportRun status.
        This is the business logic currently in compute_report_drift_task.

        Returns:
            dict with keys: report_run_id, events_detected, status
        """
        pass

    @staticmethod
    def generate_report_artifact(
        report_run: ReportRun,
        artifact_type: str = "pdf",
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate report artifact (PDF/CSV) for a report run.

        Delegates to reporting/services.py for actual generation.
        This is the business logic currently in generate_report_artifact_task.

        Returns:
            dict with keys: artifact_id, artifact_type, file_path, status
        """
        pass
```

**Implementation details:**
- Import from `upstream.models` (Customer, ReportRun, DriftEvent)
- Import from `upstream.reporting.services` (generate_weekly_drift_pdf, generate_drift_events_csv)
- Import from `upstream.services.payer_drift` (compute_weekly_payer_drift)
- Use logging (logger = logging.getLogger(__name__))
- Return structured dicts, never raise HTTP exceptions
- Handle model DoesNotExist gracefully (return error in dict or let it propagate)
- Follow stateless pattern - all dependencies passed as args

**Note:** `generate_and_send_weekly_report` doesn't exist. Replace with logic that creates ReportRun, computes drift, generates PDF, returns result. No actual email sending (that's TODO for future).
  </action>
  <verify>
```bash
python -c "from upstream.services.report_scheduler import ReportSchedulerService; import inspect; methods = [m for m in dir(ReportSchedulerService) if not m.startswith('_')]; print(f'Methods: {methods}'); assert 'schedule_weekly_report' in methods; assert 'compute_report_drift' in methods; assert 'generate_report_artifact' in methods"
```
  </verify>
  <done>
- `upstream/services/report_scheduler.py` exists with ReportSchedulerService class
- Three public static methods: schedule_weekly_report, compute_report_drift, generate_report_artifact
- Service imports domain models and delegates to existing services
- Follows stateless pattern with structured dict returns
  </done>
</task>

<task type="auto">
  <name>Update service __init__.py and refactor tasks</name>
  <files>upstream/services/__init__.py, upstream/tasks.py</files>
  <action>
**Part 1: Update services/__init__.py**
Add ReportSchedulerService to exports following existing pattern:

```python
from .report_scheduler import ReportSchedulerService

__all__ = [
    "DataQualityService",
    "ReportGenerationService",
    "AlertProcessingService",
    "ReportSchedulerService",  # NEW
]
```

**Part 2: Refactor tasks.py**
Update three report tasks to delegate to service:

1. **send_scheduled_report_task:**
   - Import: `from upstream.services.report_scheduler import ReportSchedulerService`
   - Replace `generate_and_send_weekly_report(customer)` call with:
     ```python
     from datetime import datetime, timedelta
     period_end = datetime.now().date()
     period_start = period_end - timedelta(days=7)
     result = ReportSchedulerService.schedule_weekly_report(
         customer, period_start, period_end
     )
     ```
   - Keep exception handling and logging

2. **compute_report_drift_task:**
   - Import: `from upstream.services.report_scheduler import ReportSchedulerService`
   - Replace inline logic with: `result = ReportSchedulerService.compute_report_drift(report_run)`
   - Remove duplicate status update (service handles it)
   - Keep exception handling and logging

3. **generate_report_artifact_task:**
   - Import: `from upstream.services.report_scheduler import ReportSchedulerService`
   - Replace if/elif artifact logic with: `result = ReportSchedulerService.generate_report_artifact(report_run, artifact_type)`
   - Keep exception handling and logging

**Important:** Tasks remain thin wrappers. They fetch models from IDs, call service methods, log results, return dicts. Don't move Django ORM into tasks - service methods accept model instances.
  </action>
  <verify>
```bash
# Verify service export
python -c "from upstream.services import ReportSchedulerService; print('✓ Service exported')"

# Verify tasks import service
grep -q "from upstream.services.report_scheduler import ReportSchedulerService" /workspaces/codespaces-django/upstream/tasks.py && echo "✓ Tasks import service"

# Verify tasks are thin (no business logic)
python -c "
import ast, sys
with open('/workspaces/codespaces-django/upstream/tasks.py') as f:
    tree = ast.parse(f.read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and 'report' in node.name.lower():
        lines = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])
        print(f'{node.name}: ~{lines} statements')
        if lines > 15:
            print(f'  WARNING: Task may be too complex')
"
```
  </verify>
  <done>
- `upstream/services/__init__.py` exports ReportSchedulerService
- Three report tasks in `tasks.py` import and delegate to ReportSchedulerService
- Tasks remain thin: fetch models, call service, handle exceptions, log, return
- No business logic duplication between tasks and service
  </done>
</task>

<task type="auto">
  <name>Run tests and validate extraction</name>
  <files></files>
  <action>
Run existing test suite to ensure refactor didn't break functionality:

```bash
cd /workspaces/codespaces-django
pytest upstream/tests_celery.py -xvs
```

If tests fail due to missing imports or service method signatures, adjust service implementation to match task expectations.

**Expected:** Tests pass because:
- Service methods return same dict structure as old task logic
- Tasks still fetch models and return results the same way
- Only internal implementation changed (extracted to service)

**If tests fail:** Check error messages for:
- Import errors → verify service exports correctly
- AttributeError → verify service method names match
- TypeError → verify service method signatures accept correct args
- AssertionError → verify service returns expected dict structure
  </action>
  <verify>
```bash
pytest upstream/tests_celery.py -xvs --tb=short 2>&1 | tee /tmp/test_output.txt
grep -E "(PASSED|FAILED|ERROR)" /tmp/test_output.txt | tail -5
```
  </verify>
  <done>
- Celery tests pass or failures are pre-existing (not caused by refactor)
- Tasks successfully call service methods
- Service methods return expected dict structures
- No regressions in report scheduling functionality
  </done>
</task>

</tasks>

<verification>
**Service Layer:**
- [ ] `upstream/services/report_scheduler.py` exists with ReportSchedulerService
- [ ] Service class is stateless with static methods
- [ ] Service follows established pattern (like ReportGenerationService)
- [ ] Service exports: schedule_weekly_report, compute_report_drift, generate_report_artifact

**Integration:**
- [ ] `upstream/services/__init__.py` exports ReportSchedulerService
- [ ] Tasks import from `upstream.services.report_scheduler`
- [ ] Tasks delegate to service methods (thin wrappers)
- [ ] No business logic duplication

**Tests:**
- [ ] Existing Celery tests pass
- [ ] No regressions in report scheduling functionality
</verification>

<success_criteria>
**Measurable outcomes:**
1. `upstream/services/report_scheduler.py` exists with 100+ lines
2. Service class exports 3 static methods
3. `upstream/services/__init__.py` includes ReportSchedulerService in __all__
4. `upstream/tasks.py` imports ReportSchedulerService (grep confirms)
5. Celery tests pass (exit code 0)

**Observable behavior:**
- Report scheduling logic separated from async orchestration
- Service can be tested independently of Celery
- Tasks remain focused on async coordination (fetch model, call service, log, return)
- Follows established service layer pattern in codebase
</success_criteria>

<output>
After completion, create `.planning/quick/016-extract-report-scheduling-service/016-SUMMARY.md` following the standard template with:
- Changes made (new service, refactored tasks)
- Files created/modified
- Testing verification results
- Any issues encountered
</output>

---
phase: quick-002
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - requirements.txt
  - upstream/logging_config.py
  - upstream/logging_utils.py
autonomous: true

must_haves:
  truths:
    - "Production logs output valid JSON format"
    - "JSON logs include all structured context fields"
    - "Development logs remain human-readable"
  artifacts:
    - path: "requirements.txt"
      provides: "python-json-logger dependency"
      contains: "python-json-logger"
    - path: "upstream/logging_config.py"
      provides: "JSON formatter configuration"
      contains: "pythonjsonlogger"
    - path: "upstream/logging_utils.py"
      provides: "JSONLogFormatter class"
      min_lines: 30
  key_links:
    - from: "upstream/logging_config.py"
      to: "upstream.logging_utils.JSONLogFormatter"
      via: "formatter configuration"
      pattern: "JSONLogFormatter"
---

<objective>
Enable structured JSON logging for production observability using python-json-logger library.

Purpose: Replace custom key=value formatter with industry-standard JSON format that integrates seamlessly with CloudWatch, Datadog, ELK, and other log aggregation tools.

Output: JSON-formatted logs in production with backward-compatible human-readable logs in development.
</objective>

<execution_context>
@/home/codespace/.claude/get-shit-done/workflows/execute-plan.md
@/home/codespace/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@/workspaces/codespaces-django/.planning/PROJECT.md
@/workspaces/codespaces-django/.planning/STATE.md
@/workspaces/codespaces-django/requirements.txt
@/workspaces/codespaces-django/upstream/settings/base.py
@/workspaces/codespaces-django/upstream/settings/prod.py
@/workspaces/codespaces-django/upstream/logging_config.py
@/workspaces/codespaces-django/upstream/logging_utils.py
@/workspaces/codespaces-django/upstream/logging_filters.py

**Current State:**
- Custom `StructuredLogFormatter` outputs key=value format
- Logging config uses environment-specific formatters
- PHI scrubbing filters already in place (HIPAA-compliant)
- Production uses `AggressivePHIScrubberFilter`, dev uses `SelectivePHIScrubberFilter`

**Technical Context:**
- Django 5.2 + PostgreSQL production environment
- HIPAA-compliant PHI scrubbing required on all log output
- Multi-tenant SaaS with customer isolation
- Logs include: request_id, customer_id, user_id, service_name, task_name
</context>

<tasks>

<task type="auto">
  <name>Install python-json-logger and create JSON formatter</name>
  <files>
    requirements.txt
    upstream/logging_utils.py
  </files>
  <action>
Add python-json-logger to requirements.txt:
- Add line `python-json-logger~=2.0.7` after django-auditlog line
- Use ~= for compatible version upgrades within 2.0.x

Create JSONLogFormatter in upstream/logging_utils.py:
- Import: `from pythonjsonlogger import jsonlogger`
- Create new class `JSONLogFormatter(jsonlogger.JsonFormatter)` after StructuredLogFormatter
- Override `add_fields()` method to inject context fields
- Include fields: timestamp, level, logger, message, customer_id, user_id, request_id, method, path, service_name, task_name
- Format timestamp as ISO 8601: `record.created` → `datetime.fromtimestamp(record.created).isoformat()`
- Preserve exception formatting with `exc_info` field
- Add docstring explaining usage and example JSON output

Implementation pattern:
```python
class JSONLogFormatter(jsonlogger.JsonFormatter):
    """
    JSON log formatter for production observability.

    Outputs logs in JSON format compatible with CloudWatch, Datadog, ELK.
    Automatically includes context fields from ContextualLoggerAdapter.

    Example output:
        {
          "timestamp": "2024-01-28T10:30:45.123456",
          "level": "INFO",
          "logger": "upstream.services",
          "message": "Upload complete",
          "customer_id": 123,
          "user_id": 456,
          "request_id": "abc-def-123"
        }
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Add ISO 8601 timestamp
        # Add context fields if present
        # Ensure consistent field names
```

Do NOT modify StructuredLogFormatter - keep it for development use.
  </action>
  <verify>
Run: `grep "python-json-logger" requirements.txt` (shows package)
Run: `grep "class JSONLogFormatter" upstream/logging_utils.py` (shows new class)
Run: `python -c "from pythonjsonlogger import jsonlogger; print('OK')"` after pip install
  </verify>
  <done>
- python-json-logger~=2.0.7 in requirements.txt
- JSONLogFormatter class exists in logging_utils.py
- Class inherits from jsonlogger.JsonFormatter
- add_fields() method handles context injection
- Docstring with example JSON output present
  </done>
</task>

<task type="auto">
  <name>Configure production to use JSON formatter</name>
  <files>
    upstream/logging_config.py
  </files>
  <action>
Update get_logging_config() in upstream/logging_config.py:

1. Add json_structured formatter to config["formatters"]:
```python
"json_structured": {
    "()": "upstream.logging_utils.JSONLogFormatter",
    "format": "%(timestamp)s %(level)s %(name)s %(message)s",
},
```

2. Modify handler formatter selection based on environment:
- Production environment: Use `json_structured` formatter for all file handlers (app_file, error_file, audit_file, security_file, performance_file)
- Console handler in production: Use `json_structured` (CloudWatch/Docker logs)
- Development/test: Keep existing `structured` formatter (human-readable)

Implementation:
```python
# After creating formatters dict, conditionally set handler formatters:
if environment == "production":
    formatter_name = "json_structured"
else:
    formatter_name = "structured"

# Then use formatter_name in handlers:
"console": {
    "class": "logging.StreamHandler",
    "level": log_level,
    "formatter": formatter_name,  # JSON in prod, key=value in dev
    "filters": ["phi_scrubber"],
},
```

Apply same pattern to all file handlers. Audit logs can use json_structured in all environments (machine-readable is appropriate).

Do NOT change phi_scrubber filters - PHI scrubbing must happen before JSON serialization.
  </action>
  <verify>
Run: `grep "json_structured" upstream/logging_config.py` (shows formatter config)
Run: `python manage.py check --settings=upstream.settings.prod` (validates config)
Create test script to log sample message and verify JSON output:
```python
import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'upstream.settings.prod'
import django
django.setup()
logger = logging.getLogger('upstream')
logger.info("Test JSON logging", extra={'test_field': 'value'})
```
  </verify>
  <done>
- json_structured formatter defined in logging_config.py
- Production environment uses JSON formatter for console and file handlers
- Development/test environments use structured (key=value) formatter
- PHI scrubbing filters still applied before JSON serialization
- Django check passes with prod settings
  </done>
</task>

<task type="auto">
  <name>Update documentation and validate JSON output</name>
  <files>
    upstream/logging_utils.py
    upstream/logging_config.py
  </files>
  <action>
Update module docstrings to document JSON logging:

1. In upstream/logging_utils.py module docstring:
- Add section "JSON Logging (Production)" after existing usage examples
- Show example of JSON output format
- Document that production uses JSONLogFormatter, dev uses StructuredLogFormatter
- Note that PHI scrubbing happens before JSON serialization

2. In upstream/logging_config.py module docstring:
- Update line "- Structured logging for log aggregation tools" to mention JSON format in production
- Add bullet: "- JSON-formatted logs in production (CloudWatch, Datadog, ELK compatible)"

3. Add example usage in JSONLogFormatter docstring:
```python
"""
Example output in production:
    {
      "timestamp": "2024-01-28T10:30:45.123456",
      "level": "INFO",
      "logger": "upstream.services.payer_drift",
      "message": "Drift computation complete",
      "customer_id": 123,
      "user_id": 456,
      "request_id": "abc-def-123",
      "service_name": "payer_drift",
      "events_created": 15
    }

Note: All PHI/PII is scrubbed before JSON serialization via PHIScrubberFilter.
"""
```

Create manual validation test:
- Run Django shell with prod settings
- Import logger and log test message with extra fields
- Verify JSON output includes all context fields
- Verify timestamp is ISO 8601 format
- Verify PHI scrubbing still works (test with fake SSN)

No functional changes - documentation only.
  </action>
  <verify>
Run: `grep "JSON Logging" upstream/logging_utils.py` (shows new section)
Run: `grep "JSON-formatted logs" upstream/logging_config.py` (updated)
Manual test in Django shell:
```python
from upstream.logging_utils import get_logger, set_log_context
logger = get_logger(__name__)
set_log_context(customer_id=123, user_id=456)
logger.info("Test message", extra={'test_ssn': '123-45-6789'})
# Verify JSON output, verify SSN is [REDACTED_SSN]
```
  </verify>
  <done>
- logging_utils.py docstring includes JSON logging section
- logging_config.py docstring mentions JSON format in production
- JSONLogFormatter has detailed usage example
- Manual validation confirms JSON output works
- PHI scrubbing verified in JSON format
  </done>
</task>

</tasks>

<verification>
Run full test suite to ensure logging still works:
```bash
python manage.py test upstream.tests_logging --settings=upstream.settings.test
```

Verify no regressions in existing logging functionality:
- PHI scrubbing still active (check with fake SSN in log message)
- Context fields still propagate (request_id, customer_id, user_id)
- Different formatters in different environments (dev vs prod)

Check that JSON is valid:
```bash
# In prod settings, log message should output valid JSON that can be parsed
python -c "import json; import sys; json.loads(sys.stdin.read())" < sample_log_output.json
```
</verification>

<success_criteria>
- python-json-logger package installed and importable
- JSONLogFormatter class exists and inherits from jsonlogger.JsonFormatter
- Production environment outputs valid JSON to console and files
- Development environment still uses human-readable key=value format
- PHI scrubbing filters applied before JSON serialization
- All context fields (request_id, customer_id, user_id, etc.) included in JSON output
- Timestamps in ISO 8601 format
- Django check passes for prod settings
- Existing logging tests pass
- Documentation updated with JSON logging examples
</success_criteria>

<output>
After completion, create `.planning/quick/002-enable-structured-json-logging-for-bett/002-SUMMARY.md`
</output>

# Log Retention Policy

This directory contains application logs with automatic rotation and HIPAA-compliant retention policies.

## Log Files

### Application Logs

- **app.log** - General application logs (INFO and above)
  - Rotation: Daily at midnight
  - Retention: 30 days
  - Format: Structured logging with PHI scrubbing

- **error.log** - Error and warning logs (WARNING and above)
  - Rotation: Daily at midnight
  - Retention: 90 days
  - Format: Structured logging with PHI scrubbing

- **audit.log** - Audit trail logs (HIPAA compliance)
  - Rotation: Daily at midnight
  - Retention: 2555 days (7 years)
  - Format: Audit format with timestamp
  - **CRITICAL**: This log contains HIPAA audit trail data and MUST be retained for 7 years

- **security.log** - Authentication and authorization logs
  - Rotation: Daily at midnight
  - Retention: 90 days
  - Format: Structured logging with PHI scrubbing

- **performance.log** - Performance monitoring logs
  - Rotation: Daily at midnight
  - Retention: 30 days
  - Format: Structured logging with PHI scrubbing

### Development-Only Logs

- **debug.log** - Debug-level logs (development environment only)
  - Rotation: When file reaches 10 MB
  - Retention: 7 days
  - Format: Verbose logging with full context

## Retention Policies

Our retention policies are designed to balance operational needs with HIPAA compliance requirements:

| Log Level | Retention Period | Justification |
|-----------|------------------|---------------|
| DEBUG     | 7 days           | Verbose logs for active development only |
| INFO      | 30 days          | Standard operational logs for recent troubleshooting |
| WARNING   | 90 days          | Extended retention for potential issue investigation |
| ERROR     | 90 days          | Extended retention for debugging and root cause analysis |
| AUDIT     | 7 years (2555 days) | HIPAA requirement for audit trail retention |

## PHI/PII Scrubbing

All log handlers automatically scrub Protected Health Information (PHI) and Personally Identifiable Information (PII) before writing to disk. This includes:

- Social Security Numbers (SSN)
- Medical Record Numbers (MRN)
- Dates of Birth (DOB)
- Phone numbers
- Email addresses
- Patient names
- Physical addresses
- Credit card numbers
- IP addresses (production only)

**Example**:
```
Input:  "Processing claim for patient John Doe, SSN 123-45-6789"
Output: "Processing claim for patient [REDACTED_NAME], SSN [REDACTED_SSN]"
```

## Log Format

Logs use structured formatting for easy parsing by log aggregation tools (CloudWatch, Datadog, ELK, etc.):

```
2024-01-28 10:30:45 INFO customer_id=123 user_id=456 request_id=abc message="Upload complete"
```

## Management Commands

### Show Log Statistics

Display current log file statistics:

```bash
python manage.py log_stats
```

**Output**:
- Total number of log files
- Total disk usage
- Breakdown by log type
- Oldest and newest log files
- Retention policies

### Clean Up Old Logs

Delete log files that exceed their retention period:

```bash
# Dry run (show what would be deleted)
python manage.py cleanup_logs --dry-run

# Actually delete old logs
python manage.py cleanup_logs
```

**What it does**:
- Scans all log files
- Deletes files older than their retention period
- Reports space freed
- Respects audit log 7-year retention

### Archive Old Logs

Compress log files to save disk space:

```bash
# Dry run (show what would be archived)
python manage.py archive_logs --dry-run

# Actually archive logs
python manage.py archive_logs
```

**What it does**:
- Compresses log files older than 7 days using gzip
- Moves compressed files to `logs/archive/` directory
- Typical compression ratio: 90-95% size reduction
- Maintains HIPAA compliance for audit logs

## Automated Maintenance

For production deployments, schedule these commands as cron jobs:

```bash
# Daily log archival (compress logs older than 7 days)
0 2 * * * cd /app && python manage.py archive_logs

# Weekly log cleanup (delete logs past retention period)
0 3 * * 0 cd /app && python manage.py cleanup_logs

# Daily log statistics (monitoring)
0 1 * * * cd /app && python manage.py log_stats
```

Or use Celery Beat for scheduled tasks:

```python
# In settings.py CELERY_BEAT_SCHEDULE:
'daily-log-archival': {
    'task': 'upstream.tasks.archive_logs',
    'schedule': crontab(hour=2, minute=0),
},
'weekly-log-cleanup': {
    'task': 'upstream.tasks.cleanup_logs',
    'schedule': crontab(day_of_week='sunday', hour=3, minute=0),
},
```

## HIPAA Compliance Notes

### Audit Log Requirements

HIPAA requires retaining audit logs for **6 years from the date of creation or the date when it was last in effect, whichever is later**. We conservatively use 7 years (2555 days) to ensure compliance.

Audit logs must include:
- Who accessed PHI
- When PHI was accessed
- What PHI was accessed
- What actions were performed

### Secure Storage

- All logs are stored with appropriate file permissions (600 - owner read/write only)
- Log files are automatically scrubbed of PHI/PII before writing to disk
- Archived logs (compressed) maintain the same security controls
- Logs should be backed up to secure, encrypted storage (e.g., AWS S3 with encryption)

### Log Transmission

When transmitting logs to aggregation services:
- Use encrypted connections (TLS 1.2+)
- Ensure PHI scrubbing is applied before transmission
- Choose HIPAA-compliant log aggregation providers
- Sign Business Associate Agreements (BAA) with providers

## Troubleshooting

### Disk Space Issues

If logs are consuming too much disk space:

1. Check current usage:
   ```bash
   python manage.py log_stats
   ```

2. Archive old logs to compress them:
   ```bash
   python manage.py archive_logs
   ```

3. Clean up logs past retention period:
   ```bash
   python manage.py cleanup_logs
   ```

4. Review log levels in production (ensure DEBUG is disabled)

### Missing Logs

If logs are not being written:

1. Check logs directory permissions:
   ```bash
   ls -la logs/
   ```

2. Verify logging configuration:
   ```python
   from django.conf import settings
   print(settings.LOGGING)
   ```

3. Check for errors in console output
4. Verify disk space is available

### PHI Leakage

If PHI appears in logs:

1. **IMMEDIATELY** delete the log file containing PHI
2. Review the code that logged the PHI
3. Add proper PHI scrubbing or avoid logging sensitive fields
4. Test PHI scrubbing with:
   ```python
   from upstream.logging_filters import is_phi_present
   is_phi_present("Patient SSN: 123-45-6789")  # Should return True
   ```
5. Report incident per HIPAA breach notification rules

## Environment-Specific Configuration

### Development

- Log level: DEBUG
- PHI scrubber: Selective (allows some debugging info)
- Console output: Enabled with verbose formatting
- File output: All log types including debug.log

### Production

- Log level: INFO
- PHI scrubber: Aggressive (maximum security)
- Console output: Structured logging only
- File output: app.log, error.log, audit.log, security.log, performance.log
- Recommended: Send logs to external aggregation service (CloudWatch, Datadog)

## Related Documentation

- [HIPAA Audit Logging Requirements](https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html)
- [Django Logging Documentation](https://docs.djangoproject.com/en/stable/topics/logging/)
- [Python Logging Handlers](https://docs.python.org/3/library/logging.handlers.html)
- [upstream/logging_utils.py](../upstream/logging_utils.py) - Structured logging utilities
- [upstream/logging_filters.py](../upstream/logging_filters.py) - PHI scrubbing filters
- [upstream/logging_config.py](../upstream/logging_config.py) - Centralized logging configuration

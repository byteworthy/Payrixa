"""
Centralized logging configuration with retention policies and PHI scrubbing.

This module provides HIPAA-compliant logging configuration with:
- Automatic log rotation based on size and time
- Retention policies for different log levels
- PHI/PII scrubbing on all handlers
- Structured logging for log aggregation tools
- JSON-formatted logs in production (CloudWatch, Datadog, ELK compatible)
- Environment-specific configurations

Retention Policies (HIPAA-aligned):
- DEBUG logs: 7 days (development only)
- INFO logs: 30 days
- WARNING logs: 90 days
- ERROR logs: 90 days
- CRITICAL logs: 90 days
- Audit logs: 7 years (HIPAA requirement)

Related: TECH-DEBT Phase 3 - DevOps Monitoring & Metrics
"""

from pathlib import Path
from typing import Dict, Any


def get_log_retention_days(log_level: str) -> int:
    """
    Get retention period in days for a log level.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        int: Number of days to retain logs
    """
    retention_map = {
        "DEBUG": 7,  # Short retention for verbose dev logs
        "INFO": 30,  # Standard retention for operational logs
        "WARNING": 90,  # Extended retention for potential issues
        "ERROR": 90,  # Extended retention for troubleshooting
        "CRITICAL": 90,  # Extended retention for critical incidents
    }
    return retention_map.get(log_level.upper(), 30)


def get_logging_config(
    base_dir: Path,
    environment: str = "production",
    log_level: str = "INFO",
) -> Dict[str, Any]:
    """
    Generate logging configuration dict for Django LOGGING setting.

    Args:
        base_dir: Django BASE_DIR path
        environment: Environment name ('production', 'development', 'test')
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Dict: Django LOGGING configuration
    """
    # Create logs directory structure
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    # Archive directory for rotated logs
    archive_dir = log_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    # Determine PHI scrubber based on environment
    if environment == "production":
        phi_scrubber = "upstream.logging_filters.AggressivePHIScrubberFilter"
    elif environment == "development":
        phi_scrubber = "upstream.logging_filters.SelectivePHIScrubberFilter"
    else:  # test
        phi_scrubber = "upstream.logging_filters.SelectivePHIScrubberFilter"

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        # =============================================================================
        # FILTERS: PHI/PII Scrubbing (HIPAA Compliance)
        # =============================================================================
        "filters": {
            "phi_scrubber": {
                "()": phi_scrubber,
            },
        },
        # =============================================================================
        # FORMATTERS: Structured Logging
        # =============================================================================
        "formatters": {
            "verbose": {
                "format": (
                    "{levelname} {asctime} {module} {process:d} " "{thread:d} {message}"
                ),
                "style": "{",
            },
            "structured": {
                "()": "upstream.logging_utils.StructuredLogFormatter",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json_structured": {
                "()": "upstream.logging_utils.JSONLogFormatter",
                "format": "%(timestamp)s %(level)s %(name)s %(message)s",
            },
            "audit": {
                "format": "{asctime} | {levelname} | {name} | {message}",
                "style": "{",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
    }

    # Determine formatter based on environment
    # Production: JSON for machine parsing (CloudWatch, Datadog, ELK)
    # Development/Test: Structured key=value for human readability
    if environment == "production":
        formatter_name = "json_structured"
    else:
        formatter_name = "structured"

    # Audit logs use JSON in all environments (machine-readable)
    audit_formatter = "json_structured"

    # =============================================================================
    # HANDLERS: File Rotation and Console Output
    # =============================================================================
    config["handlers"] = {
        # Console handler (stdout) - for all logs
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": formatter_name,
            "filters": ["phi_scrubber"],
        },
        # General application logs (INFO and above)
        # Rotates daily at midnight, keeps 30 days
        "app_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "app.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": get_log_retention_days("INFO"),
            "formatter": formatter_name,
            "filters": ["phi_scrubber"],
            "level": "INFO",
            "encoding": "utf-8",
        },
        # Error logs (WARNING and above)
        # Rotates daily, keeps 90 days
        "error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "error.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": get_log_retention_days("ERROR"),
            "formatter": formatter_name,
            "filters": ["phi_scrubber"],
            "level": "WARNING",
            "encoding": "utf-8",
        },
        # Audit logs (HIPAA compliance - 7 year retention required)
        # Rotates daily, keeps 2555 days (7 years)
        # Note: In production, use log aggregation service for long-term storage
        "audit_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "audit.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 2555,  # 7 years for HIPAA compliance
            "formatter": audit_formatter,
            "filters": ["phi_scrubber"],
            "level": "INFO",
            "encoding": "utf-8",
        },
        # Security logs (authentication, authorization, access control)
        # Rotates daily, keeps 90 days
        "security_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "security.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": get_log_retention_days("WARNING"),
            "formatter": formatter_name,
            "filters": ["phi_scrubber"],
            "level": "INFO",
            "encoding": "utf-8",
        },
        # Performance logs (slow queries, high latency, etc.)
        # Rotates daily, keeps 30 days
        "performance_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(log_dir / "performance.log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": get_log_retention_days("INFO"),
            "formatter": formatter_name,
            "filters": ["phi_scrubber"],
            "level": "INFO",
            "encoding": "utf-8",
        },
    }

    # =============================================================================
    # LOGGERS: Application and Third-Party
    # =============================================================================
    config["loggers"] = {
        # Django core logs
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": log_level,
            "propagate": False,
        },
        # Django request logs (includes middleware, views, etc.)
        "django.request": {
            "handlers": ["console", "error_file", "security_file"],
            "level": "WARNING",  # Log failed requests
            "propagate": False,
        },
        # Django database queries
        "django.db.backends": {
            "handlers": ["console"] if environment == "development" else [],
            "level": "DEBUG" if environment == "development" else "INFO",
            "propagate": False,
        },
        # Django security logs
        "django.security": {
            "handlers": ["console", "security_file"],
            "level": "WARNING",
            "propagate": False,
        },
        # Upstream application logs
        "upstream": {
            "handlers": ["console", "app_file", "error_file"],
            "level": log_level,
            "propagate": False,
        },
        # Upstream services (drift detection, alerts, etc.)
        "upstream.services": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Upstream tasks (Celery background jobs)
        "upstream.tasks": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Audit logging (HIPAA compliance)
        "auditlog": {
            "handlers": ["console", "audit_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Authentication and authorization
        "upstream.authentication": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },
        "upstream.permissions": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Performance monitoring
        "upstream.performance": {
            "handlers": ["console", "performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Third-party libraries (reduce noise)
        "celery": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },
        "urllib3": {
            "handlers": ["console"],
            "level": "WARNING",  # Reduce noise from HTTP requests
            "propagate": False,
        },
        "boto3": {
            "handlers": ["console"],
            "level": "WARNING",  # Reduce noise from AWS SDK
            "propagate": False,
        },
        "botocore": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    }

    # =============================================================================
    # ROOT LOGGER: Catch-all for unconfigured loggers
    # =============================================================================
    config["root"] = {
        "handlers": ["console", "app_file", "error_file"],
        "level": log_level,
    }

    # Development-specific: Add debug handler
    if environment == "development":
        config["handlers"]["debug_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_dir / "debug.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": get_log_retention_days("DEBUG"),
            "formatter": "verbose",
            "filters": ["phi_scrubber"],
            "level": "DEBUG",
            "encoding": "utf-8",
        }
        # Add debug handler to upstream logger
        config["loggers"]["upstream"]["handlers"].append("debug_file")

    return config


def cleanup_old_logs(log_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Clean up old log files based on retention policies.

    This function is called by the management command:
        python manage.py cleanup_logs

    Args:
        log_dir: Directory containing log files
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with cleanup statistics
    """
    import time

    stats = {
        "files_deleted": 0,
        "bytes_freed": 0,
        "files_archived": 0,
        "errors": [],
    }

    # Current time
    now = time.time()

    # Patterns for log files and their retention policies
    log_patterns = {
        "debug.log": get_log_retention_days("DEBUG"),
        "app.log": get_log_retention_days("INFO"),
        "error.log": get_log_retention_days("ERROR"),
        "security.log": get_log_retention_days("WARNING"),
        "performance.log": get_log_retention_days("INFO"),
        # Audit logs are kept for 7 years (handled by TimedRotatingFileHandler)
    }

    for log_pattern, retention_days in log_patterns.items():
        # Find rotated log files (e.g., app.log.2024-01-15)
        pattern_base = log_pattern.replace(".log", "")
        for log_file in log_dir.glob(f"{pattern_base}.log.*"):
            try:
                # Get file modification time
                file_age_seconds = now - log_file.stat().st_mtime
                file_age_days = file_age_seconds / (24 * 3600)

                # Delete if older than retention period
                if file_age_days > retention_days:
                    file_size = log_file.stat().st_size

                    if not dry_run:
                        log_file.unlink()

                    stats["files_deleted"] += 1
                    stats["bytes_freed"] += file_size
            except Exception as e:
                stats["errors"].append(f"Error processing {log_file}: {str(e)}")

    return stats


# =============================================================================
# ARCHIVAL STRATEGY
# =============================================================================


def archive_logs(
    log_dir: Path, archive_dir: Path, dry_run: bool = False
) -> Dict[str, Any]:
    """
    Archive old log files by compressing them.

    This function compresses log files older than 7 days to save disk space
    while maintaining HIPAA compliance.

    Args:
        log_dir: Directory containing current log files
        archive_dir: Directory to store compressed archives
        dry_run: If True, only report what would be archived

    Returns:
        Dict with archival statistics
    """
    import gzip
    import shutil
    import time

    stats = {
        "files_archived": 0,
        "bytes_before": 0,
        "bytes_after": 0,
        "compression_ratio": 0.0,
        "errors": [],
    }

    now = time.time()
    archive_threshold_days = 7  # Compress logs older than 7 days

    # Find rotated log files
    for log_file in log_dir.glob("*.log.*"):
        try:
            # Skip if already compressed
            if log_file.suffix == ".gz":
                continue

            # Check file age
            file_age_seconds = now - log_file.stat().st_mtime
            file_age_days = file_age_seconds / (24 * 3600)

            if file_age_days > archive_threshold_days:
                # Compress and move to archive
                archive_file = archive_dir / f"{log_file.name}.gz"

                if not dry_run:
                    with open(log_file, "rb") as f_in:
                        with gzip.open(archive_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Verify compressed file exists before deleting original
                    if archive_file.exists():
                        original_size = log_file.stat().st_size
                        compressed_size = archive_file.stat().st_size

                        log_file.unlink()

                        stats["files_archived"] += 1
                        stats["bytes_before"] += original_size
                        stats["bytes_after"] += compressed_size
                else:
                    # Dry run - just collect stats
                    stats["files_archived"] += 1
                    stats["bytes_before"] += log_file.stat().st_size

        except Exception as e:
            stats["errors"].append(f"Error archiving {log_file}: {str(e)}")

    # Calculate compression ratio
    if stats["bytes_before"] > 0:
        stats["compression_ratio"] = (
            1.0 - (stats["bytes_after"] / stats["bytes_before"])
        ) * 100

    return stats


# =============================================================================
# MANAGEMENT COMMAND HELPER
# =============================================================================


def get_log_statistics(log_dir: Path) -> Dict[str, Any]:
    """
    Get statistics about current log files.

    Used by management command:
        python manage.py log_stats

    Args:
        log_dir: Directory containing log files

    Returns:
        Dict with log statistics
    """
    from datetime import datetime

    stats = {
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0.0,
        "files_by_type": {},
        "oldest_log": None,
        "newest_log": None,
    }

    oldest_time = None
    newest_time = None

    for log_file in log_dir.glob("*.log*"):
        if log_file.is_file():
            stats["total_files"] += 1
            file_size = log_file.stat().st_size
            stats["total_size_bytes"] += file_size

            # Track by file type
            log_type = log_file.stem.split(".")[
                0
            ]  # Get base name (e.g., "app" from "app.log.2024-01-15")
            if log_type not in stats["files_by_type"]:
                stats["files_by_type"][log_type] = {
                    "count": 0,
                    "size_bytes": 0,
                }
            stats["files_by_type"][log_type]["count"] += 1
            stats["files_by_type"][log_type]["size_bytes"] += file_size

            # Track oldest and newest
            file_time = log_file.stat().st_mtime
            if oldest_time is None or file_time < oldest_time:
                oldest_time = file_time
                stats["oldest_log"] = {
                    "name": log_file.name,
                    "date": datetime.fromtimestamp(file_time).isoformat(),
                }
            if newest_time is None or file_time > newest_time:
                newest_time = file_time
                stats["newest_log"] = {
                    "name": log_file.name,
                    "date": datetime.fromtimestamp(file_time).isoformat(),
                }

    stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)

    return stats

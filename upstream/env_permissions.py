"""
.env File Permission Security Validator

This module provides security validation for .env file permissions to prevent
exposure of sensitive credentials including:
- FIELD_ENCRYPTION_KEY (PHI encryption - HIPAA compliance)
- SECRET_KEY (Django session security)
- DB_PASSWORD (database credentials)

HIPAA Compliance: Implements 45 CFR 164.312(a)(2)(iv) requirement for
protecting encryption keys used for ePHI.
"""

import logging
import os
import stat
from pathlib import Path

logger = logging.getLogger(__name__)


def is_ci_environment() -> bool:
    """
    Detect if running in a CI/CD environment.

    Returns:
        bool: True if running in CI (GitHub Actions, GitLab CI, etc.)
    """
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "JENKINS_HOME",
        "BUILDKITE",
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)


def get_permission_mode(file_path: Path) -> int:
    """
    Get the file permission mode.

    Args:
        file_path: Path to the file

    Returns:
        int: File permission mode (st_mode)
    """
    return file_path.stat().st_mode


def check_env_permissions(env_path: Path, strict: bool = True) -> None:
    """
    Validate .env file permissions for security compliance.

    Args:
        env_path: Path to the .env file
        strict: If True, raise exception on insecure permissions (production).
                If False, log warning only (development).

    Raises:
        ImproperlyConfigured: If permissions are insecure and strict=True

    Behavior:
        - Skips check if .env file doesn't exist (Docker/Cloud Run use env vars)
        - Skips check in CI environments (use environment variables)
        - Requires 600 (owner-only) permissions
        - Rejects any group or other access (read/write/execute)
    """
    from django.core.exceptions import ImproperlyConfigured

    # Skip if .env doesn't exist (Docker, Cloud Run use environment variables)
    if not env_path.exists():
        logger.debug(f".env file not found at {env_path}, skipping permission check")
        return

    # Skip in CI environments (they use environment variables)
    if is_ci_environment():
        logger.debug("CI environment detected, skipping .env permission check")
        return

    # Get file permissions
    mode = get_permission_mode(env_path)

    # Check for group permissions (read/write/execute)
    has_group_access = bool(mode & stat.S_IRWXG)

    # Check for other permissions (read/write/execute)
    has_other_access = bool(mode & stat.S_IRWXO)

    # Determine if permissions are insecure
    if has_group_access or has_other_access:
        # Format current permissions in octal (e.g., "666")
        current_perms = oct(stat.S_IMODE(mode))[-3:]

        error_msg = (
            f"SECURITY ERROR: .env file has insecure permissions ({current_perms}). "
            f"This exposes sensitive credentials including:\n"
            f"  - FIELD_ENCRYPTION_KEY (PHI encryption - HIPAA violation)\n"
            f"  - SECRET_KEY (Django session security)\n"
            f"  - DB_PASSWORD (database credentials)\n\n"
            f"FIX: Run 'chmod 600 {env_path}' immediately.\n\n"
            f"HIPAA Compliance: 45 CFR 164.312(a)(2)(iv) requires protection of "
            f"encryption keys used for ePHI."
        )

        if strict:
            # Production: Block application startup
            raise ImproperlyConfigured(error_msg)
        else:
            # Development: Warn but allow startup
            logger.warning(error_msg)
    else:
        # Permissions are secure
        current_perms = oct(stat.S_IMODE(mode))[-3:]
        logger.debug(f".env file has secure permissions: {current_perms}")

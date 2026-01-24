#!/usr/bin/env python3
"""
Production Settings Validator for Upstream

Validates that all required environment variables and security settings
are properly configured before production deployment.

Usage:
    python scripts/validate_production_settings.py

Exit codes:
    0 - All validations passed
    1 - Critical security issues found
    2 - Configuration warnings (can proceed with caution)
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'upstream.settings.prod')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from io import StringIO


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ValidationResult:
    """Result of a validation check."""
    def __init__(self, name, status, message, severity='error'):
        self.name = name
        self.status = status  # 'pass', 'fail', 'warn'
        self.message = message
        self.severity = severity  # 'critical', 'error', 'warning', 'info'


class ProductionValidator:
    """Validates production settings and configuration."""

    def __init__(self):
        self.results = []
        self.critical_failures = 0
        self.errors = 0
        self.warnings = 0

    def check(self, name, condition, pass_msg, fail_msg, severity='error'):
        """Perform a validation check."""
        if condition:
            self.results.append(ValidationResult(name, 'pass', pass_msg, severity))
        else:
            self.results.append(ValidationResult(name, 'fail', fail_msg, severity))
            if severity == 'critical':
                self.critical_failures += 1
            elif severity == 'error':
                self.errors += 1
            elif severity == 'warning':
                self.warnings += 1

    def warn(self, name, condition, pass_msg, warn_msg):
        """Perform a warning check."""
        if condition:
            self.results.append(ValidationResult(name, 'pass', pass_msg, 'info'))
        else:
            self.results.append(ValidationResult(name, 'warn', warn_msg, 'warning'))
            self.warnings += 1

    def validate_all(self):
        """Run all validation checks."""
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}Upstream Production Settings Validation{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        self.validate_django_core()
        self.validate_security()
        self.validate_database()
        self.validate_cache()
        self.validate_email()
        self.validate_phi_compliance()
        self.validate_deployment_checks()

        self.print_results()
        return self.get_exit_code()

    def validate_django_core(self):
        """Validate core Django settings."""
        print(f"{Colors.BLUE}🔍 Validating Core Django Settings...{Colors.END}")

        # DEBUG must be False
        self.check(
            "DEBUG Mode",
            not settings.DEBUG,
            "DEBUG is correctly set to False",
            "CRITICAL: DEBUG is True! Never deploy with DEBUG=True",
            severity='critical'
        )

        # SECRET_KEY must be strong
        self.check(
            "SECRET_KEY Strength",
            len(settings.SECRET_KEY) >= 50 and not settings.SECRET_KEY.startswith('django-insecure'),
            f"SECRET_KEY is strong ({len(settings.SECRET_KEY)} characters)",
            f"CRITICAL: SECRET_KEY is weak ({len(settings.SECRET_KEY)} chars). Generate a new one!",
            severity='critical'
        )

        # ALLOWED_HOSTS must be set
        self.check(
            "ALLOWED_HOSTS",
            len(settings.ALLOWED_HOSTS) > 0 and '*' not in settings.ALLOWED_HOSTS,
            f"ALLOWED_HOSTS configured: {', '.join(settings.ALLOWED_HOSTS)}",
            "CRITICAL: ALLOWED_HOSTS not configured or contains wildcard",
            severity='critical'
        )

        print()

    def validate_security(self):
        """Validate security settings."""
        print(f"{Colors.BLUE}🔒 Validating Security Settings...{Colors.END}")

        # HTTPS/SSL
        self.check(
            "HTTPS Redirect",
            settings.SECURE_SSL_REDIRECT,
            "HTTPS redirect enabled",
            "ERROR: SECURE_SSL_REDIRECT is False. HTTPS should be enforced!",
            severity='error'
        )

        self.check(
            "Secure Session Cookie",
            settings.SESSION_COOKIE_SECURE,
            "Session cookies are secure (HTTPS only)",
            "ERROR: SESSION_COOKIE_SECURE is False. Cookies can be intercepted!",
            severity='error'
        )

        self.check(
            "Secure CSRF Cookie",
            settings.CSRF_COOKIE_SECURE,
            "CSRF cookies are secure (HTTPS only)",
            "ERROR: CSRF_COOKIE_SECURE is False. CSRF tokens can be stolen!",
            severity='error'
        )

        # HSTS
        self.check(
            "HSTS Configuration",
            settings.SECURE_HSTS_SECONDS > 0,
            f"HSTS enabled for {settings.SECURE_HSTS_SECONDS} seconds",
            "WARNING: HSTS not configured. Consider enabling for production.",
            severity='warning'
        )

        # CSRF Trusted Origins
        self.warn(
            "CSRF Trusted Origins",
            hasattr(settings, 'CSRF_TRUSTED_ORIGINS') and len(settings.CSRF_TRUSTED_ORIGINS) > 0,
            f"CSRF trusted origins configured: {len(settings.CSRF_TRUSTED_ORIGINS)}",
            "CSRF_TRUSTED_ORIGINS not set (may be needed for reverse proxy)"
        )

        print()

    def validate_database(self):
        """Validate database configuration."""
        print(f"{Colors.BLUE}💾 Validating Database Settings...{Colors.END}")

        db_config = settings.DATABASES.get('default', {})

        # Database engine
        self.check(
            "Database Engine",
            'postgresql' in db_config.get('ENGINE', '').lower(),
            f"Using PostgreSQL: {db_config.get('ENGINE')}",
            "ERROR: Not using PostgreSQL. SQLite is not suitable for production!",
            severity='error'
        )

        # Database host
        self.check(
            "Database Host",
            db_config.get('HOST') not in ['', 'localhost', '127.0.0.1'],
            f"Database host: {db_config.get('HOST')}",
            "WARNING: Database appears to be on localhost. Consider managed database.",
            severity='warning'
        )

        # SSL mode
        ssl_mode = db_config.get('OPTIONS', {}).get('sslmode')
        self.warn(
            "Database SSL",
            ssl_mode in ['require', 'verify-ca', 'verify-full'],
            f"Database SSL mode: {ssl_mode}",
            "Database SSL not configured (recommended for production)"
        )

        print()

    def validate_cache(self):
        """Validate cache configuration."""
        print(f"{Colors.BLUE}⚡ Validating Cache Settings...{Colors.END}")

        cache_config = settings.CACHES.get('default', {})
        backend = cache_config.get('BACKEND', '')

        # Should use Redis in production
        self.warn(
            "Cache Backend",
            'redis' in backend.lower(),
            f"Using Redis cache: {backend}",
            f"Using local memory cache. Redis recommended for production."
        )

        print()

    def validate_email(self):
        """Validate email configuration."""
        print(f"{Colors.BLUE}📧 Validating Email Settings...{Colors.END}")

        # Email backend
        self.warn(
            "Email Backend",
            'console' not in settings.EMAIL_BACKEND.lower(),
            f"Email backend configured: {settings.EMAIL_BACKEND}",
            "Using console email backend (emails won't be sent)"
        )

        # Default from email
        self.check(
            "Default From Email",
            settings.DEFAULT_FROM_EMAIL and '@' in settings.DEFAULT_FROM_EMAIL,
            f"From email: {settings.DEFAULT_FROM_EMAIL}",
            "ERROR: DEFAULT_FROM_EMAIL not configured",
            severity='error'
        )

        # Portal base URL
        self.check(
            "Portal Base URL",
            settings.PORTAL_BASE_URL and settings.PORTAL_BASE_URL.startswith('https://'),
            f"Portal URL: {settings.PORTAL_BASE_URL}",
            "ERROR: PORTAL_BASE_URL not configured or not HTTPS (email links will break)",
            severity='error'
        )

        print()

    def validate_phi_compliance(self):
        """Validate PHI/HIPAA compliance settings."""
        print(f"{Colors.BLUE}🏥 Validating PHI Compliance...{Colors.END}")

        # Check if handling real PHI
        real_data_mode = getattr(settings, 'REAL_DATA_MODE', False)

        if real_data_mode:
            # Encryption key required
            encryption_key = getattr(settings, 'FIELD_ENCRYPTION_KEY', '')
            self.check(
                "Field Encryption Key",
                len(encryption_key) >= 32,
                "Field encryption key configured (PHI protection enabled)",
                "CRITICAL: REAL_DATA_MODE=True but FIELD_ENCRYPTION_KEY not set!",
                severity='critical'
            )
        else:
            self.warn(
                "Real Data Mode",
                False,  # Always show this as info
                "REAL_DATA_MODE=False (using synthetic data)",
                "REAL_DATA_MODE=False (ensure this is correct for your deployment)"
            )

        # Audit logging
        self.check(
            "Audit Logging",
            'auditlog' in settings.INSTALLED_APPS,
            "Audit logging enabled (HIPAA compliance)",
            "ERROR: Audit logging not enabled",
            severity='error'
        )

        print()

    def validate_deployment_checks(self):
        """Run Django's deployment check."""
        print(f"{Colors.BLUE}✅ Running Django Deployment Checks...{Colors.END}")

        # Capture Django check output
        output = StringIO()
        try:
            call_command('check', '--deploy', stdout=output, stderr=output)
            output_str = output.getvalue()

            # Count warnings
            warning_count = output_str.count('?:')

            if warning_count == 0:
                self.results.append(
                    ValidationResult(
                        "Django Deployment Check",
                        'pass',
                        "No Django deployment warnings",
                        'info'
                    )
                )
            else:
                self.results.append(
                    ValidationResult(
                        "Django Deployment Check",
                        'warn',
                        f"{warning_count} Django deployment warnings (see above)",
                        'warning'
                    )
                )
                self.warnings += 1

        except Exception as e:
            self.results.append(
                ValidationResult(
                    "Django Deployment Check",
                    'fail',
                    f"Error running deployment check: {str(e)}",
                    'error'
                )
            )
            self.errors += 1

        print()

    def print_results(self):
        """Print validation results."""
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}Validation Results{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        # Print all results
        for result in self.results:
            if result.status == 'pass':
                icon = f"{Colors.GREEN}✓{Colors.END}"
                color = Colors.GREEN
            elif result.status == 'warn':
                icon = f"{Colors.YELLOW}⚠{Colors.END}"
                color = Colors.YELLOW
            else:  # fail
                if result.severity == 'critical':
                    icon = f"{Colors.RED}✗{Colors.END}"
                    color = Colors.RED
                else:
                    icon = f"{Colors.RED}✗{Colors.END}"
                    color = Colors.RED

            print(f"{icon} {result.name}: {color}{result.message}{Colors.END}")

        # Print summary
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}Summary{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")

        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == 'pass')

        print(f"Total Checks: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")

        if self.critical_failures > 0:
            print(f"{Colors.RED}{Colors.BOLD}Critical Failures: {self.critical_failures}{Colors.END}")
        if self.errors > 0:
            print(f"{Colors.RED}Errors: {self.errors}{Colors.END}")
        if self.warnings > 0:
            print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")

        print()

    def get_exit_code(self):
        """Get exit code based on validation results."""
        if self.critical_failures > 0:
            print(f"{Colors.RED}{Colors.BOLD}DEPLOYMENT BLOCKED:{Colors.END} ")
            print(f"{Colors.RED}Critical security issues must be fixed before deployment.{Colors.END}\n")
            return 1
        elif self.errors > 0:
            print(f"{Colors.RED}{Colors.BOLD}DEPLOYMENT NOT RECOMMENDED:{Colors.END} ")
            print(f"{Colors.RED}Security errors detected. Fix before deploying to production.{Colors.END}\n")
            return 1
        elif self.warnings > 0:
            print(f"{Colors.YELLOW}{Colors.BOLD}DEPLOYMENT ALLOWED WITH CAUTION:{Colors.END} ")
            print(f"{Colors.YELLOW}Warnings detected. Review before deploying to production.{Colors.END}\n")
            return 2
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ READY FOR PRODUCTION DEPLOYMENT{Colors.END}")
            print(f"{Colors.GREEN}All security checks passed!{Colors.END}\n")
            return 0


def main():
    """Main entry point."""
    validator = ProductionValidator()
    exit_code = validator.validate_all()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

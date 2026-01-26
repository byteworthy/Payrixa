"""
Management command to validate monitoring and observability configuration.

Usage:
    python manage.py validate_monitoring [--strict]

This command runs all monitoring checks and reports on:
- Prometheus metrics configuration
- Sentry error tracking
- Logging configuration
- Celery monitoring
- Redis connectivity
- Required environment variables

Exit codes:
- 0: All checks passed
- 1: Critical errors found
- 2: Warnings found (--strict mode)

Related: Phase 3 - DevOps Monitoring & Metrics (Task #5)
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from io import StringIO
import sys


class Command(BaseCommand):
    help = "Validate monitoring and observability configuration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Fail on warnings (treat warnings as errors)",
        )
        parser.add_argument(
            "--deploy",
            action="store_true",
            help="Run deployment checks (includes security checks)",
        )

    def handle(self, *args, **options):
        strict = options["strict"]
        deploy = options["deploy"]

        self.stdout.write(self.style.SUCCESS("Monitoring Configuration Validation"))
        self.stdout.write("=" * 60)

        # Run Django system checks
        self.stdout.write("\nRunning monitoring checks...")

        check_args = []
        if deploy:
            check_args.append("--deploy")
        else:
            # Run deploy checks to include monitoring checks
            check_args.append("--deploy")

        output = StringIO()
        try:
            call_command("check", *check_args, stdout=output, stderr=output)
            check_output = output.getvalue()
        except SystemExit as e:
            check_output = output.getvalue()

        # Parse results
        lines = check_output.split("\n")

        error_count = 0
        warning_count = 0
        info_count = 0

        errors = []
        warnings = []
        infos = []

        for line in lines:
            if not line.strip():
                continue

            if line.startswith("ERROR") or ": (monitoring.E" in line:
                error_count += 1
                errors.append(line)
            elif line.startswith("WARNING") or ": (monitoring.W" in line:
                warning_count += 1
                warnings.append(line)
            elif line.startswith("INFO") or ": (monitoring.I" in line:
                info_count += 1
                infos.append(line)

        # Display results
        if errors:
            self.stdout.write(f"\n{self.style.ERROR('ERRORS')} ({error_count}):")
            for error in errors:
                self.stdout.write(f"  {self.style.ERROR('✗')} {error}")

        if warnings:
            self.stdout.write(f"\n{self.style.WARNING('WARNINGS')} ({warning_count}):")
            for warning in warnings:
                self.stdout.write(f"  {self.style.WARNING('⚠')} {warning}")

        if infos:
            self.stdout.write(f"\n{self.style.SUCCESS('INFO')} ({info_count}):")
            for info in infos:
                self.stdout.write(f"  {self.style.SUCCESS('ℹ')} {info}")

        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("Summary:")
        self.stdout.write(f"  Errors:   {error_count}")
        self.stdout.write(f"  Warnings: {warning_count}")
        self.stdout.write(f"  Info:     {info_count}")

        # Get monitoring status
        from upstream.monitoring_checks import get_monitoring_status

        status = get_monitoring_status()

        self.stdout.write("\nMonitoring Components:")
        for component, is_healthy in status.items():
            if component == "overall_status":
                continue

            if is_healthy is None:
                icon = "○"
                style = self.style.WARNING
                status_text = "disabled"
            elif is_healthy:
                icon = "✓"
                style = self.style.SUCCESS
                status_text = "healthy"
            else:
                icon = "✗"
                style = self.style.ERROR
                status_text = "unhealthy"

            self.stdout.write(f"  {style(icon)} {component}: {status_text}")

        # Overall status
        overall = status["overall_status"]
        if overall == "healthy":
            self.stdout.write(
                f"\n{self.style.SUCCESS('✓ Overall Status: HEALTHY')}"
            )
            exit_code = 0
        elif overall == "degraded":
            self.stdout.write(
                f"\n{self.style.WARNING('⚠ Overall Status: DEGRADED')}"
            )
            self.stdout.write(
                "  Some optional monitoring components are not configured."
            )
            exit_code = 0 if not strict else 2
        else:
            self.stdout.write(
                f"\n{self.style.ERROR('✗ Overall Status: UNHEALTHY')}"
            )
            self.stdout.write(
                "  Critical monitoring components are not working properly."
            )
            exit_code = 1

        # Exit with appropriate code
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Validation FAILED: {error_count} error(s) found"
                )
            )
            sys.exit(1)
        elif warning_count > 0 and strict:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠ Validation FAILED (strict mode): {warning_count} warning(s) found"
                )
            )
            sys.exit(2)
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✓ Validation PASSED")
            )
            sys.exit(exit_code)

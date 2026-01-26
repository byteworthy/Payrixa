"""
Management command to clean up old log files based on retention policies.

Usage:
    python manage.py cleanup_logs [--dry-run]

This command:
- Deletes log files older than their retention period
- Respects HIPAA-compliant retention policies:
  - DEBUG: 7 days
  - INFO: 30 days
  - WARNING/ERROR: 90 days
  - Audit: 7 years (2555 days)

Related: TECH-DEBT Phase 3 - DevOps Monitoring & Metrics
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from upstream.logging_config import cleanup_old_logs, get_log_statistics


class Command(BaseCommand):
    help = "Clean up old log files based on retention policies"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get log directory
        log_dir = Path(settings.BASE_DIR) / "logs"

        if not log_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Log directory does not exist: {log_dir}")
            )
            return

        self.stdout.write(self.style.SUCCESS("Log Cleanup Tool"))
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No files will be deleted")
            )

        # Show current statistics
        self.stdout.write("\nCurrent log statistics:")
        stats_before = get_log_statistics(log_dir)
        self.stdout.write(f"  Total files: {stats_before['total_files']}")
        self.stdout.write(f"  Total size: {stats_before['total_size_mb']:.2f} MB")

        # Run cleanup
        self.stdout.write("\nRunning cleanup...")
        cleanup_stats = cleanup_old_logs(log_dir, dry_run=dry_run)

        # Display results
        self.stdout.write("\nCleanup Results:")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Files deleted: {cleanup_stats['files_deleted']}")
        self.stdout.write(
            f"Space freed: {cleanup_stats['bytes_freed'] / (1024 * 1024):.2f} MB"
        )

        if cleanup_stats["errors"]:
            self.stdout.write(
                self.style.ERROR(
                    f"\nErrors encountered: {len(cleanup_stats['errors'])}"
                )
            )
            for error in cleanup_stats["errors"]:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo errors encountered"))

        # Show statistics after cleanup
        if not dry_run:
            self.stdout.write("\nLog statistics after cleanup:")
            stats_after = get_log_statistics(log_dir)
            self.stdout.write(f"  Total files: {stats_after['total_files']}")
            self.stdout.write(f"  Total size: {stats_after['total_size_mb']:.2f} MB")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a dry run. Run without --dry-run to actually delete files."
                )
            )

"""
Management command to archive old log files by compressing them.

Usage:
    python manage.py archive_logs [--dry-run]

This command:
- Compresses log files older than 7 days using gzip
- Moves compressed files to logs/archive/ directory
- Reduces disk usage while maintaining HIPAA compliance
- Typical compression ratio: 90-95% size reduction

Related: TECH-DEBT Phase 3 - DevOps Monitoring & Metrics
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from upstream.logging_config import archive_logs, get_log_statistics


class Command(BaseCommand):
    help = "Archive old log files by compressing them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without actually archiving",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get log directories
        log_dir = Path(settings.BASE_DIR) / "logs"
        archive_dir = log_dir / "archive"

        if not log_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Log directory does not exist: {log_dir}")
            )
            return

        # Ensure archive directory exists
        archive_dir.mkdir(exist_ok=True)

        self.stdout.write(self.style.SUCCESS("Log Archival Tool"))
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No files will be archived")
            )

        # Show current statistics
        self.stdout.write("\nCurrent log statistics:")
        stats_before = get_log_statistics(log_dir)
        self.stdout.write(f"  Total files: {stats_before['total_files']}")
        self.stdout.write(f"  Total size: {stats_before['total_size_mb']:.2f} MB")

        # Run archival
        self.stdout.write(
            "\nArchiving log files older than 7 days (compressing with gzip)..."
        )
        archive_stats = archive_logs(log_dir, archive_dir, dry_run=dry_run)

        # Display results
        self.stdout.write("\nArchival Results:")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Files archived: {archive_stats['files_archived']}")

        if not dry_run and archive_stats["bytes_before"] > 0:
            self.stdout.write(
                f"Size before: {archive_stats['bytes_before'] / (1024 * 1024):.2f} MB"
            )
            self.stdout.write(
                f"Size after: {archive_stats['bytes_after'] / (1024 * 1024):.2f} MB"
            )
            self.stdout.write(
                f"Compression ratio: {archive_stats['compression_ratio']:.1f}%"
            )
            self.stdout.write(
                f"Space saved: {(archive_stats['bytes_before'] - archive_stats['bytes_after']) / (1024 * 1024):.2f} MB"
            )

        if archive_stats["errors"]:
            self.stdout.write(
                self.style.ERROR(
                    f"\nErrors encountered: {len(archive_stats['errors'])}"
                )
            )
            for error in archive_stats["errors"]:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
        else:
            self.stdout.write(self.style.SUCCESS("\nNo errors encountered"))

        # Show statistics after archival
        if not dry_run:
            self.stdout.write("\nLog statistics after archival:")
            stats_after = get_log_statistics(log_dir)
            self.stdout.write(f"  Total files: {stats_after['total_files']}")
            self.stdout.write(f"  Total size: {stats_after['total_size_mb']:.2f} MB")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\nThis was a dry run. Run without --dry-run to actually archive files."
                )
            )

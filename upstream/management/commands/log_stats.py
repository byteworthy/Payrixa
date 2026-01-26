"""
Management command to show log file statistics.

Usage:
    python manage.py log_stats

This command displays:
- Total number of log files
- Total disk usage
- Breakdown by log type
- Oldest and newest log files

Related: TECH-DEBT Phase 3 - DevOps Monitoring & Metrics
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from upstream.logging_config import get_log_statistics, get_log_retention_days


class Command(BaseCommand):
    help = "Show log file statistics"

    def handle(self, *args, **options):
        # Get log directory
        log_dir = Path(settings.BASE_DIR) / "logs"

        if not log_dir.exists():
            self.stdout.write(
                self.style.WARNING(f"Log directory does not exist: {log_dir}")
            )
            return

        self.stdout.write(self.style.SUCCESS("Log Statistics"))
        self.stdout.write("=" * 60)

        # Get statistics
        stats = get_log_statistics(log_dir)

        # Overall statistics
        self.stdout.write("\nOverall Statistics:")
        self.stdout.write(f"  Total files: {stats['total_files']}")
        self.stdout.write(
            f"  Total size: {stats['total_size_mb']:.2f} MB "
            f"({stats['total_size_bytes']:,} bytes)"
        )

        # Breakdown by type
        if stats["files_by_type"]:
            self.stdout.write("\nBreakdown by Log Type:")
            for log_type, type_stats in sorted(stats["files_by_type"].items()):
                size_mb = type_stats["size_bytes"] / (1024 * 1024)
                self.stdout.write(
                    f"  {log_type:20s}: {type_stats['count']:3d} files, "
                    f"{size_mb:8.2f} MB"
                )

        # Age information
        if stats["oldest_log"]:
            self.stdout.write("\nAge Information:")
            self.stdout.write(
                f"  Oldest log: {stats['oldest_log']['name']} "
                f"({stats['oldest_log']['date']})"
            )
        if stats["newest_log"]:
            self.stdout.write(
                f"  Newest log: {stats['newest_log']['name']} "
                f"({stats['newest_log']['date']})"
            )

        # Retention policies
        self.stdout.write("\nRetention Policies:")
        self.stdout.write(f"  DEBUG logs:   {get_log_retention_days('DEBUG')} days")
        self.stdout.write(f"  INFO logs:    {get_log_retention_days('INFO')} days")
        self.stdout.write(f"  WARNING logs: {get_log_retention_days('WARNING')} days")
        self.stdout.write(f"  ERROR logs:   {get_log_retention_days('ERROR')} days")
        self.stdout.write("  Audit logs:   2555 days (7 years - HIPAA requirement)")

        # Recommendations
        self.stdout.write("\nMaintenance Commands:")
        self.stdout.write("  python manage.py cleanup_logs    # Delete old logs")
        self.stdout.write("  python manage.py archive_logs    # Compress old logs")
        self.stdout.write("  python manage.py log_stats       # Show this report")

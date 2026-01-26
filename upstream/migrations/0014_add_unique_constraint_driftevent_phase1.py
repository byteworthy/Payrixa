"""
Phase 1 of 2: Add unique index concurrently for DriftEvent.

This migration creates a unique index using PostgreSQL's CONCURRENTLY option,
which allows the index to be built without blocking reads or writes to the table.

Part of DB-02: Implement unique constraints for data integrity.
"""
from django.db import migrations, connection


def create_unique_index(apps, schema_editor):
    """Create unique index with database-specific SQL."""
    if connection.vendor == "postgresql":
        # PostgreSQL: Use CONCURRENTLY for zero-downtime
        schema_editor.execute(
            """
            CREATE UNIQUE INDEX CONCURRENTLY driftevent_signal_uniq_idx
            ON upstream_driftevent (customer_id, report_run_id, payer, cpt_group, drift_type);
        """
        )
    else:
        # SQLite/other databases: Standard unique index
        schema_editor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS driftevent_signal_uniq_idx
            ON upstream_driftevent (customer_id, report_run_id, payer, cpt_group, drift_type);
        """
        )


def drop_unique_index(apps, schema_editor):
    """Drop unique index with database-specific SQL."""
    if connection.vendor == "postgresql":
        schema_editor.execute(
            """
            DROP INDEX CONCURRENTLY IF EXISTS driftevent_signal_uniq_idx;
        """
        )
    else:
        schema_editor.execute(
            """
            DROP INDEX IF EXISTS driftevent_signal_uniq_idx;
        """
        )


class Migration(migrations.Migration):
    """
    Zero-downtime migration: Creates unique index concurrently.

    IMPORTANT: atomic = False is required for CONCURRENTLY operations.
    PostgreSQL cannot run CREATE INDEX CONCURRENTLY inside a transaction.
    """

    atomic = False  # Required for CONCURRENTLY operations

    dependencies = [
        (
            "upstream",
            "0013_claimvalidationhistory_cvh_error_count_nonnegative_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(create_unique_index, drop_unique_index),
    ]

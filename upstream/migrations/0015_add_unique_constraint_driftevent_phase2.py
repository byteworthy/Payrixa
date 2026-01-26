"""
Phase 2 of 2: Convert index to unique constraint for DriftEvent.

This migration uses SeparateDatabaseAndState to:
1. Update Django's model state with the UniqueConstraint
2. Use PostgreSQL's "UNIQUE USING INDEX" to attach constraint to existing index

The existing index from phase 1 is promoted to a constraint, which is a fast
metadata-only operation that doesn't rebuild the index.

Part of DB-02: Implement unique constraints for data integrity.
"""
from django.db import migrations, models, connection


def add_constraint(apps, schema_editor):
    """Add unique constraint with database-specific SQL."""
    if connection.vendor == "postgresql":
        # PostgreSQL: Use existing index to create constraint (fast)
        schema_editor.execute(
            """
            ALTER TABLE upstream_driftevent
            ADD CONSTRAINT driftevent_unique_signal
            UNIQUE USING INDEX driftevent_signal_uniq_idx;
        """
        )
    # SQLite: Unique index already enforces uniqueness, no constraint needed


def drop_constraint(apps, schema_editor):
    """Drop unique constraint with database-specific SQL."""
    if connection.vendor == "postgresql":
        schema_editor.execute(
            """
            ALTER TABLE upstream_driftevent
            DROP CONSTRAINT IF EXISTS driftevent_unique_signal;

            CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS driftevent_signal_uniq_idx
            ON upstream_driftevent (customer_id, report_run_id, payer, cpt_group, drift_type);
        """
        )
    # SQLite: Nothing to drop


class Migration(migrations.Migration):
    """
    Zero-downtime migration: Converts existing index to constraint.

    Uses SeparateDatabaseAndState to keep Django's model state in sync
    with the actual database schema while using PostgreSQL-specific SQL.
    """

    dependencies = [
        ("upstream", "0014_add_unique_constraint_driftevent_phase1"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Update Django's internal state to know about the constraint
                migrations.AddConstraint(
                    model_name="driftevent",
                    constraint=models.UniqueConstraint(
                        fields=[
                            "customer",
                            "report_run",
                            "payer",
                            "cpt_group",
                            "drift_type",
                        ],
                        name="driftevent_unique_signal",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_constraint, drop_constraint),
            ],
        ),
    ]

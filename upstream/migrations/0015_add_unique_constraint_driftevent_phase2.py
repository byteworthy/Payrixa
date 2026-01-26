"""
Phase 2 of 2: Convert index to unique constraint for DriftEvent.

This migration uses SeparateDatabaseAndState to:
1. Update Django's model state with the UniqueConstraint
2. Use PostgreSQL's "UNIQUE USING INDEX" to attach constraint to existing index

The existing index from phase 1 is promoted to a constraint, which is a fast
metadata-only operation that doesn't rebuild the index.

Part of DB-02: Implement unique constraints for data integrity.
"""
from django.db import migrations, models


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
                        fields=["customer", "report_run", "payer", "cpt_group", "drift_type"],
                        name="driftevent_unique_signal",
                    ),
                ),
            ],
            database_operations=[
                # Use existing index to create constraint (fast metadata operation)
                # PostgreSQL's "UNIQUE USING INDEX" promotes an existing unique index
                # to a constraint without rebuilding it
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE upstream_driftevent
                        ADD CONSTRAINT driftevent_unique_signal
                        UNIQUE USING INDEX driftevent_signal_uniq_idx;
                    """,
                    reverse_sql="""
                        ALTER TABLE upstream_driftevent
                        DROP CONSTRAINT IF EXISTS driftevent_unique_signal;
                        -- Note: Index is automatically dropped when constraint is dropped
                        -- if it was created from the index. We recreate it for rollback.
                        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS driftevent_signal_uniq_idx
                        ON upstream_driftevent (customer_id, report_run_id, payer, cpt_group, drift_type);
                    """,
                ),
            ],
        ),
    ]

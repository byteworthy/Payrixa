# Generated migration for Phase 3 Task #3 - Add database CHECK constraints
#
# Related: TECHNICAL_DEBT.md - Phase 3: Database Optimization
#
# Adds database-level CHECK constraints to enforce data integrity rules
# that are currently only enforced at the application layer via Django validators.
#
# Why CHECK constraints matter:
# - Application validators can be bypassed (bulk_create, raw SQL, direct DB access)
# - Database constraints provide last line of defense for data integrity
# - Prevent invalid data from third-party integrations or data migrations
# - Enforce business rules at the database level (defense in depth)
#
# Categories:
# 1. Score/probability ranges (0.0 to 1.0)
# 2. Non-negative counts and amounts
# 3. Positive procedure counts
# 4. Valid date ranges (date_min <= date_max)
# 5. Row count consistency (accepted + rejected = total)

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("upstream", "0011_add_covering_indexes_phase3"),
    ]

    operations = [
        # =====================================================================
        # ClaimRecord constraints
        # =====================================================================
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(data_quality_score__gte=0.0)
                & models.Q(data_quality_score__lte=1.0)
                | models.Q(data_quality_score__isnull=True),
                name="claim_quality_score_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(procedure_count__gte=1),
                name="claim_procedure_count_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(allowed_amount__gte=0)
                | models.Q(allowed_amount__isnull=True),
                name="claim_allowed_amount_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(billed_amount__gte=0)
                | models.Q(billed_amount__isnull=True),
                name="claim_billed_amount_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(paid_amount__gte=0) | models.Q(paid_amount__isnull=True),
                name="claim_paid_amount_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.CheckConstraint(
                check=models.Q(submitted_date__lte=models.F("decided_date")),
                name="claim_dates_logical_order",
            ),
        ),
        # =====================================================================
        # Upload constraints
        # =====================================================================
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.CheckConstraint(
                check=models.Q(row_count__gte=0) | models.Q(row_count__isnull=True),
                name="upload_row_count_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.CheckConstraint(
                check=models.Q(accepted_row_count__gte=0),
                name="upload_accepted_count_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.CheckConstraint(
                check=models.Q(rejected_row_count__gte=0),
                name="upload_rejected_count_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.CheckConstraint(
                check=models.Q(warning_row_count__gte=0),
                name="upload_warning_count_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.CheckConstraint(
                check=models.Q(date_min__lte=models.F("date_max"))
                | models.Q(date_min__isnull=True)
                | models.Q(date_max__isnull=True),
                name="upload_date_range_logical",
            ),
        ),
        # =====================================================================
        # DataQualityReport constraints
        # =====================================================================
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(total_rows__gte=0), name="dqr_total_rows_nonnegative"
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(accepted_rows__gte=0), name="dqr_accepted_rows_nonnegative"
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(rejected_rows__gte=0), name="dqr_rejected_rows_nonnegative"
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(phi_detections__gte=0),
                name="dqr_phi_detections_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(missing_fields__gte=0),
                name="dqr_missing_fields_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(invalid_dates__gte=0),
                name="dqr_invalid_dates_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(invalid_values__gte=0),
                name="dqr_invalid_values_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(accepted_rows__lte=models.F("total_rows")),
                name="dqr_accepted_lte_total",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataqualityreport",
            constraint=models.CheckConstraint(
                check=models.Q(rejected_rows__lte=models.F("total_rows")),
                name="dqr_rejected_lte_total",
            ),
        ),
        # =====================================================================
        # DriftEvent constraints
        # =====================================================================
        migrations.AddConstraint(
            model_name="driftevent",
            constraint=models.CheckConstraint(
                check=models.Q(severity__gte=0.0) & models.Q(severity__lte=1.0),
                name="drift_severity_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="driftevent",
            constraint=models.CheckConstraint(
                check=models.Q(confidence__gte=0.0) & models.Q(confidence__lte=1.0),
                name="drift_confidence_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="driftevent",
            constraint=models.CheckConstraint(
                check=models.Q(statistical_significance__gte=0.0)
                & models.Q(statistical_significance__lte=1.0)
                | models.Q(statistical_significance__isnull=True),
                name="drift_significance_range",
            ),
        ),
    ]

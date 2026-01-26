# Generated manually for HIGH-15: Add NOT NULL constraints
# Django migrations would require interactive input, but since there are no
# existing NULL values (verified), we can safely add NOT NULL constraints.

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("upstream", "0007_add_date_indexes_high14"),
    ]

    operations = [
        # Upload.file_encoding: Remove null=True (inconsistent with default="utf-8")
        migrations.AlterField(
            model_name="upload",
            name="file_encoding",
            field=models.CharField(blank=True, default="utf-8", max_length=50),
        ),
        # ClaimRecord.processed_at: Remove null=True (inconsistent with auto_now_add=True)
        # Provide one-off default for migration safety (even though no NULL rows exist)
        migrations.AlterField(
            model_name="claimrecord",
            name="processed_at",
            field=models.DateTimeField(
                auto_now_add=True, db_index=True, default=django.utils.timezone.now
            ),
            preserve_default=False,  # Don't keep default after migration
        ),
        # ClaimRecord.updated_at: Remove null=True (inconsistent with auto_now=True)
        # Provide one-off default for migration safety (even though no NULL rows exist)
        migrations.AlterField(
            model_name="claimrecord",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True, default=django.utils.timezone.now
            ),
            preserve_default=False,  # Don't keep default after migration
        ),
    ]

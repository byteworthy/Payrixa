# Generated migration for HIGH-12: Add unique constraints on hash fields
# Ensures deduplication works correctly by preventing duplicate hashes

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("upstream", "0004_protect_upload_audit_trail_crit8"),
    ]

    operations = [
        # Add unique constraint on Upload.file_hash scoped to customer
        # Prevents duplicate file uploads within a customer's scope
        migrations.AddConstraint(
            model_name="upload",
            constraint=models.UniqueConstraint(
                fields=["customer", "file_hash"],
                condition=models.Q(file_hash__isnull=False),
                name="upload_unique_file_hash_per_customer",
            ),
        ),
        # Add unique constraint on ClaimRecord.source_data_hash
        # scoped to customer and upload
        # Prevents duplicate row processing within an upload
        migrations.AddConstraint(
            model_name="claimrecord",
            constraint=models.UniqueConstraint(
                fields=["customer", "upload", "source_data_hash"],
                condition=models.Q(source_data_hash__isnull=False),
                name="claim_unique_source_hash_per_upload",
            ),
        ),
    ]

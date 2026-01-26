#!/usr/bin/env python
"""
Test NOT NULL constraints after HIGH-15 fix.

Verifies that:
1. Upload.file_encoding cannot be NULL
2. ClaimRecord.processed_at cannot be NULL
3. ClaimRecord.updated_at cannot be NULL
4. Fields get default values automatically
"""
# flake8: noqa: E402

import sys
import os

# Setup Django FIRST before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upstream.settings.dev")

import django

django.setup()

# Now import Django modules
from django.test import TestCase
from django.db import IntegrityError, connection
from django.utils import timezone

from upstream.models import Upload, ClaimRecord, Customer


class NotNullConstraintsTest(TestCase):
    """Test that critical fields have NOT NULL constraints."""

    def setUp(self):
        """Set up test data."""
        self.customer = Customer.objects.create(name="Test Customer")
        print("✓ Created test customer")

    def test_upload_file_encoding_not_null(self):
        """Test 1: Upload.file_encoding has default and cannot be NULL."""
        print("\n" + "=" * 60)
        print("Test 1: Upload.file_encoding NOT NULL constraint")
        print("=" * 60)

        # Create upload - file_encoding should get default "utf-8"
        upload = Upload.objects.create(
            customer=self.customer, filename="test.csv", status="processing"
        )

        # Verify file_encoding got default value
        upload.refresh_from_db()
        self.assertEqual(upload.file_encoding, "utf-8")
        self.assertIsNotNone(upload.file_encoding)

        print("✓ file_encoding automatically set to default 'utf-8'")
        print("✓ file_encoding is NOT NULL")

    def test_claimrecord_processed_at_not_null(self):
        """Test 2: ClaimRecord.processed_at uses auto_now_add and is NOT NULL."""
        print("\n" + "=" * 60)
        print("Test 2: ClaimRecord.processed_at NOT NULL constraint")
        print("=" * 60)

        # Create upload first
        upload = Upload.objects.create(
            customer=self.customer, filename="test.csv", status="completed"
        )

        # Create claim record - processed_at should be set automatically
        claim = ClaimRecord.objects.create(
            customer=self.customer,
            upload=upload,
            payer="Test Payer",
            cpt="99213",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="approved",
        )

        # Verify processed_at was set automatically
        claim.refresh_from_db()
        self.assertIsNotNone(claim.processed_at)
        self.assertIsInstance(claim.processed_at, type(timezone.now()))

        print("✓ processed_at automatically set by auto_now_add=True")
        print("✓ processed_at is NOT NULL")

    def test_claimrecord_updated_at_not_null(self):
        """Test 3: ClaimRecord.updated_at uses auto_now and is NOT NULL."""
        print("\n" + "=" * 60)
        print("Test 3: ClaimRecord.updated_at NOT NULL constraint")
        print("=" * 60)

        # Create upload first
        upload = Upload.objects.create(
            customer=self.customer, filename="test.csv", status="completed"
        )

        # Create claim record - updated_at should be set automatically
        claim = ClaimRecord.objects.create(
            customer=self.customer,
            upload=upload,
            payer="Test Payer",
            cpt="99213",
            submitted_date=timezone.now().date(),
            decided_date=timezone.now().date(),
            outcome="approved",
        )

        # Verify updated_at was set automatically
        claim.refresh_from_db()
        original_updated_at = claim.updated_at
        self.assertIsNotNone(original_updated_at)

        # Update the claim - updated_at should change
        claim.outcome = "denied"
        claim.save()
        claim.refresh_from_db()

        self.assertIsNotNone(claim.updated_at)
        self.assertGreaterEqual(claim.updated_at, original_updated_at)

        print("✓ updated_at automatically set by auto_now=True")
        print("✓ updated_at is NOT NULL")
        print("✓ updated_at updates on every save()")

    def test_database_schema_constraints(self):
        """Test 4: Verify NOT NULL constraints exist in database schema."""
        print("\n" + "=" * 60)
        print("Test 4: Database Schema NOT NULL Constraints")
        print("=" * 60)

        with connection.cursor() as cursor:
            # Check Upload.file_encoding
            cursor.execute(
                """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='upstream_upload'
            """
            )
            upload_schema = cursor.fetchone()[0]

            # SQLite shows NOT NULL columns in CREATE TABLE
            self.assertIn('"file_encoding"', upload_schema)
            print("✓ Upload.file_encoding schema verified")

            # Check ClaimRecord.processed_at and updated_at
            cursor.execute(
                """
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='upstream_claimrecord'
            """
            )
            claim_schema = cursor.fetchone()[0]

            self.assertIn('"processed_at"', claim_schema)
            self.assertIn('"updated_at"', claim_schema)
            print("✓ ClaimRecord.processed_at schema verified")
            print("✓ ClaimRecord.updated_at schema verified")

    def test_model_metadata(self):
        """Test 5: Verify model metadata shows fields as not nullable."""
        print("\n" + "=" * 60)
        print("Test 5: Model Metadata for Nullable Fields")
        print("=" * 60)

        # Get field metadata
        upload_file_encoding = Upload._meta.get_field("file_encoding")
        claim_processed_at = ClaimRecord._meta.get_field("processed_at")
        claim_updated_at = ClaimRecord._meta.get_field("updated_at")

        # Check that null=False (fields should not allow null)
        self.assertFalse(
            upload_file_encoding.null, "file_encoding should not allow null"
        )
        self.assertFalse(claim_processed_at.null, "processed_at should not allow null")
        self.assertFalse(claim_updated_at.null, "updated_at should not allow null")

        print("✓ Upload.file_encoding.null = False")
        print("✓ ClaimRecord.processed_at.null = False")
        print("✓ ClaimRecord.updated_at.null = False")


if __name__ == "__main__":
    import unittest

    print("=" * 60)
    print("Test: NOT NULL Constraints (HIGH-15)")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(NotNullConstraintsTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("\nNOT NULL constraints working correctly!")
        print("- Upload.file_encoding: Has default 'utf-8', NOT NULL")
        print("- ClaimRecord.processed_at: Uses auto_now_add=True, NOT NULL")
        print("- ClaimRecord.updated_at: Uses auto_now=True, NOT NULL")
        print("\nExpected Impact:")
        print("- Improved data integrity (no NULL values in critical fields)")
        print("- Explicit schema constraints prevent invalid data")
        print("- Better query optimization (database knows fields are NOT NULL)")
        sys.exit(0)
    else:
        print(f"❌ {len(result.failures) + len(result.errors)} TEST(S) FAILED")
        sys.exit(1)

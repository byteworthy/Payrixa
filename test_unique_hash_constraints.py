#!/usr/bin/env python
"""
Test unique hash constraints after HIGH-12 fix.

Verifies that:
1. Upload.file_hash has unique constraint per customer
2. ClaimRecord.source_data_hash has unique constraint per upload
3. Null hashes are allowed (constraint only applies when hash is not null)
4. Different customers can have same hash (multi-tenancy)
"""
# flake8: noqa: E402

import sys
import os
from datetime import date

# Setup Django FIRST before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upstream.settings.dev")

import django

django.setup()

# Now import Django modules
from django.test import TestCase
from django.db import IntegrityError

from upstream.models import Customer, Upload, ClaimRecord


class UniqueHashConstraintsTest(TestCase):
    """Test that hash fields have unique constraints for deduplication."""

    def setUp(self):
        """Set up test data."""
        # Create two test customers for multi-tenancy testing
        self.customer1 = Customer.objects.create(name="Customer 1")
        self.customer2 = Customer.objects.create(name="Customer 2")
        print(f"✓ Created test customers: {self.customer1.name}, {self.customer2.name}")

    def test_upload_file_hash_unique_per_customer(self):
        """Test 1: Upload.file_hash is unique per customer."""
        print("\n" + "=" * 60)
        print("Test 1: Upload.file_hash Unique Constraint Per Customer")
        print("=" * 60)

        # Create first upload with hash
        upload1 = Upload.objects.create(
            customer=self.customer1,
            filename="test1.csv",
            file_hash="abc123def456",
            status="success",
        )
        print(f"✓ Created upload1 with hash: {upload1.file_hash}")

        # Try to create duplicate upload with same hash for same customer
        with self.assertRaises(IntegrityError) as context:
            Upload.objects.create(
                customer=self.customer1,
                filename="test2.csv",
                file_hash="abc123def456",  # Same hash
                status="success",
            )

        # Check that constraint was violated (error message varies by database)
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "unique constraint" in error_msg or "duplicate" in error_msg,
            f"Expected unique constraint error, got: {error_msg}",
        )
        print(
            f"✓ Duplicate hash for same customer correctly rejected: "
            f"{str(context.exception)[:100]}"
        )
        print("✓ Upload.file_hash unique constraint enforced successfully")

    def test_upload_file_hash_allows_different_customers(self):
        """Test 2: Same file_hash allowed for different customers (multi-tenancy)."""
        print("\n" + "=" * 60)
        print("Test 2: Same Hash Allowed for Different Customers")
        print("=" * 60)

        # Create upload for customer 1
        upload1 = Upload.objects.create(
            customer=self.customer1,
            filename="test1.csv",
            file_hash="shared_hash_123",
            status="success",
        )
        print(f"✓ Customer 1 upload created with hash: {upload1.file_hash}")

        # Create upload with same hash for customer 2 (should work)
        upload2 = Upload.objects.create(
            customer=self.customer2,
            filename="test2.csv",
            file_hash="shared_hash_123",  # Same hash, different customer
            status="success",
        )
        print(f"✓ Customer 2 upload created with same hash: {upload2.file_hash}")

        # Verify both exist
        self.assertEqual(
            Upload.all_objects.filter(file_hash="shared_hash_123").count(), 2
        )
        print("✓ Both uploads exist with same hash (different customers)")

    def test_upload_null_hash_allowed(self):
        """Test 3: Null file_hash values are allowed (constraint only applies when not null)."""
        print("\n" + "=" * 60)
        print("Test 3: Null file_hash Values Allowed")
        print("=" * 60)

        # Create multiple uploads with null hash (should work)
        upload1 = Upload.objects.create(
            customer=self.customer1,
            filename="test1.csv",
            file_hash=None,
            status="success",
        )
        upload2 = Upload.objects.create(
            customer=self.customer1,
            filename="test2.csv",
            file_hash=None,
            status="success",
        )
        upload3 = Upload.objects.create(
            customer=self.customer1,
            filename="test3.csv",
            file_hash=None,
            status="success",
        )

        print("✓ Created 3 uploads with null hash (no constraint violation)")

        # Verify all exist
        null_hash_uploads = Upload.all_objects.filter(
            customer=self.customer1, file_hash__isnull=True
        )
        self.assertEqual(null_hash_uploads.count(), 3)
        print(f"✓ All {null_hash_uploads.count()} uploads with null hash exist")

    def test_claimrecord_source_hash_unique_per_upload(self):
        """Test 4: ClaimRecord.source_data_hash is unique per upload."""
        print("\n" + "=" * 60)
        print("Test 4: ClaimRecord.source_data_hash Unique Per Upload")
        print("=" * 60)

        # Create upload
        upload = Upload.objects.create(
            customer=self.customer1, filename="test.csv", status="success"
        )
        print(f"✓ Created upload: {upload.id}")

        # Create first claim record with hash
        claim1 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload,
            payer="Blue Cross",
            cpt="99213",
            submitted_date=date(2024, 1, 15),
            decided_date=date(2024, 2, 10),
            outcome="PAID",
            source_data_hash="row_hash_abc123",
        )
        print(f"✓ Created claim1 with source_hash: {claim1.source_data_hash}")

        # Try to create duplicate claim with same hash in same upload
        with self.assertRaises(IntegrityError) as context:
            ClaimRecord.objects.create(
                customer=self.customer1,
                upload=upload,
                payer="Aetna",
                cpt="99214",
                submitted_date=date(2024, 1, 16),
                decided_date=date(2024, 2, 11),
                outcome="DENIED",
                source_data_hash="row_hash_abc123",  # Same hash in same upload
            )

        # Check that constraint was violated (error message varies by database)
        error_msg = str(context.exception).lower()
        self.assertTrue(
            "unique constraint" in error_msg or "duplicate" in error_msg,
            f"Expected unique constraint error, got: {error_msg}",
        )
        print(
            f"✓ Duplicate hash in same upload correctly rejected: "
            f"{str(context.exception)[:100]}"
        )
        print("✓ ClaimRecord.source_data_hash unique constraint enforced successfully")

    def test_claimrecord_source_hash_allows_different_uploads(self):
        """Test 5: Same source_data_hash allowed for different uploads."""
        print("\n" + "=" * 60)
        print("Test 5: Same Hash Allowed for Different Uploads")
        print("=" * 60)

        # Create two uploads
        upload1 = Upload.objects.create(
            customer=self.customer1, filename="test1.csv", status="success"
        )
        upload2 = Upload.objects.create(
            customer=self.customer1, filename="test2.csv", status="success"
        )
        print(f"✓ Created two uploads: {upload1.id}, {upload2.id}")

        # Create claim in first upload
        claim1 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload1,
            payer="Blue Cross",
            cpt="99213",
            submitted_date=date(2024, 1, 15),
            decided_date=date(2024, 2, 10),
            outcome="PAID",
            source_data_hash="shared_row_hash",
        )
        print(f"✓ Claim1 created in upload1 with hash: {claim1.source_data_hash}")

        # Create claim with same hash in second upload (should work)
        claim2 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload2,
            payer="Blue Cross",
            cpt="99213",
            submitted_date=date(2024, 1, 15),
            decided_date=date(2024, 2, 10),
            outcome="PAID",
            source_data_hash="shared_row_hash",  # Same hash, different upload
        )
        print(f"✓ Claim2 created in upload2 with same hash: {claim2.source_data_hash}")

        # Verify both exist
        claims_with_hash = ClaimRecord.all_objects.filter(
            source_data_hash="shared_row_hash"
        )
        self.assertEqual(claims_with_hash.count(), 2)
        print("✓ Both claims exist with same hash (different uploads)")

    def test_claimrecord_null_source_hash_allowed(self):
        """Test 6: Null source_data_hash values are allowed."""
        print("\n" + "=" * 60)
        print("Test 6: Null source_data_hash Values Allowed")
        print("=" * 60)

        # Create upload
        upload = Upload.objects.create(
            customer=self.customer1, filename="test.csv", status="success"
        )

        # Create multiple claims with null hash (should work)
        claim1 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload,
            payer="Blue Cross",
            cpt="99213",
            submitted_date=date(2024, 1, 15),
            decided_date=date(2024, 2, 10),
            outcome="PAID",
            source_data_hash=None,
        )
        claim2 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload,
            payer="Aetna",
            cpt="99214",
            submitted_date=date(2024, 1, 16),
            decided_date=date(2024, 2, 11),
            outcome="DENIED",
            source_data_hash=None,
        )
        claim3 = ClaimRecord.objects.create(
            customer=self.customer1,
            upload=upload,
            payer="Medicare",
            cpt="99215",
            submitted_date=date(2024, 1, 17),
            decided_date=date(2024, 2, 12),
            outcome="PAID",
            source_data_hash=None,
        )

        print("✓ Created 3 claim records with null hash (no constraint violation)")

        # Verify all exist
        null_hash_claims = ClaimRecord.all_objects.filter(
            upload=upload, source_data_hash__isnull=True
        )
        self.assertEqual(null_hash_claims.count(), 3)
        print(f"✓ All {null_hash_claims.count()} claims with null hash exist")

    def test_hash_index_performance(self):
        """Test 7: Verify hash fields have indexes for query performance."""
        print("\n" + "=" * 60)
        print("Test 7: Hash Field Indexes Exist")
        print("=" * 60)

        from django.db import connection

        # Get table indexes
        with connection.cursor() as cursor:
            # Check Upload indexes
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='upstream_upload' AND name LIKE '%hash%'"
            )
            upload_indexes = [row[0] for row in cursor.fetchall()]

            # Check ClaimRecord indexes
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND tbl_name='upstream_claimrecord' AND name LIKE '%hash%'"
            )
            claim_indexes = [row[0] for row in cursor.fetchall()]

        print(f"  Upload hash indexes: {upload_indexes}")
        print(f"  ClaimRecord hash indexes: {claim_indexes}")

        # Verify indexes exist (may vary by DB, but constraint itself should exist)
        self.assertGreater(
            len(upload_indexes) + len(claim_indexes),
            0,
            "Hash fields should have indexes",
        )
        print("✓ Hash fields have database indexes for performance")


if __name__ == "__main__":
    import unittest

    print("=" * 60)
    print("Test: Unique Hash Constraints (HIGH-12)")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(UniqueHashConstraintsTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("\nUnique hash constraints are working correctly!")
        print("- Upload.file_hash is unique per customer")
        print("- ClaimRecord.source_data_hash is unique per upload")
        print("- Null hashes are allowed (partial uniqueness)")
        print(
            "- Multi-tenancy is preserved (same hash for different customers/uploads)"
        )
        print("- Deduplication will now work reliably")
        sys.exit(0)
    else:
        print(f"❌ {len(result.failures) + len(result.errors)} TEST(S) FAILED")
        sys.exit(1)

#!/usr/bin/env python
"""
Test CSV upload functionality after HIGH-5 refactoring.

Verifies that the refactored process_csv_upload method works correctly.
"""
# flake8: noqa: E402

import sys
import os
from io import BytesIO
from datetime import date

# Setup Django FIRST before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upstream.settings.dev")

import django

django.setup()

# Now import Django modules
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import User

from upstream.models import Customer, ClaimRecord, Upload, DataQualityReport
from upstream.views import UploadsView


@override_settings(ALLOWED_HOSTS=["*"])
class CSVUploadRefactoringTest(TestCase):
    """Test that refactored CSV upload methods work correctly."""

    def setUp(self):
        """Set up test data."""
        # Create test customer
        self.customer = Customer.objects.create(name="Test CSV Upload Customer")
        print(f"✓ Created test customer: {self.customer.name}")

        # Create test user and assign to customer
        self.user = User.objects.create_user(
            username="test_upload_user", password="testpass123", is_staff=True
        )
        self.user.customer = self.customer
        self.user.save()
        print("✓ Created test user")

        # Create upload instance
        self.upload = Upload.objects.create(
            customer=self.customer, filename="test_refactoring.csv", status="processing"
        )
        print(f"✓ Created test upload: {self.upload.id}")

        self.factory = RequestFactory()
        self.view = UploadsView()

    def test_valid_csv_processing(self):
        """Test 1: Valid CSV data should be processed successfully."""
        csv_content = b"""payer,cpt,submitted_date,decided_date,outcome,allowed_amount
Blue Cross,99213,2024-01-15,2024-02-10,PAID,150.00
Aetna,99214,2024-01-16,2024-02-11,DENIED,
Medicare,99215,2024-01-17,2024-02-12,PAID,200.50"""

        csv_file = BytesIO(csv_content)
        csv_file.name = "test.csv"

        # Process CSV
        self.view.process_csv_upload(self.upload, csv_file)

        # Verify claim records created (use all_objects to bypass customer scoping)
        claims = ClaimRecord.all_objects.filter(upload=self.upload)
        self.assertEqual(claims.count(), 3, "Should create 3 claim records")
        print(f"✓ Test 1: Created {claims.count()} claim records")

        # Verify upload metadata
        self.assertEqual(self.upload.row_count, 3, "row_count should be 3")
        self.assertEqual(
            self.upload.date_min, date(2024, 1, 15), "date_min should be 2024-01-15"
        )
        self.assertEqual(
            self.upload.date_max, date(2024, 2, 12), "date_max should be 2024-02-12"
        )
        print("✓ Test 1: Upload metadata correct")

        # Verify quality report (use all_objects to bypass customer scoping)
        qr = DataQualityReport.all_objects.get(upload=self.upload)
        self.assertEqual(qr.total_rows, 3, "total_rows should be 3")
        self.assertEqual(qr.accepted_rows, 3, "accepted_rows should be 3")
        self.assertEqual(qr.rejected_rows, 0, "rejected_rows should be 0")
        print("✓ Test 1: Quality report created correctly")

    def test_partial_success_with_rejections(self):
        """Test 2: CSV with some invalid rows should accept valid ones."""
        csv_content = b"""payer,cpt,submitted_date,decided_date,outcome,allowed_amount
Blue Cross,99213,2024-01-15,2024-02-10,PAID,150.00
Aetna,99214,invalid-date,2024-02-11,DENIED,
Medicare,99215,2024-01-17,2024-02-12,PAID,200.50"""

        csv_file = BytesIO(csv_content)
        csv_file.name = "test_partial.csv"

        # Process CSV
        self.view.process_csv_upload(self.upload, csv_file)

        # Verify only valid claims created (use all_objects to bypass customer scoping)
        claims = ClaimRecord.all_objects.filter(upload=self.upload)
        self.assertEqual(
            claims.count(), 2, "Should create 2 claim records (1 rejected)"
        )
        print(f"✓ Test 2: Created {claims.count()} valid claim records")

        # Verify quality report tracks rejections (use all_objects to bypass customer scoping)
        qr = DataQualityReport.all_objects.get(upload=self.upload)
        self.assertEqual(qr.total_rows, 3, "total_rows should be 3")
        self.assertEqual(qr.accepted_rows, 2, "accepted_rows should be 2")
        self.assertEqual(qr.rejected_rows, 1, "rejected_rows should be 1")
        self.assertEqual(qr.invalid_dates, 1, "invalid_dates counter should be 1")
        # JSONField converts integer keys to strings
        self.assertIn("3", qr.rejection_details, "Row 3 should be in rejection_details")
        self.assertIn(
            "invalid-date",
            qr.rejection_details["3"],
            "Rejection should mention invalid-date",
        )
        print("✓ Test 2: Quality report tracks rejections correctly")

    def test_outcome_normalization(self):
        """Test 3: Outcome normalization works correctly."""
        csv_content = b"""payer,cpt,submitted_date,decided_date,outcome
Blue Cross,99213,2024-01-15,2024-02-10,APPROVED
Aetna,99214,2024-01-16,2024-02-11,REJECTED
Medicare,99215,2024-01-17,2024-02-12,UNKNOWN"""

        csv_file = BytesIO(csv_content)
        csv_file.name = "test_outcomes.csv"

        # Process CSV
        self.view.process_csv_upload(self.upload, csv_file)

        # Verify outcome normalization (use all_objects to bypass customer scoping)
        claims = ClaimRecord.all_objects.filter(upload=self.upload).order_by(
            "submitted_date"
        )
        self.assertEqual(claims[0].outcome, "PAID", "APPROVED should map to PAID")
        self.assertEqual(claims[1].outcome, "DENIED", "REJECTED should map to DENIED")
        self.assertEqual(claims[2].outcome, "OTHER", "UNKNOWN should map to OTHER")
        print(
            "✓ Test 3: Outcome normalization works (APPROVED→PAID, REJECTED→DENIED, UNKNOWN→OTHER)"
        )

        # Verify warning created for unusual outcome (use all_objects to bypass customer scoping)
        qr = DataQualityReport.all_objects.get(upload=self.upload)
        self.assertEqual(len(qr.warnings), 1, "Should have 1 warning")
        self.assertIn(
            "UNKNOWN", qr.warnings[0]["message"], "Warning should mention UNKNOWN"
        )
        print("✓ Test 3: Warning created for unusual outcome value")

    def test_missing_required_column(self):
        """Test 4: Missing required column should raise ValueError."""
        csv_content = b"""payer,cpt,submitted_date,decided_date
Blue Cross,99213,2024-01-15,2024-02-10"""

        csv_file = BytesIO(csv_content)
        csv_file.name = "test_missing_column.csv"

        # Should raise ValueError for missing 'outcome' column
        with self.assertRaises(ValueError) as context:
            self.view.process_csv_upload(self.upload, csv_file)

        self.assertIn("Missing required column: outcome", str(context.exception))
        print("✓ Test 4: Missing required column raises ValueError")


if __name__ == "__main__":
    import unittest

    print("=" * 60)
    print("Test: CSV Upload After HIGH-5 Refactoring")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(CSVUploadRefactoringTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("\nRefactored CSV upload methods work correctly!")
        print("The 161-line fat method is now split into focused, testable methods.")
        sys.exit(0)
    else:
        print(f"❌ {len(result.failures) + len(result.errors)} TEST(S) FAILED")
        sys.exit(1)

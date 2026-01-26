#!/usr/bin/env python
"""
Test date validation in ClaimRecordViewSet (HIGH-7)

Verifies that malformed dates return 400 Bad Request instead of 500 errors.
"""

import sys
import os
from datetime import date
from decimal import Decimal

# Setup Django FIRST before any imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "upstream.settings.dev")

import django

django.setup()

# Now import Django modules
from django.test import TestCase, override_settings
from django.contrib.auth.models import User

from upstream.models import Customer, ClaimRecord, Upload


@override_settings(ALLOWED_HOSTS=["*"])
class DateValidationTest(TestCase):
    """Test that malformed dates return 400 instead of 500."""

    def setUp(self):
        """Set up test data."""
        # Create test customer
        self.customer = Customer.objects.create(name="Test Date Validation Customer")
        print(f"✓ Created test customer: {self.customer.name}")

        # Create test user and assign to customer
        self.user = User.objects.create_user(
            username="test_api_user", password="testpass123", is_staff=True
        )
        self.user.customer = self.customer
        self.user.save()
        print("✓ Created test user")

        # Create test upload and claims
        upload = Upload.objects.create(
            customer=self.customer,
            status="completed",
            filename="test_validation.csv",
            row_count=5,
        )

        for i in range(5):
            ClaimRecord.objects.create(
                customer=self.customer,
                upload=upload,
                payer="Test Insurance",
                cpt="99213",
                submitted_date=date(2024, 1, i + 1),
                decided_date=date(2024, 1, i + 10),
                outcome="PAID",
                allowed_amount=Decimal("1000.00"),
            )
        print(f"✓ Created 5 test claims")

        # Authenticate client
        self.client.force_login(self.user)

    def test_valid_date_format(self):
        """Test 1: Valid date format should work."""
        response = self.client.get(
            "/api/claims/?start_date=2024-01-01&end_date=2024-01-31"
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Valid dates should return 200, got {response.status_code}",
        )
        print("✓ Test 1: Valid date format (YYYY-MM-DD) returns 200")

    def test_invalid_start_date(self):
        """Test 2: Invalid start_date should return 400."""
        response = self.client.get("/api/claims/?start_date=not-a-date")
        self.assertEqual(
            response.status_code,
            400,
            f"Invalid start_date should return 400, got {response.status_code}",
        )
        data = response.json()
        self.assertIn("start_date", data, "Response should include start_date error")
        print(
            f"✓ Test 2: Invalid start_date returns 400 with error: {data['start_date']}"
        )

    def test_invalid_end_date(self):
        """Test 3: Invalid end_date should return 400."""
        response = self.client.get("/api/claims/?end_date=2024-13-45")
        self.assertEqual(
            response.status_code,
            400,
            f"Invalid end_date should return 400, got {response.status_code}",
        )
        data = response.json()
        self.assertIn("end_date", data, "Response should include end_date error")
        print(f"✓ Test 3: Invalid end_date returns 400 with error: {data['end_date']}")

    def test_wrong_date_format(self):
        """Test 4: Invalid format (different separator) should return 400."""
        response = self.client.get("/api/claims/?start_date=2024/01/15")
        self.assertEqual(
            response.status_code,
            400,
            f"Wrong date format should return 400, got {response.status_code}",
        )
        print("✓ Test 4: Wrong date format (YYYY/MM/DD) returns 400")

    def test_malformed_date(self):
        """Test 5: Completely malformed date should return 400."""
        response = self.client.get("/api/claims/?start_date=abc123xyz")
        self.assertEqual(
            response.status_code,
            400,
            f"Malformed date should return 400, got {response.status_code}",
        )
        print("✓ Test 5: Malformed date returns 400")

    def test_valid_start_date_only(self):
        """Test 6: Valid single start_date parameter should work."""
        response = self.client.get("/api/claims/?start_date=2024-01-05")
        self.assertEqual(
            response.status_code,
            200,
            f"Valid start_date only should return 200, got {response.status_code}",
        )
        print("✓ Test 6: Single valid start_date parameter works")

    def test_valid_end_date_only(self):
        """Test 7: Valid end_date only should work."""
        response = self.client.get("/api/claims/?end_date=2024-01-15")
        self.assertEqual(
            response.status_code,
            200,
            f"Valid end_date only should return 200, got {response.status_code}",
        )
        print("✓ Test 7: Single valid end_date parameter works")


if __name__ == "__main__":
    import unittest

    print("=" * 60)
    print("Test: Date Validation in ClaimRecordViewSet (HIGH-7)")
    print("=" * 60)

    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(DateValidationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print("\nDate validation is working correctly!")
        print("Malformed dates now return 400 Bad Request instead of 500 errors.")
        sys.exit(0)
    else:
        print(f"❌ {len(result.failures)} TEST(S) FAILED")
        sys.exit(1)
